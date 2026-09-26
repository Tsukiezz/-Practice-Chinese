import 'dart:async';
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

class HanziGoApp extends StatefulWidget {
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
  State<HanziGoApp> createState() => _HanziGoAppState();
}

class _HanziGoAppState extends State<HanziGoApp> {
  @override
  void initState() {
    super.initState();
    ThemeManager.init();
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<ThemeMode>(
      valueListenable: ThemeManager.themeMode,
      builder: (context, mode, child) {
        return MaterialApp(
          title: 'HanziGo',
          debugShowCheckedModeBanner: false,
          theme: AppTheme.light,
          darkTheme: AppTheme.dark,
          themeMode: mode,
          home: AppShell(
            readingRepository: widget.readingRepository,
            listeningRepository: widget.listeningRepository,
            authService: widget.authService,
          ),
        );
      },
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

class _AppShellState extends State<AppShell> with WidgetsBindingObserver {
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
  int _index = 0;
  final List<int> _tabHistory = [];
  Timer? _inactivityTimer;
  int _lastRecordTime = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _bootstrap();
    _startInactivityTimer();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _inactivityTimer?.cancel();
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
      _readingRepository =
          widget.readingRepository ??
          ReadingExamService(
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
    _readingRepository =
        widget.readingRepository ??
        ReadingExamService(
          baseUrl: _apiBaseUrl,
          tokenProvider: () async => _authService.token,
          client: _httpClient,
        );
    _listeningRepository =
        widget.listeningRepository ??
        ListeningExamService(
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
    if (_authService.isSessionExpiredDueToInactivity) {
      await _authService.clearSession();
    }
    if (_authService.isAuthenticated) {
      try {
        await _authService.refreshUser(_apiBaseUrl);
        await _authService.recordActivity();
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

    final savedTab = getSavedReturnTab();
    if (savedTab != null && savedTab >= 0 && savedTab <= 6) {
      _index = savedTab;
      _tabHistory.add(0);
      clearSavedReturnTab();
    }
  }

  void _startInactivityTimer() {
    _inactivityTimer?.cancel();
    _inactivityTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      if (_authenticated && _authService.isSessionExpiredDueToInactivity) {
        _handleInactivityLogout();
      }
    });
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed && _authenticated) {
      if (_authService.isSessionExpiredDueToInactivity) {
        _handleInactivityLogout();
      }
    }
  }

  void _onUserActivity() {
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    if (now - _lastRecordTime >= 15) {
      _lastRecordTime = now;
      _authService.recordActivity();
    }
  }

  Future<void> _handleInactivityLogout() async {
    await _logout();
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Phiên đăng nhập đã tự động kết thúc do không hoạt động trong 30 phút. Vui lòng đăng nhập lại.'),
          backgroundColor: Color(0xFFC53030),
          duration: Duration(seconds: 5),
        ),
      );
    }
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

  void _navigateToTab(int newIndex) {
    if (_index == newIndex) return;
    setState(() {
      _tabHistory.add(_index);
      _index = newIndex;
    });
  }

  void _navigateBack() {
    if (_tabHistory.isNotEmpty) {
      setState(() {
        _index = _tabHistory.removeLast();
      });
    } else {
      setState(() {
        _index = 0;
      });
    }
  }

  Future<void> _logout() async {
    await _authService.logout();
    _readingRepository = null;
    _index = 0;
    _tabHistory.clear();
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

    final isDark = Theme.of(context).brightness == Brightness.dark;
    return PopScope(
      canPop: _tabHistory.isEmpty,
      onPopInvokedWithResult: (didPop, result) {
        if (didPop) return;
        if (_tabHistory.isNotEmpty) {
          _navigateBack();
        }
      },
      child: Listener(
        behavior: HitTestBehavior.translucent,
        onPointerDown: (_) => _onUserActivity(),
        onPointerMove: (_) => _onUserActivity(),
        child: Scaffold(
          appBar: PreferredSize(
            preferredSize: const Size.fromHeight(60),
            child: Container(
              decoration: BoxDecoration(
                color: isDark ? const Color(0xFF14201C) : Colors.white,
                border: Border(
                  bottom: BorderSide(
                    color: isDark ? const Color(0xFF283B34) : const Color(0xFF1B4D3E).withValues(alpha: 0.12),
                    width: 1,
                  ),
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: isDark ? 0.2 : 0.04),
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
                      Expanded(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'HanziGo · Hán Ngữ Xanh',
                              overflow: TextOverflow.ellipsis,
                              maxLines: 1,
                              style: TextStyle(
                                fontSize: 15,
                                fontWeight: FontWeight.w800,
                                color: isDark ? const Color(0xFF4DB697) : const Color(0xFF1B4D3E),
                                letterSpacing: 0.2,
                              ),
                            ),
                            Text(
                              'Ứng dụng học tiếng Trung',
                              overflow: TextOverflow.ellipsis,
                              maxLines: 1,
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w500,
                                color: isDark ? const Color(0xFF8FA69C) : const Color(0xFF707974),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 8),
                      ValueListenableBuilder<ThemeMode>(
                        valueListenable: ThemeManager.themeMode,
                        builder: (context, mode, _) {
                          final isDarkMode = mode == ThemeMode.dark;
                          return IconButton(
                            tooltip: isDarkMode ? 'Chuyển sang Giao diện Sáng' : 'Chuyển sang Giao diện Tối',
                            icon: Icon(
                              isDarkMode ? Icons.light_mode_rounded : Icons.dark_mode_outlined,
                              color: isDarkMode ? const Color(0xFFF6E05E) : const Color(0xFF1B4D3E),
                              size: 22,
                            ),
                            onPressed: ThemeManager.toggle,
                          );
                        },
                      ),
                      const SizedBox(width: 4),
                      if (_authService.currentUser != null)
                        GestureDetector(
                          onTap: () => _navigateToTab(6),
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                            decoration: BoxDecoration(
                              color: isDark ? const Color(0xFF1C2C26) : const Color(0xFFE9F3ED),
                              borderRadius: const BorderRadius.all(Radius.circular(20)),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(
                                  Icons.person_rounded,
                                  size: 16,
                                  color: isDark ? const Color(0xFF4DB697) : const Color(0xFF1B4D3E),
                                ),
                                const SizedBox(width: 6),
                                ConstrainedBox(
                                  constraints: const BoxConstraints(maxWidth: 120),
                                  child: Text(
                                    _authService.currentUser!.name,
                                    overflow: TextOverflow.ellipsis,
                                    style: TextStyle(
                                      fontSize: 12,
                                      fontWeight: FontWeight.w700,
                                      color: isDark ? const Color(0xFFE2ECE7) : const Color(0xFF1B4D3E),
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
                onOpenLessons: () => _navigateToTab(1),
                onOpenListening: () => _navigateToTab(2),
                onOpenReading: () => _navigateToTab(3),
                onOpenDictionary: () => _navigateToTab(4),
                onOpenAiExam: () => _navigateToTab(5),
                onOpenProfile: () => _navigateToTab(6),
              ),
              LessonsScreen(
                service: _studentService,
                onBack: _navigateBack,
              ),
              ListeningScreen(
                repository: _listeningRepository!,
                draftOwner: _authService.currentUser?.id,
                onBack: _navigateBack,
              ),
              PracticeScreen(
                repository: _readingRepository!,
                draftOwner: _authService.currentUser?.id,
                onBack: _navigateBack,
              ),
              VocabularyScreen(
                service: _studentService,
                onBack: _navigateBack,
              ),
              AiExamScreen(
                service: _aiExamService,
                onBack: _navigateBack,
              ),
              ProfileScreen(
                onLogout: _logout,
                studentService: _studentService,
                comprehensiveRepository: _comprehensiveRepository,
                user: _authService.currentUser,
                onBack: _navigateBack,
                onEditProfile: kIsWeb
                    ? () => openAccount(_authService.token!, returnTab: _index)
                    : null,
                onOpenAdmin: kIsWeb && (_authService.currentUser?.isAdmin ?? false)
                    ? () => openAdmin(_authService.token ?? '')
                    : null,
              ),
            ],
          ),
          bottomNavigationBar: NavigationBar(
            selectedIndex: _index,
            onDestinationSelected: (value) => _navigateToTab(value),
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
        ),
      ),
    );
  }
}
