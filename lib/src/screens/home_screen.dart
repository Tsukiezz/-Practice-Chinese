import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({
    super.key,
    required this.onOpenLessons,
    this.userName = '',
    this.onOpenListening,
    this.onOpenReading,
    this.onOpenDictionary,
    this.onOpenProfile,
    this.onOpenAiExam,
  });
  final String userName;
  final VoidCallback onOpenLessons;
  final VoidCallback? onOpenListening,
      onOpenReading,
      onOpenDictionary,
      onOpenProfile,
      onOpenAiExam;

  @override
  Widget build(BuildContext context) => SafeArea(
    child: Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 840),
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 24, 20, 28),
          children: [
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'HANZIGO · KHÔNG GIAN HỌC TẬP',
                        style: TextStyle(
                          fontSize: 11,
                          letterSpacing: 1.2,
                          color: AppTheme.jade,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        userName.trim().isEmpty
                            ? 'Xin chào bạn!'
                            : 'Xin chào, ${userName.trim()}',
                        style: const TextStyle(
                          fontSize: 26,
                          fontWeight: FontWeight.w800,
                          color: AppTheme.ink,
                        ),
                      ),
                    ],
                  ),
                ),
                IconButton.filledTonal(
                  onPressed: onOpenProfile,
                  tooltip: 'Tài khoản của tôi',
                  icon: const Icon(Icons.person_outline_rounded),
                ),
              ],
            ),
            const SizedBox(height: 24),
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF163F35), Color(0xFF397765)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(28),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    '学 / HỌC THEO NHỊP CỦA BẠN',
                    style: TextStyle(
                      color: Color(0xFFE2C391),
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 20),
                  const Text(
                    'Một chút mỗi ngày.\nTự tin hơn mỗi bước.',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 28,
                      height: 1.2,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'Chọn một bài học nhỏ và bắt đầu hành trình tiếng Trung hôm nay.',
                    style: TextStyle(
                      color: Color(0xFFE0ECE5),
                      fontSize: 15,
                      height: 1.5,
                    ),
                  ),
                  const SizedBox(height: 24),
                  FilledButton.icon(
                    onPressed: onOpenLessons,
                    style: FilledButton.styleFrom(
                      backgroundColor: const Color(0xFFEAD8B3),
                      foregroundColor: const Color(0xFF163F35),
                    ),
                    icon: const Icon(Icons.arrow_forward_rounded),
                    label: const Text('Bắt đầu học'),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 28),
            const Text(
              'Hôm nay bạn muốn học gì?',
              style: TextStyle(fontSize: 21, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 6),
            const Text(
              'Chạm để bắt đầu, học từng bước vừa sức.',
              style: TextStyle(color: Color(0xFF60736A), height: 1.5),
            ),
            const SizedBox(height: 16),
            _card(
              'Bài học',
              'Khám phá kiến thức và luyện viết',
              Icons.menu_book_rounded,
              const Color(0xFFE3EEE8),
              onOpenLessons,
            ),
            _card(
              'Luyện nghe',
              'Nghe hội thoại, hiểu từng câu',
              Icons.headphones_rounded,
              const Color(0xFFF3E9D5),
              onOpenListening,
            ),
            _card(
              'Luyện đọc phát âm AI',
              'Đọc qua micro, HSK 1–6 & chủ đề, AI chấm và sửa lỗi',
              Icons.record_voice_over_rounded,
              const Color(0xFFE4EAF6),
              onOpenReading,
            ),
            _card(
              'Tra từ điển',
              'Hán tự, pinyin và phát âm',
              Icons.search_rounded,
              const Color(0xFFF3E3DE),
              onOpenDictionary,
            ),
            _card(
              'Kiểm tra AI',
              'Tạo đề thi tùy chọn, làm bài đếm ngược và AI chấm sửa',
              Icons.assignment_turned_in_rounded,
              const Color(0xFFE8F0EC),
              onOpenAiExam,
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: onOpenProfile,
              icon: const Icon(Icons.insights_rounded),
              label: const Text('Xem tiến trình của tôi'),
            ),
          ],
        ),
      ),
    ),
  );

  Widget _card(
    String title,
    String subtitle,
    IconData icon,
    Color color,
    VoidCallback? onTap,
  ) => Padding(
    padding: const EdgeInsets.only(bottom: 12),
    child: Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(22),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(13),
                decoration: BoxDecoration(
                  color: color,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Icon(icon, color: AppTheme.ink),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      subtitle,
                      style: const TextStyle(
                        color: Color(0xFF60736A),
                        fontSize: 13,
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right_rounded, color: AppTheme.jade),
            ],
          ),
        ),
      ),
    ),
  );
}
