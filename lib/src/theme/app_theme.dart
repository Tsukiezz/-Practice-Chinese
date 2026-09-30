import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

enum InterfacePalette {
  dark('Tối hiện tại', Color(0xFF397765), Brightness.dark),
  purple('Tím pastel', Color(0xFF7653A6), Brightness.light),
  red('Đỏ đậm', Color(0xFF941D38), Brightness.dark),
  blue('Xanh dương', Color(0xFF175BBB), Brightness.light),
  yellow('Vàng pastel', Color(0xFF8B6900), Brightness.light),
  orange('Cam', Color(0xFFAE460D), Brightness.light);

  const InterfacePalette(this.label, this.seed, this.brightness);
  final String label;
  final Color seed;
  final Brightness brightness;
}

class ThemeManager {
  static final palette = ValueNotifier<InterfacePalette>(InterfacePalette.dark);
  static final ValueNotifier<ThemeMode> themeMode =
      ValueNotifier<ThemeMode>(ThemeMode.light);

  static Future<void> init() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final mode = prefs.getString('app_theme_mode');
      final saved = prefs.getString('app_theme_palette');
      palette.value = InterfacePalette.values.firstWhere(
        (p) => p.name == saved, orElse: () => InterfacePalette.dark);
      if (mode == 'dark') {
        themeMode.value = ThemeMode.dark;
      } else {
        themeMode.value = ThemeMode.light;
      }
    } catch (_) {}
  }

  static Future<void> toggle() async {
    final next =
        themeMode.value == ThemeMode.light ? ThemeMode.dark : ThemeMode.light;
    themeMode.value = next;
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(
          'app_theme_mode', next == ThemeMode.dark ? 'dark' : 'light');
    } catch (_) {}
  }

  static bool get isDark => themeMode.value == ThemeMode.dark;

  static Future<void> selectPalette(InterfacePalette value) async {
    palette.value = value;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('app_theme_palette', value.name);
  }
}

