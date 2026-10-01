"""Browser checks against an isolated database and a locally built Flutter app."""
import hashlib
import json
import os
from pathlib import Path
import socket
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
os.environ['TESTING'] = '1'
os.environ.setdefault('WEB_APP_DIR', str(ROOT.parents[2] / '.tools/theme-check/build/web'))
import uvicorn
from playwright.sync_api import sync_playwright, expect
import database as storage
from main import app


def main():
    with tempfile.TemporaryDirectory() as temp:
        storage.DB_PATH = Path(temp) / 'themes.db'
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0))
            port=sock.getsockname()[1]
        server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='error'))
        worker=threading.Thread(target=server.run,daemon=True)
        worker.start()
        for _ in range(150):
            if server.started: break
            time.sleep(.1)
        assert server.started
        now=int(time.time())
        with storage.database() as conn:
            uid=conn.execute('INSERT INTO users(name,email,password_hash,salt,role,created_at) VALUES(?,?,?,?,?,?)',
                ('Theme student','themes@local.test','unused','unused','student',now)).lastrowid
            conn.execute('INSERT INTO sessions VALUES(?,?,?)',(hashlib.sha256(b'theme-smoke').hexdigest(),uid,now+3600))
        user={'id':uid,'name':'Theme student','email':'themes@local.test','role':'student','expires_at':now+3600}
        base=f'http://127.0.0.1:{port}'
        output=ROOT/'test-results'
        output.mkdir(exist_ok=True)
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(channel='msedge',headless=True)
                context=browser.new_context(viewport={'width':1200,'height':900})
                def local_canvas(route):
                    suffix=route.request.url.split('/flutter-canvaskit/',1)[1].split('/',1)[1]
                    asset=Path(os.environ['WEB_APP_DIR']) / 'canvaskit' / suffix
                    if asset.is_file():
                        route.fulfill(path=str(asset), content_type='application/wasm' if asset.suffix=='.wasm' else 'application/javascript', headers={'Access-Control-Allow-Origin':'*'})
                    else:
                        route.continue_()
                context.route('https://www.gstatic.com/flutter-canvaskit/**',local_canvas)
                context.add_init_script("sessionStorage.setItem('hanzigo_account_token','theme-smoke')")
                page=context.new_page()
                errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(base+'/account')
                expect(page.locator('#profile-section')).to_be_visible()
                for palette in ['purple','red','blue','yellow','orange','pink','dark']:
                    page.locator('#palette-choice').select_option(palette)
                    page.locator('#palette-enabled').check()
                    expect(page.locator('html')).to_have_attribute('data-learner-theme',palette)
                    page.screenshot(path=str(output/f'account-theme-{palette}.png'))
                    page.reload()
                    expect(page.locator('#palette-choice')).to_have_value(palette)
                    expect(page.locator('#palette-enabled')).to_be_checked()
                page.locator('#palette-enabled').uncheck()
                expect(page.locator('html')).to_have_attribute('data-learner-theme','light')
                page.evaluate('user => {localStorage.setItem("flutter.auth_token",JSON.stringify("theme-smoke"));localStorage.setItem("flutter.auth_user",JSON.stringify(JSON.stringify(user)));}',user)
                chat_accents = set()
                for palette in ['purple','blue','yellow','orange','pink','red','dark']:
                    page.evaluate('p => {localStorage.setItem("flutter.app_theme_palette",JSON.stringify(p));localStorage.setItem("flutter.app_theme_mode",JSON.stringify("dark"));}',palette)
                    page.goto(base+'/')
                    try:
                        page.locator('flutter-view').wait_for(timeout=30000)
                    except Exception:
                        page.screenshot(path=str(output/'flutter-load-error.png'))
                        print('Browser errors:',errors,flush=True)
                        raise
                    page.wait_for_timeout(3500)
                    page.screenshot(path=str(output/f'flutter-theme-{palette}.png'))
                    accent = page.locator('#launch').evaluate('(el) => getComputedStyle(el).backgroundColor')
                    chat_accents.add(accent)
                    if palette not in ['dark']:
                        assert accent != 'rgb(23, 99, 78)', (palette, accent)
                    # The exact pages reported by the user, not just the home screen.
                    page.mouse.click(600, 864)
                    page.wait_for_timeout(900)
                    page.screenshot(path=str(output/f'flutter-reading-{palette}.png'))
                    page.mouse.click(943, 864)
                    page.wait_for_timeout(900)
                    page.screenshot(path=str(output/f'flutter-exam-{palette}.png'))
                assert len(chat_accents) == 7, chat_accents
                page.evaluate('()=>{localStorage.removeItem("flutter.auth_user");localStorage.removeItem("flutter.auth_token");}')
                page.reload()
                page.wait_for_timeout(3500)
                page.screenshot(path=str(output/'flutter-login-default.png'))
                assert page.locator('#launch').evaluate('(el) => getComputedStyle(el).backgroundColor') == 'rgb(23, 99, 78)'
                assert not errors,errors
                browser.close()
            print('PASS: seven account palettes persist; switch restores light; Flutter pages render without browser errors')
        finally:
            server.should_exit=True
            worker.join(10)


if __name__=='__main__': main()
