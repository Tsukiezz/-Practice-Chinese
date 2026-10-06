import 'dart:js_interop';
import 'dart:convert';
import 'package:web/web.dart' as web;

void setChatTheme(Map<String, String> colors) {
  web.window.dispatchEvent(web.CustomEvent('hanzigo-chat-theme',
      web.CustomEventInit(detail: jsonEncode(colors).toJS)));
}

void setChatSession(String? token) {
  web.window.dispatchEvent(web.CustomEvent('hanzigo-chat-session',
      web.CustomEventInit(detail: (token ?? '').toJS)));
}

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

void openReading(String token, {int? hsk}) {
  if (token.isNotEmpty) web.window.sessionStorage.setItem('hanzigo_account_token', token);
  web.window.location.assign(hsk == null ? '/reading' : '/reading?hsk=$hsk');
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

bool openPayment(String url) {
  final saved = web.window.localStorage.getItem('flutter.auth_token');
  if (saved != null) {
    try {
      final token = jsonDecode(saved);
      if (token is String && token.isNotEmpty) {
        web.window.sessionStorage.setItem('hanzigo_account_token', token);
      }
    } catch (_) {}
  }
  web.window.location.assign(url);
  return true;
}
