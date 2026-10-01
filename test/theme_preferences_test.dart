import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:hanzi_go/src/theme/app_theme.dart';
import 'package:hanzi_go/src/screens/profile_screen.dart';

double contrast(Color a, Color b) {
  final x = a.computeLuminance(), y = b.computeLuminance();
  return (x > y ? x + .05 : y + .05) / (x > y ? y + .05 : x + .05);
}

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
    ThemeManager.themeMode.value = ThemeMode.light;
    ThemeManager.palette.value = InterfacePalette.dark;
  });

  test('all palettes provide readable surfaces, fields and buttons', () {
    for (final palette in InterfacePalette.values) {
      final theme = AppTheme.colored(palette), s = theme.colorScheme;
      for (final background in [theme.scaffoldBackgroundColor, s.surface,
        theme.cardTheme.color!, theme.inputDecorationTheme.fillColor!]) {
        expect(contrast(s.onSurface, background), greaterThanOrEqualTo(4.5), reason: palette.name);
      }
      expect(contrast(s.onPrimary, s.primary), greaterThanOrEqualTo(4.5), reason: palette.name);
      if (palette.brightness == Brightness.light) {
        expect(theme.scaffoldBackgroundColor.computeLuminance(), inExclusiveRange(.55, .86), reason: palette.name);
        expect(contrast(s.onSurfaceVariant, theme.scaffoldBackgroundColor), greaterThanOrEqualTo(4.5), reason: palette.name);
      }
    }
  });

  testWidgets('banner and chat accents follow each palette with readable white text', (tester) async {
    final colors = <Color>{};
    Color? banner;
    for (final palette in InterfacePalette.values) {
      await tester.pumpWidget(MaterialApp(theme: AppTheme.colored(palette), home: Builder(
        builder: (context) {
          final gradient = AppTheme.bannerGradient(context);
          banner = gradient.colors.first;
          for (final background in gradient.colors) {
            expect(contrast(Colors.white, background), greaterThanOrEqualTo(4.5), reason: palette.name);
          }
          expect(AppTheme.chatColors(context)['accent'], startsWith('#'));
          return Container(decoration: BoxDecoration(gradient: gradient));
        },
      )));
      await tester.pumpAndSettle();
      colors.add(banner!);
    }
    expect(colors.length, InterfacePalette.values.length);
  });

  test('selection persists and the switch returns to light without losing it', () async {
    await ThemeManager.selectPalette(InterfacePalette.purple);
    expect(ThemeManager.isDark, isFalse);
    await ThemeManager.toggle();
    expect(ThemeManager.isDark, isTrue);
    await ThemeManager.toggle();
    expect(ThemeManager.isDark, isFalse);
    await ThemeManager.init();
    expect(ThemeManager.palette.value, InterfacePalette.purple);
    expect(ThemeManager.isDark, isFalse);
  });

  testWidgets('profile offers all seven palettes and toggles without overflow', (tester) async {
    await tester.pumpWidget(MaterialApp(theme: AppTheme.light, home: const ProfileScreen()));
    await tester.scrollUntilVisible(find.text('Màu khi bật Dark mode'), 200);
    for (final palette in InterfacePalette.values) {
      expect(find.widgetWithText(ChoiceChip, palette.label), findsOneWidget);
    }
    await tester.tap(find.widgetWithText(ChoiceChip, 'Tím pastel'));
    await tester.pumpAndSettle();
    expect(ThemeManager.palette.value, InterfacePalette.purple);
    expect(tester.takeException(), isNull);
  });
}
