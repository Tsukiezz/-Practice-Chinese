import 'package:flutter/material.dart';
import 'dart:convert';

import '../theme/app_theme.dart';
import '../widgets/common.dart';
import '../services/student_service.dart';
import '../services/auth_service.dart';
import 'results_screen.dart';
import 'custom_exam_history_screen.dart';
import 'dashboard_screen.dart';
import '../services/custom_exam_service.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({
    super.key,
    this.onLogout,
    this.studentService,
    this.user,
    this.onEditProfile,
    this.onOpenAdmin,
  });

  final VoidCallback? onLogout;
  final StudentService? studentService;
  final AuthUser? user;
  final VoidCallback? onEditProfile;
  final VoidCallback? onOpenAdmin;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 840),
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
                        content:
                            const Text('Bạn cần đăng nhập lại để luyện tập.'),
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
              if (onEditProfile != null)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: OutlinedButton.icon(
                    onPressed: onEditProfile,
                    icon: const Icon(Icons.manage_accounts_outlined),
                    label: const Text('Hồ sơ, ảnh đại diện và mật khẩu'),
                  ),
                ),
              if (onOpenAdmin != null)
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 10, 20, 4),
                  child: Card(
                    color: const Color(0xFFFBF3EA),
                    elevation: 0,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                      side: const BorderSide(
                          color: Color(0xFFE0C49F), width: 1.2),
                    ),
                    child: ListTile(
                      leading: const CircleAvatar(
                        backgroundColor: Color(0xFF912018),
                        foregroundColor: Colors.white,
                        child: Icon(Icons.admin_panel_settings, size: 20),
                      ),
                      title: const Text(
                        'Không gian Quản trị viên',
                        style: TextStyle(
                            fontWeight: FontWeight.w800,
                            color: Color(0xFF7A271A)),
                      ),
                      subtitle: const Text(
                        'Quản lý học viên, kho từ, đề thi HSK 1–6 & hệ thống AI',
                        style: TextStyle(fontSize: 12),
                      ),
                      trailing: const Icon(Icons.arrow_forward_rounded,
                          color: Color(0xFF912018)),
                      onTap: onOpenAdmin,
                    ),
                  ),
                ),
              const _SectionTitle('Tiến độ và lịch sử'),
              if (studentService != null)
                Card(
                  margin: const EdgeInsets.symmetric(horizontal: 20),
                  child: ListTile(
                    leading:
                        const Icon(Icons.radar_rounded, color: AppTheme.jade),
                    title: const Text(
                      'Tiến độ học tập',
                      style: TextStyle(fontWeight: FontWeight.w800),
                    ),
                    subtitle:
                        const Text('Ngày học liên tiếp, kỹ năng và góp ý'),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) =>
                            DashboardScreen(service: studentService!),
                      ),
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
                                Text(
                                  'Lịch sử bài làm',
                                  style: TextStyle(fontWeight: FontWeight.w800),
                                ),
                                Text(
                                  'Xem lại điểm và nhận xét',
                                  style: TextStyle(
                                    color: Colors.grey,
                                    fontSize: 11,
                                  ),
                                ),
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
                            service: CustomExamService.instance!,
                          ),
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
                                Text(
                                  'Lịch sử đề tùy chỉnh',
                                  style: TextStyle(fontWeight: FontWeight.w800),
                                ),
                                Text(
                                  'Theo điểm, loại đề, năng lực',
                                  style: TextStyle(
                                    color: Colors.grey,
                                    fontSize: 11,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          Icon(Icons.chevron_right_rounded, color: Colors.grey),
                        ],
                      ),
                    ),
                  ),
                ),
              const _SectionTitle('Thông tin học tập'),
              const _Setting(
                icon: Icons.track_changes_rounded,
                title: 'Mục tiêu mỗi ngày',
                value: '15 phút',
              ),
              const _Setting(
                icon: Icons.notifications_none_rounded,
                title: 'Nhắc nhở học tập',
                value: '20:00',
              ),
              const _Setting(
                icon: Icons.translate_rounded,
                title: 'Trình độ hiện tại',
                value: 'HSK 2',
              ),
            ],
          ),
        ),
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
          Text(
            value,
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w800,
              color: AppTheme.jade,
            ),
          ),
          Text(
            label,
            textAlign: TextAlign.center,
            style: const TextStyle(color: Colors.grey, fontSize: 12),
          ),
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
  Future<String>? _avatar;

  @override
  void initState() {
    super.initState();
    _future = widget.service?.fetchMyDashboard();
    _avatar = widget.service?.fetchAvatar();
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
        FutureBuilder<String>(
            future: _avatar,
            builder: (context, snapshot) {
              final avatar = snapshot.data ?? '';
              ImageProvider? image;
              if (avatar.startsWith('data:image/')) {
                try {
                  image = MemoryImage(base64Decode(avatar.split(',').last));
                } on FormatException {
                  image = null;
                }
              }
              return CircleAvatar(
                radius: 46,
                backgroundColor: const Color(0xFFFFE6DA),
                backgroundImage: image,
                child: image != null
                    ? null
                    : Text(
                        initial,
                        style: const TextStyle(
                          color: AppTheme.red,
                          fontSize: 34,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
              );
            }),
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
      child: Text(
        text,
        style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
      ),
    );
  }
}

class _Setting extends StatelessWidget {
  const _Setting({
    required this.icon,
    required this.title,
    required this.value,
  });
  final IconData icon;
  final String title;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.fromLTRB(20, 0, 20, 9),
      child: ListTile(
        leading: Icon(icon, color: AppTheme.jade),
        title: Text(
          title,
          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
        ),
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
          decoration: BoxDecoration(
            color: const Color(0xFFE9F3ED),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Text(
            value,
            style: const TextStyle(
              color: AppTheme.jade,
              fontSize: 12,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
      ),
    );
  }
}
