"""Check a deployed site using explicitly supplied demo-account credentials.

Set DEMO_URL, DEMO_ADMIN_EMAIL/PASSWORD, DEMO_STUDENT_EMAIL/PASSWORD.
The optional --write-check records stage 1 of the first lesson for the demo student.
No AI requests or production configuration changes are made.
"""
import os
from pathlib import Path
import re
import sys

import httpx
from playwright.sync_api import sync_playwright, expect  # type: ignore


def run():
    base = os.environ['DEMO_URL'].rstrip('/')
    output = Path(__file__).with_name('test-results')
    output.mkdir(exist_ok=True)
    credentials = {role: {'email': os.environ[f'DEMO_{role.upper()}_EMAIL'],
                          'password': os.environ[f'DEMO_{role.upper()}_PASSWORD']}
                   for role in ('admin', 'student')}
    with httpx.Client(base_url=base, timeout=60) as client:
        for path in ('/', '/api/health', '/admin', '/media/listening-greeting.mp3'):
            response = client.get(path)
            assert response.status_code == 200, (path, response.status_code)
        lessons = client.get('/api/lessons').json()
        assert lessons['total'] == 48
        assert client.get('/api/vocabulary/page?limit=1').json()['total'] >= 4993
        assert client.get('/api/vocabulary/page?search=pingguo').json()['total'] > 0
        for role, body in credentials.items():
            response = client.post('/api/auth/login', json=body)
            assert response.status_code == 200, (role, response.status_code)
            session = response.json()
            assert session['user']['role'] == role
            headers = {'Authorization': 'Bearer ' + session['token']}
            response = client.get('/api/admin/users', headers=headers)
            assert response.status_code == (200 if role == 'admin' else 403)
            if role == 'student' and '--write-check' in sys.argv:
                lesson_id = lessons['items'][0]['id']
                saved = client.put(f'/api/me/lessons/{lesson_id}/progress', json={'stage': 1}, headers=headers)
                assert saved.status_code == 200
                # A new login and new request must read the stored database value.
                new_session = client.post('/api/auth/login', json=body).json()
                progress = client.get('/api/me/lessons', headers={'Authorization': 'Bearer ' + new_session['token']}).json()
                assert any(p['lesson_id'] == lesson_id and p['stage'] >= 1 for p in progress)
        print('PASS: public pages, API, audio, credentials, role isolation and requested write check', flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel=os.getenv('PLAYWRIGHT_CHANNEL') or None)
        expect.set_options(timeout=60000)
        for role in ('admin', 'student'):
            page = browser.new_page(viewport={'width': 390, 'height': 844})
            page.set_default_timeout(60000)
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(base)
            page.locator('flt-semantics-placeholder').evaluate('(el) => el.click()')
            for label, value in [('Email', credentials[role]['email']), ('Mật khẩu', credentials[role]['password'])]:
                field = page.get_by_role('textbox', name=re.compile('^' + re.escape(label) + r'(?:\s|$)'))
                field.click()
                expect(field).to_be_focused()
                for _ in range(3):
                    field.press('ControlOrMeta+A')
                    field.press('Backspace')
                    field.press_sequentially(value, delay=60)
                    if field.input_value() == value:
                        break
                expect(field).to_have_value(value)
                field.press('Tab')
            page.get_by_role('button', name='Đăng nhập', exact=True).click()
            if role == 'admin':
                expect(page).to_have_url(base + '/admin')
                expect(page.get_by_role('heading', name='Tổng quan', exact=True)).to_be_visible()
            else:
                page.get_by_role('tab', name='Bài học', exact=True).click()
                expect(page.get_by_text('Từng bài nhỏ, tiến bộ lớn', exact=True)).to_be_visible()
            page.wait_for_timeout(1000)
            page.screenshot(path=str(output / f'vercel-{role}-mobile.png'))
            page.set_viewport_size({'width': 1280, 'height': 900})
            page.wait_for_timeout(1000)
            page.screenshot(path=str(output / f'vercel-{role}-desktop.png'))
            assert not errors, errors
            print(f'PASS: {role} browser login, mobile and desktop', flush=True)
            page.close()
        browser.close()


if __name__ == '__main__':
    run()
