import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../services/student_service.dart';
import '../theme/app_theme.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key, required this.service});
  final StudentService service;

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  late Future<_DashboardData> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<_DashboardData> _load() async {
    final summary = await widget.service.fetchMyDashboard();
    try {
      return _DashboardData(
        summary,
        await widget.service.fetchCapabilityReport(),
      );
    } on StudentApiException {
      return _DashboardData(
        summary,
        CapabilityReport(
          skillScores: summary.skillScores,
          feedback: 'Đã hiển thị thống kê học tập. Nhận xét AI tạm thời chưa có; kéo xuống để thử lại.',
          strengths: const [],
          improvements: const [],
        ),
      );
    }
  }

  void _reload() => setState(() => _future = _load());

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Dashboard học tập')),
    body: FutureBuilder<_DashboardData>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.cloud_off, size: 52, color: AppTheme.red),
                  const SizedBox(height: 12),
                  const Text(
                    'Không tải được Dashboard',
                    style: TextStyle(fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 6),
                  Text(snapshot.error.toString(), textAlign: TextAlign.center),
                  const SizedBox(height: 14),
                  FilledButton(
                    onPressed: _reload,
                    child: const Text('Thử lại'),
                  ),
                ],
              ),
            ),
          );
        }
        final data = snapshot.data!;
        return RefreshIndicator(
          onRefresh: () async => _reload(),
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              FutureBuilder<Map<String, dynamic>>(
                future: widget.service.fetchStudyGoals(),
                builder: (context, snapshot) {
                  if (snapshot.hasError) {
                    return const Text('Chưa tải được mục tiêu học tập.');
                  }
                  if (!snapshot.hasData) return const LinearProgressIndicator();
                  final goals = snapshot.data!;
                  return Card(
                    child: Padding(
                      padding: const EdgeInsets.all(18),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Mục tiêu của bạn',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Hôm nay: ${goals['daily_done']}/${goals['daily_goal']} bài',
                          ),
                          Text(
                            'Tuần này: ${goals['weekly_done']}/${goals['weekly_goal']} bài',
                          ),
                          const Text(
                            'Điều chỉnh mục tiêu trong Thông tin cá nhân.',
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
              Row(
                children: [
                  _Metric(
                    'Chuỗi ngày',
                    '${data.dashboard.streak}',
                    Icons.local_fire_department,
                  ),
                  _Metric(
                    'Bài đã làm',
                    '${data.dashboard.results}',
                    Icons.assignment_turned_in,
                  ),
                  _Metric(
                    'Từ đã tra',
                    '${data.dashboard.vocabularyCount}',
                    Icons.translate,
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Tiến độ ${data.dashboard.progressPercent.toStringAsFixed(0)}%',
                        style: const TextStyle(fontWeight: FontWeight.w800),
                      ),
                      const SizedBox(height: 10),
                      LinearProgressIndicator(
                        value: data.dashboard.progressPercent / 100,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '${data.dashboard.needsReview} bài cần ôn lại',
                        style: TextStyle(color: Colors.grey.shade700),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                'Năng lực tổng thể',
                style: TextStyle(fontSize: 19, fontWeight: FontWeight.w900),
              ),
              const SizedBox(height: 12),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    children: [
                      SizedBox(
                        height: 250,
                        child: CustomPaint(
                          key: const Key('skill-radar'),
                          painter: _RadarPainter(
                            data.report.skillScores,
                            isDark: Theme.of(context).brightness == Brightness.dark,
                          ),
                          child: const SizedBox.expand(),
                        ),
                      ),
                      Text(data.report.feedback, textAlign: TextAlign.center),
                    ],
                  ),
                ),
              ),
              if (data.report.strengths.isNotEmpty) ...[
                const SizedBox(height: 16),
                _AdviceCard('Điểm mạnh', data.report.strengths, AppTheme.jade),
              ],
              if (data.report.improvements.isNotEmpty) ...[
                const SizedBox(height: 12),
                _AdviceCard(
                  'Nên cải thiện',
                  data.report.improvements,
                  AppTheme.orange,
                ),
              ],
            ],
          ),
        );
      },
    ),
  );
}

class _DashboardData {
  const _DashboardData(this.dashboard, this.report);
  final StudentDashboard dashboard;
  final CapabilityReport report;
}

class _Metric extends StatelessWidget {
  const _Metric(this.label, this.value, this.icon);
  final String label, value;
  final IconData icon;

  @override
  Widget build(BuildContext context) => Expanded(
    child: Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 5),
        child: Column(
          children: [
            Icon(icon, color: AppTheme.jade),
            const SizedBox(height: 6),
            Text(
              value,
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
            ),
            Text(
              label,
              style: const TextStyle(fontSize: 10),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    ),
  );
}

class _AdviceCard extends StatelessWidget {
  const _AdviceCard(this.title, this.items, this.color);
  final String title;
  final List<String> items;
  final Color color;

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: TextStyle(color: color, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 8),
          ...items.map(
            (item) => Padding(
              padding: const EdgeInsets.only(bottom: 5),
              child: Text('• $item'),
            ),
          ),
        ],
      ),
    ),
  );
}

class _RadarPainter extends CustomPainter {
  _RadarPainter(this.scores, {this.isDark = false});
  final bool isDark;
  final Map<String, double> scores;
  static const labels = ['Nghe', 'Đọc', 'Viết'];
  static const keys = ['listening', 'reading', 'writing'];

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = math.min(size.width, size.height) * .34;
    final grid = Paint()
      ..color = isDark ? const Color(0xFF283B34) : const Color(0xFFD9DDD9)
      ..style = PaintingStyle.stroke;
    final fill = Paint()
      ..color = AppTheme.jade.withValues(alpha: .25)
      ..style = PaintingStyle.fill;
    final line = Paint()
      ..color = AppTheme.jade
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;
    List<Offset> polygon(double scale) => List.generate(3, (i) {
      final angle = -math.pi / 2 + i * 2 * math.pi / 3;
      return center + Offset(math.cos(angle), math.sin(angle)) * radius * scale;
    });
    for (final scale in [.25, .5, .75, 1.0]) {
      canvas.drawPath(_path(polygon(scale)), grid);
    }
    final values = List.generate(
      3,
      (i) => polygon((scores[keys[i]] ?? 0) / 100)[i],
    );
    canvas.drawPath(_path(values), fill);
    canvas.drawPath(_path(values), line);
    for (var i = 0; i < 3; i++) {
      final point = polygon(1.18)[i];
      final painter = TextPainter(
        text: TextSpan(
          text: '${labels[i]} ${(scores[keys[i]] ?? 0).round()}',
          style: const TextStyle(
            color: isDark ? const Color(0xFFE2ECE7) : AppTheme.ink,
            fontSize: 11,
            fontWeight: FontWeight.w700,
          ),
        ),
        textDirection: TextDirection.ltr,
      )..layout();
      painter.paint(
        canvas,
        point - Offset(painter.width / 2, painter.height / 2),
      );
    }
  }

  Path _path(List<Offset> points) {
    final path = Path()..moveTo(points.first.dx, points.first.dy);
    for (final point in points.skip(1)) {
      path.lineTo(point.dx, point.dy);
    }
    return path..close();
  }

  @override
  bool shouldRepaint(covariant _RadarPainter oldDelegate) =>
      oldDelegate.scores != scores;
}
