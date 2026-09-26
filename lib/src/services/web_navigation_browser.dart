import 'package:web/web.dart' as web;

void openAccount(String token, {int? returnTab}) {
  web.window.sessionStorage.setItem('hanzigo_account_token', token);
  if (returnTab != null) {
    web.window.sessionStorage.setItem('hanzigo_return_tab', returnTab.toString());
  }
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

void openReading(String token) {
  web.window.sessionStorage.setItem('hanzigo_account_token', token);
  web.window.location.assign('/reading');
}

int? getSavedReturnTab() {
  try {
    final val = web.window.sessionStorage.getItem('hanzigo_return_tab');
    if (val != null && val.isNotEmpty) {
      return int.tryParse(val);
    }
  } catch (_) {}
  return null;
}

void clearSavedReturnTab() {
  try {
    web.window.sessionStorage.removeItem('hanzigo_return_tab');
  } catch (_) {}
}
