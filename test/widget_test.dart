import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hanzi_go/src/app.dart';
import 'package:hanzi_go/src/models/reading_exam.dart';
import 'package:hanzi_go/src/services/reading_exam_service.dart';
import 'package:hanzi_go/src/services/listening_exam_service.dart';
import 'package:hanzi_go/src/services/auth_service.dart';

const _listeningExam = ReadingExam(
  id: 8,
  title: 'HSK 1 · Nghe hiểu mẫu',
  hsk: 1,
  durationMinutes: 10,
  version: 1,
  questions: [
    ReadingQuestion(
      id: 'l1',
      section: 'listening',
      prompt: 'Nghe và chọn nghĩa đúng',
      options: ['một', 'ngày mai', 'màu xanh'],
      audioUrl: 'https://example.com/audio.mp3',
    ),
  ],
);

const _exam = ReadingExam(
  id: 7,
  title: 'Đề đọc HSK 1',
  hsk: 1,
  durationMinutes: 10,
  version: 2,
  questions: [
    ReadingQuestion(
      id: 'q1',
      section: 'reading',
      prompt: '"你好" có nghĩa là gì?',
      options: ['Xin chào', 'Cảm ơn'],
    ),
    ReadingQuestion(
      id: 'q2',
      section: 'reading',
      prompt: 'Điền từ: 我___学习中文。',
      options: [],
    ),
  ],
);

class _FakeReadingRepository implements ReadingExamRepository {
  _FakeReadingRepository({this.loadError, this.submitError});

  final ReadingApiException? loadError;
  final ReadingApiException? submitError;
  Map<String, String>? submittedAnswers;

  @override
  Future<List<ReadingExam>> fetchReadingExams(int hsk) async {
    if (loadError != null) throw loadError!;
    return hsk == 1 ? const [_exam] : const [];
  }

  @override
  Future<ReadingResult> submitReadingExam(
    ReadingExam exam,
    Map<String, String> answers,
  ) async {
    if (submitError != null) throw submitError!;
    submittedAnswers = Map.of(answers);
    return const ReadingResult(
      id: 12,
      score: 100,
      feedback: 'Gemini đánh giá bài đọc tốt.',
      reviewItems: [
        ReadingReviewItem(
          id: 'q1',
          prompt: '"你好" có nghĩa là gì?',
          answer: 'Xin chào',
          submittedAnswer: 'Xin chào',
          explanation: '你好 là xin chào.',
        ),
        ReadingReviewItem(
          id: 'q2',
          prompt: 'Điền từ: 我___学习中文。',
          answer: '喜欢',
          submittedAnswer: '喜欢',
          explanation: '喜欢 nghĩa là yêu thích.',
        ),
      ],
    );
  }
}

class _FakeListeningRepository implements ListeningExamRepository {
  _FakeListeningRepository({this.loadError, this.submitError});

  final ListeningApiException? loadError;
  final ListeningApiException? submitError;
  Map<String, String>? submittedAnswers;

  @override
  Future<List<ReadingExam>> fetchListeningExams(int hsk) async {
    if (loadError != null) throw loadError!;
    return hsk == 1 ? const [_listeningExam] : const [];
  }

  @override
  Future<ReadingResult> submitListeningExam(
    ReadingExam exam,
    Map<String, String> answers,
  ) async {
    if (submitError != null) throw submitError!;
    submittedAnswers = Map.of(answers);
    return const ReadingResult(
      id: 13,
      score: 100,
      feedback: 'Nghe tốt lắm.',
      reviewItems: [
        ReadingReviewItem(
          id: 'l1',
          prompt: 'Nghe và chọn nghĩa đúng',
          answer: 'một',
          submittedAnswer: 'một',
          explanation: '一个人',
        ),
      ],
    );
  }
}

