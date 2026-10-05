import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:hanzi_go/src/services/auth_service.dart';
import 'package:hanzi_go/src/services/benefits_service.dart';
import 'package:hanzi_go/src/theme/app_theme.dart';
import 'package:hanzi_go/src/screens/appearance_screen.dart';
import 'package:hanzi_go/src/widgets/hanzi_drawing_canvas.dart';

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
    BenefitsService.instance.clear();
    ThemeManager.themeMode.value = ThemeMode.light;
  });
  tearDown(() => BenefitsService.instance.clear());

  test('cached premium flag does not outlive its expiry', () {
    const user = AuthUser(id: 1, name: 'Test', email: 'test@example.test', role: 'student',
      expiresAt: 0, premiumUntil: 1, isPremium: true);
    expect(user.isVip, isFalse);
  });

  test('server preferences survive reload and clear on account switch', () async {
    var state = <String, dynamic>{'premium_until': DateTime.now().millisecondsSinceEpoch ~/ 1000 + 3600,
      'brush': 'default', 'palette': 'dark', 'streak_freezes': 3};
    final client = MockClient((request) async {
      expect(request.headers['Authorization'], 'Bearer test-token');
      if (request.method == 'PUT') state = {...state, ...jsonDecode(request.body) as Map<String, dynamic>};
      return http.Response(jsonEncode(state), 200);
    });
    await BenefitsService.instance.connect('https://example.test/api', 'test-token', client);
    await BenefitsService.instance.select(brush: 'calligraphy', palette: InterfacePalette.blue);
    expect(BenefitsService.instance.brush, 'calligraphy');
    expect(ThemeManager.palette.value, InterfacePalette.blue);
    await BenefitsService.instance.connect('https://example.test/api', 'test-token', client);
    expect(BenefitsService.instance.brush, 'calligraphy');
    BenefitsService.instance.clear();
    expect(BenefitsService.instance.brush, 'default');
    expect(ThemeManager.palette.value, InterfacePalette.dark);
  });

  test('failed server save never unlocks cosmetics', () async {
    final client = MockClient((request) async => request.method == 'GET'
      ? http.Response('{"premium_until":0,"brush":"default","palette":"dark"}', 200)
      : http.Response('{"detail":"Premium required"}', 403));
    await BenefitsService.instance.connect('https://example.test/api', 'free-token', client);
    await expectLater(BenefitsService.instance.select(brush: 'ink'), throwsException);
    expect(BenefitsService.instance.brush, 'default');
  });

  testWidgets('free appearance shows locks and default canvas keeps drawing', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: AppearanceScreen()));
    expect(find.text('Màu tùy chọn dành cho Premium'), findsOneWidget);
    expect(find.byIcon(Icons.lock_outline), findsWidgets);
    final controller = HanziCanvasController();
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: SingleChildScrollView(
      child: HanziDrawingCanvas(controller: controller, canvasKey: const Key('canvas'))))));
    expect(find.text('Bút lông 🔒'), findsOneWidget);
    final gesture = await tester.startGesture(tester.getCenter(find.byKey(const Key('canvas'))));
    await gesture.moveBy(const Offset(30, 30));
    await gesture.up();
    expect(controller.strokeCount, 1);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
    controller.dispose();
  });
}
