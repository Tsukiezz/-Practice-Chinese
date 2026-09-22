import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import 'screens/home_screen.dart';
import 'screens/lessons_screen.dart';
import 'screens/listening_screen.dart';
import 'screens/login_screen.dart';
import 'screens/practice_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/vocabulary_screen.dart';
import 'screens/ai_exam_screen.dart';
import 'services/auth_service.dart';
import 'services/web_navigation.dart';
import 'services/reading_exam_service.dart';
import 'services/student_service.dart';
import 'services/listening_exam_service.dart';
import 'services/custom_exam_service.dart';
import 'services/ai_exam_service.dart';
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
  static String get _apiBaseUrl {
    const configured = String.fromEnvironment('HANZIGO_API_URL');
    return configured.isNotEmpty
        ? configured
        : (kIsWeb
              ? Uri.base.resolve('/api').toString()
              : 'http://localhost:8010/api');
  }

  http.Client? _httpClient;
  late AuthService _authService;
  late StudentService _studentService;
  late AIExamService _aiExamService;
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
      _aiExamService = AIExamService(
        baseUrl: _apiBaseUrl,
        tokenProvider: () async => _authService.token,
      );
      _listeningRepository =
          widget.listeningRepository ??
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
    _aiExamService = AIExamService(
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
    if (_authService.isAuthenticated) {
      try {
        await _authService.refreshUser(_apiBaseUrl);
      } on Exception {
        await _authService.clearSession();
      }
    }
    if (await _routeAdmin()) return;
    if (!mounted) return;
    setState(() {
      _authenticated = _authService.isAuthenticated;
      _loading = false;
    });
  }

  Future<bool> _routeAdmin() async {
    if (kIsWeb &&
        _authService.isAuthenticated &&
        _authService.currentUser?.isAdmin == true) {
      final token = _authService.token!;
      await _authService.clearSession();
      openAdmin(token);
      return true;
    }
    return false;
  }

  void _onLoginSuccess() async {
    if (await _routeAdmin() || !mounted) return;
    await CustomExamService.create();
    if (!mounted) return;
    setState(() => _authenticated = true);
  }

  Future<void> _logout() async {
    await _authService.logout();
    _readingRepository = null;
    _index = 0;
    if (!mounted) return;
    setState(() => _authenticated = false);
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    if (!_authenticated) {
      return LoginScreen(
        baseUrl: _apiBaseUrl,
        authService: _authService,
        onLoginSuccess: _onLoginSuccess,
      );
    }

    _readingRepository ??=
        widget.readingRepository ??
        ReadingExamService(
          baseUrl: _apiBaseUrl,
          tokenProvider: () async => _authService.token,
          client: _httpClient,
        );

    return Scaffold(
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(60),
        child: Container(
          decoration: BoxDecoration(
            color: Colors.white,
            border: Border(
              bottom: BorderSide(
                color: const Color(0xFF1B4D3E).withValues(alpha: 0.12),
                width: 1,
              ),
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.04),
                blurRadius: 6,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: SafeArea(
            bottom: false,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
              child: Row(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      color: const Color(0xFF1B4D3E),
                      borderRadius: BorderRadius.circular(10),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF1B4D3E).withValues(alpha: 0.25),
                          blurRadius: 6,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: const Center(
                      child: Text(
                        '汉',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 19,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  const Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'HanziGo · Hán Ngữ Xanh',
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w800,
                          color: Color(0xFF1B4D3E),
                          letterSpacing: 0.2,
                        ),
                      ),
                      Text(
                        'Ứng dụng học tiếng Trung',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w500,
                          color: Color(0xFF707974),
                        ),
                      ),
                    ],
                  ),
                  const Spacer(),
                  if (_authService.currentUser != null)
                    GestureDetector(
                      onTap: () => setState(() => _index = 6),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                        decoration: BoxDecoration(
                          color: const Color(0xFFE9F3ED),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(
                              Icons.person_rounded,
                              size: 16,
                              color: Color(0xFF1B4D3E),
                            ),
                            const SizedBox(width: 6),
                            ConstrainedBox(
                              constraints: const BoxConstraints(maxWidth: 120),
                              child: Text(
                                _authService.currentUser!.name,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w700,
                                  color: Color(0xFF1B4D3E),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
      ),
      body: IndexedStack(
        index: _index,
        children: [
          HomeScreen(
            userName: _authService.currentUser?.name ?? '',
            onOpenLessons: () => setState(() => _index = 1),
            onOpenListening: () => setState(() => _index = 2),
            onOpenReading: () => setState(() => _index = 3),
            onOpenDictionary: () => setState(() => _index = 4),
            onOpenAiExam: () => setState(() => _index = 5),
            onOpenProfile: () => setState(() => _index = 6),
          ),
          LessonsScreen(service: _studentService),
          ListeningScreen(
            repository: _listeningRepository!,
            draftOwner: _authService.currentUser?.id,
          ),
          PracticeScreen(
            repository: _readingRepository!,
            draftOwner: _authService.currentUser?.id,
          ),
          VocabularyScreen(service: _studentService),
          AiExamScreen(service: _aiExamService),
          ProfileScreen(
            onLogout: _logout,
            studentService: _studentService,
            comprehensiveRepository: _comprehensiveRepository,
            user: _authService.currentUser,
            onEditProfile: kIsWeb
                ? () => openAccount(_authService.token!)
                : null,
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
            label: 'Trang chủ',
          ),
          NavigationDestination(
            icon: Icon(Icons.menu_book_outlined),
            selectedIcon: Icon(Icons.menu_book_rounded),
            label: 'Bài học',
          ),
          NavigationDestination(
            icon: Icon(Icons.headphones_outlined),
            selectedIcon: Icon(Icons.headphones_rounded),
            label: 'Nghe',
          ),
          NavigationDestination(
            icon: Icon(Icons.psychology_outlined),
            selectedIcon: Icon(Icons.psychology_rounded),
            label: 'Đọc',
          ),
          NavigationDestination(
            icon: Icon(Icons.style_outlined),
            selectedIcon: Icon(Icons.style_rounded),
            label: 'Từ vựng',
          ),
          NavigationDestination(
            icon: Icon(Icons.assignment_turned_in_outlined),
            selectedIcon: Icon(Icons.assignment_turned_in_rounded),
            label: 'Kiểm tra',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline_rounded),
            selectedIcon: Icon(Icons.person_rounded),
            label: 'Cá nhân',
          ),
        ],
      ),
    );
  }

  int _index = 0;
}
