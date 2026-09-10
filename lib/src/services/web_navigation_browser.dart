import 'package:web/web.dart' as web;

void openAdmin(String token) {
  web.window.sessionStorage.setItem('hanzigo_admin_token', token);
  web.window.location.replace('/admin');
}
