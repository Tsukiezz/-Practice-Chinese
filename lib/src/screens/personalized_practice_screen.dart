import 'package:flutter/material.dart';

import '../services/student_service.dart';

class PersonalizedPracticeScreen extends StatefulWidget {
  const PersonalizedPracticeScreen({super.key, required this.service});
  final StudentService service;
  @override
  State<PersonalizedPracticeScreen> createState() =>
      _PersonalizedPracticeScreenState();
}

class _PersonalizedPracticeScreenState
    extends State<PersonalizedPracticeScreen> {
  bool _busy = false;
  String? _error;
  int? _plan;
  List<dynamic> _tasks = [];
  final List<TextEditingController> _answers = [];
  final Map<int, String> _feedback = {};
  @override
  void dispose() {
    for (final c in _answers) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _generate() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final result = await widget.service.generatePersonalizedPractice();
      if (!mounted) return;
      for (final c in _answers) {
        c.dispose();
      }
      setState(() {
        _plan = result['id'] as int?;
        _tasks = result['tasks'] as List;
        _answers.clear();
        _answers.addAll(_tasks.map((_) => TextEditingController()));
        _feedback.clear();
        if (_tasks.isEmpty) _error = 'Chưa có bài dưới 80 điểm cần ôn. Bạn hãy làm bài kiểm tra trước.';
      });
    } on StudentApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _submit(int index) async {
    if (_answers[index].text.trim().isEmpty) {
      setState(() => _error = 'Hãy nhập câu trả lời.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final result = await widget.service.submitPersonalizedPractice(
        _plan!,
        index,
        _answers[index].text,
      );
      if (mounted) {
        setState(
          () => _feedback[index] =
              "Điểm: ${result['score']}/100\n${result['feedback']}\nKết quả đã lưu vào lịch sử.",
        );
      }
    } on StudentApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Bài ôn dành cho bạn')),
    body: SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Text(
            'AI tạo bài luyện câu mới từ lỗi sai trong những bài dưới 80 điểm của bạn.',
          ),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: _busy ? null : _generate,
            icon: const Icon(Icons.auto_awesome),
            label: Text(_busy ? 'Đang xử lý…' : 'Tạo bài ôn từ lỗi sai'),
          ),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 16),
              child: Text(_error!, style: const TextStyle(color: Colors.red)),
            ),
          for (var i = 0; i < _tasks.length; i++)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Bài ${i + 1}',
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                    Text(_tasks[i]['prompt'] as String),
                    const SizedBox(height: 8),
                    Text('Gợi ý: ${_tasks[i]['hint']}'),
                    TextField(
                      controller: _answers[i],
                      enabled: !_busy,
                      minLines: 2,
                      maxLines: 5,
                      maxLength: 500,
                      decoration: const InputDecoration(
                        labelText: 'Câu trả lời tiếng Trung',
                      ),
                    ),
                    FilledButton(
                      onPressed: _busy ? null : () => _submit(i),
                      child: const Text('Nộp bài'),
                    ),
                    if (_feedback[i] != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 12),
                        child: Text(_feedback[i]!),
                      ),
                  ],
                ),
              ),
            ),
        ],
      ),
    ),
  );
}
