"""Isolated desktop/mobile chat smoke using a deterministic AI provider."""
import hashlib
import os
from pathlib import Path
import socket
import tempfile
import threading
import time

os.environ['TESTING'] = '1'

import uvicorn
from playwright.sync_api import sync_playwright, expect
import database as storage
import support_chat
from main import app


def main():
    with tempfile.TemporaryDirectory() as temp:
        storage.DB_PATH = Path(temp) / 'smoke.db'
        support_chat.generate_reply = lambda history: (
            '你好 · nǐ hǎo · Xin chào.\nĐọc thanh 3, rồi luyện với ví dụ 你好！',
            'thanh toán' in history[-1]['content'])
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port, log_level='error'))
        worker = threading.Thread(target=server.run, daemon=True)
        worker.start()
        for _ in range(100):
            if server.started:
                break
            time.sleep(.1)
        assert server.started
        with storage.database() as conn:
            for name, role in [('Smoke student','student'),('Smoke admin','admin')]:
                cur = conn.execute('INSERT INTO users(name,email,password_hash,salt,role,created_at) VALUES(?,?,?,?,?,?)',
                    (name,role+'@smoke.test','unused','unused',role,int(time.time())))
                conn.execute('INSERT INTO sessions VALUES(?,?,?)',
                    (hashlib.sha256(('smoke-'+role).encode()).hexdigest(),cur.lastrowid,int(time.time())+3600))
        url = f'http://127.0.0.1:{port}'
        screenshots = Path(__file__).resolve().parents[1] / 'test-results'
        screenshots.mkdir(exist_ok=True)
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(channel=os.getenv('PLAYWRIGHT_CHANNEL','msedge'),headless=True)
                guest = browser.new_context(viewport={'width':390,'height':844})
                page = guest.new_page()
                page.goto(url+'/admin')
                page.set_content('<html><body><h1>HanziGo</h1><script src="/admin/assets/support-widget.js"></script></body></html>')
                page.get_by_role('button',name='💬 Hỏi HanziGo').click()
                page.get_by_role('textbox',name='Tin nhắn',exact=True).fill('Hướng dẫn cách đọc 你好')
                page.get_by_role('button',name='Gửi',exact=True).click()
                expect(page.locator('.message.assistant')).to_contain_text('nǐ hǎo',timeout=10000)
                page.get_by_role('textbox',name='Tin nhắn',exact=True).fill('Tôi cần hỗ trợ thanh toán')
                page.get_by_role('button',name='Gửi',exact=True).click()
                expect(page.locator('.message.assistant').last).to_contain_text(support_chat.HANDOFF,timeout=10000)
                page.screenshot(path=str(screenshots/'chat-guest-mobile.png'))
                admin = browser.new_context(viewport={'width':1440,'height':1000})
                admin.add_init_script("sessionStorage.setItem('hanzigo_admin_token','smoke-admin')")
                inbox = admin.new_page()
                inbox.goto(url+'/admin')
                inbox.locator('[data-toggle-group="system"]').click()
                inbox.locator('[data-page="chats"]').click()
                inbox.locator('.chat-thread').first.click()
                expect(inbox.locator('.chat-history')).to_contain_text('thanh toán')
                expect(inbox.locator('.chat-history')).to_contain_text(support_chat.HANDOFF)
                inbox.get_by_role('textbox',name='Trả lời người dùng').fill('Quản trị viên đã nhận thông tin của bạn.')
                inbox.get_by_role('button',name='Gửi trả lời',exact=True).click()
                expect(page.locator('.message.admin')).to_contain_text('đã nhận thông tin',timeout=10000)
                inbox.screenshot(path=str(screenshots/'chat-admin-desktop.png'))
                inbox.set_viewport_size({'width':390,'height':844})
                assert inbox.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                inbox.screenshot(path=str(screenshots/'chat-admin-mobile.png'))
                # Switching to a non-remembered student session must not show guest history.
                page.evaluate("window.dispatchEvent(new CustomEvent('hanzigo-chat-session',{detail:'smoke-student'}))")
                expect(page.locator('.message')).to_have_count(0)
                page.get_by_role('textbox',name='Tin nhắn',exact=True).fill('<img src=x onerror=alert(1)> giải thích 你好')
                page.get_by_role('button',name='Gửi',exact=True).click()
                expect(page.locator('.message.assistant')).to_have_count(1,timeout=10000)
                expect(page.locator('.message.user img')).to_have_count(0)
                page.evaluate("window.dispatchEvent(new CustomEvent('hanzigo-chat-session',{detail:''}))")
                expect(page.locator('.message.admin')).to_contain_text('đã nhận thông tin',timeout=10000)
                browser.close()
                print('PASS: mobile guest chat, AI handoff, admin inbox/reply, responsive layout, identity switching, safe text rendering')
        finally:
            server.should_exit = True
            worker.join(timeout=10)


if __name__ == '__main__':
    main()
