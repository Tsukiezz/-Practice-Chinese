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
    final values = await Future.wait<Object>([
      widget.service.fetchMyDashboard(),
      widget.service.fetchCapabilityReport(),
    ]);
    return _DashboardData(
      values[0] as StudentDashboard,
      values[1] as CapabilityReport,
    );
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
                      const Icon(Icons.cloud_off,
                          size: 52, color: AppTheme.red),
                      const SizedBox(height: 12),
                      const Text('Không tải được Dashboard',
                          style: TextStyle(fontWeight: FontWeight.w800)),
                      const SizedBox(height: 6),
                      Text(snapshot.error.toString(),
                          textAlign: TextAlign.center),
                      const SizedBox(height: 14),
                      FilledButton(
                          onPressed: _reload, child: const Text('Thử lại')),
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
                  Row(
                    children: [
                      _Metric('Chuỗi ngày', '${data.dashboard.streak}',
                          Icons.local_fire_department),
                      _Metric('Bài đã làm', '${data.dashboard.results}',
                          Icons.assignment_turned_in),
                      _Metric('Từ đã tra', '${data.dashboard.vocabularyCount}',
                          Icons.translate),
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
                              style:
                                  const TextStyle(fontWeight: FontWeight.w800)),
                          const SizedBox(height: 10),
                          LinearProgressIndicator(
                              value: data.dashboard.progressPercent / 100),
                          const SizedBox(height: 8),
                          Text('${data.dashboard.needsReview} bài cần ôn lại',
                              style: TextStyle(color: Colors.grey.shade700)),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  const Text('Năng lực tổng thể',
                      style:
                          TextStyle(fontSize: 19, fontWeight: FontWeight.w900)),
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
                              painter: _RadarPainter(data.report.skillScores),
                              child: const SizedBox.expand(),
                            ),
                          ),
                          Text(data.report.feedback,
                              textAlign: TextAlign.center),
                        ],
                      ),
                    ),
                  ),
                  if (data.report.strengths.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    _AdviceCard(
                        'Điểm mạnh', data.report.strengths, AppTheme.jade),
                  ],
                  if (data.report.improvements.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    _AdviceCard('Nên cải thiện', data.report.improvements,
                        AppTheme.orange),
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
                Text(value,
                    style: const TextStyle(
                        fontSize: 20, fontWeight: FontWeight.w900)),
                Text(label,
                    style: const TextStyle(fontSize: 10),
                    textAlign: TextAlign.center),
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
              Text(title,
                  style: TextStyle(color: color, fontWeight: FontWeight.w900)),
              const SizedBox(height: 8),
              ...items.map((item) => Padding(
                    padding: const EdgeInsets.only(bottom: 5),
                    child: Text('• $item'),
                  )),
            ],
          ),
        ),
      );
}

class _RadarPainter extends CustomPainter {
  _RadarPainter(this.scores);
  final Map<String, double> scores;
  static const labels = ['Nghe', 'Đọc', 'Viết', 'Viết tay'];
  static const keys = ['listening', 'reading', 'writing', 'handwriting'];

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = math.min(size.width, size.height) * .34;
    final grid = Paint()
      ..color = const Color(0xFFD9DDD9)
      ..style = PaintingStyle.stroke;
    final fill = Paint()
      ..color = AppTheme.jade.withValues(alpha: .25)
      ..style = PaintingStyle.fill;
    final line = Paint()
      ..color = AppTheme.jade
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;
    List<Offset> polygon(double scale) => List.generate(4, (i) {
          final angle = -math.pi / 2 + i * math.pi / 2;
          return center +
              Offset(math.cos(angle), math.sin(angle)) * radius * scale;
        });
    for (final scale in [.25, .5, .75, 1.0]) {
      canvas.drawPath(_path(polygon(scale)), grid);
    }
    final values =
        List.generate(4, (i) => polygon((scores[keys[i]] ?? 0) / 100)[i]);
    canvas.drawPath(_path(values), fill);
    canvas.drawPath(_path(values), line);
    for (var i = 0; i < 4; i++) {
      final point = polygon(1.18)[i];
      final painter = TextPainter(
        text: TextSpan(
            text: '${labels[i]} ${(scores[keys[i]] ?? 0).round()}',
            style: const TextStyle(
                color: AppTheme.ink,
                fontSize: 11,
                fontWeight: FontWeight.w700)),
        textDirection: TextDirection.ltr,
      )..layout();
      painter.paint(
          canvas, point - Offset(painter.width / 2, painter.height / 2));
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
