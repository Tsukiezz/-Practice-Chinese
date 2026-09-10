"""Exercise the built Flutter website and Admin through one origin, using a temp DB.

WEB_APP_DIR must point at `flutter build web` output. No real AI calls.
"""
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import httpx
from playwright.sync_api import sync_playwright, expect
import database as storage
from main import hash_password
from listening_demo import seed_listening


def run():
    expect.set_options(timeout=30000)
    web_dir = Path(os.environ['WEB_APP_DIR']).resolve()
    assert (web_dir / 'index.html').is_file(), 'Build Flutter web first'
    with tempfile.TemporaryDirectory() as temp:
        storage.DB_PATH = Path(temp) / 'unified.db'
        seed_listening(publish=True)
        password = secrets.token_urlsafe(18)
        with storage.database() as conn:
            for name, email, role in [('Admin', 'admin@example.test', 'admin'), ('Student', 'student@example.test', 'student')]:
                salt = secrets.token_hex(16)
                conn.execute('INSERT INTO users(name,email,password_hash,salt,role,created_at) VALUES(?,?,?,?,?,?)',
                    (name, email, hash_password(password, salt), salt, role, int(time.time())))
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        base = f'http://127.0.0.1:{port}'
        env = {**os.environ, 'DATABASE_PATH': str(storage.DB_PATH), 'WEB_APP_DIR': str(web_dir)}
        server_code = (
            "import main,uvicorn; "
            "main.grade_listening_exam=lambda *args: {'score':100,'feedback':'Test grading'}; "
            f"uvicorn.run(main.app,host='127.0.0.1',port={port})"
        )
        server = subprocess.Popen([sys.executable, '-c', server_code], cwd=Path(__file__).parent,
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        phase = 'server startup'
        try:
            for _ in range(100):
                try:
                    if httpx.get(base + '/api/health', timeout=1).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(.1)
            with sync_playwright() as p:
                channel = os.getenv('PLAYWRIGHT_CHANNEL')
                browser = p.chromium.launch(headless=True, **({'channel': channel} if channel else {}))
                page = browser.new_page(viewport={'width': 1100, 'height': 900})
                page.set_default_timeout(30000)
                errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))

                def login(email):
                    page.goto(base)
                    page.locator('flt-semantics-placeholder').evaluate('(el) => el.click()')
                    # Flutter replaces its semantics input while focus settles.
                    # Verify the typed value instead of submitting a partial password.
                    for label, value in [('Email', email), ('Mật khẩu', password)]:
                        field = page.get_by_role('textbox', name=label, exact=True)
                        field.click()
                        expect(field).to_be_focused()
                        for _ in range(3):
                            field.press('ControlOrMeta+A')
                            field.press('Backspace')
                            field.press_sequentially(value, delay=80)
                            if field.input_value() == value:
                                break
                        expect(field).to_have_value(value)
                    field.press('Tab')
                    page.get_by_role('button', name='Đăng nhập', exact=True).click()

                phase = 'admin login'
                login('admin@example.test')
                expect(page).to_have_url(base + '/admin')
                expect(page.get_by_role('heading', name='Tổng quan', exact=True)).to_be_visible()
                print('PASS: Admin login on shared website', flush=True)
                page.get_by_role('button', name='Đăng xuất', exact=True).click()
                expect(page).to_have_url(base + '/')

                phase = 'student login'
                login('student@example.test')
                expect(page.get_by_role('tab', name='Nghe', exact=True)).to_be_visible()
                page.get_by_role('tab', name='Nghe', exact=True).click()
                print('PASS: student login on shared website', flush=True)
                phase = 'listening playback'
                page.get_by_text('HSK 1 · Nghe Chào hỏi (mẫu)').click()
                with page.expect_response(lambda r: '/media/listening-greeting.mp3' in r.url) as audio:
                    page.get_by_role('button', name='Phát âm thanh', exact=True).click()
                assert audio.value.status in (200, 206)
                expect(page.get_by_text('Đang phát...', exact=True)).to_be_visible()
                expect(page.get_by_text('Không thể phát audio.', exact=True)).not_to_be_visible()
                phase = 'listening submission'
                page.get_by_text('Tiểu Minh', exact=True).click()
                page.get_by_role('button', name='Nộp bài', exact=True).click()
                expect(page.get_by_text('Test grading')).to_be_visible()
                print('PASS: bundled audio playback and listening submission', flush=True)
                phase = 'reload and student logout'
                page.reload()
                page.locator('flt-semantics-placeholder').evaluate('(el) => el.click()')
                expect(page.get_by_role('tab', name='Nghe', exact=True)).to_be_visible()
                page.get_by_role('tab', name='Cá nhân', exact=True).click()
                logout = page.get_by_text('Đăng xuất', exact=True)
                for _ in range(10):
                    if logout.count():
                        break
                    page.mouse.move(550, 450)
                    page.mouse.wheel(0, 600)
                    page.wait_for_timeout(150)
                logout.click()
                page.get_by_role('alertdialog').get_by_role('button', name='Đăng xuất', exact=True).click()
                expect(page.get_by_role('textbox', name='Email', exact=True)).to_be_visible()
                # A student cannot unlock Admin by writing a token into browser storage.
                phase = 'role protection'
                auth = httpx.post(base + '/api/auth/login', json={'email':'student@example.test','password':password}).json()
                page.evaluate('(token) => sessionStorage.setItem("hanzigo_admin_token", token)', auth['token'])
                page.goto(base + '/admin')
                expect(page).to_have_url(base + '/')
                assert httpx.get(base + '/api/admin/exams', headers={'Authorization':'Bearer '+auth['token']}).status_code == 403
                assert not errors, errors
                browser.close()
            print('PASS: one-origin login, Admin/student routing, logout, reload, listening audio and submission, role protection.')
        except Exception as error:
            message = str(error).replace(password, '[redacted]')
            message = message.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
            print(f'::error title=Unified web - {phase}::{message}', flush=True)
            raise
        finally:
            server.terminate()
            server.wait(timeout=10)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    run()
