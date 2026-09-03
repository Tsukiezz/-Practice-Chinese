import 'package:flutter/material.dart';

import '../data/learning_data.dart';
import '../theme/app_theme.dart';
import '../widgets/common.dart';

class LessonsScreen extends StatelessWidget {
  const LessonsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        children: [
          const ScreenHeader(
            eyebrow: 'Lộ trình HSK',
            title: 'Bài học của bạn',
            trailing: Icon(Icons.search_rounded),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Row(
              children: ['Tất cả', 'HSK 1', 'HSK 2', 'Giao tiếp'].map((label) {
                final selected = label == 'Tất cả';
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: Chip(
                    label: Text(label),
                    backgroundColor: selected ? const Color(0xFFFFE7DC) : Colors.white,
                    labelStyle: TextStyle(
                      color: selected ? AppTheme.red : Colors.grey,
                      fontWeight: FontWeight.w700,
                      fontSize: 11,
                    ),
                    side: BorderSide.none,
                  ),
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 10),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
              itemCount: lessons.length,
              itemBuilder: (context, index) {
                final item = lessons[index];
                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(20),
                    onTap: () => _openLesson(context, item),
                    child: Padding(
                      padding: const EdgeInsets.all(17),
                      child: Row(
                        children: [
                          HanziAvatar(item.icon, size: 62, color: Color(item.color)),
                          const SizedBox(width: 15),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(item.level, style: const TextStyle(color: AppTheme.red, fontSize: 9, fontWeight: FontWeight.w800)),
                                const SizedBox(height: 5),
                                Text(item.title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                                Text(item.subtitle, style: const TextStyle(color: Colors.grey, fontSize: 10)),
                                const SizedBox(height: 10),
                                ProgressLine(value: item.progress),
                              ],
                            ),
                          ),
                          const Icon(Icons.chevron_right_rounded),
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  void _openLesson(BuildContext context, Lesson lesson) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) => Padding(
        padding: const EdgeInsets.fromLTRB(24, 4, 24, 32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            HanziAvatar(lesson.icon, size: 88, color: Color(lesson.color)),
            const SizedBox(height: 16),
            Text(lesson.title, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800)),
            const SizedBox(height: 6),
            Text(lesson.subtitle, style: const TextStyle(color: Colors.grey)),
            const SizedBox(height: 22),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: () => Navigator.pop(context),
                child: Text(lesson.progress > 0 ? 'Tiếp tục học' : 'Bắt đầu bài học'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
