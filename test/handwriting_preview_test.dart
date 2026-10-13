import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hanzi_go/src/screens/handwriting_screen.dart';
import 'package:hanzi_go/src/services/student_service.dart';
import 'package:hanzi_go/src/widgets/hanzi_drawing_canvas.dart';
import 'package:hanzi_go/src/widgets/stroke_order_preview.dart';
import 'handwriting_word_test.dart' show WordService, draw;

class PreviewService extends WordService {
  @override
  Future<HanziStrokeGuide> fetchStrokeGuide(String char) async => HanziStrokeGuide(
    char: char, pinyin: 'ni', meaning: 'sample', hsk: 1, totalStrokes: 2,
    strokes: const [[Offset(100, 100), Offset(700, 700)], [Offset(700, 100), Offset(100, 700)]],
  );
}

void main() {
  testWidgets('compact preview leaves drawing guides off on mobile', (tester) async {
    await tester.binding.setSurfaceSize(const Size(320, 900));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(MaterialApp(home: HandwritingScreen(service: PreviewService(), startInPractice: true)));
    await tester.pump(const Duration(milliseconds: 300));
    final canvas = tester.widget<HanziDrawingCanvas>(find.byType(HanziDrawingCanvas));
    expect(canvas.guideStrokes, isNull);
    expect(canvas.showStrokeNumbers, isFalse);
    expect(canvas.activeGuideStrokeIndex, isNull);
    expect(tester.widget<StrokeOrderPreview>(find.byType(StrokeOrderPreview)).character, '你');
    await tester.pump(const Duration(seconds: 12));
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });
  testWidgets('preview follows a multi-character word and resets guide switches', (tester) async {
    await tester.binding.setSurfaceSize(const Size(900, 1800));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final service = PreviewService();
    await tester.pumpWidget(MaterialApp(home: HandwritingScreen(service: service, startInPractice: true)));
    await tester.pump(const Duration(milliseconds: 300));
    await tester.tap(find.text('Chọn chữ & hướng dẫn'));
    await tester.pump();
    await tester.tap(find.widgetWithText(FilterChip, 'Nét mờ'));
    await tester.pump();
    await tester.enterText(find.byType(TextField), 'xin chao');
    await tester.pump(const Duration(milliseconds: 500));
    await tester.pump();
    await tester.tap(find.text('你好啊'));
    await tester.pump(const Duration(milliseconds: 300));
    expect(tester.widget<FilterChip>(find.widgetWithText(FilterChip, 'Nét mờ')).selected, isFalse);
    expect(tester.widget<FilterChip>(find.widgetWithText(FilterChip, 'Số nét 1..N')).selected, isFalse);
    for (final character in ['你', '好', '啊']) {
      await tester.scrollUntilVisible(find.byKey(const Key('practice-stroke-preview')), -300,
        scrollable: find.byType(Scrollable).first);
      expect(tester.widget<StrokeOrderPreview>(find.byType(StrokeOrderPreview)).character, character);
      draw(tester);
      await tester.pump();
      await Scrollable.ensureVisible(tester.element(find.byKey(const Key('submit-handwriting'))), alignment: 0.5);
      await tester.pump(const Duration(milliseconds: 300));
      await tester.tap(find.byKey(const Key('submit-handwriting')));
      await tester.pump(const Duration(milliseconds: 300));
    }
    expect(service.targets, ['你', '好', '啊']);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });
}
