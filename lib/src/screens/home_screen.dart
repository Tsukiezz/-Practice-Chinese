import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({
    super.key,
    required this.onOpenLessons,
    this.userName = '',
    this.onOpenPractice,
    this.onOpenDictionary,
    this.onOpenProfile,
  });
  final String userName;
  final VoidCallback onOpenLessons;
  final VoidCallback? onOpenPractice, onOpenDictionary, onOpenProfile;

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
                        '学 / TIẾP TỤC HÀNH TRÌNH',
                        style: TextStyle(
                          color: Color(0xFFE2C391),
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 20),
                      const Text(
                        'Học một chút hôm nay.\nTiến bộ thêm một bước.',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 28,
                          height: 1.2,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const SizedBox(height: 12),
                      const Text(
                        'Mở lộ trình của bạn và tiếp tục từ bài học phù hợp nhất.',
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
                  'Bắt đầu từ đâu?',
                  style: TextStyle(fontSize: 21, fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Chọn đúng mục tiêu, mọi công cụ liên quan sẽ nằm cùng một chỗ.',
                  style: TextStyle(color: Color(0xFF60736A), height: 1.5),
                ),
                const SizedBox(height: 16),
                LayoutBuilder(
                  builder: (context, constraints) {
                    final twoColumns = constraints.maxWidth >= 620;
                    final width = twoColumns
                        ? (constraints.maxWidth - 12) / 2
                        : constraints.maxWidth;
                    return Wrap(
                      spacing: 12,
                      runSpacing: 12,
                      children: [
                        SizedBox(
                          width: width,
                          child: _card(
                            'Bài học',
                            'Theo lộ trình HSK và tiếp tục bài đang học',
                            Icons.menu_book_rounded,
                            const Color(0xFFE3EEE8),
                            onOpenLessons,
                          ),
                        ),
                        SizedBox(
                          width: width,
                          child: _card(
                            'Luyện tập',
                            'Nghe, đọc, viết, kiểm tra và ôn lỗi sai',
                            Icons.grid_view_rounded,
                            const Color(0xFFF3E9D5),
                            onOpenPractice,
                          ),
                        ),
                        SizedBox(
                          width: width,
                          child: _card(
                            'Từ điển',
                            'Tra bằng bàn phím hoặc viết tay, lưu vào sổ tay',
                            Icons.search_rounded,
                            const Color(0xFFF3E3DE),
                            onOpenDictionary,
                          ),
                        ),
                      ],
                    );
                  },
                ),
                const SizedBox(height: 20),
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
  ) =>
      Material(
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
      );
}
