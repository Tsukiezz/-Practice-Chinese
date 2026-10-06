import 'dart:async';
import 'package:flutter/material.dart';
import '../services/student_service.dart';
import 'streak_card.dart';

DateTime vietnamTime(DateTime time) => time.toUtc().add(const Duration(hours: 7));
String vietnamGreeting(DateTime time, String name) {
  final hour = vietnamTime(time).hour;
  return '${hour >= 6 && hour < 18 ? 'Chào buổi sáng' : 'Chào buổi tối'}, ${name.trim().isEmpty ? 'bạn' : name.trim()}';
}

class VietnamGreeting extends StatefulWidget {
  const VietnamGreeting({super.key, required this.name});
  final String name;
  @override
  State<VietnamGreeting> createState() => _VietnamGreetingState();
}

class _VietnamGreetingState extends State<VietnamGreeting> {
  late final Timer _timer;
  DateTime _now = DateTime.now();
  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() => _now = DateTime.now());
    });
  }
  @override
  void dispose() { _timer.cancel(); super.dispose(); }
  @override
  Widget build(BuildContext context) {
    final time = vietnamTime(_now);
    String two(int n) => n.toString().padLeft(2, '0');
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(vietnamGreeting(_now, widget.name), style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800)),
      const SizedBox(height: 6),
      Text('${two(time.hour)}:${two(time.minute)}:${two(time.second)} · ${two(time.day)}/${two(time.month)}/${time.year} · Giờ Việt Nam',
        style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.onSurfaceVariant)),
    ]);
  }
}

void openStreakDetails(BuildContext context, StudentService service) {
  Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => StreakDetailsScreen(service: service)));
}

class StreakDetailsScreen extends StatefulWidget {
  const StreakDetailsScreen({super.key, required this.service});
  final StudentService service;
  @override
  State<StreakDetailsScreen> createState() => _StreakDetailsScreenState();
}

class _StreakDetailsScreenState extends State<StreakDetailsScreen> {
  late Future<StudentDashboard> _future;
  @override
  void initState() { super.initState(); _future = widget.service.fetchMyDashboard(); }
  void _reload() => setState(() => _future = widget.service.fetchMyDashboard());
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Chuỗi ngày học & bảo lưu')),
    body: FutureBuilder<StudentDashboard>(future: _future, builder: (context, snapshot) {
      if (snapshot.hasError) return Center(child: OutlinedButton(onPressed: _reload, child: const Text('Thử tải lại chuỗi ngày học')));
      if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
      return SingleChildScrollView(padding: const EdgeInsets.all(16), child: Center(child: SizedBox(width: 720,
        child: StreakCard(details: snapshot.data!.streakDetails, onRefresh: _reload))));
    }),
  );
}

class HeaderStreak extends StatefulWidget {
  const HeaderStreak({super.key, required this.service, required this.refreshKey});
  final StudentService service;
  final Object refreshKey;
  @override
  State<HeaderStreak> createState() => _HeaderStreakState();
}

class _HeaderStreakState extends State<HeaderStreak> {
  Timer? _timer;
  int? _streak;
  int _generation = 0;
  @override
  void initState() {
    super.initState(); _refresh();
    _timer = Timer.periodic(const Duration(minutes: 1), (_) => _refresh());
  }
  @override
  void didUpdateWidget(covariant HeaderStreak oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.service != widget.service || oldWidget.refreshKey != widget.refreshKey) _refresh();
  }
  Future<void> _refresh() async {
    final generation = ++_generation;
    try {
      final dashboard = await widget.service.fetchMyDashboard();
      if (mounted && generation == _generation) setState(() => _streak = dashboard.streak);
    } catch (_) {
      if (mounted && generation == _generation) setState(() => _streak = null);
    }
  }
  @override
  void dispose() { _timer?.cancel(); super.dispose(); }
  @override
  Widget build(BuildContext context) {
    final count = _streak;
    final color = count == null || count == 0 ? Theme.of(context).colorScheme.onSurfaceVariant
        : count >= 30 ? Colors.deepOrange : count >= 7 ? Colors.orange : const Color(0xFFCA5800);
    return Tooltip(message: count == null ? 'Xem chuỗi ngày học' : 'Chuỗi $count ngày · xem bảo lưu',
      child: TextButton(
        onPressed: () async {
          await Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => StreakDetailsScreen(service: widget.service)));
          if (mounted) _refresh();
        },
        style: TextButton.styleFrom(minimumSize: const Size(44, 44), padding: const EdgeInsets.symmetric(horizontal: 4)),
        child: Semantics(label: count == null ? 'Chuỗi ngày học chưa tải được' : 'Chuỗi $count ngày', excludeSemantics: true,
          child: Row(mainAxisSize: MainAxisSize.min, children: [Icon(Icons.local_fire_department, color: color, size: 24),
            Text(count == null ? '—' : '$count', style: TextStyle(color: color, fontWeight: FontWeight.w800))])),
      ));
  }
}
