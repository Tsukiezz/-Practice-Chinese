"""Browser smoke test for learner support sessions (isolated mocked API)."""
import asyncio
import base64
import json
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)
        page = await browser.new_page(viewport={"width":390,"height":844})
        state = {"now": 1800000000, "started": 0, "messages": [], "active": False, "serial":0, "requests":[], "fail_next":False}
        def snapshot():
            return {"id":"thread1", "active":state["active"], "session_key":str(state["started"]),
                    "state":"ai" if state["active"] else "closed", "busy_until":0,
                    "server_now":state["now"], "expires_at":state["now"]+300,
                    "messages":state["messages"] if state["active"] else []}
        async def route(req):
            if '/attachments/' in req.request.url:
                data = {'filename':'notes.txt','data_base64':base64.b64encode(b'Learn Chinese').decode()}
            elif req.request.url.endswith('/session'):
                state["started"] += 1
                state["active"] = True
                state["messages"] = []
                data = snapshot()
            elif req.request.method == 'POST':
                body = req.request.post_data_json
                state['requests'].append(body['request_id'])
                if state['fail_next']:
                    state['fail_next'] = False
                    await req.fulfill(status=503, content_type='application/json', body=json.dumps({'detail':'Temporary test error'}))
                    return
                state['serial'] += 1
                state["messages"] += [{"id":state["serial"],"role":"user","content":body["content"],"created_at":state["now"],"request_id":body["request_id"],"attachment":({"id":1,"filename":body["attachment"]["filename"],"size":12} if body.get("attachment") else None)}]
                await asyncio.sleep(0.3)
                data = {"accepted":True}
            else:
                data = snapshot()
            await req.fulfill(status=200, content_type='application/json', body=json.dumps(data))
        await page.route('https://support.test/api/chat/**', route)
        await page.route('https://support.test/', lambda r: r.fulfill(body='<html><body></body></html>', content_type='text/html'))
        await page.goto('https://support.test/')
        await page.clock.install()
        await page.add_script_tag(content=Path('admin/support-widget.js').read_text(encoding='utf-8'))
        assert await page.locator('button:visible').count() == 1
        assert state['started'] == 0
        assert '💬' in await page.locator('#launch').inner_text()
        await page.locator('#launch').click()
        assert state['started'] == 0
        assert not await page.locator('textarea').is_visible()
        await page.locator('#start').click()
        await page.locator('textarea').fill('My private question')
        await page.locator('#send').click()
        assert await page.locator('textarea').input_value() == ''
        await page.locator('textarea').fill('Next draft while waiting for AI')
        await page.wait_for_function("document.querySelector('body > div').shadowRoot.querySelector('#messages').textContent.includes('My private question')")
        assert await page.locator('textarea').input_value() == 'Next draft while waiting for AI'
        await page.locator('textarea').fill('Unsent private draft')
        state['active'] = False
        state['now'] += 301
        await page.clock.fast_forward(301000)
        await page.locator('#start').wait_for(state='visible')
        assert await page.locator('#messages').inner_text() == ''
        assert await page.locator('textarea').input_value() == ''
        assert await page.locator('#start').is_visible()
        assert not await page.locator('textarea').is_visible()
        assert state['started'] == 1
        await page.locator('#start').click()
        assert state['started'] == 2
        assert 'My private question' not in await page.locator('#messages').inner_text()
        await page.locator('textarea').wait_for(state='visible')
        await page.locator('#file').set_input_files({'name':'notes.txt','mimeType':'text/plain','buffer':b'Learn Chinese'})
        await page.wait_for_function("!document.querySelector('body > div').shadowRoot.querySelector('#send').disabled")
        await page.locator('#send').click()
        await page.get_by_role('button', name='Tải notes.txt', exact=False).wait_for()
        assert await page.locator('textarea').input_value() == ''
        assert not await page.locator('#selected').is_visible()
        async with page.expect_download() as download_info:
            await page.get_by_role('button', name='Tải notes.txt', exact=False).click()
        downloaded = await download_info.value
        assert downloaded.suggested_filename == 'notes.txt'
        state['fail_next'] = True
        await page.locator('textarea').fill('Retry this question')
        await page.locator('#send').click()
        await page.locator('#retry-send').wait_for(state='visible')
        await page.locator('textarea').fill('New draft after the error')
        await page.locator('#retry-send').click()
        await page.wait_for_function("!document.querySelector('body > div').shadowRoot.querySelector('#send').disabled")
        assert state['requests'][-1] == state['requests'][-2]
        assert await page.locator('textarea').input_value() == 'New draft after the error'
        await page.screenshot(path='test-results/support-session-mobile.png')
        admin = await browser.new_page()
        await admin.set_content('<main></main>')
        await admin.add_script_tag(content=Path('admin/support-inbox.js').read_text(encoding='utf-8').replace('export function ', 'function '))
        await admin.evaluate('''() => {
          const archived = {id:'archive',name:'Test learner',state:'closed',busy_until:0,updated_at:1800000000,
            messages:[{id:1,role:'user',content:'Archived private question',created_at:1800000000}]};
          renderChatInbox(document.querySelector('main'), {items:[archived],total:1,counts:{closed:1}}, async () => archived);
        }''')
        await admin.locator('.chat-thread').click()
        await admin.get_by_text('Archived private question', exact=True).wait_for()
        assert await admin.locator('.chat-compose textarea').is_disabled()
        assert await admin.locator('.chat-compose button.primary').is_disabled()
        assert await admin.locator('.resume').is_disabled()
        assert await admin.locator('.take').is_disabled()
        await browser.close()
        print('PASS: inner start button, immediate draft clearing, next draft preserved, file upload, expiry and admin archive')

asyncio.run(main())
