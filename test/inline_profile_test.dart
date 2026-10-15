import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:hanzi_go/src/widgets/inline_account.dart';
import 'package:hanzi_go/src/widgets/inline_install.dart';

void main() {
  testWidgets('Password changes require matching confirmation and re-login', (tester) async {
    var changed = false, posts = 0;
    final client = MockClient((request) async {
      if (request.method == 'POST') {
        posts++;
        expect(request.url.path, '/api/account/password');
        expect(jsonDecode(request.body)['new_password'], 'new-password-123');
        return http.Response('', 204);
      }
      return http.Response('{"name":"Learner","email":"a@example.test"}', 200);
    });
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: ListView(children: [
      InlineAccount(baseUrl: 'http://test/api', token: 'token', client: client,
        onPasswordChanged: () => changed = true),
    ]))));
    await tester.tap(find.text('Thông tin cá nhân'));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('Đổi mật khẩu'));
    await tester.drag(find.byType(ListView), const Offset(0, -250));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Đổi mật khẩu'));
    await tester.pumpAndSettle();
    await tester.enterText(find.widgetWithText(TextFormField, 'Mật khẩu cũ'), 'old-password');
    await tester.enterText(find.widgetWithText(TextFormField, 'Mật khẩu mới'), 'new-password-123');
    await tester.enterText(find.widgetWithText(TextFormField, 'Nhập lại mật khẩu mới'), 'wrong');
    await tester.ensureVisible(find.text('Lưu mật khẩu'));
    await tester.drag(find.byType(ListView), const Offset(0, -450));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Lưu mật khẩu'));
    await tester.pumpAndSettle();
    expect(posts, 0);
    expect(find.text('Mật khẩu chưa khớp.'), findsOneWidget);
    await tester.enterText(find.widgetWithText(TextFormField, 'Nhập lại mật khẩu mới'), 'new-password-123');
    await tester.ensureVisible(find.text('Lưu mật khẩu'));
    await tester.tap(find.text('Lưu mật khẩu'));
    await tester.pumpAndSettle();
    expect(posts, 1);
    expect(changed, isTrue);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Account load can retry and failed saves retain input',
      (tester) async {
    var calls = 0;
    final client = MockClient((request) async {
      calls++;
      if (calls == 1 || request.method == 'PUT') {
        return http.Response('{"detail":"Try again"}', 503);
      }
      return http.Response('{"name":"Original","email":"a@example.test"}', 200);
    });
    await tester.pumpWidget(MaterialApp(
        home: Scaffold(
            body: ListView(children: [
      InlineAccount(baseUrl: 'http://test/api', token: 'token', client: client),
    ]))));
    await tester.tap(find.text('Thông tin cá nhân'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Try again'), findsOneWidget);
    await tester.tap(find.text('Tải thông tin'));
    await tester.pumpAndSettle();
    await tester.enterText(
        find.widgetWithText(TextFormField, 'Họ tên'), 'Unsaved');
    await tester.ensureVisible(find.text('Lưu thay đổi'));
    await tester.tap(find.text('Lưu thay đổi'));
    await tester.pumpAndSettle();
    expect(find.text('Unsaved'), findsOneWidget);
    expect(find.textContaining('Try again'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Profile loads lazily, saves in place, and retains goals/avatar',
      (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    var gets = 0, saves = 0, refreshed = 0;
    final client = MockClient((request) async {
      expect(request.headers['Authorization'], 'Bearer user-token');
      if (request.method == 'GET') gets++;
      if (request.method == 'PUT') {
        saves++;
        final data = jsonDecode(request.body);
        expect(data['name'], 'New name');
        expect(data['phone'], '0123456789');
        expect(data['daily_goal'], 3);
        expect(data['weekly_goal'], 15);
        expect(data['avatar'], '');
      }
      return http.Response(
          jsonEncode({
            'name': 'Original',
            'email': 'a@example.test',
            'phone': '0123456789',
            'birth_date': '2000-01-02',
            'avatar': '',
            'daily_goal': 3,
            'weekly_goal': 15
          }),
          200);
    });
    await tester.pumpWidget(MaterialApp(
        home: Scaffold(
            body: ListView(children: [
      InlineAccount(
          baseUrl: 'http://test/api',
          token: 'user-token',
          client: client,
          onSaved: () => refreshed++),
    ]))));
    expect(gets, 0);
    await tester.tap(find.text('Thông tin cá nhân'));
    await tester.pumpAndSettle();
    expect(gets, 1);
    await tester.enterText(
        find.widgetWithText(TextFormField, 'Họ tên'), 'New name');
    await tester.ensureVisible(find.text('Lưu thay đổi'));
    await tester.tap(find.text('Lưu thay đổi'));
    await tester.pumpAndSettle();
    expect(saves, 1);
    expect(refreshed, 1);
    expect(find.text('Đã lưu thông tin cá nhân.'), findsWidgets);
    expect(find.byType(InlineAccount), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Install guides expand without replacing the profile',
      (tester) async {
    await tester.pumpWidget(MaterialApp(
        home: Scaffold(
            body: ListView(children: const [
      Text('Cá nhân'),
      InlineInstall(),
    ]))));
    await tester.tap(find.text('Cài HanziGo trên Android / iOS'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('iPhone / iPad · Safari'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Mở HanziGo bằng Safari'), findsOneWidget);
    expect(find.text('Cá nhân'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
