import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import 'screens/home_screen.dart';
import 'screens/lessons_screen.dart';
import 'screens/listening_screen.dart';
import 'screens/login_screen.dart';
import 'screens/practice_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/vocabulary_screen.dart';
import 'services/auth_service.dart';
import 'services/reading_exam_service.dart';
import 'services/student_service.dart';
import 'services/listening_exam_service.dart';
import 'services/custom_exam_service.dart';
import 'theme/app_theme.dart';

class HanziGoApp extends StatelessWidget {
  const HanziGoApp({
    super.key,
    this.readingRepository,
    this.listeningRepository,
    this.authService,
  });

  final ReadingExamRepository? readingRepository;
  final ListeningExamRepository? listeningRepository;
  final AuthService? authService;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'HanziGo',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      home: AppShell(
        readingRepository: readingRepository,
        listeningRepository: listeningRepository,
        authService: authService,
      ),
    );
  }
}

class AppShell extends StatefulWidget {
  const AppShell({
    super.key,
    this.readingRepository,
    this.listeningRepository,
    this.authService,
  });

  final ReadingExamRepository? readingRepository;
  final ListeningExamRepository? listeningRepository;
  final AuthService? authService;

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  static const _apiBaseUrl = String.fromEnvironment(
    'HANZIGO_API_URL',
    defaultValue: 'http://localhost:8010/api',
  );

  http.Client? _httpClient;
  late AuthService _authService;
  late StudentService _studentService;
  bool _loading = true;
  bool _authenticated = false;
  ReadingExamRepository? _readingRepository;
  ReadingExamRepository? _comprehensiveRepository;
  ListeningExamRepository? _listeningRepository;

  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  @override
  void dispose() {
    _httpClient?.close();
    super.dispose();
  }

  Future<void> _bootstrap() async {
    if (widget.authService != null) {
      _authService = widget.authService!;
      _studentService = StudentService(
        baseUrl: _apiBaseUrl,
        tokenProvider: () async => _authService.token,
      );
      _listeningRepository = widget.listeningRepository ??
          ListeningExamService(
            baseUrl: _apiBaseUrl,
            tokenProvider: () async => _authService.token,
          );
      _comprehensiveRepository = ReadingExamService(
        baseUrl: _apiBaseUrl,
        tokenProvider: () async => _authService.token,
        comprehensive: true,
      );
      _authenticated = true;
      _loading = false;
      return;
    }

    _httpClient = http.Client();
    _authService = await AuthService.load(_httpClient!);
    _studentService = StudentService(
      baseUrl: _apiBaseUrl,
      tokenProvider: () async => _authService.token,
      client: _httpClient,
    );
    _listeningRepository ??= ListeningExamService(
      baseUrl: _apiBaseUrl,
      tokenProvider: () async => _authService.token,
      client: _httpClient,
    );
    _comprehensiveRepository = ReadingExamService(
      baseUrl: _apiBaseUrl,
      tokenProvider: () async => _authService.token,
      client: _httpClient,
      comprehensive: true,
    );
    try {
      await CustomExamService.create();
    } on Exception {
      // Local custom exams are optional and must not block the whole app.
    }
    if (!mounted) return;
    setState(() {
      _authenticated = _authService.isAuthenticated;
      _loading = false;
    });
  }

  void _onLoginSuccess() {
    setState(() => _authenticated = true);
  }

  Future<void> _logout() async {
    await _authService.logout();
    if (!mounted) return;
    setState(() => _authenticated = false);
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (!_authenticated) {
      return LoginScreen(
        baseUrl: _apiBaseUrl,
        onLoginSuccess: _onLoginSuccess,
      );
    }

    _readingRepository ??= widget.readingRepository ??
        ReadingExamService(
          baseUrl: _apiBaseUrl,
          tokenProvider: () async => _authService.token,
          client: _httpClient,
        );

    return Scaffold(
      body: IndexedStack(
        index: _index,
        children: [
          HomeScreen(onOpenLessons: () => setState(() => _index = 1)),
          const LessonsScreen(),
          ListeningScreen(repository: _listeningRepository!),
          PracticeScreen(repository: _readingRepository!),
          VocabularyScreen(service: _studentService),
          ProfileScreen(
            onLogout: _logout,
            studentService: _studentService,
            comprehensiveRepository: _comprehensiveRepository,
            user: _authService.currentUser,
          ),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (value) => setState(() => _index = value),
        destinations: const [
          NavigationDestination(
              icon: Icon(Icons.home_outlined),
              selectedIcon: Icon(Icons.home_rounded),
              label: 'Trang chủ'),
          NavigationDestination(
              icon: Icon(Icons.menu_book_outlined),
              selectedIcon: Icon(Icons.menu_book_rounded),
              label: 'Bài học'),
          NavigationDestination(
              icon: Icon(Icons.headphones_outlined),
              selectedIcon: Icon(Icons.headphones_rounded),
              label: 'Nghe'),
          NavigationDestination(
              icon: Icon(Icons.psychology_outlined),
              selectedIcon: Icon(Icons.psychology_rounded),
              label: 'Đọc'),
          NavigationDestination(
              icon: Icon(Icons.style_outlined),
              selectedIcon: Icon(Icons.style_rounded),
              label: 'Từ vựng'),
          NavigationDestination(
              icon: Icon(Icons.person_outline_rounded),
              selectedIcon: Icon(Icons.person_rounded),
              label: 'Cá nhân'),
        ],
      ),
    );
  }

  int _index = 0;
}
