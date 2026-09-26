import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ThemeManager {
  static final ValueNotifier<ThemeMode> themeMode =
      ValueNotifier<ThemeMode>(ThemeMode.light);

  static Future<void> init() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final mode = prefs.getString('app_theme_mode');
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
}

class AppTheme {
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
      colorScheme: scheme.copyWith(primary: jade, secondary: red),
      scaffoldBackgroundColor: cream,
      fontFamily: 'HanziGoHSK',
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        foregroundColor: ink,
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
      ),
      scaffoldBackgroundColor: const Color(0xFF101916),
      fontFamily: 'HanziGoHSK',
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        foregroundColor: Color(0xFFE2ECE7),
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
