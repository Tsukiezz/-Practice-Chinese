import 'dart:convert';

import 'package:flutter/material.dart';

import '../services/student_service.dart';
import '../theme/app_theme.dart';
import 'handwriting_screen.dart';

class ReviewScreen extends StatefulWidget {
  const ReviewScreen({super.key, required this.service});
  final StudentService service;

  @override
  State<ReviewScreen> createState() => _ReviewScreenState();
}

class _ReviewScreenState extends State<ReviewScreen> {
  String _kind = 'writing';
  late Future<List<StudentResult>> _future;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() => _future = widget.service.fetchReviewItems(_kind);
  void _reload() => setState(_load);

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: const Text('Ôn tập dưới 80'),
          actions: [
            IconButton(
              tooltip: 'Viết đoạn văn mới',
              onPressed: () => _openWriting(),
              icon: const Icon(Icons.add),
            ),
          ],
        ),
        body: Column(
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: SegmentedButton<String>(
                segments: const [
                  ButtonSegment(
                      value: 'writing',
                      label: Text('Đoạn văn'),
                      icon: Icon(Icons.article)),
                  ButtonSegment(
                      value: 'handwriting',
                      label: Text('Chữ viết tay'),
                      icon: Icon(Icons.draw)),
                ],
                selected: {_kind},
                onSelectionChanged: (value) => setState(() {
                  _kind = value.first;
                  _load();
                }),
              ),
            ),
            Expanded(
              child: FutureBuilder<List<StudentResult>>(
                future: _future,
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return const Center(child: CircularProgressIndicator());
                  }
                  if (snapshot.hasError) {
                    return _Message(
                        'Không tải được danh sách', snapshot.error.toString(),
                        onRetry: _reload);
                  }
                  final results = snapshot.data ?? const [];
                  if (results.isEmpty) {
                    return _Message(
                      'Không có bài dưới 80',
                      _kind == 'writing'
                          ? 'Các đoạn văn yếu sẽ tự động xuất hiện tại đây.'
                          : 'Các chữ viết tay yếu sẽ tự động xuất hiện khi có kết quả từ Canvas.',
                    );
                  }
                  return RefreshIndicator(
                    onRefresh: () async => _reload(),
                    child: ListView.separated(
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
                      itemCount: results.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 10),
                      itemBuilder: (_, index) {
                        final result = results[index];
                        return Card(
                          child: ListTile(
                            leading: CircleAvatar(
                              backgroundColor: const Color(0xFFFFEBDD),
                              child: Text('${result.reviewScore.round()}',
                                  style: const TextStyle(color: AppTheme.red)),
                            ),
                            title: Text(_kind == 'writing'
                                ? 'Đoạn văn cần sửa'
                                : 'Chữ cần luyện lại'),
                            subtitle: Text(
                                result.reviewFeedback.isEmpty
                                    ? 'Chưa có nhận xét'
                                    : result.reviewFeedback,
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis),
                            trailing: const Icon(Icons.chevron_right),
                            onTap: () => _kind == 'writing'
                                ? _openWriting(result)
                                : Navigator.of(context)
                                    .push(
                                      MaterialPageRoute(
                                        builder: (_) => HandwritingScreen(
                                          service: widget.service,
                                          source: result,
                                        ),
                                      ),
                                    )
                                    .then((_) => _reload()),
                          ),
                        );
                      },
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      );

  String _writingContent(StudentResult? result) {
    if (result == null) return '';
    try {
      final value = jsonDecode(result.content) as Map<String, dynamic>;
      return value['content'] as String? ?? '';
    } on Object {
      return result.content;
    }
  }

  Future<void> _openWriting([StudentResult? source]) async {
    final controller = TextEditingController(text: _writingContent(source));
    String? error;
    bool submitting = false;
    final completed = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title:
              Text(source == null ? 'Viết đoạn văn' : 'Sửa đoạn văn dưới 80'),
          content: SizedBox(
            width: 520,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (source?.feedback.isNotEmpty == true) ...[
                    Text('Góp ý cũ: ${source!.feedback}',
                        style: const TextStyle(color: AppTheme.red)),
                    const SizedBox(height: 12),
                  ],
                  TextField(
                    key: const Key('writing-editor'),
                    controller: controller,
                    enabled: !submitting,
                    minLines: 6,
                    maxLines: 12,
                    maxLength: 10000,
                    decoration: const InputDecoration(
                      hintText: 'Nhập đoạn văn tiếng Trung...',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  if (error != null)
                    Text(error!, style: const TextStyle(color: AppTheme.red)),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
                onPressed:
                    submitting ? null : () => Navigator.pop(context, false),
                child: const Text('Hủy')),
            FilledButton(
              onPressed: submitting
                  ? null
                  : () async {
                      final text = controller.text.trim();
                      if (text.isEmpty) {
                        setDialogState(
                            () => error = 'Hãy nhập nội dung trước khi nộp.');
                        return;
                      }
                      setDialogState(() {
                        submitting = true;
                        error = null;
                      });
                      try {
                        final result = source == null
                            ? await widget.service.submitWriting(text)
                            : await widget.service
                                .resubmitWriting(source.id, text);
                        if (!dialogContext.mounted) return;
                        Navigator.pop(dialogContext, result.score >= 80);
                        if (!mounted) return;
                        ScaffoldMessenger.of(this.context).showSnackBar(
                          SnackBar(
                              content: Text(
                                  'Gemini chấm ${result.score.toStringAsFixed(0)} điểm. ${result.feedback}')),
                        );
                      } on StudentApiException catch (e) {
                        setDialogState(() {
                          submitting = false;
                          error = e.message;
                        });
                      }
                    },
              child: submitting
                  ? const SizedBox.square(
                      dimension: 20,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('Nộp cho Gemini'),
            ),
          ],
        ),
      ),
    );
    controller.dispose();
    if (completed != null) _reload();
  }
}

class _Message extends StatelessWidget {
  const _Message(this.title, this.message, {this.onRetry});
  final String title, message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.task_alt, size: 52, color: AppTheme.jade),
              const SizedBox(height: 10),
              Text(title, style: const TextStyle(fontWeight: FontWeight.w900)),
              const SizedBox(height: 6),
              Text(message, textAlign: TextAlign.center),
              if (onRetry != null) ...[
                const SizedBox(height: 12),
                FilledButton(onPressed: onRetry, child: const Text('Thử lại')),
              ],
            ],
          ),
        ),
      );
}
