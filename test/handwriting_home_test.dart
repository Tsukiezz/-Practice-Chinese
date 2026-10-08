import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hanzi_go/src/screens/handwriting_screen.dart';
import 'package:hanzi_go/src/widgets/hanzi_drawing_canvas.dart';
import 'handwriting_word_test.dart' show WordService;

void main() {
  testWidgets('Writing opens first and dictionary is a secondary action', (tester) async {
    var openedDictionary = false;
    await tester.pumpWidget(MaterialApp(home: HandwritingScreen(
      service: WordService(), startInPractice: true,
      onOpenVocabulary: () => openedDictionary = true,
    )));
    await tester.pumpAndSettle();
    expect(find.byType(HanziDrawingCanvas), findsOneWidget);
    expect(find.byType(TextField), findsNothing);
    expect(find.text('Chọn chữ & hướng dẫn'), findsOneWidget);
    expect(find.byTooltip('Xám đá (Premium)'), findsOneWidget);
    await tester.tap(find.text('Từ vựng'));
    expect(openedDictionary, isTrue);
    await tester.tap(find.text('Chọn chữ & hướng dẫn'));
    await tester.pumpAndSettle();
    expect(find.byType(TextField), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
