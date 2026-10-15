"""Browser checks for Android PWA install flow, using a local static server."""
import asyncio
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


async def check(base):
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel='msedge', headless=True)
        context = await browser.new_context(viewport={'width': 360, 'height': 800}, is_mobile=True, has_touch=True)
        page = await context.new_page()
        await page.goto(base + '/install-android.html')
        await page.evaluate('navigator.serviceWorker.ready')
        await page.wait_for_function('navigator.serviceWorker.controller !== null')
        assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        await page.locator('[data-install-app]').click()
        assert 'Chrome' in await page.locator('[data-install-status]').inner_text()
        for outcome in ['dismissed', 'accepted']:
            await page.evaluate('''outcome => {
                const event = new Event('beforeinstallprompt', {cancelable:true});
                event.prompt = async () => { window.promptCount = (window.promptCount || 0) + 1; };
                event.userChoice = Promise.resolve({outcome});
                window.dispatchEvent(event);
            }''', outcome)
            assert await page.locator('[data-install-app]').inner_text() == 'Cài HanziGo'
            await page.locator('[data-install-app]').click()
            await page.wait_for_function('!document.querySelector("[data-install-app]").disabled')
        assert await page.evaluate('window.promptCount') == 2
        await page.evaluate("window.dispatchEvent(new Event('appinstalled'))")
        assert not await page.locator('[data-install-app]').is_visible()
        assert await page.evaluate('caches.keys()') == []
        await context.set_offline(True)
        response = await page.reload()
        assert response.status == 503
        assert 'HanziGo đang chờ kết nối' in await page.locator('h1').inner_text()
        assert await page.evaluate("fetch('/api/chat/messages').then(() => false).catch(() => true)")
        await context.set_offline(False)
        await page.get_by_role('link', name='Thử lại').click()
        await page.locator('[data-install-app]').wait_for()
        output = ROOT / 'test-results'
        output.mkdir(exist_ok=True)
        await page.screenshot(path=str(output / 'android-install-mobile.png'), full_page=True)
        standalone = await context.new_page()
        await standalone.add_init_script('''const original = window.matchMedia.bind(window);
            window.matchMedia = query => query === '(display-mode: standalone)' ? {matches:true} : original(query);''')
        await standalone.goto(base + '/install-android.html')
        assert not await standalone.locator('[data-install-app]').is_visible()
        assert 'cửa sổ ứng dụng' in await standalone.locator('[data-install-status]').inner_text()
        await browser.close()
        print('PASS: mobile layout, manual install, prompt outcomes, standalone, offline recovery, API pass-through')


if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT / 'web')))
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        asyncio.run(check(f'http://127.0.0.1:{server.server_port}'))
    finally:
        server.shutdown()
        server.server_close()
