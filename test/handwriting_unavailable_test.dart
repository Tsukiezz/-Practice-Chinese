import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hanzi_go/src/screens/handwriting_screen.dart';
import 'package:hanzi_go/src/services/student_service.dart';
import 'handwriting_preview_test.dart' show PreviewService;
import 'handwriting_word_test.dart' show draw;

class UnavailableRecognitionService extends PreviewService {
  @override
  Future<HandwritingRecognitionResult> recognizeHandwriting(
    List<List<Map<String, double>>> strokes, {bool guest = false}) async {
    throw Exception('Recognition unavailable');
  }
}

void main() {
  testWidgets('blind practice uses self-check when recognition is unavailable', (tester) async {
    await tester.binding.setSurfaceSize(const Size(900, 1800));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final service = UnavailableRecognitionService();
    await tester.pumpWidget(MaterialApp(home: HandwritingScreen(
      service: service, startInPractice: true)));
    await tester.pump(const Duration(milliseconds: 300));
    await tester.tap(find.text('Chọn chữ & hướng dẫn'));
    await tester.pump();
    await tester.tap(find.byKey(const Key('blind-pinyin-mode')));
    await tester.pump(const Duration(milliseconds: 300));
    draw(tester);
    await tester.pump();
    await Scrollable.ensureVisible(
      tester.element(find.byKey(const Key('submit-handwriting'))), alignment: 0.5);
    await tester.pump(const Duration(milliseconds: 300));
    await tester.tap(find.byKey(const Key('submit-handwriting')));
    await tester.pump(const Duration(milliseconds: 300));
    expect(find.text('So sánh với đáp án'), findsOneWidget);
    expect(find.textContaining('Chính xác!'), findsNothing);
    expect(find.textContaining('Chưa đúng, thử lại'), findsNothing);
    expect(service.targets, isEmpty);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });
}
