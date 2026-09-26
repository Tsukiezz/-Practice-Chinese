import 'package:flutter/material.dart';

import '../theme/app_theme.dart';
import '../widgets/common.dart';
import '../services/student_service.dart';

class ResultsScreen extends StatefulWidget {
  const ResultsScreen({
    super.key,
    required this.service,
    this.onBack,
  });

  final StudentService service;
  final VoidCallback? onBack;

  @override
  State<ResultsScreen> createState() => _ResultsScreenState();
}

class _ResultsScreenState extends State<ResultsScreen> {
  late Future<List<StudentResult>> _resultsFuture;
  String? _error;

  @override
  void initState() {
    super.initState();
    _resultsFuture = widget.service.fetchMyResults();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            ScreenHeader(
              eyebrow: 'Tiến độ học tập',
              title: 'Kết quả của bạn',
              showBackButton: widget.onBack != null || Navigator.of(context).canPop(),
              onBack: widget.onBack ?? (Navigator.of(context).canPop() ? () => Navigator.of(context).pop() : null),
              trailing: const Icon(Icons.bar_chart_rounded, color: AppTheme.jade),
            ),
            Expanded(child: _buildBody()),
          ],
        ),
      ),
    );
  }

  Widget _buildBody() {
    return FutureBuilder<List<StudentResult>>(
      future: _resultsFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return _MessageState(
            icon: Icons.cloud_off_rounded,
            title: 'Không tải được kết quả',
            message: _error ?? snapshot.error.toString(),
            actionLabel: 'Thử lại',
            onAction: () {
              setState(() {
                _error = null;
                _resultsFuture = widget.service.fetchMyResults();
              });
            },
          );
        }

        final results = snapshot.data ?? const <StudentResult>[];
        if (results.isEmpty) {
          return _MessageState(
            icon: Icons.inbox_rounded,
            title: 'Chưa có kết quả',
            message: 'Hãy làm bài luyện tập để xem kết quả ở đây.',
          );
        }

        return ListView.separated(
          padding: const EdgeInsets.fromLTRB(20, 4, 20, 24),
          itemCount: results.length,
          separatorBuilder: (_, __) => const SizedBox(height: 12),
          itemBuilder: (context, index) {
            final result = results[index];
            final passed = result.score >= 80;
            final isDark = Theme.of(context).brightness == Brightness.dark;
            return Card(
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Row(
                  children: [
                    Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color: passed
                            ? (isDark ? const Color(0xFF1E3228) : const Color(0xFFE4F4E9))
                            : (isDark ? const Color(0xFF382320) : const Color(0xFFFFF1E8)),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Center(
                        child: Text(
                          '${result.score.toInt()}',
                          style: TextStyle(
                            color: passed
                                ? (isDark ? const Color(0xFF4DB697) : AppTheme.jade)
                                : (isDark ? const Color(0xFFFF7A66) : AppTheme.orange),
                            fontWeight: FontWeight.w900,
                            fontSize: 18,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '${result.examId ?? 'Bài'} · ${_kindLabel(result.kind)}',
                            style: TextStyle(
                              fontWeight: FontWeight.w800,
                              color: isDark ? const Color(0xFFF0FDF4) : AppTheme.ink,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Chấm bởi: ${_gradedByLabel(result.gradedBy)}',
                            style: TextStyle(
                              color: isDark ? const Color(0xFFA3BFB3) : Colors.grey.shade600,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Icon(
                      passed
                          ? Icons.check_circle_rounded
                          : Icons.arrow_circle_right_rounded,
                      color: passed
                          ? (isDark ? const Color(0xFF4DB697) : AppTheme.jade)
                          : (isDark ? const Color(0xFFA3BFB3) : Colors.grey),
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  String _kindLabel(String kind) {
    return switch (kind) {
      'exam' => 'Bài thi',
      'writing' => 'Bài viết',
      'handwriting' => 'Viết tay',
      _ => kind,
    };
  }

  String _gradedByLabel(String gradedBy) {
    return switch (gradedBy) {
      'automatic' => 'Tự động',
      'ai' => 'AI',
      'admin' => 'Giáo viên',
      _ => gradedBy,
    };
  }
}

class _MessageState extends StatelessWidget {
  const _MessageState({
    required this.icon,
    required this.title,
    required this.message,
    this.actionLabel,
    this.onAction,
  });

  final IconData icon;
  final String title;
  final String message;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
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
            if (actionLabel != null && onAction != null) ...[
              const SizedBox(height: 16),
              FilledButton(onPressed: onAction, child: Text(actionLabel!)),
            ],
          ],
        ),
      ),
    );
  }
}
