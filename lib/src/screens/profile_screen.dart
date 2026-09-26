import 'package:flutter/material.dart';
import 'dart:convert';

import 'personalized_practice_screen.dart';
import '../theme/app_theme.dart';
import '../widgets/common.dart';
import '../services/student_service.dart';
import '../services/auth_service.dart';
import 'results_screen.dart';
import 'custom_exam_history_screen.dart';
import 'dashboard_screen.dart';
import 'review_screen.dart';
import 'handwriting_screen.dart';
import 'handwriting_retry_screen.dart';
import 'translation_screen.dart';
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
    this.onEditProfile,
    this.onOpenAdmin,
    this.onBack,
  });

  final VoidCallback? onLogout;
  final StudentService? studentService;
  final ReadingExamRepository? comprehensiveRepository;
  final AuthUser? user;
  final VoidCallback? onEditProfile;
  final VoidCallback? onOpenAdmin;
  final VoidCallback? onBack;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7F9F8),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.only(bottom: 24),
          children: [
            ScreenHeader(
              eyebrow: 'Hồ sơ học tập',
              title: 'Cá nhân',
              showBackButton: onBack != null || Navigator.of(context).canPop(),
              onBack: onBack ??
                  (Navigator.of(context).canPop()
                      ? () => Navigator.of(context).pop()
                      : null),
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
                  side: const BorderSide(color: Color(0xFFE0C49F), width: 1.2),
                ),
                child: ListTile(
                  leading: const CircleAvatar(
                    backgroundColor: Color(0xFF912018),
                    foregroundColor: Colors.white,
                    child: Icon(Icons.admin_panel_settings, size: 20),
                  ),
                  title: const Text(
                    'Không gian Quản trị viên',
                    style: TextStyle(fontWeight: FontWeight.w800, color: Color(0xFF7A271A)),
                  ),
                  subtitle: const Text(
                    'Quản lý học viên, kho từ, đề thi HSK 1–6 & hệ thống AI',
                    style: TextStyle(fontSize: 12),
                  ),
                  trailing: const Icon(Icons.arrow_forward_rounded, color: Color(0xFF912018)),
                  onTap: onOpenAdmin,
                ),
              ),
            ),
          const _SectionTitle('Cài đặt giao diện'),
          Card(
            margin: const EdgeInsets.symmetric(horizontal: 20),
            child: ValueListenableBuilder<ThemeMode>(
              valueListenable: ThemeManager.themeMode,
              builder: (context, mode, _) {
                final isDark = mode == ThemeMode.dark;
                return SwitchListTile(
                  secondary: Icon(
                    isDark ? Icons.dark_mode_rounded : Icons.light_mode_rounded,
                    color: isDark ? const Color(0xFFF6E05E) : AppTheme.jade,
                  ),
                  title: const Text(
                    'Chế độ Tối (Dark mode)',
                    style: TextStyle(fontWeight: FontWeight.w800),
                  ),
                  subtitle: Text(
                    isDark ? 'Giao diện tối dịu mắt' : 'Giao diện sáng tiêu chuẩn',
                  ),
                  value: isDark,
                  onChanged: (_) => ThemeManager.toggle(),
                );
              },
            ),
          ),
          const _SectionTitle('Kết quả học tập'),
          if (studentService != null)
            Card(
              child: ListTile(
                leading: const Icon(Icons.auto_awesome),
                title: const Text('Bài ôn cá nhân hóa'),
                subtitle: const Text('Tạo bài luyện mới từ lỗi sai của bạn'),
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) =>
                        PersonalizedPracticeScreen(service: studentService!),
                  ),
                ),
              ),
            ),
          if (comprehensiveRepository != null)
            Card(
              margin: const EdgeInsets.symmetric(horizontal: 20),
              child: ListTile(
                leading: const Icon(Icons.fact_check, color: AppTheme.jade),
                title: const Text(
                  'Bài test tổng hợp',
                  style: TextStyle(fontWeight: FontWeight.w800),
                ),
                subtitle: const Text('Nghe · Đọc · Viết trong cùng một đề'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => PracticeScreen(
                      repository: comprehensiveRepository!,
                      draftOwner: user?.id,
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
                title: const Text(
                  'Viết tay chữ Hán',
                  style: TextStyle(fontWeight: FontWeight.w800),
                ),
                subtitle: const Text(
                  'Tra từ viết tay hoặc chấm thứ tự nét offline',
                ),
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
                leading: const Icon(
                  Icons.auto_fix_high,
                  color: AppTheme.orange,
                ),
                title: const Text(
                  'Sửa câu tiếng Trung',
                  style: TextStyle(fontWeight: FontWeight.w800),
                ),
                subtitle: const Text(
                  'Kiểm tra ngữ pháp và phân tích ngữ cảnh bằng AI',
                ),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => TranslationScreen(service: studentService!),
                  ),
                ),
              ),
            ),
          if (studentService != null)
            Card(
              margin: const EdgeInsets.symmetric(horizontal: 20),
              child: ListTile(
                key: const Key('open-handwriting-retry'),
                leading: const Icon(Icons.history_edu, color: AppTheme.orange),
                title: const Text(
                  'Luyện lại chữ dưới 80',
                  style: TextStyle(fontWeight: FontWeight.w800),
                ),
                subtitle: const Text(
                  'Chọn một hoặc nhiều chữ và luyện bằng Canvas offline',
                ),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) =>
                        HandwritingRetryScreen(service: studentService!),
                  ),
                ),
              ),
            ),
          if (studentService != null)
            Card(
              margin: const EdgeInsets.symmetric(horizontal: 20),
              child: ListTile(
                leading: const Icon(Icons.radar_rounded, color: AppTheme.jade),
                title: const Text(
                  'Dashboard & năng lực',
                  style: TextStyle(fontWeight: FontWeight.w800),
                ),
                subtitle: const Text('Streak, tiến độ và đánh giá AI'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => DashboardScreen(service: studentService!),
                  ),
                ),
              ),
            ),
          if (studentService != null)
            Card(
              margin: const EdgeInsets.symmetric(horizontal: 20),
              child: ListTile(
                leading: const Icon(
                  Icons.replay_circle_filled,
                  color: AppTheme.orange,
                ),
                title: const Text(
                  'Ôn tập dưới 80 điểm',
                  style: TextStyle(fontWeight: FontWeight.w800),
                ),
                subtitle: const Text('Đồng bộ Đọc · Nghe · Kiểm tra · Viết tay · Từ vựng'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => ReviewScreen(service: studentService!),
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
          const _SectionTitle('Cài đặt học tập'),
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
        FutureBuilder<String>(future: _avatar, builder: (context, snapshot) {
          final avatar = snapshot.data ?? '';
          ImageProvider? image;
          if (avatar.startsWith('data:image/')) {
            try { image = MemoryImage(base64Decode(avatar.split(',').last)); }
            on FormatException { image = null; }
          }
          return CircleAvatar(
          radius: 46,
          backgroundColor: const Color(0xFFFFE6DA),
          backgroundImage: image,
          child: image != null ? null : Text(
            initial,
            style: const TextStyle(
              color: AppTheme.red,
              fontSize: 34,
              fontWeight: FontWeight.w800,
            ),
          ),
        ); }),
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
              final under80 = dashboard.under80Breakdown;
              final readingUnder80 = under80['reading'] ?? 0;
              final listeningUnder80 = under80['listening'] ?? 0;
              final examUnder80 = under80['exam'] ?? 0;
              final handwritingUnder80 = (under80['handwriting'] ?? 0) + (under80['writing'] ?? 0);
              final vocabWeak = under80['vocabulary'] ?? 0;
              final totalUnder80 = dashboard.needsReview;

              return Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                    child: Row(
                      children: [
                        _ProfileStat('${dashboard.streak}', 'Ngày liên tiếp'),
                        _ProfileStat('${dashboard.results}', 'Bài đã làm'),
                        _ProfileStat('${dashboard.vocabularyCount}', 'Từ đã tra'),
                        _ProfileStat(
                          '${dashboard.averageScore.toStringAsFixed(0)}đ',
                          'Điểm trung bình',
                        ),
                      ],
                    ),
                  ),

                  // Trung tâm Ôn tập dưới 80 điểm - Đồng bộ tất cả 5 kỹ năng
                  Padding(
                    padding: const EdgeInsets.fromLTRB(20, 4, 20, 14),
                    child: Card(
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(18),
                        side: const BorderSide(color: Color(0xFFF0D5C3), width: 1.2),
                      ),
                      color: const Color(0xFFFFF9F5),
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Row(
                                  children: [
                                    Icon(Icons.replay_circle_filled, color: AppTheme.orange, size: 22),
                                    SizedBox(width: 8),
                                    Text(
                                      'Ôn tập dưới 80 điểm',
                                      style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16, color: Color(0xFF8C3A00)),
                                    ),
                                  ],
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: totalUnder80 > 0 ? const Color(0xFFFFECE0) : const Color(0xFFE8F5E9),
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Text(
                                    totalUnder80 > 0 ? '$totalUnder80 mục cần ôn' : 'Đã đạt chuẩn',
                                    style: TextStyle(
                                      color: totalUnder80 > 0 ? AppTheme.red : Colors.green,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 12,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 6),
                            const Text(
                              'Đồng bộ tự động từ kết quả làm bài của bạn trên tất cả 5 kỹ năng:',
                              style: TextStyle(color: Color(0xFF7A5C4A), fontSize: 12),
                            ),
                            const SizedBox(height: 12),
                            Wrap(
                              spacing: 8,
                              runSpacing: 8,
                              children: [
                                _SkillReviewBadge(
                                  icon: Icons.mic_none_outlined,
                                  label: 'Đọc',
                                  count: readingUnder80,
                                  unit: 'mục <80%',
                                  onTap: () => widget.service == null
                                      ? null
                                      : Navigator.of(context).push(
                                          MaterialPageRoute(
                                            builder: (_) => ReviewScreen(
                                              service: widget.service!,
                                              initialKind: 'reading',
                                            ),
                                          ),
                                        ).then((_) => _retry()),
                                ),
                                _SkillReviewBadge(
                                  icon: Icons.headphones_outlined,
                                  label: 'Nghe',
                                  count: listeningUnder80,
                                  unit: 'bài <80đ',
                                  onTap: () => widget.service == null
                                      ? null
                                      : Navigator.of(context).push(
                                          MaterialPageRoute(
                                            builder: (_) => ReviewScreen(
                                              service: widget.service!,
                                              initialKind: 'listening',
                                            ),
                                          ),
                                        ).then((_) => _retry()),
                                ),
                                _SkillReviewBadge(
                                  icon: Icons.assignment_outlined,
                                  label: 'Kiểm tra',
                                  count: examUnder80,
                                  unit: 'đề <80đ',
                                  onTap: () => widget.service == null
                                      ? null
                                      : Navigator.of(context).push(
                                          MaterialPageRoute(
                                            builder: (_) => ReviewScreen(
                                              service: widget.service!,
                                              initialKind: 'exam',
                                            ),
                                          ),
                                        ).then((_) => _retry()),
                                ),
                                _SkillReviewBadge(
                                  icon: Icons.draw_outlined,
                                  label: 'Viết tay',
                                  count: handwritingUnder80,
                                  unit: 'chữ <80đ',
                                  onTap: () => widget.service == null
                                      ? null
                                      : Navigator.of(context).push(
                                          MaterialPageRoute(
                                            builder: (_) => ReviewScreen(
                                              service: widget.service!,
                                              initialKind: 'handwriting',
                                            ),
                                          ),
                                        ).then((_) => _retry()),
                                ),
                                _SkillReviewBadge(
                                  icon: Icons.menu_book_outlined,
                                  label: 'Từ vựng',
                                  count: vocabWeak,
                                  unit: 'từ cần nhớ',
                                  onTap: () => widget.service == null
                                      ? null
                                      : Navigator.of(context).push(
                                          MaterialPageRoute(
                                            builder: (_) => ReviewScreen(
                                              service: widget.service!,
                                              initialKind: 'vocabulary',
                                            ),
                                          ),
                                        ).then((_) => _retry()),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),

                  // Tiến độ năng lực đồng bộ
                  Padding(
                    padding: const EdgeInsets.fromLTRB(20, 0, 20, 14),
                    child: Card(
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(18),
                        side: const BorderSide(color: Color(0xFFDDE5E0)),
                      ),
                      color: Colors.white,
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Row(
                              children: [
                                Icon(Icons.analytics_outlined, color: AppTheme.jade, size: 20),
                                SizedBox(width: 8),
                                Text(
                                  'Năng lực đồng bộ theo kỹ năng',
                                  style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15, color: AppTheme.ink),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            _SkillProgressBar(
                              label: 'Đọc phát âm (AI Voice)',
                              score: dashboard.skillScores['reading'] ?? 0,
                              icon: Icons.mic,
                            ),
                            _SkillProgressBar(
                              label: 'Luyện nghe hiểu',
                              score: dashboard.skillScores['listening'] ?? 0,
                              icon: Icons.headphones,
                            ),
                            _SkillProgressBar(
                              label: 'Kiểm tra & Đề thi AI',
                              score: dashboard.skillScores['exam'] ?? 0,
                              icon: Icons.assignment_turned_in,
                            ),
                            _SkillProgressBar(
                              label: 'Viết tay & Đoạn văn',
                              score: dashboard.skillScores['writing'] ?? 0,
                              icon: Icons.draw,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
              );
            },
          ),
      ],
    );
  }
}

class _SkillReviewBadge extends StatelessWidget {
  const _SkillReviewBadge({
    required this.icon,
    required this.label,
    required this.count,
    required this.unit,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final int count;
  final String unit;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final hasItems = count > 0;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(
          color: hasItems ? const Color(0xFFFFECE3) : Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: hasItems ? const Color(0xFFF5B895) : const Color(0xFFE2EBE5),
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 16, color: hasItems ? AppTheme.red : AppTheme.jade),
            const SizedBox(width: 6),
            Text(
              '$label: ',
              style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12),
            ),
            Text(
              '$count $unit',
              style: TextStyle(
                color: hasItems ? AppTheme.red : const Color(0xFF5C6F64),
                fontWeight: hasItems ? FontWeight.bold : FontWeight.w500,
                fontSize: 12,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SkillProgressBar extends StatelessWidget {
  const _SkillProgressBar({
    required this.label,
    required this.score,
    required this.icon,
  });

  final String label;
  final double score;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final percent = (score / 100.0).clamp(0.0, 1.0);
    final color = score >= 80 ? Colors.green : (score >= 50 ? Colors.orange : AppTheme.red);

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 15, color: const Color(0xFF5C6F64)),
              const SizedBox(width: 6),
              Expanded(
                child: Text(label, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
              ),
              Text(
                '${score.toStringAsFixed(0)}%',
                style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 13),
              ),
            ],
          ),
          const SizedBox(height: 5),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: percent,
              minHeight: 6,
              backgroundColor: const Color(0xFFE5EDE8),
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
        ],
      ),
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
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              value,
              style: const TextStyle(color: Colors.grey, fontSize: 11),
            ),
            const Icon(Icons.chevron_right_rounded, color: Colors.grey),
          ],
        ),
      ),
    );
  }
}
