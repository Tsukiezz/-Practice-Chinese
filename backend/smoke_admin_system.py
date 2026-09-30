"""Exercise AI settings, stable inbox updates and full audit details in a browser."""
import hashlib
import os
from pathlib import Path
import socket
import tempfile
import threading
import time

os.environ['TESTING'] = '1'
os.environ['GEMINI_API_KEY'] = 'local-smoke-placeholder'

import uvicorn
from playwright.sync_api import sync_playwright, expect
import ai_provider
import database as storage
from main import app


def main():
    with tempfile.TemporaryDirectory() as temp:
        storage.DB_PATH = Path(temp) / 'admin-system.db'
        ai_provider.gemini_grade = lambda *args, **kwargs: {'score':100,'feedback':'Kết nối kiểm thử thành công'}
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0))
            port = sock.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='error'))
        worker = threading.Thread(target=server.run,daemon=True)
        worker.start()
        for _ in range(150):
            if server.started:
                break
            time.sleep(.1)
        assert server.started
        now = int(time.time())
        with storage.database() as conn:
            admin = conn.execute('INSERT INTO users(name,email,password_hash,salt,role,created_at) VALUES(?,?,?,?,?,?)',
                ('Quản trị viên','admin@local.test','unused','unused','admin',now)).lastrowid
            conn.execute('INSERT INTO sessions VALUES(?,?,?)',(hashlib.sha256(b'admin-system-smoke').hexdigest(),admin,now+3600))
            conn.execute("UPDATE ai_config SET enabled=1,model='gemini-test-model' WHERE id=1")
            for i in range(8):
                user_id = None
                name = ['Linh Nguyễn','Minh Anh'][i] if i < 2 else 'Khách ' + str(10234+i)
                if i < 2:
                    user_id = conn.execute('INSERT INTO users(name,email,password_hash,salt,role,created_at) VALUES(?,?,?,?,?,?)',
                        (name,'learner'+str(i)+'@local.test','unused','unused','student',now)).lastrowid
                tid = 'smoke-thread-'+str(i)
                conn.execute('INSERT INTO chat_threads(id,user_id,name,state,created_at,updated_at) VALUES(?,?,?,?,?,?)',
                    (tid,user_id,name,['waiting','ai','admin'][i%3],now-1800,now-i*120))
                for m in range(130 if i == 0 else 3):
                    role = ['user','assistant','admin'][m%3]
                    text = ['Em muốn phân biệt cách dùng 了 và 过, thầy cô giải thích thêm giúp em nhé.',
                            '了 (le) diễn tả sự hoàn thành hoặc thay đổi trạng thái.\n过 (guo) diễn tả kinh nghiệm đã từng có.\n\n我吃了饭。Wǒ chī le fàn. Tôi đã ăn cơm.\n我去过北京。Wǒ qù guo Běijīng. Tôi từng đến Bắc Kinh.',
                            'Bạn thử đặt hai câu về chuyến du lịch của mình. Mình sẽ xem và góp ý cho bạn.'][m%3]
                    conn.execute('INSERT INTO chat_messages(thread_id,role,content,created_at) VALUES(?,?,?,?)',
                        (tid,role,text,now-1700+m*10))
            for i in range(125):
                storage.audit(conn,admin,'update','vocabulary',i,{'meaning':'before-'+str(i),'hanzi':'学习'}, {'meaning':'after-'+str(i),'hanzi':'学习'})
        output = Path(__file__).resolve().parents[1] / 'test-results'
        output.mkdir(exist_ok=True)
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(channel=os.getenv('PLAYWRIGHT_CHANNEL','msedge'),headless=True)
                login_page = browser.new_page(viewport={'width':390,'height':844})
                login_page.goto(f'http://127.0.0.1:{port}/admin')
                password = login_page.locator('[name=password]')
                password.fill('Visibility-only-test')
                login_page.locator('#toggle-password').click()
                expect(password).to_have_attribute('type', 'text')
                expect(password).to_have_value('Visibility-only-test')
                login_page.locator('#toggle-password').click()
                expect(password).to_have_attribute('type', 'password')
                expect(login_page.locator('#login button[type=submit]')).to_be_enabled()
                login_page.screenshot(path=str(output / 'admin-password-mobile.png'))
                login_page.close()
                context = browser.new_context(viewport={'width':1440,'height':1100})
                context.add_init_script("sessionStorage.setItem('hanzigo_admin_token','admin-system-smoke')")
                page = context.new_page()
                errors, config_requests = [], []
                page.on('pageerror',lambda error: errors.append(str(error)))
                page.on('request',lambda request: config_requests.append(request.url) if request.url.endswith('/api/admin/ai-config') and request.method == 'GET' else None)
                page.goto(f'http://127.0.0.1:{port}/admin')
                page.locator('[data-toggle-group="system"]').click()

                def navigate(name):
                    if page.locator('#menu-toggle').is_visible() and page.locator('#menu-toggle').get_attribute('aria-expanded') != 'true':
                        page.locator('#menu-toggle').click()
                    page.locator('[data-page="'+name+'"]').click()

                navigate('ai')
                expect(page.locator('#ai-form')).to_be_visible()
                assert len(config_requests) == 1, config_requests
                prompt = page.locator('[name="system_prompt"]')
                prompt.fill(prompt.input_value()+'\nHướng dẫn rõ từng lỗi và kèm ví dụ.')
                draft = prompt.input_value()
                page.locator('[data-toggle-group="students"]').click()
                expect(prompt).to_have_value(draft)
                assert len(config_requests) == 1
                expect(page.locator('.ai-test')).to_be_disabled()
                page.locator('.ai-save').click()
                expect(page.locator('#ai-error')).to_have_text('Đã lưu thành công.')
                expect(page.locator('.ai-save')).to_be_disabled()
                page.locator('.ai-test').click()
                expect(page.locator('.ai-connection-result')).to_have_class('ai-connection-result success')
                page.screenshot(path=str(output/'admin-ai-desktop.png'),full_page=True)
                navigate('logs')
                expect(page.locator('.audit-count')).to_contain_text('127 bản ghi')
                expect(page.locator('.audit-table tbody tr')).to_have_count(50)
                page.locator('.audit-next').click()
                expect(page.locator('.audit-pagination span')).to_have_text('51–100 / 127')
                page.get_by_role('searchbox',name='Tìm trong nhật ký').fill('after-124')
                page.get_by_role('button',name='Áp dụng bộ lọc').click()
                expect(page.locator('.audit-table tbody tr')).to_have_count(1)
                page.get_by_role('button',name='Xem đầy đủ').click()
                expect(page.locator('.audit-diff')).to_contain_text('before-124')
                expect(page.locator('.audit-diff')).to_contain_text('after-124')
                page.screenshot(path=str(output/'admin-audit-detail.png'),full_page=True)
                page.get_by_role('button',name='Đóng chi tiết nhật ký').click()
                page.locator('.audit-clear').click()
                expect(page.locator('.audit-table tbody tr')).to_have_count(50)
                page.screenshot(path=str(output/'admin-audit-desktop.png'),full_page=True)
                navigate('chats')
                page.locator('.chat-thread').first.click()
                expect(page.locator('.chat-bubble')).to_have_count(50)
                page.locator('.chat-older').click()
                expect(page.locator('.chat-bubble')).to_have_count(100)
                page.locator('.chat-older').click()
                expect(page.locator('.chat-bubble')).to_have_count(130)
                expect(page.locator('.chat-older')).to_be_hidden()
                page.get_by_role('textbox',name='Trả lời người dùng').fill('Bản nháp giữ lại khi đổi hội thoại')
                page.locator('.chat-thread').nth(1).click()
                page.locator('.chat-thread').first.click()
                expect(page.get_by_role('textbox',name='Trả lời người dùng')).to_have_value('Bản nháp giữ lại khi đổi hội thoại')
                expect(page.locator('.chat-bubble')).to_have_count(50)
                page.locator('.chat-thread').first.evaluate('(el)=>{el.__stableMarker=123}')
                page.locator('.chat-history').evaluate('(el)=>{el.scrollTop=20}')
                with storage.database() as conn:
                    conn.execute("INSERT INTO chat_messages(thread_id,role,content,created_at) VALUES('smoke-thread-0','user','Em vừa gửi thêm ví dụ mới.',?)",(now+1,))
                expect(page.locator('.chat-bubble')).to_have_count(51,timeout=12000)
                assert page.locator('.chat-history').evaluate('(el)=>el.scrollTop') < 40
                assert page.locator('.chat-thread').first.evaluate('(el)=>el.__stableMarker') == 123
                expect(page.locator('.chat-new')).to_be_visible()
                page.locator('.chat-new').click()
                page.screenshot(path=str(output/'admin-inbox-desktop.png'),full_page=True)
                page.set_viewport_size({'width':390,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                page.screenshot(path=str(output/'admin-inbox-mobile.png'),full_page=True)
                page.locator('.chat-back').click()
                expect(page.locator('.chat-list')).to_be_visible()
                page.locator('.chat-thread').first.click()
                expect(page.locator('.chat-detail')).to_be_visible()
                navigate('ai')
                expect(page.locator('#ai-form')).to_be_visible()
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                page.screenshot(path=str(output/'admin-ai-mobile.png'),full_page=True)
                navigate('logs')
                expect(page.locator('.audit-table tbody tr')).to_have_count(50)
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                page.screenshot(path=str(output/'admin-audit-mobile.png'))
                assert not errors, errors
                browser.close()
            print('PASS: AI saves/tests without redraw, one navigation request, audit filters/pages/full changes, stable polling, old messages, drafts, desktop/mobile layouts')
        finally:
            server.should_exit = True
            worker.join(timeout=10)


if __name__ == '__main__':
    main()
