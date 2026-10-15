import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:hanzi_go/src/screens/ai_exam_screen.dart';
import 'package:hanzi_go/src/services/ai_exam_service.dart';

void main() {
  AIExamService service() => AIExamService(
    baseUrl: 'http://test/api', tokenProvider: () async => 'test',
    client: MockClient((r) async => http.Response(
      r.url.path.endsWith('/topics') ? '[]' : '{}', 200)),
  );

  testWidgets('Exam tab back button calls app navigation on mobile', (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    var backs = 0;
    await tester.pumpWidget(MaterialApp(home: AiExamScreen(
      service: service(), onBack: () => backs++)));
    await tester.pumpAndSettle();
    expect(find.text('Quay lại'), findsOneWidget);
    await tester.tap(find.text('Quay lại'));
    expect(backs, 1);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Pushed exam screen can return without an app callback', (tester) async {
    await tester.pumpWidget(MaterialApp(home: Builder(builder: (context) => Scaffold(
      body: TextButton(onPressed: () => Navigator.push(context,
        MaterialPageRoute<void>(builder: (_) => AiExamScreen(service: service()))),
        child: const Text('Mở đề thi')),
    ))));
    await tester.tap(find.text('Mở đề thi'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Quay lại'));
    await tester.pumpAndSettle();
    expect(find.text('Mở đề thi'), findsOneWidget);
    expect(find.byType(AiExamScreen), findsNothing);
  });
}
