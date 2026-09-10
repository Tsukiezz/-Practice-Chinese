import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:hanzi_go/src/services/auth_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test('login stores server role, refresh verifies role, logout clears session',
      () async {
    SharedPreferences.setMockInitialValues({});
    final client = MockClient((request) async {
      if (request.url.path.endsWith('/login')) {
        return http.Response(
            jsonEncode({
              'token': 'test-token',
              'expires_in': 3600,
              'user': {
                'id': 1,
                'name': 'Test',
                'email': 'test@example.test',
                'role': 'admin'
              }
            }),
            200);
      }
      expect(request.headers['Authorization'], 'Bearer test-token');
      if (request.url.path.endsWith('/me')) {
        return http.Response(
            jsonEncode({
              'id': 1,
              'name': 'Test',
              'email': 'test@example.test',
              'role': 'student'
            }),
            200);
      }
      return http.Response('', 204);
    });
    final auth = await AuthService.load(client);
    await auth.login(
        baseUrl: 'http://localhost/api',
        email: 'test@example.test',
        password: 'test-password');
    expect(auth.currentUser!.isAdmin, true);
    expect(auth.isAuthenticated, true);
    await auth.refreshUser('http://localhost/api');
    expect(auth.currentUser!.isAdmin, false);
    await auth.logout();
    expect(auth.token, isNull);
    expect(auth.isAuthenticated, false);
    client.close();
  });
}
