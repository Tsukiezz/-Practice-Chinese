import 'package:flutter/material.dart';

class AppTheme {
  static const red = Color(0xFFDC554F);
  static const ink = Color(0xFF24332E);
  static const cream = Color(0xFFFFF9F1);
  static const jade = Color(0xFF397765);
  static const orange = Color(0xFFE98151);

  static ThemeData get light {
    final scheme = ColorScheme.fromSeed(
      seedColor: red,
      brightness: Brightness.light,
      surface: cream,
    );
    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme.copyWith(primary: red, secondary: jade),
      scaffoldBackgroundColor: cream,
      fontFamily: 'sans-serif',
      appBarTheme: const AppBarTheme(
          backgroundColor: Colors.transparent,
          elevation: 0,
          foregroundColor: ink),
      navigationBarTheme: NavigationBarThemeData(
        height: 72,
        backgroundColor: Colors.white,
        indicatorColor: red.withValues(alpha: .14),
        labelTextStyle: WidgetStateProperty.resolveWith((states) => TextStyle(
            fontSize: 11,
            fontWeight: states.contains(WidgetState.selected)
                ? FontWeight.w700
                : FontWeight.w500,
            color: states.contains(WidgetState.selected)
                ? red
                : Colors.grey.shade600)),
      ),
      cardTheme: CardThemeData(
          color: Colors.white,
          elevation: 0,
          shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(20),
              side: const BorderSide(color: Color(0xFFF0E8DE)))),
      filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
              minimumSize: const Size(0, 50),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(15)),
              textStyle: const TextStyle(fontWeight: FontWeight.w700))),
    );
  }
}
