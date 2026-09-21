import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:hanzi_go/src/screens/lessons_screen.dart';
import 'package:hanzi_go/src/screens/lesson_study_screen.dart';
import 'package:hanzi_go/src/services/student_service.dart';

final _fixture = jsonDecode(
  File('test/fixtures/lesson_course.json').readAsStringSync(),
) as Map<String, dynamic>;
final _lessons = (_fixture['lessons'] as List).cast<Map<String, dynamic>>();

class LessonFake extends StudentService {
  LessonFake()
      : super(baseUrl: 'http://test/api', tokenProvider: () async => 'session');
  bool failLoad = false, failSave = false;
  int stage = 0, submissions = 0;
  Map<String, int>? sent;
  @override
  Future<Map<String, dynamic>> fetchLessons() async {
    if (failLoad) throw const StudentApiException(503, 'Tạm thời mất kết nối');
    return {..._fixture, 'items': _lessons};
  }

  @override
  Future<List<Map<String, dynamic>>> fetchLessonProgress() async => stage == 0
      ? []
      : [
          {'lesson_id': 'hsk1-01', 'stage': stage, 'best_score': 100},
        ];
  @override
  Future<Map<String, dynamic>> fetchLesson(String id) async =>
      _lessons.firstWhere((l) => l['id'] == id);
  @override
  Future<void> saveLessonStage(String id, int value) async {
    if (failSave) throw const StudentApiException(503, 'Mất kết nối');
    stage = value;
  }

  @override
  Future<Map<String, dynamic>> submitLesson(
    String id,
    Map<String, int> answers,
  ) async {
    if (failSave) throw const StudentApiException(503, 'Mất kết nối');
    submissions++;
    sent = Map.of(answers);
    stage = 4;
    return {
      'score': 100,
      'passed': true,
      'progress': {'best_score': 100},
      'review': [
        for (final q in _lessons.first['questions'] as List)
          {
            'id': q['id'],
            'correct': true,
            'answer': q['answer'],
            'explanation': q['explanation'],
          },
      ],
    };
  }
}

void main() {
  test(
      'lesson service uses authenticated progress and server-side answer submission',
      () async {
    final paths = <String>[];
    final service = StudentService(
      baseUrl: 'http://test/api',
      tokenProvider: () async => 'token',
      client: MockClient((r) async {
        paths.add('${r.method} ${r.url.path}');
        expect(r.headers['Authorization'], 'Bearer token');
        if (r.method == 'POST') {
          expect(jsonDecode(r.body), {
            'answers': {'q1': 2, 'q2': 0, 'q3': 1, 'q4': 2},
          });
        }
        if (r.method == 'PUT') expect(jsonDecode(r.body), {'stage': 2});
        return http.Response(
          r.url.path == '/api/me/lessons' ? '[]' : '{}',
          200,
        );
      }),
    );
    await service.fetchLessons();
    await service.fetchLesson('hsk1-01');
    await service.fetchLessonProgress();
    await service.saveLessonStage('hsk1-01', 2);
    await service.submitLesson('hsk1-01', {'q1': 2, 'q2': 0, 'q3': 1, 'q4': 2});
    expect(paths, [
      'GET /api/lessons',
      'GET /api/lessons/hsk1-01',
      'GET /api/me/lessons',
      'PUT /api/me/lessons/hsk1-01/progress',
      'POST /api/me/lessons/hsk1-01/submit',
    ]);
  });

  testWidgets('320px roadmap filters HSK6, search and empty state', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(320, 740);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: LessonsScreen(service: LessonFake())),
      ),
    );
    await tester.pumpAndSettle();
    final filter = find.byKey(const ValueKey('hsk-filter-6'));
    await tester.ensureVisible(filter);
    await tester.tap(filter);
    await tester.pumpAndSettle();
    expect(find.textContaining('HSK 6 · Đọc sâu'), findsOneWidget);
    final input = find.byType(TextField);
    await tester.ensureVisible(input);
    await tester.enterText(input, 'khongtontai');
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('Xóa bộ lọc'));
    expect(find.text('Chưa có bài phù hợp với bộ lọc.'), findsOneWidget);
    await tester.tap(find.text('Xóa bộ lọc'));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });

  testWidgets('loading failure offers retry without inventing progress', (
    tester,
  ) async {
    final service = LessonFake()..failLoad = true;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: LessonsScreen(service: service)),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.textContaining('Chưa tải được lộ trình'), findsOneWidget);
    service.failLoad = false;
    await tester.tap(find.text('Thử lại'));
    await tester.pumpAndSettle();
    expect(find.textContaining('0/2 bài hoàn thành'), findsOneWidget);
  });

  testWidgets(
    'mobile study resumes, retries save, submits and explains answers',
    (tester) async {
      tester.view.physicalSize = const Size(320, 740);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final service = LessonFake()..failSave = true;
      await tester.pumpWidget(
        MaterialApp(
          home: LessonStudyScreen(
            service: service,
            lessonId: 'hsk1-01',
            initialStage: 1,
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text('02 · Mẫu câu và cách dùng'), findsOneWidget);
      final next = find.byKey(const ValueKey('lesson-next'));
      await tester.tap(next);
      await tester.pumpAndSettle();
      expect(find.textContaining('Chưa lưu được'), findsOneWidget);
      service.failSave = false;
      await tester.tap(next);
      await tester.pumpAndSettle();
      expect(service.stage, 2);
      final translation = find.text('Xem bản dịch tiếng Việt');
      await tester.scrollUntilVisible(translation, 200,
          scrollable: find
              .descendant(
                  of: find.byType(ListView), matching: find.byType(Scrollable))
              .first);
      await tester.tap(translation);
      await tester.pumpAndSettle();
      expect(
        find.text((_lessons.first['reading'] as Map)['meaning'] as String),
        findsOneWidget,
      );
      await tester.tap(next);
      await tester.pumpAndSettle();
      await tester.tap(next);
      await tester.pumpAndSettle();
      expect(find.textContaining('Bạn cần chọn'), findsOneWidget);
      expect(service.submissions, 0);
      for (final q in _lessons.first['questions'] as List) {
        final option = find.byKey(ValueKey('answer-${q['id']}-${q['answer']}'));
        await tester.scrollUntilVisible(option, 200,
            scrollable: find
                .descendant(
                    of: find.byType(ListView),
                    matching: find.byType(Scrollable))
                .first);
        await Scrollable.ensureVisible(tester.element(option), alignment: 0.35);
        await tester.pumpAndSettle();
        await tester.tap(option);
        await tester.pumpAndSettle();
      }
      await tester.tap(next);
      await tester.pumpAndSettle();
      expect(service.sent!.length, 4);
      expect(find.text('100% · Đã hoàn thành bài'), findsOneWidget);
      expect(service.submissions, 1);
      await tester.scrollUntilVisible(find.text('Làm lại câu hỏi'), 200,
          scrollable: find
              .descendant(
                  of: find.byType(ListView), matching: find.byType(Scrollable))
              .first);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Làm lại câu hỏi'));
      await tester.pumpAndSettle();
      expect(find.text('Nộp bài · 0/4 câu'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('desktop roadmap and large text do not overflow', (tester) async {
    tester.view.physicalSize = const Size(1100, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(
        builder: (_, child) => MediaQuery(
          data: const MediaQueryData(textScaler: TextScaler.linear(1.5)),
          child: child!,
        ),
        home: Scaffold(body: LessonsScreen(service: LessonFake())),
      ),
    );
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byKey(const ValueKey('lesson-hsk6-01')));
    expect(tester.takeException(), isNull);
  });
}
