import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:hanzi_go/src/screens/login_screen.dart';
import 'package:hanzi_go/src/services/auth_service.dart';

void main() {
  testWidgets(
      'Tuyen registration validates confirmation and returns authenticated student',
      (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    SharedPreferences.setMockInitialValues({});
    var requests = 0;
    var succeeded = false;
    final auth = await AuthService.load(MockClient((request) async {
      requests++;
      if (request.url.path == '/api/auth/register-request') {
        return http.Response.bytes(
            utf8.encode(jsonEncode({'status': 'ok', 'message': 'Mã xác thực đã được gửi'})),
            200,
            headers: {'content-type': 'application/json; charset=utf-8'});
      }
      expect(request.url.path, '/api/auth/register-verify');
      return http.Response(
          jsonEncode({
            'token': 'registered',
            'user': {
              'id': 2,
              'name': 'Tuyen',
              'email': 'tuyen@example.test',
              'role': 'student'
            }
          }),
          201);
    }));
    await tester.pumpWidget(MaterialApp(
        home: LoginScreen(
            baseUrl: 'http://test/api',
            authService: auth,
            onLoginSuccess: () => succeeded = true)));
    await tester.tap(find.text('Đăng ký mới'));
    await tester.pumpAndSettle();
    final fields = find.byType(TextField);
    await tester.enterText(fields.at(0), 'Tuyen');
    await tester.enterText(fields.at(1), 'tuyen@example.test');
    await tester.enterText(fields.at(2), 'password-123');
    await tester.enterText(fields.at(3), 'wrong-password');
    await tester.ensureVisible(find.byType(CheckboxListTile));
    await tester.tap(find.byType(CheckboxListTile));
    await tester.pumpAndSettle();
    final submit = find.widgetWithText(ElevatedButton, 'Tạo tài khoản');
    await tester.ensureVisible(submit);
    await tester.tap(submit);
    await tester.pumpAndSettle();
    expect(find.text('Mật khẩu xác nhận không khớp.'), findsOneWidget);
    expect(requests, 0);
    await tester.enterText(fields.at(3), 'password-123');
    await tester.ensureVisible(submit);
    await tester.tap(submit);
    await tester.pumpAndSettle();
    expect(requests, 1);
    final codeField = find.byType(TextField).first;
    await tester.enterText(codeField, '123456');
    final confirmBtn =
        find.widgetWithText(ElevatedButton, 'Xác nhận & Hoàn tất');
    await tester.ensureVisible(confirmBtn);
    await tester.tap(confirmBtn);
    await tester.pumpAndSettle();
    expect(requests, 2);
    expect(auth.currentUser!.role, 'student');
    expect(succeeded, isTrue);
  });

  testWidgets('mobile login shows server error and permits retry',
      (tester) async {
    tester.view.physicalSize = const Size(320, 568);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    SharedPreferences.setMockInitialValues({});
    final auth = await AuthService.load(MockClient(
        (_) async => http.Response('{"detail":"Incorrect password"}', 401)));
    await tester.pumpWidget(MaterialApp(
        home: LoginScreen(
            baseUrl: 'http://test/api',
            authService: auth,
            onLoginSuccess: () {})));
    await tester.enterText(find.byType(TextField).at(0), 'test@example.test');
    await tester.enterText(find.byType(TextField).at(1), 'password-123');
    final submit = find.widgetWithText(ElevatedButton, 'Đăng nhập');
    await tester.ensureVisible(submit);
    await tester.tap(submit);
    await tester.pumpAndSettle();
    expect(find.text('Incorrect password'), findsOneWidget);
    expect(tester.widget<ElevatedButton>(submit).onPressed, isNotNull);
    expect(auth.token, isNull);
    expect(tester.takeException(), isNull);
  });

  testWidgets('session expires when user has been inactive for more than 24 hours',
      (tester) async {
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    final staleTime = now - 90000; // hơn 24 giờ trước (25 giờ)
    final userJson = jsonEncode({
      'id': 10,
      'name': 'Hoc Vien Cu',
      'email': 'cu@example.test',
      'role': 'student',
      'expires_at': now + 50000,
    });
    SharedPreferences.setMockInitialValues({
      'auth_token': 'stale_token_123',
      'auth_user': userJson,
      'auth_last_active_at': staleTime,
    });

    final auth = await AuthService.load(MockClient((_) async => http.Response('{}', 200)));
    expect(auth.isSessionExpiredDueToInactivity, isTrue);
    expect(auth.isAuthenticated, isFalse);

    // Khi người dùng mới hoạt động gần đây (ví dụ 10 phút trước)
    final recentTime = now - 600;
    SharedPreferences.setMockInitialValues({
      'auth_token': 'fresh_token_456',
      'auth_user': userJson,
      'auth_last_active_at': recentTime,
    });
    final activeAuth = await AuthService.load(MockClient((_) async => http.Response('{}', 200)));
    expect(activeAuth.isSessionExpiredDueToInactivity, isFalse);
    expect(activeAuth.isAuthenticated, isTrue);
  });
}