class AppTheme {
  static ThemeData colored(InterfacePalette palette) {
    if (palette == InterfacePalette.dark) return dark;
    final scheme = ColorScheme.fromSeed(
      seedColor: palette.seed, brightness: palette.brightness);
    final base = palette.brightness == Brightness.dark ? dark : light;
    return base.copyWith(
      brightness: palette.brightness,
      colorScheme: scheme,
      scaffoldBackgroundColor: scheme.surfaceContainerLow,
      canvasColor: scheme.surface,
      dividerColor: scheme.outlineVariant,
      disabledColor: scheme.onSurfaceVariant,
      iconTheme: IconThemeData(color: scheme.primary),
      textTheme: base.textTheme.apply(
        bodyColor: scheme.onSurface, displayColor: scheme.onSurface),
      appBarTheme: base.appBarTheme.copyWith(
        backgroundColor: scheme.surface, foregroundColor: scheme.onSurface),
      cardTheme: base.cardTheme.copyWith(color: scheme.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20),
          side: BorderSide(color: scheme.outlineVariant))),
      inputDecorationTheme: base.inputDecorationTheme.copyWith(
        fillColor: scheme.surfaceContainerLowest,
        hintStyle: TextStyle(color: scheme.onSurfaceVariant),
        labelStyle: TextStyle(color: scheme.onSurfaceVariant),
        prefixIconColor: scheme.primary, suffixIconColor: scheme.onSurfaceVariant,
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: scheme.outline)),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: scheme.primary, width: 1.5))),
      chipTheme: base.chipTheme.copyWith(
        backgroundColor: scheme.surfaceContainer,
        selectedColor: scheme.secondaryContainer,
        labelStyle: TextStyle(color: scheme.onSurface),
        secondaryLabelStyle: TextStyle(color: scheme.onSecondaryContainer),
        side: BorderSide(color: scheme.outline)),
      navigationBarTheme: base.navigationBarTheme.copyWith(
        backgroundColor: scheme.surface,
        indicatorColor: scheme.secondaryContainer,
        labelTextStyle: WidgetStatePropertyAll(TextStyle(
          color: scheme.onSurface, fontSize: 11, fontWeight: FontWeight.w600))),
      dialogTheme: DialogThemeData(backgroundColor: scheme.surface,
        titleTextStyle: base.textTheme.titleLarge?.copyWith(color: scheme.onSurface),
        contentTextStyle: base.textTheme.bodyMedium?.copyWith(color: scheme.onSurface)),
      bottomSheetTheme: BottomSheetThemeData(backgroundColor: scheme.surface),
      popupMenuTheme: PopupMenuThemeData(color: scheme.surface,
        textStyle: TextStyle(color: scheme.onSurface)),
      textSelectionTheme: TextSelectionThemeData(cursorColor: scheme.primary,
        selectionColor: scheme.primary.withValues(alpha: .25)),
    );
  }

  static const red = Color(0xFFDC554F);
  static const ink = Color(0xFF24332E);
  static const cream = Color(0xFFF5F7F4);
  static const jade = Color(0xFF397765);
  static const orange = Color(0xFFE98151);

  static ThemeData get light {
    final scheme = ColorScheme.fromSeed(
      seedColor: jade,
      brightness: Brightness.light,
      surface: cream,
    );
    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme.copyWith(
        primary: jade,
        secondary: red,
        surface: cream,
        onSurface: ink,
      ),
      scaffoldBackgroundColor: cream,
      fontFamily: 'HanziGoHSK',
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        foregroundColor: ink,
      ),
      textTheme: const TextTheme(
        displayLarge: TextStyle(color: ink, fontWeight: FontWeight.w800),
        displayMedium: TextStyle(color: ink, fontWeight: FontWeight.w800),
        displaySmall: TextStyle(color: ink, fontWeight: FontWeight.w700),
        headlineLarge: TextStyle(color: ink, fontWeight: FontWeight.w800),
        headlineMedium: TextStyle(color: ink, fontWeight: FontWeight.w800),
        headlineSmall: TextStyle(color: ink, fontWeight: FontWeight.w700),
        titleLarge: TextStyle(color: ink, fontWeight: FontWeight.w800),
        titleMedium: TextStyle(color: ink, fontWeight: FontWeight.w700),
        titleSmall: TextStyle(color: ink, fontWeight: FontWeight.w600),
        bodyLarge: TextStyle(color: ink, height: 1.5),
        bodyMedium: TextStyle(color: Color(0xFF334155), height: 1.4),
        bodySmall: TextStyle(color: Color(0xFF64748B)),
        labelLarge: TextStyle(color: ink, fontWeight: FontWeight.w700),
        labelMedium: TextStyle(color: Color(0xFF64748B)),
        labelSmall: TextStyle(color: Color(0xFF64748B)),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: Colors.white,
        selectedColor: const Color(0xFFE6F0EB),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        labelStyle: const TextStyle(color: Color(0xFF4A5568), fontWeight: FontWeight.w600),
        secondaryLabelStyle: const TextStyle(color: jade, fontWeight: FontWeight.w700),
        side: const BorderSide(color: Color(0xFFDBE1DC)),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
      navigationBarTheme: NavigationBarThemeData(
        height: 72,
        backgroundColor: Colors.white,
        indicatorColor: jade.withValues(alpha: .14),
        labelTextStyle: WidgetStateProperty.resolveWith(
          (states) => TextStyle(
            fontSize: 11,
            fontWeight: states.contains(WidgetState.selected)
                ? FontWeight.w700
                : FontWeight.w500,
            color: states.contains(WidgetState.selected)
                ? jade
                : Colors.grey.shade600,
          ),
        ),
      ),
      cardTheme: CardThemeData(
        color: Colors.white,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: const BorderSide(color: Color(0xFFF0E8DE)),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        hintStyle: const TextStyle(color: Color(0xFF94A3B8)),
        labelStyle: const TextStyle(color: Color(0xFF475569)),
        prefixIconColor: jade,
        suffixIconColor: const Color(0xFF64748B),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: Color(0xFFDDE5E0)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: jade, width: 1.5),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size(0, 50),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(15),
          ),
          textStyle: const TextStyle(
              fontFamily: 'HanziGoHSK', fontWeight: FontWeight.w700),
        ),
      ),
    );
  }

  static ThemeData get dark {
    final scheme = ColorScheme.fromSeed(
      seedColor: jade,
      brightness: Brightness.dark,
      surface: const Color(0xFF16231F),
    );
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: scheme.copyWith(
        primary: const Color(0xFF4DB697),
        secondary: const Color(0xFFFF6B6B),
        surface: const Color(0xFF16231F),
        onSurface: const Color(0xFFF0FDF4),
        onPrimary: const Color(0xFF101916),
      ),
      scaffoldBackgroundColor: const Color(0xFF101916),
      fontFamily: 'HanziGoHSK',
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        foregroundColor: Color(0xFFE2ECE7),
      ),
      textTheme: const TextTheme(
        displayLarge: TextStyle(color: Color(0xFFF0FDF4), fontWeight: FontWeight.w800),
        displayMedium: TextStyle(color: Color(0xFFF0FDF4), fontWeight: FontWeight.w800),
        displaySmall: TextStyle(color: Color(0xFFF0FDF4), fontWeight: FontWeight.w700),
        headlineLarge: TextStyle(color: Color(0xFFF0FDF4), fontWeight: FontWeight.w800),
        headlineMedium: TextStyle(color: Color(0xFFF0FDF4), fontWeight: FontWeight.w800),
        headlineSmall: TextStyle(color: Color(0xFFF0FDF4), fontWeight: FontWeight.w700),
        titleLarge: TextStyle(color: Color(0xFFF0FDF4), fontWeight: FontWeight.w800),
        titleMedium: TextStyle(color: Color(0xFFF0FDF4), fontWeight: FontWeight.w700),
        titleSmall: TextStyle(color: Color(0xFFE2ECE7), fontWeight: FontWeight.w600),
        bodyLarge: TextStyle(color: Color(0xFFE2ECE7), height: 1.5),
        bodyMedium: TextStyle(color: Color(0xFFCBD5E1), height: 1.4),
        bodySmall: TextStyle(color: Color(0xFFA3BFB3)),
        labelLarge: TextStyle(color: Color(0xFFF0FDF4), fontWeight: FontWeight.w700),
        labelMedium: TextStyle(color: Color(0xFFA3BFB3)),
        labelSmall: TextStyle(color: Color(0xFFA3BFB3)),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: const Color(0xFF1A2924),
        selectedColor: const Color(0xFF285444),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        labelStyle: const TextStyle(color: Color(0xFFA3BFB3), fontWeight: FontWeight.w600),
        secondaryLabelStyle: const TextStyle(color: Color(0xFFF0FDF4), fontWeight: FontWeight.w700),
        side: const BorderSide(color: Color(0xFF283B34)),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
      navigationBarTheme: NavigationBarThemeData(
        height: 72,
        backgroundColor: const Color(0xFF14201C),
        indicatorColor: const Color(0xFF4DB697).withValues(alpha: .22),
        labelTextStyle: WidgetStateProperty.resolveWith(
          (states) => TextStyle(
            fontSize: 11,
            fontWeight: states.contains(WidgetState.selected)
                ? FontWeight.w700
                : FontWeight.w500,
            color: states.contains(WidgetState.selected)
                ? const Color(0xFF4DB697)
                : const Color(0xFF8FA69C),
          ),
        ),
      ),
      cardTheme: CardThemeData(
        color: const Color(0xFF1A2924),
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: const BorderSide(color: Color(0xFF283B34)),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFF1A2924),
        hintStyle: const TextStyle(color: Color(0xFF7A9388)),
        labelStyle: const TextStyle(color: Color(0xFFA3BFB3)),
        prefixIconColor: const Color(0xFF4DB697),
        suffixIconColor: const Color(0xFFA3BFB3),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: Color(0xFF283B34)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: Color(0xFF4DB697), width: 1.5),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size(0, 50),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(15),
          ),
          textStyle: const TextStyle(
              fontFamily: 'HanziGoHSK', fontWeight: FontWeight.w700),
        ),
      ),
    );
  }
}
