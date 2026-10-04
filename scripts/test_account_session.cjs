const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const html = fs.readFileSync(path.join(__dirname, '../admin/account.html'), 'utf8');
const source = html.slice(html.indexOf('let token='), html.indexOf("let avatar="));
function tokenFor(session, persisted) {
  return vm.runInNewContext(source + '\ntoken;', {
    sessionStorage: { getItem: () => session },
    localStorage: { getItem: () => persisted },
  });
}
assert.equal(tokenFor(null, JSON.stringify('flutter-session')), 'flutter-session');
assert.equal(tokenFor('account-session', null), 'account-session');
assert.equal(tokenFor(null, null), '');
assert.equal(tokenFor(null, 'broken-json'), '');
console.log('Account session bridge: 4 checks passed');
