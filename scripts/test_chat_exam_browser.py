"""Real browser regression of chat hiding and blocked activation during exams."""
from pathlib import Path
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    page = browser.new_page(viewport={'width':390, 'height':844})
    leases = set()
    def route(request):
        if '/api/chat/exam-guard' in request.request.url:
            if request.request.method == 'POST':
                data = request.request.post_data_json
                if data['active']: leases.add(data['lease'])
                else: leases.discard(data['lease'])
            request.fulfill(json={'blocked':bool(leases)})
        elif '/api/chat/session' in request.request.url:
            request.fulfill(json={'id':'test','active':True,'messages':[], 'session_key':'test',
                'server_now':100,'expires_at':400,'busy_until':0,'state':'ai'})
        else:
            request.fulfill(body='<html><body>Test</body></html>',content_type='text/html')
    page.route('https://test.local/**',route)
    page.goto('https://test.local/')
    page.add_script_tag(path=str(Path('admin/support-widget.js').resolve()))
    page.evaluate("window.dispatchEvent(new CustomEvent('hanzigo-chat-session',{detail:'test-token'}))")
    page.get_by_role('button',name='💬 Hỏi HanziGo').click()
    assert page.get_by_role('region',name='Trò chuyện với HanziGo').is_visible()
    assert page.evaluate("window.hanziGoExamGuard.start('exam_browser_test')") is True
    assert not page.get_by_role('button',name='💬 Hỏi HanziGo').is_visible()
    assert not page.get_by_role('region',name='Trò chuyện với HanziGo').is_visible()
    page.evaluate("document.querySelector('div').shadowRoot.querySelector('#launch').click()")
    assert not page.get_by_role('region',name='Trò chuyện với HanziGo').is_visible()
    assert page.evaluate("window.hanziGoExamGuard.start('exam_second_test')") is True
    page.evaluate("window.hanziGoExamGuard.end('exam_browser_test')")
    assert not page.get_by_role('button',name='💬 Hỏi HanziGo').is_visible()
    page.evaluate("window.hanziGoExamGuard.end('exam_second_test')")
    page.get_by_role('button',name='💬 Hỏi HanziGo').wait_for(state='visible')
    page.get_by_role('button',name='💬 Hỏi HanziGo').click()
    assert page.get_by_role('region',name='Trò chuyện với HanziGo').is_visible()
    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
    browser.close()
print('Browser exam chat guard passed')
