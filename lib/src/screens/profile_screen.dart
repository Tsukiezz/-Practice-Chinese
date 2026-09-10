import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/common.dart';
import '../services/student_service.dart';
import '../services/auth_service.dart';
import 'results_screen.dart';
import 'custom_exam_screen.dart';
import 'custom_exam_history_screen.dart';
import 'dashboard_screen.dart';
import 'review_screen.dart';
import 'handwriting_screen.dart';
import '../services/custom_exam_service.dart';
import '../services/reading_exam_service.dart';
import 'practice_screen.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({
    super.key,
    this.onLogout,
    this.studentService,
    this.comprehensiveRepository,
    this.user,
  });

  final VoidCallback? onLogout;
  final StudentService? studentService;
  final ReadingExamRepository? comprehensiveRepository;
  final AuthUser? user;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.only(bottom: 24),
        children: [
          ScreenHeader(
            eyebrow: 'Hồ sơ học tập',
            title: 'Cá nhân',
            trailing: IconButton(
              icon: const Icon(Icons.logout_rounded),
              tooltip: 'Đăng xuất',
              onPressed: () async {
                final confirmed = await showDialog<bool>(
                  context: context,
                  builder: (context) => AlertDialog(
                    title: const Text('Đăng xuất?'),
                    content: const Text('Bạn cần đăng nhập lại để luyện tập.'),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.pop(context, false),
                        child: const Text('Hủy'),
                      ),
                      FilledButton(
                        onPressed: () => Navigator.pop(context, true),
                        child: const Text('Đăng xuất'),
                      ),
                    ],
                  ),
                );
                if (confirmed == true) {
                  onLogout?.call();
                }
              },
            ),
          ),
          _ProfileOverview(
            service: studentService,
            name: user?.name ?? 'Học viên',
            email: user?.email ?? '',
          ),
          const _SectionTitle('Kết quả học tập'),
          if (comprehensiveRepository != null)
            Card(
              margin: const EdgeInsets.symmetric(horizontal: 20),
              child: ListTile(
                leading: const Icon(Icons.fact_check, color: AppTheme.jade),
                title: const Text('Bài test tổng hợp',
                    style: TextStyle(fontWeight: FontWeight.w800)),
                subtitle: const Text('Nghe · Đọc · Viết trong cùng một đề'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => PracticeScreen(
                      repository: comprehensiveRepository!,
                      title: 'Test Tổng hợp',
                      eyebrow: 'Bài luyện · Ba kỹ năng',
                      skillLabel: 'NGHE · ĐỌC · VIẾT',
                    ),
                  ),
                ),
              ),
            ),
          if (studentService != null)
            Card(
              margin: const EdgeInsets.symmetric(horizontal: 20),
              child: ListTile(
                leading: const Icon(Icons.gesture, color: AppTheme.red),
                title: const Text('Viết tay chữ Hán',
                    style: TextStyle(fontWeight: FontWeight.w800)),
                subtitle:
                    const Text('Tra từ viết tay hoặc chấm thứ tự nét offline'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => HandwritingScreen(service: studentService!),
                  ),
                ),
              ),
            ),
          if (studentService != null)
            Card(
              margin: const EdgeInsets.symmetric(horizontal: 20),
              child: ListTile(
                leading: const Icon(Icons.radar_rounded, color: AppTheme.jade),
                title: const Text('Dashboard & năng lực',
                    style: TextStyle(fontWeight: FontWeight.w800)),
                subtitle: const Text('Streak, tiến độ và đánh giá AI'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(
                      builder: (_) =>
                          DashboardScreen(service: studentService!)),
                ),
              ),
            ),
          if (studentService != null)
            Card(
              margin: const EdgeInsets.symmetric(horizontal: 20),
              child: ListTile(
                leading: const Icon(Icons.replay_circle_filled,
                    color: AppTheme.orange),
                title: const Text('Ôn tập dưới 80',
                    style: TextStyle(fontWeight: FontWeight.w800)),
                subtitle: const Text('Viết tay và đoạn văn cần luyện lại'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(
                      builder: (_) => ReviewScreen(service: studentService!)),
                ),
              ),
            ),
          if (studentService != null)
            Card(
              margin: const EdgeInsets.symmetric(horizontal: 20),
              child: InkWell(
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (context) =>
                          ResultsScreen(service: studentService!),
                    ),
                  );
                },
                borderRadius: BorderRadius.circular(20),
                child: const Padding(
                  padding: EdgeInsets.all(18),
                  child: Row(
                    children: [
                      Icon(Icons.history_rounded, color: AppTheme.jade),
                      SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Lịch sử bài làm',
                                style: TextStyle(fontWeight: FontWeight.w800)),
                            Text('Xem lại điểm và nhận xét',
                                style: TextStyle(
                                    color: Colors.grey, fontSize: 11)),
                          ],
                        ),
                      ),
                      Icon(Icons.chevron_right_rounded, color: Colors.grey),
                    ],
                  ),
                ),
              ),
            ),
          if (CustomExamService.instance != null)
            Card(
              margin: const EdgeInsets.symmetric(horizontal: 20),
              child: InkWell(
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (context) => CustomExamScreen(
                          service: CustomExamService.instance!),
                    ),
                  );
                },
                borderRadius: BorderRadius.circular(20),
                child: const Padding(
                  padding: EdgeInsets.all(18),
                  child: Row(
                    children: [
                      Icon(Icons.edit_note_rounded, color: AppTheme.jade),
                      SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Tạo đề thi tùy chỉnh',
                                style: TextStyle(fontWeight: FontWeight.w800)),
                            Text('Tạo đề Nghe hoặc Đọc',
                                style: TextStyle(
                                    color: Colors.grey, fontSize: 11)),
                          ],
                        ),
                      ),
                      Icon(Icons.chevron_right_rounded, color: Colors.grey),
                    ],
                  ),
                ),
              ),
            ),
          if (CustomExamService.instance != null)
            Card(
              margin: const EdgeInsets.symmetric(horizontal: 20),
              child: InkWell(
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (context) => CustomExamHistoryScreen(
                          service: CustomExamService.instance!),
                    ),
                  );
                },
                borderRadius: BorderRadius.circular(20),
                child: const Padding(
                  padding: EdgeInsets.all(18),
                  child: Row(
                    children: [
                      Icon(Icons.bar_chart_rounded, color: AppTheme.orange),
                      SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Lịch sử đề tùy chỉnh',
                                style: TextStyle(fontWeight: FontWeight.w800)),
                            Text('Theo điểm, loại đề, năng lực',
                                style: TextStyle(
                                    color: Colors.grey, fontSize: 11)),
                          ],
                        ),
                      ),
                      Icon(Icons.chevron_right_rounded, color: Colors.grey),
                    ],
                  ),
                ),
              ),
            ),
          const _SectionTitle('Cài đặt học tập'),
          const _Setting(
              icon: Icons.track_changes_rounded,
              title: 'Mục tiêu mỗi ngày',
              value: '15 phút'),
          const _Setting(
              icon: Icons.notifications_none_rounded,
              title: 'Nhắc nhở học tập',
              value: '20:00'),
          const _Setting(
              icon: Icons.translate_rounded,
              title: 'Trình độ hiện tại',
              value: 'HSK 2'),
        ],
      ),
    );
  }
}

