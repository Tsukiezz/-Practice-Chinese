import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hanzi_go/src/screens/dashboard_screen.dart';
import 'package:hanzi_go/src/screens/handwriting_screen.dart';
import 'package:hanzi_go/src/screens/review_screen.dart';
import 'package:hanzi_go/src/screens/vocabulary_screen.dart';
import 'package:hanzi_go/src/services/student_service.dart';

StudentResult _studentResult({
  int id = 1,
  String kind = 'writing',
  double score = 60,
  String feedback = 'Cần luyện lại.',
  double? latestScore,
  String? latestFeedback,
}) =>
    StudentResult(
      id: id,
      examId: null,
      kind: kind,
      content: jsonEncode({'content': '我学习中文。', 'target': '一'}),
      score: score,
      originalScore: score,
      feedback: feedback,
      gradedBy: 'ai',
      version: 1,
      createdAt: 1,
      overrides: const [],
      latestScore: latestScore,
      latestFeedback: latestFeedback,
    );

class _FakeStudentService extends StudentService {
  _FakeStudentService()
      : super(baseUrl: 'http://test/api', tokenProvider: () async => 'token');

  String? handwritingTarget;
  List<VocabularyEntry> history = const [];

  static const word = VocabularyEntry(
    id: 1,
    hanzi: '你好',
    pinyin: 'nǐ hǎo',
    meaning: 'xin chào',
    hsk: 1,
    example: '你好！',
    audioUrl: '',
  );

  @override
  Future<StudentDashboard> fetchMyDashboard() async => const StudentDashboard(
        results: 4,
        averageScore: 82,
        needsReview: 1,
        vocabularyCount: 6,
        streak: 3,
        progressPercent: 82,
        skillScores: {
          'listening': 90,
          'reading': 80,
          'writing': 70,
          'handwriting': 88,
        },
      );

  @override
  Future<CapabilityReport> fetchCapabilityReport() async =>
      const CapabilityReport(
        skillScores: {
          'listening': 90,
          'reading': 80,
          'writing': 70,
          'handwriting': 88,
        },
        feedback: 'Gemini nhận thấy kỹ năng nghe là điểm mạnh.',
        strengths: ['Nghe tốt'],
        improvements: ['Luyện viết câu dài hơn'],
      );

  @override
  Future<List<VocabularyEntry>> fetchVocabulary({String search = ''}) async =>
      const [word];

  @override
  Future<List<VocabularyEntry>> fetchDictionaryHistory() async => history;

  @override
  Future<VocabularyEntry> recordDictionaryLookup(
    VocabularyEntry word,
    String query,
  ) async {
    history = [word];
    return word;
  }

  @override
  Future<List<StudentResult>> fetchReviewItems(String kind) async => [
        _studentResult(
          kind: kind,
          latestScore: 72,
          latestFeedback: 'Lần gần nhất đã tiến bộ.',
        ),
      ];

  @override
  Future<StudentResult> submitHandwriting(
    String target,
    List<List<Map<String, double>>> strokes, {
    int? sourceResultId,
  }) async {
    handwritingTarget = target;
    return _studentResult(
      kind: 'handwriting',
      score: 92,
      feedback: 'Nét viết cân đối.',
    );
  }
}

void main() {
  testWidgets('Dashboard hiển thị dữ liệu thật và nhận xét Gemini',
      (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: DashboardScreen(service: _FakeStudentService()),
    ));
    await tester.pumpAndSettle();

    expect(find.text('3'), findsOneWidget);
    expect(find.text('4'), findsOneWidget);
    expect(find.text('6'), findsOneWidget);
    expect(find.byKey(const Key('skill-radar')), findsOneWidget);
    expect(find.text('Gemini nhận thấy kỹ năng nghe là điểm mạnh.'),
        findsOneWidget);
  });

  testWidgets('mở từ sẽ ghi lịch sử và tạo Flashcard', (tester) async {
    final service = _FakeStudentService();
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(body: VocabularyScreen(service: service)),
    ));
    await tester.pumpAndSettle();

    await tester.tap(find.text('nǐ hǎo'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Đóng'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Lịch sử'));
    await tester.pumpAndSettle();

    expect(find.text('Ôn Flashcard (1 từ)'), findsOneWidget);
  });

  testWidgets('Canvas ngón tay gửi nét cho Gemini và hiện điểm',
      (tester) async {
    final service = _FakeStudentService();
    await tester
        .pumpWidget(MaterialApp(home: HandwritingScreen(service: service)));
    await tester.enterText(find.byKey(const Key('handwriting-target')), '一');
    await tester.pump();
    final canvas = find.byKey(const Key('handwriting-canvas'));
    final gesture = await tester.startGesture(tester.getCenter(canvas));
    await gesture.moveBy(const Offset(80, 5));
    await gesture.moveBy(const Offset(80, 5));
    await gesture.up();
    await tester.pump();
    await tester.drag(find.byType(ListView), const Offset(0, -500));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('submit-handwriting')));
    await tester.pumpAndSettle();

    expect(service.handwritingTarget, '一');
    expect(find.text('92 điểm'), findsOneWidget);
    expect(find.text('Nét viết cân đối.'), findsOneWidget);
  });

  testWidgets('danh sách ôn tập hiện kết quả nộp lại gần nhất', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: ReviewScreen(service: _FakeStudentService()),
    ));
    await tester.pumpAndSettle();

    expect(find.text('72'), findsOneWidget);
    expect(find.text('Lần gần nhất đã tiến bộ.'), findsOneWidget);
  });
}
