import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/common.dart';
import '../services/student_service.dart';
import 'results_screen.dart';
import 'custom_exam_screen.dart';
import 'custom_exam_history_screen.dart';
import '../services/custom_exam_service.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key, this.onLogout, this.studentService});

  final VoidCallback? onLogout;
  final StudentService? studentService;

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
          const CircleAvatar(
            radius: 46,
            backgroundColor: Color(0xFFFFE6DA),
            child: Text(
              'A',
              style: TextStyle(color: AppTheme.red, fontSize: 34, fontWeight: FontWeight.w800),
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            'Minh Anh',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 21, fontWeight: FontWeight.w800),
          ),
          const Text(
            'Trình độ HSK 2',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.grey, fontSize: 12),
          ),
          Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: const [
                _ProfileStat('12', 'Ngày liên tiếp'),
                _ProfileStat('420', 'Tổng XP'),
                _ProfileStat('86', 'Từ đã học'),
              ],
            ),
          ),
          const _SectionTitle('Thành tích'),
          Card(
            margin: const EdgeInsets.symmetric(horizontal: 20),
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFFE9D6),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: const Icon(Icons.local_fire_department_rounded, color: AppTheme.orange),
                  ),
                  const SizedBox(width: 14),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Chăm chỉ mỗi ngày', style: TextStyle(fontWeight: FontWeight.w800)),
                        Text('Hoàn thành chuỗi học 7 ngày', style: TextStyle(color: Colors.grey, fontSize: 11)),
                      ],
                    ),
                  ),
                  const Icon(Icons.check_circle, color: AppTheme.jade),
                ],
              ),
            ),
          ),
          const _SectionTitle('Kết quả học tập'),
          if (studentService != null)
            Card(
              margin: const EdgeInsets.symmetric(horizontal: 20),
              child: InkWell(
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (context) => ResultsScreen(service: studentService!),
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
                            Text('Lịch sử bài làm', style: TextStyle(fontWeight: FontWeight.w800)),
                            Text('Xem lại điểm và nhận xét', style: TextStyle(color: Colors.grey, fontSize: 11)),
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
                      builder: (context) => CustomExamScreen(service: CustomExamService.instance!),
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
                            Text('Tạo đề thi tùy chỉnh', style: TextStyle(fontWeight: FontWeight.w800)),
                            Text('Tạo đề Nghe hoặc Đọc', style: TextStyle(color: Colors.grey, fontSize: 11)),
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
                      builder: (context) => CustomExamHistoryScreen(service: CustomExamService.instance!),
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
                            Text('Lịch sử đề tùy chỉnh', style: TextStyle(fontWeight: FontWeight.w800)),
                            Text('Theo điểm, loại đề, năng lực', style: TextStyle(color: Colors.grey, fontSize: 11)),
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
          const _Setting(icon: Icons.track_changes_rounded, title: 'Mục tiêu mỗi ngày', value: '15 phút'),
          const _Setting(icon: Icons.notifications_none_rounded, title: 'Nhắc nhở học tập', value: '20:00'),
          const _Setting(icon: Icons.translate_rounded, title: 'Trình độ hiện tại', value: 'HSK 2'),
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
          Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: AppTheme.jade)),
          Text(label, style: const TextStyle(color: Colors.grey, fontSize: 9)),
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
      child: Text(text, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
    );
  }
}

class _Setting extends StatelessWidget {
  const _Setting({required this.icon, required this.title, required this.value});
  final IconData icon;
  final String title;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.fromLTRB(20, 0, 20, 9),
      child: ListTile(
        leading: Icon(icon, color: AppTheme.jade),
        title: Text(title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700)),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(value, style: const TextStyle(color: Colors.grey, fontSize: 11)),
            const Icon(Icons.chevron_right_rounded, color: Colors.grey),
          ],
        ),
      ),
    );
  }
}
