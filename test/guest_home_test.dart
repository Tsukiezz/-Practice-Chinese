import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:hanzi_go/src/screens/home_screen.dart';
import 'package:hanzi_go/src/screens/vocabulary_screen.dart';
import 'package:hanzi_go/src/services/student_service.dart';

void main() {
  testWidgets('mobile home uses account name and opens lessons', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(320, 740);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    var opened = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: HomeScreen(
            userName: 'Nguyễn Văn Nguyên',
            onOpenLessons: () => opened = true,
          ),
        ),
      ),
    );
    expect(find.text('Xin chào, Nguyễn Văn Nguyên'), findsOneWidget);
    expect(find.text('Minh Anh'), findsNothing);
    await tester.tap(find.text('Bắt đầu học'));
    expect(opened, isTrue);
    expect(tester.takeException(), isNull);
  });

  testWidgets('guest can read word without private API calls', (tester) async {
    final requests = <String>[];
    final service = StudentService(
      baseUrl: 'http://test/api',
      tokenProvider: () async => null,
      client: MockClient((request) async {
        requests.add(request.url.path);
        expect(request.headers.containsKey('Authorization'), isFalse);
        return http.Response.bytes(
          utf8.encode(
            jsonEncode({
              'total': 1,
              'offset': 0,
              'limit': 40,
              'topics': [],
              'items': [
                {
                  'id': 1,
                  'hanzi': '你好',
                  'pinyin': 'ni hao',
                  'meaning': 'Xin chào',
                  'hsk': 1,
                  'example': '你好！',
                  'audio_url': '',
                },
              ]
            }),
          ),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      }),
    );
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: VocabularyScreen(service: service, guest: true)),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('你好'));
    await tester.pumpAndSettle();
    expect(find.text('你好！'), findsOneWidget);
    expect(requests, ['/api/vocabulary/page']);
    expect(find.text('Lịch sử'), findsNothing);
    await expectLater(
      service.fetchSavedVocabulary(),
      throwsA(isA<StudentApiException>()),
    );
  });
}
