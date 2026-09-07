"""End-to-end Admin smoke test; temporary DB, no external AI calls.

Run after installing requirements-dev.txt and Playwright Chromium, or set
PLAYWRIGHT_CHANNEL=msedge to use an installed Microsoft Edge.
"""
import os
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
from playwright.sync_api import expect, sync_playwright

import database as storage
from main import hash_password
from seed import seed


def run():
    artifacts = Path(__file__).resolve().parent.parent / "test-results"
    artifacts.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        storage.DB_PATH = Path(temp) / "browser.db"
        seed()
        password = secrets.token_urlsafe(18)
        with storage.database() as conn:
            for name, email, role in [("Nguyên", "admin@example.test", "admin"), ("Học viên", "student@example.test", "student")]:
                salt = secrets.token_hex(16)
                conn.execute("INSERT INTO users(name,email,password_hash,salt,role,created_at) VALUES(?,?,?,?,?,?)",
                             (name, email, hash_password(password, salt), salt, role, int(time.time())))
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        env = {**os.environ, "DATABASE_PATH": str(storage.DB_PATH)}
        server = subprocess.Popen([sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)],
                                  cwd=Path(__file__).parent, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(100):
                try:
                    if httpx.get(base + "/api/health", timeout=1).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(.1)
            else:
                raise RuntimeError("Test server did not start")
            with sync_playwright() as playwright:
                channel = os.getenv("PLAYWRIGHT_CHANNEL")
                browser = playwright.chromium.launch(headless=True, **({"channel": channel} if channel else {}))
                page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
                page.set_default_timeout(10000)
                def navigate(name):
                    toggle = page.locator('#menu-toggle')
                    if toggle.is_visible():
                        expect(toggle).to_have_attribute('aria-expanded','false')
                        expect(page.locator('#admin-menu')).not_to_be_visible()
                        toggle.click()
                        expect(page.locator('#admin-menu')).to_be_visible()
                    page.get_by_role('button',name=name,exact=True).click()
                    if toggle.is_visible():
                        expect(toggle).to_have_attribute('aria-expanded','false')
                        expect(page.locator('#admin-menu')).not_to_be_visible()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(base + "/admin")
                page.get_by_label("Email", exact=True).fill("admin@example.test")
                page.get_by_label("Mật khẩu", exact=True).fill(password)
                page.get_by_role("button", name="Đăng nhập →").click()
                expect(page.get_by_role("heading", name="Tổng quan", exact=True)).to_be_visible()
                expect(page.locator('.stat')).to_have_count(8)
                expect(page.locator('.stat:visible')).to_have_count(4)
                page.locator('.advanced-stats summary').click()
                expect(page.locator('.stat:visible')).to_have_count(8)
                page.locator('.advanced-stats summary').click()
                page.screenshot(path=str(artifacts / "admin-desktop.png"), full_page=True)

                page.get_by_role("button", name="Kho từ & nét chuẩn", exact=True).click()
                page.get_by_role("button", name="+ Thêm từ", exact=True).click()
                editor = page.locator('dialog')
                editor.get_by_label("Chữ Hán", exact=True).fill("二")
                editor.get_by_label("Pinyin", exact=True).fill("èr")
                editor.get_by_label("Nghĩa tiếng Việt", exact=True).fill("hai")
                canvas = editor.locator('canvas').bounding_box()
                page.mouse.move(canvas['x'] + 40, canvas['y'] + 80)
                page.mouse.down()
                page.mouse.move(canvas['x'] + 180, canvas['y'] + 80, steps=10)
                page.mouse.up()
                editor.get_by_role("button", name="Lưu thay đổi", exact=True).click()
                expect(editor).not_to_be_visible()
                expect(page.get_by_role('cell',name='二',exact=True)).to_be_visible()
                row = page.locator('tr').filter(has=page.get_by_role('cell', name='二', exact=True))
                row.get_by_role('button',name='Sửa',exact=True).click()
                expect(editor.locator('#stroke-count')).to_have_text('1 nét đã vẽ')
                editor.get_by_label('Nghĩa tiếng Việt',exact=True).fill('số hai')
                editor.get_by_role('button',name='Lưu thay đổi',exact=True).click()
                expect(editor).not_to_be_visible()

                page.get_by_role('button',name='Ngân hàng đề',exact=True).click()
                page.get_by_role('button',name='+ Tạo đề thi',exact=True).click()
                editor.get_by_label('Tên đề',exact=True).fill('Đề kiểm thử trình duyệt')
                editor.get_by_label('Trạng thái',exact=True).select_option('published')
                editor.get_by_label('Mã câu',exact=True).fill('browser-q1')
                editor.get_by_label('Yêu cầu / nội dung',exact=True).fill('Chọn nghĩa của 二')
                editor.get_by_label('Lựa chọn (mỗi dòng một đáp án)',exact=True).fill('một\nhai')
                editor.get_by_label('Đáp án / rubric chấm',exact=True).fill('hai')
                editor.get_by_role('button',name='Lưu thay đổi',exact=True).click()
                expect(editor).not_to_be_visible()
                expect(page.get_by_role('cell').filter(has_text='Đề kiểm thử trình duyệt')).to_be_visible()
                student = httpx.post(base+'/api/auth/login',json={'email':'student@example.test','password':password}).json()
                auth = {'Authorization':'Bearer '+student['token']}
                exams = httpx.get(base+'/api/exams',headers=auth).json()
                exam = next(e for e in exams if e['title']=='Đề kiểm thử trình duyệt')
                result = httpx.post(base+f"/api/exams/{exam['id']}/submit",headers=auth,json={'version':exam['version'],'answers':{'browser-q1':'một'}})
                assert result.status_code == 201, result.text
                page.get_by_role('button',name='Duyệt kết quả',exact=True).click()
                page.get_by_role('button',name='Xem & duyệt',exact=True).click()
                editor.get_by_label('Điểm điều chỉnh (0–100)',exact=True).fill('85')
                editor.get_by_label('Lý do điều chỉnh',exact=True).fill('Đối chiếu bài làm trong kiểm thử tích hợp')
                editor.get_by_role('button',name='Lưu điểm điều chỉnh',exact=True).click()
                expect(editor).not_to_be_visible()
                expect(page.locator('.score')).to_have_text('85')
                assert httpx.get(base+'/api/me/dashboard',headers=auth).json()['average_score']==85
                page.get_by_role('button',name='Xem & duyệt',exact=True).click()
                expect(editor.get_by_text('0 → 85',exact=True)).to_be_visible()
                editor.get_by_role('button',name='Hủy',exact=True).click()

                learner = browser.new_page(viewport={'width':320,'height':740},is_mobile=True,has_touch=True)
                learner.on('pageerror', lambda error: errors.append(str(error)))
                learner.goto(base+'/review')
                learner.get_by_label('Email',exact=True).fill('student@example.test')
                learner.get_by_label('Mật khẩu',exact=True).fill(password)
                learner.get_by_role('button',name='Đăng nhập',exact=True).tap()
                learner.get_by_label('Lý do phúc khảo',exact=True).fill('Xin kiểm tra lại phần điểm bài làm')
                learner.get_by_role('button',name='Gửi yêu cầu',exact=True).tap()
                expect(learner.get_by_text('Đang chờ xử lý',exact=True)).to_be_visible()
                assert learner.evaluate('document.documentElement.scrollWidth <= innerWidth')
                page.set_viewport_size({'width':320,'height':740})
                page.get_by_role('button',name='Yêu cầu phúc khảo',exact=True).click()
                expect(page.locator('[data-appeal]')).to_have_count(1)
                page.get_by_role('button',name='Xử lý',exact=True).click()
                editor.get_by_label('Điểm sau phúc khảo',exact=True).fill('90')
                editor.get_by_label('Phản hồi cho học viên',exact=True).fill('Đã kiểm tra bài và điều chỉnh thành 90 điểm')
                assert editor.evaluate('el => el.scrollWidth <= el.clientWidth')
                page.screenshot(path=str(artifacts/'admin-mobile-appeal.png'),full_page=True)
                editor.get_by_role('button',name='Hoàn tất phúc khảo',exact=True).click()
                expect(editor).not_to_be_visible()
                expect(page.locator('.score')).to_have_text('90')
                learner.get_by_role('button',name='Tải lại',exact=True).tap()
                expect(learner.get_by_role('heading',name=re.compile('90 điểm'))).to_be_visible()
                expect(learner.get_by_text('Đã xử lý',exact=True)).to_be_visible()
                learner.screenshot(path=str(artifacts/'learner-mobile-appeal.png'),full_page=True)
                learner.get_by_role('button',name='Đăng xuất',exact=True).tap()
                learner.close()
                page.set_viewport_size({'width':1440,'height':1000})
                page.get_by_role('button',name='Cấu hình AI',exact=True).click()
                page.get_by_label('Model',exact=True).fill('test-model')
                page.get_by_role('button',name='Lưu cấu hình',exact=True).click()
                expect(page.get_by_label('Model',exact=True)).to_have_value('test-model')
                expect(page.locator('#notice')).to_have_text('Đã lưu cấu hình AI')
                page.get_by_role('button',name='Nhật ký quản trị',exact=True).click()
                page.get_by_role('button',name='Xem',exact=True).first.click()
                expect(editor.get_by_role('heading',name='Sau thay đổi')).to_be_visible()
                editor.get_by_role('button',name='Đóng',exact=True).click()

                page.get_by_role('button',name='Người dùng',exact=True).click()
                page.get_by_label('Tìm tài khoản',exact=True).fill('student@example.test')
                page.get_by_role('button',name='Tìm kiếm',exact=True).click()
                expect(page.locator('tbody tr')).to_have_count(1)
                page.get_by_role('button',name='Chỉnh sửa',exact=True).click()
                editor.get_by_label('Tài khoản hoạt động',exact=True).uncheck()
                editor.get_by_role('button',name='Lưu thay đổi',exact=True).click()
                expect(editor).not_to_be_visible()
                expect(page.get_by_role('cell',name='Đã khóa',exact=True)).to_be_visible()
                assert httpx.get(base+'/api/me',headers=auth).status_code==401

                page.get_by_role('button',name='Xem giao diện điện thoại',exact=True).click()
                expect(page.get_by_role('button',name='Trở về giao diện máy tính',exact=True)).to_have_attribute('aria-pressed','true')
                assert page.locator('#app').bounding_box()['width'] <= 440
                expect(page.locator('#menu-toggle')).to_be_visible()
                expect(page.locator('#admin-menu')).not_to_be_visible()
                page.locator('#menu-toggle').click()
                expect(page.locator('#admin-menu')).to_be_visible()
                page.keyboard.press('Escape')
                expect(page.locator('#admin-menu')).not_to_be_visible()
                expect(page.locator('#menu-toggle')).to_be_focused()
                page.locator('#menu-toggle').click()
                page.locator('#content h1').click()
                expect(page.locator('#admin-menu')).not_to_be_visible()
                assert page.locator('tbody tr').first.evaluate("el => getComputedStyle(el).display") == 'grid'
                page.screenshot(path=str(artifacts / 'admin-phone-preview.png'),full_page=True)
                page.get_by_role('button',name='Trở về giao diện máy tính',exact=True).click()
                assert page.locator('tbody tr').first.evaluate("el => getComputedStyle(el).display") == 'table-row'

                page.set_viewport_size({'width':320,'height':740})
                for name in ['Người dùng','Kho từ & nét chuẩn','Ngân hàng đề','Duyệt kết quả','Nhật ký quản trị']:
                    navigate(name)
                    expect(page.locator('tbody tr').first).to_be_visible()
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), name
                    assert page.locator('.table-wrap').first.evaluate('el => el.scrollWidth <= el.clientWidth'), name

                page.set_viewport_size({'width':390,'height':844})
                navigate('Tổng quan')
                expect(page.locator('.stat')).to_have_count(8)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                page.screenshot(path=str(artifacts / 'admin-mobile.png'),full_page=True)
                page.locator('#menu-toggle').click()
                page.screenshot(path=str(artifacts / 'admin-mobile-menu.png'),full_page=True)
                page.locator('#menu-toggle').click()
                navigate('Kho từ & nét chuẩn')
                page.get_by_role('button',name='+ Thêm từ',exact=True).click()
                expect(editor).to_be_visible()
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                assert editor.evaluate('el => el.scrollWidth <= el.clientWidth')
                page.screenshot(path=str(artifacts / 'admin-mobile-form.png'),full_page=True)
                editor.get_by_role('button',name='Hủy',exact=True).click()
                page.reload()
                expect(page.get_by_role('heading',name='Tổng quan',exact=True)).to_be_visible()
                expect(page.locator('#admin-menu')).not_to_be_visible()
                page.locator('#menu-toggle').click()
                page.get_by_role('button',name='Đăng xuất',exact=True).click()
                expect(page.get_by_role('heading',name='Đăng nhập quản trị',exact=True)).to_be_visible()
                assert not errors, errors
                phone = browser.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
                phone.on('pageerror', lambda error: errors.append(str(error)))
                phone.add_init_script("Object.defineProperty(Crypto.prototype, 'randomUUID', {value: undefined, configurable: true})")
                phone.goto(base+'/admin')
                phone.get_by_label('Email',exact=True).fill('admin@example.test')
                phone.get_by_label('Mật khẩu',exact=True).fill(password)
                phone.get_by_role('button',name='Đăng nhập →').tap()
                expect(phone.locator('.stat:visible')).to_have_count(4)
                expect(phone.locator('#admin-menu')).not_to_be_visible()
                phone.locator('#menu-toggle').tap()
                phone.get_by_role('button',name='Ngân hàng đề',exact=True).tap()
                expect(phone.locator('#admin-menu')).not_to_be_visible()
                phone.get_by_role('button',name='+ Tạo đề thi',exact=True).tap()
                expect(phone.locator('dialog')).to_be_visible()
                expect(phone.locator('[data-key=id]')).to_have_value(re.compile(r'^q-.+'))
                assert phone.locator('dialog').evaluate('el => el.scrollWidth <= el.clientWidth')
                phone.get_by_role('button',name='Hủy',exact=True).tap()
                phone.locator('#menu-toggle').tap()
                phone.get_by_role('button',name='Đăng xuất',exact=True).tap()
                expect(phone.get_by_role('heading',name='Đăng nhập quản trị',exact=True)).to_be_visible()
                assert not errors, errors
                phone.close()
                browser.close()
            print('PASS: desktop/mobile admin, vocabulary and strokes, exams, score synchronization, users, AI config, audit, session/logout; no JavaScript errors.')
        finally:
            server.terminate()
            server.wait(timeout=10)


if __name__ == '__main__':
    run()
