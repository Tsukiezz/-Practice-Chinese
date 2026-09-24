import 'package:flutter/material.dart';

import '../services/ai_exam_service.dart';
import '../services/listening_exam_service.dart';
import '../services/reading_exam_service.dart';
import '../services/student_service.dart';
import '../theme/app_theme.dart';
import 'ai_exam_screen.dart';
import 'handwriting_retry_screen.dart';
import 'handwriting_screen.dart';
import 'listening_screen.dart';
import 'personalized_practice_screen.dart';
import 'practice_screen.dart';
import 'review_screen.dart';
import 'translation_screen.dart';

class PracticeHubScreen extends StatelessWidget {
  const PracticeHubScreen({
    super.key,
    required this.studentService,
    required this.aiExamService,
    required this.readingRepository,
    required this.listeningRepository,
    required this.comprehensiveRepository,
    this.draftOwner,
  });

  final StudentService studentService;
  final AIExamService aiExamService;
  final ReadingExamRepository readingRepository;
  final ListeningExamRepository listeningRepository;
  final ReadingExamRepository comprehensiveRepository;
  final int? draftOwner;

  @override
  Widget build(BuildContext context) {
    final sections = <_PracticeSection>[
      _PracticeSection(
        title: 'Kỹ năng',
        subtitle: 'Chọn một kỹ năng để luyện theo nhịp của bạn.',
        items: [
          _PracticeItem(
            title: 'Luyện nghe',
            subtitle: 'Nghe hội thoại và trả lời theo cấp độ HSK',
            icon: Icons.headphones_rounded,
            color: const Color(0xFFF3E9D5),
            onTap: () => _openEmbedded(
              context,
              'Luyện nghe',
              ListeningScreen(
                repository: listeningRepository,
                draftOwner: draftOwner,
              ),
            ),
          ),
          _PracticeItem(
            title: 'Luyện đọc',
            subtitle: 'Đọc hiểu, sắp xếp câu và trả lời theo cấp độ',
            icon: Icons.chrome_reader_mode_rounded,
            color: const Color(0xFFE4EAF6),
            onTap: () => _openEmbedded(
              context,
              'Luyện đọc',
              PracticeScreen(
                repository: readingRepository,
                draftOwner: draftOwner,
              ),
            ),
          ),
          _PracticeItem(
            title: 'Viết tay chữ Hán',
            subtitle: 'Tra chữ viết tay hoặc luyện đúng thứ tự nét',
            icon: Icons.gesture_rounded,
            color: const Color(0xFFF3E3DE),
            onTap: () => _open(
              context,
              HandwritingScreen(service: studentService),
            ),
          ),
          _PracticeItem(
            title: 'Dịch & sửa câu',
            subtitle: 'Dịch văn bản, kiểm tra ngữ pháp và ngữ cảnh',
            icon: Icons.auto_fix_high_rounded,
            color: const Color(0xFFE8F0EC),
            onTap: () => _open(
              context,
              TranslationScreen(service: studentService),
            ),
          ),
        ],
      ),
      _PracticeSection(
        title: 'Kiểm tra',
        subtitle: 'Đánh giá kiến thức và xem góp ý sau khi nộp bài.',
        items: [
          _PracticeItem(
            title: 'Kiểm tra AI',
            subtitle: 'Tạo đề theo cấp độ, chủ đề và số lượng câu',
            icon: Icons.assignment_turned_in_rounded,
            color: const Color(0xFFE3EEE8),
            onTap: () => _openEmbedded(
              context,
              'Kiểm tra AI',
              AiExamScreen(service: aiExamService),
            ),
          ),
          _PracticeItem(
            title: 'Kiểm tra tổng hợp',
            subtitle: 'Nghe, đọc và viết trong cùng một bài',
            icon: Icons.fact_check_rounded,
            color: const Color(0xFFF1E8F5),
            onTap: () => _openEmbedded(
              context,
              'Kiểm tra tổng hợp',
              PracticeScreen(
                repository: comprehensiveRepository,
                draftOwner: draftOwner,
                title: 'Kiểm tra tổng hợp',
                eyebrow: 'Bài luyện · Ba kỹ năng',
                skillLabel: 'NGHE · ĐỌC · VIẾT',
              ),
            ),
          ),
        ],
      ),
      _PracticeSection(
        title: 'Dành cho bạn',
        subtitle: 'Tập trung vào những nội dung bạn còn chưa vững.',
        items: [
          _PracticeItem(
            title: 'Bài ôn cá nhân hóa',
            subtitle: 'Tạo bài luyện mới từ những lỗi sai gần đây',
            icon: Icons.auto_awesome_rounded,
            color: const Color(0xFFFFEED5),
            onTap: () => _open(
              context,
              PersonalizedPracticeScreen(service: studentService),
            ),
          ),
          _PracticeItem(
            title: 'Ôn lại bài chưa đạt',
            subtitle: 'Xem lại bài viết và nội dung dưới 80 điểm',
            icon: Icons.replay_circle_filled_rounded,
            color: const Color(0xFFFBE5DD),
            onTap: () => _open(
              context,
              ReviewScreen(service: studentService),
            ),
          ),
          _PracticeItem(
            title: 'Luyện lại chữ chưa đạt',
            subtitle: 'Chọn các chữ cần cải thiện và luyện lại',
            icon: Icons.history_edu_rounded,
            color: const Color(0xFFE5EFEA),
            onTap: () => _open(
              context,
              HandwritingRetryScreen(service: studentService),
            ),
          ),
        ],
      ),
    ];

    return SafeArea(
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1120),
          child: CustomScrollView(
            key: const PageStorageKey('practice-hub'),
            slivers: [
              const SliverPadding(
                padding: EdgeInsets.fromLTRB(20, 24, 20, 8),
                sliver: SliverToBoxAdapter(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'LUYỆN TẬP THEO MỤC TIÊU',
                        style: TextStyle(
                          color: AppTheme.jade,
                          fontSize: 11,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 1.2,
                        ),
                      ),
                      SizedBox(height: 7),
                      Text(
                        'Hôm nay bạn muốn luyện gì?',
                        style: TextStyle(
                          color: AppTheme.ink,
                          fontSize: 27,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      SizedBox(height: 7),
                      Text(
                        'Mỗi lần chỉ cần chọn một mục. Kết quả và lịch sử vẫn được lưu trong phần Cá nhân.',
                        style: TextStyle(
                          color: Color(0xFF60736A),
                          fontSize: 14,
                          height: 1.5,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              for (final section in sections) ...[
                SliverPadding(
                  padding: const EdgeInsets.fromLTRB(20, 22, 20, 10),
                  sliver: SliverToBoxAdapter(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          section.title,
                          style: const TextStyle(
                            color: AppTheme.ink,
                            fontSize: 19,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          section.subtitle,
                          style: const TextStyle(
                            color: Color(0xFF60736A),
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                SliverPadding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  sliver: SliverLayoutBuilder(
                    builder: (context, constraints) {
                      final width = constraints.crossAxisExtent;
                      final columns = width >= 900 ? 3 : (width >= 560 ? 2 : 1);
                      return SliverGrid(
                        delegate: SliverChildBuilderDelegate(
                          (context, index) => _PracticeCard(
                            item: section.items[index],
                          ),
                          childCount: section.items.length,
                        ),
                        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: columns,
                          mainAxisSpacing: 12,
                          crossAxisSpacing: 12,
                          mainAxisExtent: 132,
                        ),
                      );
                    },
                  ),
                ),
              ],
              const SliverToBoxAdapter(child: SizedBox(height: 28)),
            ],
          ),
        ),
      ),
    );
  }

  void _open(BuildContext context, Widget page) {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => page));
  }

  void _openEmbedded(BuildContext context, String title, Widget page) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => Scaffold(
          appBar: AppBar(title: Text(title)),
          body: page,
        ),
      ),
    );
  }
}

class _PracticeSection {
  const _PracticeSection({
    required this.title,
    required this.subtitle,
    required this.items,
  });

  final String title;
  final String subtitle;
  final List<_PracticeItem> items;
}

class _PracticeItem {
  const _PracticeItem({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;
}

class _PracticeCard extends StatelessWidget {
  const _PracticeCard({required this.item});

  final _PracticeItem item;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.zero,
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: item.onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 50,
                height: 50,
                decoration: BoxDecoration(
                  color: item.color,
                  borderRadius: BorderRadius.circular(15),
                ),
                child: Icon(item.icon, color: AppTheme.ink),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      item.subtitle,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: Color(0xFF60736A),
                        fontSize: 12,
                        height: 1.35,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 6),
              const Icon(Icons.chevron_right_rounded, color: AppTheme.jade),
            ],
          ),
        ),
      ),
    );
  }
}
