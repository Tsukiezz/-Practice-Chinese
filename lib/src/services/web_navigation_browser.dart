import 'package:web/web.dart' as web;

void openAccount(String token) {
  web.window.sessionStorage.setItem('hanzigo_account_token', token);
  web.window.location.assign('/account');
}

void openRecovery() => web.window.location.assign('/recover');

void openAdmin(String token) {
  web.window.sessionStorage.setItem('hanzigo_admin_token', token);
  web.window.location.replace('/admin');
}

void openExam(String token) {
  web.window.sessionStorage.setItem('hanzigo_account_token', token);
  web.window.location.assign('/exam');
}