class _ProfileStat extends StatelessWidget {
  const _ProfileStat(this.value, this.label);
  final String value, label;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        children: [
          Text(value,
              style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.jade)),
          Text(label, style: const TextStyle(color: Colors.grey, fontSize: 9)),
        ],
      ),
    );
  }
}

class _ProfileOverview extends StatefulWidget {
  const _ProfileOverview({
    required this.service,
    required this.name,
    required this.email,
  });

  final StudentService? service;
  final String name;
  final String email;

  @override
  State<_ProfileOverview> createState() => _ProfileOverviewState();
}

class _ProfileOverviewState extends State<_ProfileOverview> {
  Future<StudentDashboard>? _future;

  @override
  void initState() {
    super.initState();
    _future = widget.service?.fetchMyDashboard();
  }

  void _retry() => setState(() {
        _future = widget.service?.fetchMyDashboard();
      });

  @override
  Widget build(BuildContext context) {
    final initial = widget.name.trim().isEmpty
        ? 'H'
        : widget.name.trim().characters.first.toUpperCase();
    return Column(
      children: [
        CircleAvatar(
          radius: 46,
          backgroundColor: const Color(0xFFFFE6DA),
          child: Text(
            initial,
            style: const TextStyle(
              color: AppTheme.red,
              fontSize: 34,
              fontWeight: FontWeight.w800,
            ),
          ),
        ),
        const SizedBox(height: 12),
        Text(
          widget.name,
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w800),
        ),
        if (widget.email.isNotEmpty)
          Text(
            widget.email,
            textAlign: TextAlign.center,
            style: const TextStyle(color: Colors.grey, fontSize: 12),
          ),
        if (_future != null)
          FutureBuilder<StudentDashboard>(
            future: _future,
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Padding(
                  padding: EdgeInsets.all(24),
                  child: CircularProgressIndicator(),
                );
              }
              if (snapshot.hasError) {
                return Padding(
                  padding: const EdgeInsets.all(16),
                  child: OutlinedButton.icon(
                    onPressed: _retry,
                    icon: const Icon(Icons.refresh),
                    label: const Text('Tải lại thống kê cá nhân'),
                  ),
                );
              }
              final dashboard = snapshot.data!;
              return Padding(
                padding: const EdgeInsets.all(20),
                child: Row(
                  children: [
                    _ProfileStat('${dashboard.streak}', 'Ngày liên tiếp'),
                    _ProfileStat('${dashboard.results}', 'Bài đã làm'),
                    _ProfileStat('${dashboard.vocabularyCount}', 'Từ đã tra'),
                  ],
                ),
              );
            },
          ),
      ],
    );
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.text);
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 14, 20, 10),
      child: Text(text,
          style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
    );
  }
}

class _Setting extends StatelessWidget {
  const _Setting(
      {required this.icon, required this.title, required this.value});
  final IconData icon;
  final String title;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.fromLTRB(20, 0, 20, 9),
      child: ListTile(
        leading: Icon(icon, color: AppTheme.jade),
        title: Text(title,
            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700)),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(value,
                style: const TextStyle(color: Colors.grey, fontSize: 11)),
            const Icon(Icons.chevron_right_rounded, color: Colors.grey),
          ],
        ),
      ),
    );
  }
}