void main() {
  testWidgets('hiển thị trang chủ học tiếng Trung', (tester) async {
    await tester.pumpWidget(
      HanziGoApp(
        readingRepository: _FakeReadingRepository(),
        listeningRepository: _FakeListeningRepository(),
        authService: AuthService.test(),
      ),
    );
    expect(
      find.text('Mỗi ngày một chút,\ntiến bộ thật nhiều.'),
      findsOneWidget,
    );
    expect(find.text('Từ vựng hôm nay'), findsOneWidget);
  });

  testWidgets('tải và lọc đề đọc theo cấp độ HSK', (tester) async {
    await tester.pumpWidget(
      HanziGoApp(
        readingRepository: _FakeReadingRepository(),
        listeningRepository: _FakeListeningRepository(),
        authService: AuthService.test(),
      ),
    );
    await tester.tap(find.text('Đọc'));
    await tester.pumpAndSettle();

    expect(find.text('Test Đọc'), findsOneWidget);
    expect(find.text('Đề đọc HSK 1'), findsOneWidget);

    await tester.tap(find.byKey(const Key('hsk-3')));
    await tester.pumpAndSettle();

    expect(find.text('Chưa có đề Đọc HSK 3'), findsOneWidget);
  });

  testWidgets('tải và lọc đề nghe theo cấp độ HSK', (tester) async {
    await tester.pumpWidget(
      HanziGoApp(
        readingRepository: _FakeReadingRepository(),
        listeningRepository: _FakeListeningRepository(),
        authService: AuthService.test(),
      ),
    );
    await tester.tap(find.text('Nghe'));
    await tester.pumpAndSettle();

    expect(find.text('Test Nghe'), findsOneWidget);
    expect(find.text('HSK 1 · Nghe hiểu mẫu'), findsOneWidget);
  });

  testWidgets('nộp bài nghe và xem kết quả', (tester) async {
    final repository = _FakeListeningRepository();
    await tester.pumpWidget(
      HanziGoApp(
        readingRepository: _FakeReadingRepository(),
        listeningRepository: repository,
        authService: AuthService.test(),
      ),
    );
    await tester.tap(find.text('Nghe'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('listening-exam-8')));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('listening-answer-một')));
    await tester.pump();
    await tester.ensureVisible(find.byKey(const Key('listening-question-action')));
    await tester.tap(find.byKey(const Key('listening-question-action')));
    await tester.pumpAndSettle();

    expect(repository.submittedAnswers, {'l1': 'một'});
    expect(find.byKey(const Key('listening-result')), findsOneWidget);
    expect(find.text('100'), findsOneWidget);
    expect(find.text('KẾT QUẢ ĐÃ ĐƯỢC LƯU'), findsOneWidget);
  });

  testWidgets('hiển thị lỗi tải đề và cho phép thử lại', (tester) async {
    await tester.pumpWidget(
      HanziGoApp(
        readingRepository: _FakeReadingRepository(
          loadError: const ReadingApiException(401, 'Phiên đã hết hạn'),
        ),
        listeningRepository: _FakeListeningRepository(),
        authService: AuthService.test(),
      ),
    );
    await tester.tap(find.text('Đọc'));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('exam-error')), findsOneWidget);
    expect(find.text('Phiên đã hết hạn'), findsOneWidget);
    expect(find.text('Thử lại'), findsOneWidget);
  });

  testWidgets('nộp cả trắc nghiệm và điền từ rồi xem kết quả', (tester) async {
    final repository = _FakeReadingRepository();
    await tester.pumpWidget(
      HanziGoApp(
        readingRepository: repository,
        listeningRepository: _FakeListeningRepository(),
        authService: AuthService.test(),
      ),
    );
    await tester.tap(find.text('Đọc'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('exam-7')));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('answer-Xin chào')));
    await tester.pump();
    await tester.ensureVisible(find.byKey(const Key('question-action')));
    await tester.tap(find.byKey(const Key('question-action')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('text-answer')), findsOneWidget);
    await tester.enterText(find.byKey(const Key('text-answer')), '喜欢');
    await tester.pump();
    await tester.ensureVisible(find.byKey(const Key('question-action')));
    await tester.tap(find.byKey(const Key('question-action')));
    await tester.pumpAndSettle();

    expect(repository.submittedAnswers, {'q1': 'Xin chào', 'q2': '喜欢'});
    expect(find.byKey(const Key('reading-result')), findsOneWidget);
    expect(find.text('100'), findsOneWidget);
    expect(find.text('KẾT QUẢ ĐÃ ĐƯỢC LƯU'), findsOneWidget);
    expect(find.byKey(const Key('ai-feedback')), findsOneWidget);
  });

  testWidgets('hiển thị lỗi 409 khi đề thay đổi trước lúc nộp', (tester) async {
    final repository = _FakeReadingRepository(
      submitError: const ReadingApiException(409, 'Dữ liệu đã thay đổi'),
    );
    await tester.pumpWidget(
      HanziGoApp(
        readingRepository: repository,
        listeningRepository: _FakeListeningRepository(),
        authService: AuthService.test(),
      ),
    );
    await tester.tap(find.text('Đọc'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('exam-7')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('answer-Xin chào')));
    await tester.pump();
    await tester.ensureVisible(find.byKey(const Key('question-action')));
    await tester.tap(find.byKey(const Key('question-action')));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('text-answer')), '喜欢');
    await tester.pump();
    await tester.ensureVisible(find.byKey(const Key('question-action')));
    await tester.tap(find.byKey(const Key('question-action')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('submit-error')), findsOneWidget);
    expect(find.textContaining('Đề vừa được cập nhật'), findsOneWidget);
  });
}
