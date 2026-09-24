import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import 'screens/home_screen.dart';
import 'screens/lessons_screen.dart';
import 'screens/login_screen.dart';
import 'screens/practice_hub_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/vocabulary_screen.dart';
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
      _readingRepository = widget.readingRepository ??
          ReadingExamService(
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
    _aiExamService = AIExamService(
      baseUrl: _apiBaseUrl,
      tokenProvider: () async => _authService.token,
      client: _httpClient,
    );
    _readingRepository = widget.readingRepository ??
        ReadingExamService(
          baseUrl: _apiBaseUrl,
          tokenProvider: () async => _authService.token,
          client: _httpClient,
        );
    _listeningRepository = widget.listeningRepository ??
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

    _readingRepository ??= widget.readingRepository ??
        ReadingExamService(
          baseUrl: _apiBaseUrl,
          tokenProvider: () async => _authService.token,
          client: _httpClient,
        );

    final pages = <Widget>[
      HomeScreen(
        userName: _authService.currentUser?.name ?? '',
        onOpenLessons: () => _selectPage(1),
        onOpenPractice: () => _selectPage(2),
        onOpenDictionary: () => _selectPage(3),
        onOpenProfile: () => _selectPage(4),
      ),
      LessonsScreen(service: _studentService),
      PracticeHubScreen(
        studentService: _studentService,
        aiExamService: _aiExamService,
        readingRepository: _readingRepository!,
        listeningRepository: _listeningRepository!,
        comprehensiveRepository: _comprehensiveRepository!,
        draftOwner: _authService.currentUser?.id,
      ),
      VocabularyScreen(service: _studentService),
      ProfileScreen(
        onLogout: _logout,
        studentService: _studentService,
        user: _authService.currentUser,
        onEditProfile: kIsWeb ? () => openAccount(_authService.token!) : null,
        onOpenAdmin: kIsWeb && (_authService.currentUser?.isAdmin ?? false)
            ? () => openAdmin(_authService.token ?? '')
            : null,
      ),
    ];

    final body = IndexedStack(index: _index, children: pages);
    final isDesktop = MediaQuery.sizeOf(context).width >= 900;
    return isDesktop ? _desktopShell(body) : _mobileShell(body);
  }

  void _selectPage(int value) => setState(() => _index = value);

  Widget _mobileShell(Widget body) {
    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 58,
        backgroundColor: Colors.white,
        surfaceTintColor: Colors.white,
        titleSpacing: 16,
        title: const _Brand(horizontal: true),
        actions: [
          if (_authService.currentUser != null)
            Padding(
              padding: const EdgeInsets.only(right: 10),
              child: IconButton.filledTonal(
                onPressed: () => _selectPage(4),
                tooltip: 'Tài khoản của tôi',
                icon: const Icon(Icons.person_outline_rounded),
              ),
            ),
        ],
        bottom: const PreferredSize(
          preferredSize: Size.fromHeight(1),
          child: Divider(height: 1, color: Color(0xFFE2E8E4)),
        ),
      ),
      body: body,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: _selectPage,
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
            icon: Icon(Icons.grid_view_outlined),
            selectedIcon: Icon(Icons.grid_view_rounded),
            label: 'Luyện tập',
          ),
          NavigationDestination(
            icon: Icon(Icons.search_outlined),
            selectedIcon: Icon(Icons.search_rounded),
            label: 'Từ điển',
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

  Widget _desktopShell(Widget body) {
    return Scaffold(
      body: Row(
        children: [
          Container(
            width: 248,
            decoration: const BoxDecoration(
              color: Colors.white,
              border: Border(
                right: BorderSide(color: Color(0xFFE2E8E4)),
              ),
            ),
            child: SafeArea(
              child: Column(
                children: [
                  const Padding(
                    padding: EdgeInsets.fromLTRB(20, 18, 20, 16),
                    child: _Brand(horizontal: true),
                  ),
                  const Divider(height: 1),
                  Expanded(
                    child: NavigationRail(
                      extended: true,
                      minExtendedWidth: 247,
                      selectedIndex: _index,
                      onDestinationSelected: _selectPage,
                      labelType: NavigationRailLabelType.none,
                      groupAlignment: -0.85,
                      destinations: const [
                        NavigationRailDestination(
                          icon: Icon(Icons.home_outlined),
                          selectedIcon: Icon(Icons.home_rounded),
                          label: Text('Trang chủ'),
                        ),
                        NavigationRailDestination(
                          icon: Icon(Icons.menu_book_outlined),
                          selectedIcon: Icon(Icons.menu_book_rounded),
                          label: Text('Bài học'),
                        ),
                        NavigationRailDestination(
                          icon: Icon(Icons.grid_view_outlined),
                          selectedIcon: Icon(Icons.grid_view_rounded),
                          label: Text('Luyện tập'),
                        ),
                        NavigationRailDestination(
                          icon: Icon(Icons.search_outlined),
                          selectedIcon: Icon(Icons.search_rounded),
                          label: Text('Từ điển'),
                        ),
                        NavigationRailDestination(
                          icon: Icon(Icons.person_outline_rounded),
                          selectedIcon: Icon(Icons.person_rounded),
                          label: Text('Cá nhân'),
                        ),
                      ],
                    ),
                  ),
                  if (_authService.currentUser != null)
                    Padding(
                      padding: const EdgeInsets.all(14),
                      child: ListTile(
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                        tileColor: const Color(0xFFE9F3ED),
                        leading: const CircleAvatar(
                          backgroundColor: Color(0xFF1B4D3E),
                          foregroundColor: Colors.white,
                          child: Icon(Icons.person_rounded, size: 19),
                        ),
                        title: Text(
                          _authService.currentUser!.name,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        subtitle: const Text(
                          'Xem tài khoản',
                          style: TextStyle(fontSize: 11),
                        ),
                        onTap: () => _selectPage(4),
                      ),
                    ),
                ],
              ),
            ),
          ),
          Expanded(child: body),
        ],
      ),
    );
  }

  int _index = 0;
}

class _Brand extends StatelessWidget {
  const _Brand({required this.horizontal});

  final bool horizontal;

  @override
  Widget build(BuildContext context) {
    final mark = Container(
      width: 36,
      height: 36,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: const Color(0xFF1B4D3E),
        borderRadius: BorderRadius.circular(10),
      ),
      child: const Text(
        '汉',
        style: TextStyle(
          color: Colors.white,
          fontSize: 19,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
    final name = const Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'HanziGo · Hán Ngữ Xanh',
          overflow: TextOverflow.ellipsis,
          maxLines: 1,
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w800,
            color: Color(0xFF1B4D3E),
          ),
        ),
        Text(
          'Học tiếng Trung mỗi ngày',
          overflow: TextOverflow.ellipsis,
          maxLines: 1,
          style: TextStyle(fontSize: 11, color: Color(0xFF707974)),
        ),
      ],
    );
    if (!horizontal) return Column(children: [mark, name]);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [mark, const SizedBox(width: 10), Expanded(child: name)],
    );
  }
}
