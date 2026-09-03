import 'package:flutter/material.dart';

import 'screens/home_screen.dart';
import 'screens/lessons_screen.dart';
import 'screens/practice_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/vocabulary_screen.dart';
import 'theme/app_theme.dart';

class HanziGoApp extends StatelessWidget {
  const HanziGoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'HanziGo',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      home: const AppShell(),
    );
  }
}

class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _index = 0;

  late final List<Widget> _pages = [
    HomeScreen(onOpenLessons: () => setState(() => _index = 1)),
    const LessonsScreen(),
    const PracticeScreen(),
    const VocabularyScreen(),
    const ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _index, children: _pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (value) => setState(() => _index = value),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home_rounded), label: 'Trang chủ'),
          NavigationDestination(icon: Icon(Icons.menu_book_outlined), selectedIcon: Icon(Icons.menu_book_rounded), label: 'Bài học'),
          NavigationDestination(icon: Icon(Icons.psychology_outlined), selectedIcon: Icon(Icons.psychology_rounded), label: 'Luyện tập'),
          NavigationDestination(icon: Icon(Icons.style_outlined), selectedIcon: Icon(Icons.style_rounded), label: 'Từ vựng'),
          NavigationDestination(icon: Icon(Icons.person_outline_rounded), selectedIcon: Icon(Icons.person_rounded), label: 'Cá nhân'),
        ],
      ),
    );
  }
}
