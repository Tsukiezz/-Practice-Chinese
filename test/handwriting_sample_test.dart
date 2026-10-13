import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hanzi_go/src/widgets/handwriting_sample_card.dart';
import 'package:hanzi_go/src/screens/home_screen.dart';

void main() {
  testWidgets('home advertises one sample and opens its practice callback', (tester) async {
    tester.view.physicalSize = const Size(320, 740);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    var opened = false;
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: HomeScreen(
      onOpenLessons: () {}, onOpenHandwritingSample: () => opened = true,
    ))));
    await tester.scrollUntilVisible(find.byKey(const Key('home-handwriting-sample')), 200,
      scrollable: find.byType(Scrollable).first);
    await tester.ensureVisible(find.byKey(const Key('home-handwriting-sample')));
    await tester.pump(const Duration(milliseconds: 300));
    expect(find.byType(HandwritingSampleCard), findsOneWidget);
    await tester.tap(find.byKey(const Key('home-handwriting-sample')));
    expect(opened, isTrue);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('sample loops and opens practice without layout errors', (tester) async {
    var opened = 0;
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: SizedBox(
      width: 320,
      child: HandwritingSampleCard(onPractice: () => opened++),
    ))));
    await tester.pump(const Duration(seconds: 8));
    expect(tester.takeException(), isNull);
    await tester.pump(const Duration(seconds: 13));
    expect(tester.binding.transientCallbackCount, greaterThan(0));
    await tester.tap(find.byType(FilledButton));
    expect(opened, 1);
    await tester.tap(find.byKey(const Key('home-handwriting-sample')));
    expect(opened, 2);
    await tester.pumpWidget(const SizedBox());
    await tester.pump();
    expect(tester.binding.transientCallbackCount, 0);
    expect(tester.takeException(), isNull);
  });
}
