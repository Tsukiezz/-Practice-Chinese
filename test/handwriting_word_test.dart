import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hanzi_go/src/screens/handwriting_screen.dart';
import 'package:hanzi_go/src/services/student_service.dart';
import 'package:hanzi_go/src/widgets/hanzi_drawing_canvas.dart';

class WordService extends StudentService {
  WordService() : super(baseUrl: 'http://test/api', tokenProvider: () async => 'test');
  final targets = <String>[];
  @override
  Future<HanziStrokeGuide> fetchStrokeGuide(String hanzi) async => throw Exception('No guide');
  @override
  Future<List<VocabularyEntry>> fetchVocabulary({String search = ''}) async => const [
    VocabularyEntry(id: 1, hanzi: '你好啊', pinyin: 'nǐ hǎo a', meaning: 'xin chào', hsk: 1, example: '', audioUrl: ''),
  ];
  @override
  Future<HandwritingGradeResult> submitHandwriting(String target, List<List<Map<String, double>>> strokes, {int? sourceResultId}) async {
    targets.add(target);
    return const HandwritingGradeResult(score: 35, feedback: 'Cần luyện thêm.', wrongStrokes: []);
  }
  @override
  Future<HandwritingRecognitionResult> recognizeHandwriting(List<List<Map<String, double>>> strokes, {bool guest = false}) async {
    expect(strokes.length, 2);
    return const HandwritingRecognitionResult(score: 95, feedback: 'Xin chào', recognizedHanzi: '你好', candidates: []);
  }
}

void draw(WidgetTester tester) {
  final canvas = tester.widget<HanziDrawingCanvas>(find.byType(HanziDrawingCanvas));
  canvas.controller.start(const Offset(30, 50), const Size(100, 100));
  canvas.controller.update(const Offset(70, 50), const Size(100, 100));
  canvas.controller.end();
  canvas.onChanged!();
}

void main() {
  testWidgets('lookup removes keyboard exits and displays a complete two-character result', (tester) async {
    await tester.binding.setSurfaceSize(const Size(900, 1400));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(MaterialApp(home: HandwritingScreen(service: WordService(), guest: true)));
    await tester.pumpAndSettle();
    expect(find.byIcon(Icons.keyboard), findsNothing);
    expect(find.byKey(const Key('switch-to-keyboard-btn')), findsNothing);
    draw(tester); draw(tester);
    await tester.pump();
    await tester.ensureVisible(find.byKey(const Key('submit-handwriting')));
    await tester.tap(find.byKey(const Key('submit-handwriting')));
    await tester.pumpAndSettle();
    expect(find.text('你好'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
  testWidgets('practice keeps all characters and advances even for a low nonzero score', (tester) async {
    await tester.binding.setSurfaceSize(const Size(900, 1600));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final service = WordService();
    await tester.pumpWidget(MaterialApp(home: HandwritingScreen(service: service)));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Luyện nét'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'xin chào');
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pumpAndSettle();
    await tester.tap(find.text('你好啊'));
    await tester.pumpAndSettle();
    for (var i = 0; i < 3; i++) {
      expect(find.text('Từ: 你好啊 · Chữ ${i + 1}/3'), findsOneWidget);
      draw(tester);
      await tester.pump();
      await tester.ensureVisible(find.byKey(const Key('submit-handwriting')));
      await tester.tap(find.byKey(const Key('submit-handwriting')));
      await tester.pumpAndSettle();
    }
    expect(service.targets, ['你', '好', '啊']);
    expect(find.byKey(const Key('practice-word-complete')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
