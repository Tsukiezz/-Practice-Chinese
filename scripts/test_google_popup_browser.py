"""WebKit/Chromium user-activation checks with a fake GIS client, never real OAuth."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def check(base):
    with sync_playwright() as p:
        for engine in ('webkit', 'chromium'):
            browser = (p.webkit.launch(headless=True) if engine == 'webkit'
                       else p.chromium.launch(channel='msedge', headless=True))
            context = browser.new_context(viewport={'width': 390, 'height': 844},
                                          is_mobile=True, has_touch=True)
            page = context.new_page()
            page.goto(base + '/install-android.html')
            page.set_content('<button id="google">Google sign in</button>')
            page.add_script_tag(url=base + '/google_auth.js')
            page.evaluate("""() => {
                window.google = {accounts:{oauth2:{
                    initTokenClient(options) {
                        window.lastOptions = options;
                        return {requestAccessToken() {
                            window.activeAtPopup = navigator.userActivation.isActive;
                            window.popupHandle = window.open('about:blank', 'google-test');
                            if (!window.popupHandle) options.error_callback({type:'popup_failed_to_open'});
                        }};
                    }
                }}};
                document.querySelector('#google').onclick = () => {
                    window.hanziGoGoogle.signIn('local-test-client')
                        .catch(err => {window.lastError = err.code;});
                };
            }""")
            with page.expect_popup() as opened:
                page.locator('#google').tap()
            assert page.evaluate('window.activeAtPopup') is True
            opened.value.close()
            page.evaluate("window.lastOptions.error_callback({type:'popup_closed'})")
            page.wait_for_function("window.lastError === 'popup_closed'")
            # A fresh tap can retry; no sticky connecting/popup state in the bridge.
            with page.expect_popup() as retry:
                page.locator('#google').tap()
            assert page.evaluate('window.activeAtPopup') is True
            retry.value.close()
            browser.close()
            print(f'PASS: {engine} mobile touch opens popup with active gesture and can retry')


if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', 0),
        partial(QuietHandler, directory=str(ROOT / 'web')))
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        check(f'http://127.0.0.1:{server.server_port}')
    finally:
        server.shutdown()
        server.server_close()
