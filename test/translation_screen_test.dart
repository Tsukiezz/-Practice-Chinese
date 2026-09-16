import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hanzi_go/src/screens/translation_screen.dart';
import 'package:hanzi_go/src/services/student_service.dart';

class _GrammarService extends StudentService {
  _GrammarService()
      : super(baseUrl: 'http://test/api', tokenProvider: () async => 'token');

  String? sentence;
  String? intendedContext;

  @override
  Future<GrammarAnalysisResult> analyzeGrammar(
    String sentence, {
    String context = '',
  }) async {
    this.sentence = sentence;
    intendedContext = context;
    return const GrammarAnalysisResult(
      score: 72,
      feedback: 'Thứ tự trạng từ chưa tự nhiên.',
      errors: [
        GrammarCorrectionError(
          position: 'trước 学习',
          original: '学习每天',
          suggestion: '每天学习',
          reason: 'Trạng từ thời gian đứng trước động từ.',
        ),
      ],
      correctedSentence: '我每天学习中文。',
    );
  }
}

void main() {
  testWidgets('gửi câu thật và hiển thị phân tích có cấu trúc', (tester) async {
    final service = _GrammarService();
    await tester.pumpWidget(
      MaterialApp(home: TranslationScreen(service: service)),
    );

    await tester.enterText(
      find.byKey(const Key('grammar-sentence')),
      '我学习每天中文。',
    );
    await tester.enterText(
      find.byKey(const Key('grammar-context')),
      'Tôi học tiếng Trung mỗi ngày.',
    );
    await tester.tap(find.byKey(const Key('submit-grammar')));
    await tester.pumpAndSettle();

    expect(service.sentence, '我学习每天中文。');
    expect(service.intendedContext, 'Tôi học tiếng Trung mỗi ngày.');
    expect(find.byKey(const Key('grammar-result')), findsOneWidget);
    expect(find.text('我每天学习中文。'), findsOneWidget);
    expect(find.text('学习每天  →  每天学习'), findsOneWidget);
    expect(find.textContaining('Trạng từ thời gian'), findsOneWidget);
  });

  testWidgets('không gửi khi câu trống', (tester) async {
    final service = _GrammarService();
    await tester.pumpWidget(
      MaterialApp(home: TranslationScreen(service: service)),
    );

    await tester.tap(find.byKey(const Key('submit-grammar')));
    await tester.pump();

    expect(service.sentence, isNull);
    expect(find.byKey(const Key('grammar-error')), findsOneWidget);
  });
}
