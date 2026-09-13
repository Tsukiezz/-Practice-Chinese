import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:hanzi_go/src/services/auth_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test('registration sends identity only and saves the server session',
      () async {
    SharedPreferences.setMockInitialValues({});
    final client = MockClient((request) async {
      expect(request.url.path, '/api/auth/register');
      expect(jsonDecode(request.body), {
        'name': 'Tuyến',
        'email': 'tuyen@example.test',
        'password': ' pass-123 '
      });
      return http.Response(
          jsonEncode({
            'token': 'new-token',
            'expires_in': 3600,
            'user': {
              'id': 3,
              'name': 'Tuyến',
              'email': 'tuyen@example.test',
              'role': 'student'
            }
          }),
          201,
          headers: {'content-type': 'application/json; charset=utf-8'});
    });
    final auth = await AuthService.load(client);
    await auth.register(
        baseUrl: 'http://test/api',
        name: ' Tuyến ',
        email: ' tuyen@example.test ',
        password: ' pass-123 ');
    expect(auth.currentUser!.name, 'Tuyến');
    expect(auth.currentUser!.isAdmin, false);
    expect((await AuthService.load(client)).token, 'new-token');
  });

  test('unchecked remember keeps session in memory only', () async {
    SharedPreferences.setMockInitialValues({'auth_token': 'old-token'});
    final client = MockClient((request) async => http.Response(
        jsonEncode({
          'token': 'temporary-token',
          'user': {
            'id': 1,
            'name': 'Test',
            'email': 'test@example.test',
            'role': 'student'
          }
        }),
        200));
    final auth = await AuthService.load(client);
    await auth.login(
        baseUrl: 'http://test/api',
        email: 'test@example.test',
        password: 'password',
        remember: false);
    expect(auth.isAuthenticated, true);
    expect(auth.token, 'temporary-token');
    expect((await AuthService.load(client)).token, isNull);
  });

  test(
      'registration reports duplicate and validation responses without saving session',
      () async {
    for (final response in [
      http.Response('{"detail":"Email already used"}', 409),
      http.Response('{"detail":[{"msg":"invalid"}]}', 422),
      http.Response('<html>Unavailable</html>', 503)
    ]) {
      SharedPreferences.setMockInitialValues({});
      final auth = await AuthService.load(MockClient((_) async => response));
      await expectLater(
          auth.register(
              baseUrl: 'http://test/api',
              name: 'Test',
              email: 'test@example.test',
              password: 'password'),
          throwsA(isA<AuthException>()));
      expect(auth.token, isNull);
    }
  });
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
