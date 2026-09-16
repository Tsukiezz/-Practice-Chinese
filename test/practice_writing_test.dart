import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hanzi_go/src/models/reading_exam.dart';
import 'package:hanzi_go/src/screens/practice_screen.dart';
import 'package:hanzi_go/src/services/reading_exam_service.dart';

const _writingExam = ReadingExam(
  id: 44,
  title: 'Test viết UC-04',
  hsk: 1,
  durationMinutes: 15,
  version: 1,
  questions: [
    ReadingQuestion(
      id: 'canvas',
      section: 'writing',
      questionType: 'hanzi_canvas',
      prompt: 'Viết chữ 一',
      options: [],
    ),
    ReadingQuestion(
      id: 'essay',
      section: 'writing',
      questionType: 'essay',
      prompt: 'Viết về gia đình',
      options: [],
    ),
  ],
);

class _WritingRepository implements ReadingExamRepository {
  Map<String, dynamic>? submittedAnswers;

  @override
  Future<List<ReadingExam>> fetchReadingExams(int hsk) async =>
      hsk == 1 ? const [_writingExam] : const [];

  @override
  Future<ReadingResult> submitReadingExam(
    ReadingExam exam,
    Map<String, dynamic> answers,
  ) async {
    submittedAnswers = Map<String, dynamic>.from(answers);
    return const ReadingResult(
      id: 1,
      score: 80.5,
      feedback: 'Đã chấm hai câu viết.',
      reviewItems: [],
    );
  }
}

void main() {
  testWidgets('canvas nhận chuột và essay gửi object đúng contract',
      (tester) async {
    await tester.binding.setSurfaceSize(const Size(1000, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final repository = _WritingRepository();
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(body: PracticeScreen(repository: repository)),
    ));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('exam-44')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('exam-hanzi-canvas')), findsOneWidget);

    final canvas = find.byKey(const Key('exam-hanzi-canvas'));
    final center = tester.getCenter(canvas);
    await tester.dragFrom(center.translate(-120, 0), const Offset(240, 0));
    await tester.pump();
    await tester.ensureVisible(find.byKey(const Key('question-action')));
    await tester.tap(find.byKey(const Key('question-action')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('essay-answer')), findsOneWidget);
    await tester.enterText(
      find.byKey(const Key('essay-answer')),
      '我家有三个人。我们每天一起吃饭。',
    );
    await tester.pump();
    await tester.ensureVisible(find.byKey(const Key('question-action')));
    await tester.pumpAndSettle();
    expect(
      tester
          .widget<FilledButton>(find.byKey(const Key('question-action')))
          .onPressed,
      isNotNull,
    );
    await tester.tap(find.byKey(const Key('question-action')));
    await tester.pumpAndSettle();

    final canvasAnswer =
        repository.submittedAnswers!['canvas'] as Map<String, dynamic>;
    final essayAnswer =
        repository.submittedAnswers!['essay'] as Map<String, dynamic>;
    expect(canvasAnswer['kind'], 'hanzi_canvas');
    expect(canvasAnswer['strokes'], isNotEmpty);
    expect(essayAnswer, {
      'kind': 'essay',
      'text': '我家有三个人。我们每天一起吃饭。',
    });
  });
}
