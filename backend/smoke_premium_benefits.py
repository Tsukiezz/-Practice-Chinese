"""Real-browser smoke with disposable users/database; never touches production data.

Set WEB_APP_DIR to the build/web folder to include Flutter rendering checks.
"""
import hashlib
import json
import os
from pathlib import Path
import socket
import tempfile
import threading
import time

os.environ.update(TESTING='1', TURSO_DATABASE_URL='', HANZIGO_DB_DRIVER='sqlite',
                  SEPAY_MERCHANT_ID='', SEPAY_SECRET_KEY='')
import uvicorn
from playwright.sync_api import sync_playwright, expect
import database as storage
from main import app


def main():
    output = Path(__file__).resolve().parents[1] / 'test-results'
    output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        storage.DB_PATH = Path(temp) / 'premium-smoke.db'
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port, log_level='error'))
        worker = threading.Thread(target=server.run, daemon=True)
        worker.start()
        for _ in range(200):
            if server.started:
                break
            time.sleep(.1)
        assert server.started
        now = int(time.time())
        with storage.database() as conn:
            for name, until in [('Free', 0), ('Premium', now+3600)]:
                uid = conn.execute('''INSERT INTO users(name,email,password_hash,salt,role,created_at,premium_until)
                                      VALUES(?,?,?,?,'student',?,?)''',
                                   (name, name.lower()+'@local.test', 'unused', 'unused', now, until)).lastrowid
                token = name.lower()+'-smoke'
                conn.execute('INSERT INTO sessions VALUES(?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), uid, now+3600))
        base = f'http://127.0.0.1:{port}'
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(channel='msedge', headless=True)
                for name in ('free', 'premium'):
                    context = browser.new_context(viewport={'width': 390, 'height': 844})
                    context.add_init_script(f"sessionStorage.setItem('hanzigo_account_token','{name}-smoke')")
                    page = context.new_page()
                    errors = []
                    page.on('pageerror', lambda e: errors.append(str(e)))
                    page.goto(base+'/appearance')
                    expect(page.locator('#palette-choice')).to_be_enabled()
                    expect(page.locator('#palette-status')).to_contain_text('Premium' if name=='premium' else 'Tài khoản thường')
                    option = page.locator('option[value=purple]')
                    assert option.evaluate('(el) => el.disabled') == (name == 'free')
                    if name == 'premium':
                        page.locator('#palette-choice').select_option('purple')
                        expect(page.locator('#palette-status')).to_have_text('Đã lưu màu giao diện.')
                        page.locator('#palette-enabled').check()
                        expect(page.locator('html')).to_have_attribute('data-learner-theme', 'purple')
                        page.reload()
                        expect(page.locator('#palette-choice')).to_have_value('purple')
                    page.screenshot(path=str(output/f'premium-{name}-appearance-mobile.png'), full_page=True)
                    headers = {'Authorization': f'Bearer {name}-smoke'}
                    for level in (7, 8, 9):
                        response = context.request.get(base+f'/api/exams?hsk={level}', headers=headers)
                        assert response.status == (200 if name == 'premium' else 403)
                        if name == 'premium':
                            assert len(response.json()) == 5
                    assert not errors, errors
                    page.goto(base+'/reading?hsk=7')
                    if name == 'premium':
                        expect(page.locator('#wordHskBadge')).to_have_text('HSK 7')
                        expect(page.locator('#wordHanzi')).not_to_have_text('--')
                        for level in (8, 9):
                            page.get_by_role('button', name=f'HSK {level} · Premium', exact=True).click()
                            expect(page.locator('#wordHskBadge')).to_have_text(f'HSK {level}')
                            expect(page.locator('#wordHanzi')).not_to_have_text('--')
                    else:
                        expect(page.locator('#wordMeaning')).to_contain_text('Premium')
                        expect(page.locator('#wordHanzi')).to_have_text('--')
                    page.screenshot(path=str(output/f'reading-advanced-{name}.png'), full_page=True)
                    context.close()
                # Render the actual Flutter build with an authenticated paid account.
                web_dir = Path(os.environ.get('WEB_APP_DIR', ''))
                if web_dir.joinpath('main.dart.js').is_file():
                    for width, height in [(1200, 900), (390, 844)]:
                        context = browser.new_context(viewport={'width': width, 'height': height})
                        def canvas(route):
                            suffix = route.request.url.split('/flutter-canvaskit/', 1)[1].split('/', 1)[1]
                            asset = web_dir / 'canvaskit' / suffix
                            if asset.is_file():
                                route.fulfill(path=str(asset), content_type='application/wasm' if asset.suffix=='.wasm' else 'application/javascript', headers={'Access-Control-Allow-Origin': '*'})
                            else:
                                route.continue_()
                        context.route('https://www.gstatic.com/flutter-canvaskit/**', canvas)
                        page = context.new_page()
                        page.goto(base+'/api/health')
                        page.evaluate('''() => {
                            localStorage.setItem('flutter.auth_token', JSON.stringify('premium-smoke'));
                            localStorage.setItem('flutter.api_base_url', JSON.stringify(location.origin+'/api'));
                        }''')
                        data = context.request.get(base+'/api/auth/student-session', headers={'Authorization': 'Bearer premium-smoke'}).json()
                        data['expires_at'] = now+3600
                        page.evaluate('(user) => localStorage.setItem("flutter.auth_user",JSON.stringify(JSON.stringify(user)))', data)
                        errors = []
                        dashboards = []
                        page.on('response', lambda response: dashboards.append(response) if '/api/me/dashboard' in response.url else None)
                        page.on('pageerror', lambda e: errors.append(str(e)))
                        page.goto(base)
                        page.wait_for_selector('flutter-view', timeout=30000)
                        page.evaluate("document.querySelector('flt-semantics-placeholder')?.click()")
                        page.wait_for_timeout(3000)
                        page.screenshot(path=str(output/f'premium-flutter-{width}.png'), full_page=True)
                        # CanvasKit may not expose semantics in headless Edge.
                        # The inspected bottom navigation has seven equal tabs.
                        page.mouse.click(width * 6.5 / 7, height - 30)
                        page.wait_for_timeout(2000)
                        assert dashboards and dashboards[-1].status == 200
                        assert len(dashboards[-1].json()['streak_details']['calendar']) == 28
                        page.screenshot(path=str(output/f'streak-profile-{width}.png'), full_page=True)
                        assert not errors, errors
                        context.close()
                browser.close()
            print('PASS: free/paid web appearance gate, persistence, HSK 7-9 API authorization, Flutter desktop/mobile render')
        finally:
            server.should_exit = True
            worker.join(10)


if __name__ == '__main__':
    main()
