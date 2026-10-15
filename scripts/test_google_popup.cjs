// Deterministic GIS boundary checks. No real Google credentials or requests.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('web/google_auth.js', 'utf8');
function fixture(sdk = true) {
  let options, calls = 0;
  const window = {addEventListener() {}, dispatchEvent() {}};
  if (sdk) window.google = {accounts: {oauth2: {
    initTokenClient(value) {
      options = value;
      return {requestAccessToken() { calls++; }};
    },
  }}};
  vm.runInNewContext(source, {
    window, Promise, JSON,
    setInterval() { throw Error('Popup must not be delayed by a timer'); },
    fetch: async () => ({ok: true, json: async () => ({
      email: 'learner@example.test', name: 'Learner', sub: '123',
    })}),
  });
  return {window, get options() {return options;}, get calls() {return calls;}};
}
(async () => {
  const f = fixture();
  const result = f.window.hanziGoGoogle.signIn('client');
  assert.equal(f.calls, 1, 'GIS request must run synchronously inside user tap');
  f.options.callback({access_token: 'fake-local-test'});
  assert.equal((await result).email, 'learner@example.test');
  const blocked = f.window.hanziGoGoogle.signIn('client');
  f.options.error_callback({type: 'popup_failed_to_open', message: 'Failed to open popup window'});
  await assert.rejects(blocked, e => e.code === 'popup_failed_to_open' && e.message.includes('Safari'));
  const closed = f.window.hanziGoGoogle.signIn('client');
  f.options.error_callback({type: 'popup_closed'});
  await assert.rejects(closed, e => e.message.includes('đóng cửa sổ'));
  const noSdk = fixture(false);
  await assert.rejects(noSdk.window.hanziGoGoogle.signIn('client'), e => e.code === 'SDK_NOT_LOADED');
  assert.equal(noSdk.calls, 0);
  console.log('PASS: synchronous popup, success, blocked, cancelled, SDK-not-ready; no delayed opening');
})().catch(error => { console.error(error); process.exitCode = 1; });
