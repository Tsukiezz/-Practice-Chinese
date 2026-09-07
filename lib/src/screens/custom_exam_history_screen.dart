import 'package:flutter/material.dart';

import '../theme/app_theme.dart';
import '../widgets/common.dart';
import '../services/custom_exam_service.dart';

class CustomExamHistoryScreen extends StatefulWidget {
  const CustomExamHistoryScreen({super.key, required this.service});

  final CustomExamService service;

  @override
  State<CustomExamHistoryScreen> createState() => _CustomExamHistoryScreenState();
}

class _CustomExamHistoryScreenState extends State<CustomExamHistoryScreen> {
  late final Future<List<CustomExamResult>> _resultsFuture;

  @override
  void initState() {
    super.initState();
    _resultsFuture = widget.service.loadResults();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Lịch sử làm bài'),
      ),
      body: SafeArea(
        child: FutureBuilder<List<CustomExamResult>>(
          future: _resultsFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return _MessageState(
                icon: Icons.cloud_off_rounded,
                title: 'Không tải được lịch sử',
                message: snapshot.error.toString(),
              );
            }

            final results = snapshot.data ?? const <CustomExamResult>[];
            if (results.isEmpty) {
              return _MessageState(
                icon: Icons.inbox_rounded,
                title: 'Chưa có bài làm nào',
                message: 'Hãy tạo đề và làm bài để xem lịch sử tại đây.',
              );
            }

            final grouped = <String, List<CustomExamResult>>{};
            for (final result in results) {
              final key = result.examId;
              grouped.putIfAbsent(key, () => <CustomExamResult>[]).add(result);
            }

            final averageScore = results.map((r) => r.score).reduce((a, b) => a + b) / results.length;
            final passCount = results.where((r) => r.score >= 80).length;
            final failCount = results.length - passCount;

            return ListView(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
              children: [
                Row(
                  children: [
                    Expanded(
                      child: _SummaryCard(
                        label: 'Điểm TB',
                        value: averageScore.toStringAsFixed(1),
                        color: averageScore >= 80 ? AppTheme.jade : AppTheme.orange,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _SummaryCard(
                        label: 'Đạt',
                        value: '$passCount',
                        color: AppTheme.jade,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _SummaryCard(
                        label: 'Chưa đạt',
                        value: '$failCount',
                        color: AppTheme.red,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                const Text(
                  'Chi tiết từng đề',
                  style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 10),
                ...grouped.entries.map((entry) {
                  final examResults = entry.value;
                  final latest = examResults.last;
                  final passed = latest.score >= 80;
                  return Card(
                    margin: const EdgeInsets.only(bottom: 10),
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundColor: passed ? const Color(0xFFE4F4E9) : const Color(0xFFFFF1E8),
                        child: Text(
                          latest.score.toStringAsFixed(0),
                          style: TextStyle(
                            color: passed ? AppTheme.jade : AppTheme.orange,
                            fontWeight: FontWeight.w900,
                            fontSize: 18,
                          ),
                        ),
                      ),
                      title: Text(
                        'Đề ${entry.key}',
                        style: const TextStyle(fontWeight: FontWeight.w800),
                      ),
                      subtitle: Text(
                        '${examResults.length} lần làm · ${passed ? 'Đạt' : 'Chưa đạt'}',
                      ),
                      trailing: const Icon(Icons.chevron_right_rounded, color: Colors.grey),
                      onTap: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (context) => _ExamDetailScreen(
                              examId: entry.key,
                              results: examResults,
                            ),
                          ),
                        );
                      },
                    ),
                  );
                }),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _ExamDetailScreen extends StatelessWidget {
  const _ExamDetailScreen({
    required this.examId,
    required this.results,
  });

  final String examId;
  final List<CustomExamResult> results;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Chi tiết đề $examId')),
      body: SafeArea(
        child: ListView.separated(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
          itemCount: results.length,
          separatorBuilder: (_, __) => const SizedBox(height: 10),
          itemBuilder: (context, index) {
            final result = results[index];
            final passed = result.score >= 80;
            final date = DateTime.fromMillisecondsSinceEpoch(result.createdAt * 1000);
            return Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: passed ? const Color(0xFFE4F4E9) : const Color(0xFFFFF1E8),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            result.score.toStringAsFixed(0),
                            style: TextStyle(
                              color: passed ? AppTheme.jade : AppTheme.orange,
                              fontWeight: FontWeight.w900,
                              fontSize: 16,
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Lần ${index + 1}',
                                style: const TextStyle(fontWeight: FontWeight.w800),
                              ),
                              Text(
                                '${date.day}/${date.month}/${date.year}',
                                style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
                              ),
                            ],
                          ),
                        ),
                        Icon(
                          passed ? Icons.check_circle_rounded : Icons.arrow_circle_right_rounded,
                          color: passed ? AppTheme.jade : Colors.grey,
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text('Số câu trả lời đúng: ${result.answers.length}'),
                    Text('Trạng thái: ${passed ? "Đạt" : "Chưa đạt"}'),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}

class _SummaryCard extends StatelessWidget {
  const _SummaryCard({
    required this.label,
    required this.value,
    required this.color,
  });

  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Text(
              value,
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.w900,
                color: color,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}

class _MessageState extends StatelessWidget {
  const _MessageState({
    required this.icon,
    required this.title,
    required this.message,
  });

  final IconData icon;
  final String title;
  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: AppTheme.jade, size: 54),
            const SizedBox(height: 14),
            Text(
              title,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 6),
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}
