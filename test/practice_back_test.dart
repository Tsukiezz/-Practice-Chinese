import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:hanzi_go/src/screens/practice_screen.dart';
import 'package:hanzi_go/src/services/reading_exam_service.dart';

void main() {
  testWidgets('Test Tong hop has a working back button on mobile', (tester) async {
    SharedPreferences.setMockInitialValues({});
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final repository = ReadingExamService(baseUrl: 'http://test/api',
      tokenProvider: () async => 'test', comprehensive: true,
      client: MockClient((_) async => http.Response('[]', 200)));
    await tester.pumpWidget(MaterialApp(home: Builder(builder: (context) => Scaffold(
      body: TextButton(onPressed: () => Navigator.push(context,
        MaterialPageRoute<void>(builder: (_) => PracticeScreen(
          repository: repository, title: 'Test Tổng hợp'))),
        child: const Text('Open'))))));
    await tester.tap(find.text('Open'));
    await tester.pumpAndSettle();
    expect(find.text('Quay lại'), findsOneWidget);
    await tester.tap(find.text('Quay lại'));
    await tester.pumpAndSettle();
    expect(find.byType(PracticeScreen), findsNothing);
    expect(find.text('Open'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
