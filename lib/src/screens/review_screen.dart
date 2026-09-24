import 'dart:convert';

import 'package:flutter/material.dart';

import '../services/student_service.dart';
import '../theme/app_theme.dart';
import 'handwriting_screen.dart';

class ReviewScreen extends StatefulWidget {
  const ReviewScreen({
    super.key,
    required this.service,
    this.initialKind = 'writing',
  });

  final StudentService service;
  final String initialKind;

  @override
  State<ReviewScreen> createState() => _ReviewScreenState();
}

class _ReviewScreenState extends State<ReviewScreen> {
  late String _kind;
  late Future<List<StudentResult>> _future;

  final List<Map<String, dynamic>> _skills = const [
    {'kind': 'writing', 'label': 'Đoạn văn', 'icon': Icons.article_outlined},
    {'kind': 'handwriting', 'label': 'Viết tay', 'icon': Icons.draw_outlined},
    {'kind': 'reading', 'label': 'Đọc phát âm', 'icon': Icons.mic_none_outlined},
    {'kind': 'listening', 'label': 'Nghe hiểu', 'icon': Icons.headphones_outlined},
    {'kind': 'exam', 'label': 'Kiểm tra', 'icon': Icons.assignment_outlined},
    {'kind': 'vocabulary', 'label': 'Từ vựng', 'icon': Icons.menu_book_outlined},
  ];

  @override
  void initState() {
    super.initState();
    _kind = widget.initialKind;
    _load();
  }

