import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hanzi_go/src/widgets/learning_status.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:hanzi_go/src/services/student_service.dart';

void main() {
  testWidgets('Header flame shows server count and refreshes when tab changes', (tester) async {
    var count = 3;
    final client = MockClient((_) async => http.Response(jsonEncode({
      'results': 0, 'average_score': 0, 'needs_review': 0, 'vocabulary_count': 0,
      'streak': count, 'progress_percent': 0, 'skill_scores': {},
      'streak_details': {'current': count, 'next_milestone': 14},
    }), 200));
    final service = StudentService(baseUrl: 'https://example.test/api', tokenProvider: () async => 'test', client: client);
    Widget frame(int tab) => MaterialApp(home: Scaffold(body: HeaderStreak(service: service, refreshKey: tab)));
    await tester.pumpWidget(frame(0));
    await tester.pumpAndSettle();
    expect(find.text('3'), findsOneWidget);
    expect(find.byIcon(Icons.local_fire_department), findsOneWidget);
    count = 7;
    await tester.pumpWidget(frame(1));
    await tester.pumpAndSettle();
    expect(find.text('7'), findsOneWidget);
    expect(find.text('3'), findsNothing);
    await tester.tap(find.text('7'));
    await tester.pumpAndSettle();
    expect(find.text('Chuỗi ngày học & bảo lưu'), findsOneWidget);
    expect(find.text('7 ngày liên tiếp'), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
    client.close();
  });
  test('Vietnam greeting switches at exactly 06:00 and 18:00 UTC+7', () {
    expect(vietnamGreeting(DateTime.utc(2026, 10, 5, 22, 59), 'An'), 'Chào buổi tối, An');
    expect(vietnamGreeting(DateTime.utc(2026, 10, 5, 23), 'An'), 'Chào buổi sáng, An');
    expect(vietnamGreeting(DateTime.utc(2026, 10, 6, 10, 59), 'An'), 'Chào buổi sáng, An');
    expect(vietnamGreeting(DateTime.utc(2026, 10, 6, 11), 'An'), 'Chào buổi tối, An');
    expect(vietnamTime(DateTime.utc(2026, 10, 5, 23)).day, 6);
    expect(vietnamGreeting(DateTime.utc(2026, 10, 6, 11), ' '), 'Chào buổi tối, bạn');
  });

  testWidgets('Vietnam clock renders and disposes its timer', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: Scaffold(body: VietnamGreeting(name: 'An'))));
    expect(find.textContaining('Giờ Việt Nam'), findsOneWidget);
    expect(find.textContaining(', An'), findsOneWidget);
    await tester.pump(const Duration(seconds: 1));
    await tester.pumpWidget(const SizedBox());
    expect(tester.takeException(), isNull);
  });
}
