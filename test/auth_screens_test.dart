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
      expect(request.url.path, '/api/auth/register');
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
    expect(succeeded, true);
    expect(auth.currentUser!.role, 'student');
    expect(tester.takeException(), isNull);
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
}
