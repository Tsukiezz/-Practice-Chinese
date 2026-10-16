const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('web/facebook_auth.js', 'utf8');
function context(enabled, reply) {
  let calls = 0;
  const window = {FB: {init() {}, login(cb) { calls++; cb(reply); }}};
  vm.runInNewContext(source, {window, fetch: async () => ({ok: true,
    json: async () => ({enabled, app_id: '123', version: 'v99.0'})}),
    document: {createElement() { throw Error('Unexpected SDK load'); }}});
  return {api: window.hanziGoFacebook, calls: () => calls};
}
(async () => {
  const disabled = context(false);
  assert.equal(await disabled.api.prepare('/api'), false);
  await assert.rejects(disabled.api.signIn());
  assert.equal(disabled.calls(), 0);
  const ready = context(true, {authResponse: {accessToken: 'verified-later'}});
  assert.equal(await ready.api.prepare('/api'), true);
  const pending = ready.api.signIn();
  assert.equal(ready.calls(), 1, 'Popup starts synchronously during click');
  assert.equal(await pending, 'verified-later');
  const cancel = context(true, {});
  await cancel.api.prepare('/api');
  await assert.rejects(cancel.api.signIn());
  console.log('Facebook SDK bridge tests passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
