import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hanzi_go/src/screens/handwriting_retry_screen.dart';
import 'package:hanzi_go/src/services/student_service.dart';

class _RetryService extends StudentService {
  _RetryService()
      : super(baseUrl: 'http://test/api', tokenProvider: () async => 'token');

  final List<HandwritingRetryItem> items = [
    const HandwritingRetryItem(
      hanzi: '一',
      latestScore: 40,
      attempts: 2,
      lastPracticedAt: 1,
    ),
    const HandwritingRetryItem(
      hanzi: '人',
      latestScore: 70,
      attempts: 1,
      lastPracticedAt: 2,
    ),
  ];
  final List<String> submittedTargets = [];

  @override
  Future<List<HandwritingRetryItem>> fetchHandwritingRetryItems() async =>
      List.unmodifiable(items);

  @override
  Future<HandwritingGradeResult> submitHandwriting(
    String target,
    List<List<Map<String, double>>> strokes, {
    int? sourceResultId,
  }) async {
    submittedTargets.add(target);
    items.removeWhere((item) => item.hanzi == target);
    return const HandwritingGradeResult(
      score: 85,
      feedback: 'Đã đạt yêu cầu.',
      wrongStrokes: [],
      countScore: 100,
      orderPositionScore: 75,
      directionScore: 85,
    );
  }
}

void main() {
  testWidgets('chọn nhiều chữ và loại khỏi danh sách sau khi đạt 80',
      (tester) async {
    await tester.binding.setSurfaceSize(const Size(900, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final service = _RetryService();
    await tester.pumpWidget(MaterialApp(
      home: HandwritingRetryScreen(service: service),
    ));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('handwriting-retry-list')), findsOneWidget);
    await tester.tap(find.byKey(const Key('retry-一')));
    await tester.tap(find.byKey(const Key('retry-人')));
    await tester.pump();
    await tester.tap(find.byKey(const Key('start-retry-session')));
    await tester.pumpAndSettle();
    expect(find.text('一'), findsOneWidget);

    final firstCanvas = find.byKey(const Key('retry-canvas'));
    await tester.ensureVisible(firstCanvas);
    await tester.pumpAndSettle();
    final firstGesture = find.descendant(
      of: firstCanvas,
      matching: find.byType(GestureDetector),
    );
    final firstDetector = tester.widget<GestureDetector>(firstGesture);
    firstDetector.onPanStart!(
      DragStartDetails(localPosition: const Offset(100, 200)),
    );
    firstDetector.onPanUpdate!(
      DragUpdateDetails(
        globalPosition: const Offset(300, 200),
        localPosition: const Offset(300, 200),
        delta: const Offset(200, 0),
      ),
    );
    firstDetector.onPanEnd!(DragEndDetails());
    await tester.pump();
    await tester.ensureVisible(find.byKey(const Key('submit-retry')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('submit-retry')));
    await tester.pump(const Duration(milliseconds: 300));
    expect(find.byKey(const Key('retry-error')), findsNothing);
    expect(service.submittedTargets, ['一']);
    expect(find.text('人'), findsOneWidget);

    final secondCanvas = find.byKey(const Key('retry-canvas'));
    await tester.ensureVisible(secondCanvas);
    await tester.pumpAndSettle();
    final secondGesture = find.descendant(
      of: secondCanvas,
      matching: find.byType(GestureDetector),
    );
    final secondDetector = tester.widget<GestureDetector>(secondGesture);
    secondDetector.onPanStart!(
      DragStartDetails(localPosition: const Offset(200, 100)),
    );
    secondDetector.onPanUpdate!(
      DragUpdateDetails(
        globalPosition: const Offset(200, 300),
        localPosition: const Offset(200, 300),
        delta: const Offset(0, 200),
      ),
    );
    secondDetector.onPanEnd!(DragEndDetails());
    await tester.pump();
    await tester.ensureVisible(find.byKey(const Key('submit-retry')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('submit-retry')));
    await tester.pump(const Duration(milliseconds: 300));

    expect(service.submittedTargets, ['一', '人']);
    expect(find.byKey(const Key('retry-empty')), findsOneWidget);
  });
}