  void _load() => _future = widget.service.fetchReviewItems(_kind);
  void _reload() => setState(_load);

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: const Text('Ôn tập dưới 80 điểm'),
          actions: [
            if (_kind == 'writing')
              IconButton(
                tooltip: 'Viết đoạn văn mới',
                onPressed: () => _openWriting(),
                icon: const Icon(Icons.add),
              ),
          ],
        ),
        body: Column(
          children: [
            // Horizontal skills selector for all 5 core learning functions
            Container(
              height: 54,
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: _skills.length,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (context, index) {
                  final s = _skills[index];
                  final isSelected = s['kind'] == _kind;
                  return ChoiceChip(
                    avatar: Icon(
                      s['icon'] as IconData,
                      size: 16,
                      color: isSelected ? Colors.white : AppTheme.jade,
                    ),
                    label: Text(s['label'] as String),
                    selected: isSelected,
                    selectedColor: AppTheme.jade,
                    labelStyle: TextStyle(
                      color: isSelected ? Colors.white : Colors.black87,
                      fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                      fontSize: 13,
                    ),
                    onSelected: (_) => setState(() {
                      _kind = s['kind'] as String;
                      _load();
                    }),
                  );
                },
              ),
            ),
            const Divider(height: 1),
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
                      'Không có bài dưới 80 điểm',
                      _emptyMessageForKind(_kind),
                    );
                  }
                  return RefreshIndicator(
                    onRefresh: () async => _reload(),
                    child: ListView.separated(
                      padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
                      itemCount: results.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 10),
                      itemBuilder: (_, index) {
                        final result = results[index];
                        final score = result.reviewScore.round();
                        final color = score >= 80 ? Colors.green : (score >= 50 ? Colors.orange : AppTheme.red);

                        return Card(
                          elevation: 0,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                            side: const BorderSide(color: Color(0xFFE2EBE5)),
                          ),
                          child: ListTile(
                            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                            leading: CircleAvatar(
                              backgroundColor: color.withOpacity(0.12),
                              child: Text(
                                '$score',
                                style: TextStyle(color: color, fontWeight: FontWeight.bold),
                              ),
                            ),
                            title: Text(
                              _itemTitle(result),
                              style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
                            ),
                            subtitle: Text(
                              _itemSubtitle(result),
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(color: Color(0xFF5C6F64), fontSize: 13),
                            ),
                            trailing: const Icon(Icons.chevron_right, color: Colors.grey),
                            onTap: () => _handleItemTap(result),
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

  String _emptyMessageForKind(String kind) {
    switch (kind) {
      case 'reading':
        return 'Tất cả các từ bạn luyện phát âm đều đạt trên 80%. Tuyệt vời!';
      case 'listening':
        return 'Bạn chưa có bài luyện nghe nào dưới 80 điểm.';
      case 'exam':
        return 'Bạn chưa có đề thi nào dưới 80 điểm.';
      case 'handwriting':
        return 'Các chữ viết tay dưới 80 điểm sẽ tự động xuất hiện tại đây.';
      case 'vocabulary':
        return 'Chưa có từ vựng nào cần lưu ý thêm.';
      default:
        return 'Các bài luyện chưa đạt điểm cao sẽ tự động hiển thị để bạn ôn lại.';
    }
  }

  String _itemTitle(StudentResult result) {
    if (result.title != null && result.title!.isNotEmpty) {
      return result.title!;
    }
    if (_kind == 'writing') return 'Đoạn văn cần sửa';
    if (_kind == 'handwriting') return 'Chữ cần luyện lại';
    if (_kind == 'reading') return 'Từ cần luyện đọc lại';
    if (_kind == 'exam') return 'Đề thi cần cải thiện';
    return 'Mục cần ôn tập';
  }

  String _itemSubtitle(StudentResult result) {
    if (result.subtitle != null && result.subtitle!.isNotEmpty) {
      return result.subtitle!;
    }
    if (result.reviewFeedback.isNotEmpty) {
      return result.reviewFeedback;
    }
    return 'Chưa có nhận xét chi tiết';
  }

  void _handleItemTap(StudentResult result) {
    if (_kind == 'writing') {
      _openWriting(result);
    } else if (_kind == 'handwriting') {
      Navigator.of(context)
          .push(
            MaterialPageRoute(
              builder: (_) => HandwritingScreen(
                service: widget.service,
                source: result,
              ),
            ),
          )
          .then((_) => _reload());
    } else {
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
          title: Text(_itemTitle(result)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Điểm số / Độ chính xác: ${result.reviewScore.toStringAsFixed(1)} / 100'),
              const SizedBox(height: 8),
              Text(
                result.reviewFeedback.isNotEmpty ? result.reviewFeedback : (_itemSubtitle(result)),
                style: const TextStyle(height: 1.4),
              ),
            ],
          ),
          actions: [
            FilledButton(
              style: FilledButton.styleFrom(backgroundColor: AppTheme.jade),
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Đã hiểu'),
            ),
          ],
        ),
      );
    }
  }

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
          title: Text(source == null ? 'Viết đoạn văn' : 'Sửa đoạn văn dưới 80'),
          content: SizedBox(
            width: 520,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Viết lại đoạn văn tiếng Trung để AI chấm điểm:'),
                  const SizedBox(height: 12),
                  TextField(
                    controller: controller,
                    minLines: 4,
                    maxLines: 8,
                    decoration: const InputDecoration(
                      hintText: 'Nhập đoạn văn tiếng Trung...',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  if (error != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Text(error!, style: const TextStyle(color: Colors.red)),
                    ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Hủy'),
            ),
            FilledButton(
              onPressed: submitting
                  ? null
                  : () async {
                      final text = controller.text.trim();
                      if (text.isEmpty) return;
                      setDialogState(() {
                        submitting = true;
                        error = null;
                      });
                      try {
                        final result = source == null
                            ? await widget.service.submitWriting(text)
                            : await widget.service.resubmitWriting(source.id, text);
                        if (!dialogContext.mounted) return;
                        Navigator.pop(dialogContext, result.score >= 80);
                        if (!mounted) return;
                        ScaffoldMessenger.of(this.context).showSnackBar(
                          SnackBar(
                            content: Text('Gemini chấm ${result.score.toStringAsFixed(0)} điểm. ${result.feedback}'),
                          ),
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
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
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
