import 'package:flutter/material.dart';

import '../services/student_service.dart';
import '../theme/app_theme.dart';

class TranslationScreen extends StatefulWidget {
  const TranslationScreen({super.key, required this.service});

  final StudentService service;

  @override
  State<TranslationScreen> createState() => _TranslationScreenState();
}

class _TranslationScreenState extends State<TranslationScreen> {
  final _sentenceController = TextEditingController();
  final _contextController = TextEditingController();

  bool _loading = false;
  String? _error;
  GrammarAnalysisResult? _result;

  @override
  void dispose() {
    _sentenceController.dispose();
    _contextController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Sửa câu tiếng Trung')),
        body: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 820),
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  const Text(
                    'Gemini kiểm tra ngữ pháp và mức độ phù hợp với ngữ cảnh. '
                    'Câu giống hệt sẽ dùng lại kết quả đã lưu để tiết kiệm quota.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.grey),
                  ),
                  const SizedBox(height: 18),
                  TextField(
                    key: const Key('grammar-sentence'),
                    controller: _sentenceController,
                    enabled: !_loading,
                    minLines: 3,
                    maxLines: 6,
                    maxLength: 200,
                    decoration: const InputDecoration(
                      labelText: 'Câu tiếng Trung',
                      hintText: 'Ví dụ: 我每天学习中文。',
                      alignLabelWithHint: true,
                      prefixIcon: Icon(Icons.translate_rounded),
                    ),
                  ),
                  const SizedBox(height: 10),
                  TextField(
                    key: const Key('grammar-context'),
                    controller: _contextController,
                    enabled: !_loading,
                    minLines: 2,
                    maxLines: 4,
                    maxLength: 200,
                    decoration: const InputDecoration(
                      labelText: 'Ý muốn nói hoặc tình huống (không bắt buộc)',
                      hintText: 'Ví dụ: Tôi học tiếng Trung mỗi ngày.',
                      alignLabelWithHint: true,
                      prefixIcon: Icon(Icons.chat_bubble_outline),
                    ),
                  ),
                  const SizedBox(height: 8),
                  FilledButton.icon(
                    key: const Key('submit-grammar'),
                    onPressed: _loading ? null : _submit,
                    icon: _loading
                        ? const SizedBox.square(
                            dimension: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.auto_fix_high_rounded),
                    label: const Text('Kiểm tra và sửa câu'),
                  ),
                  if (_error != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 14),
                      child: Text(
                        _error!,
                        key: const Key('grammar-error'),
                        textAlign: TextAlign.center,
                        style: const TextStyle(color: AppTheme.red),
                      ),
                    ),
                  if (_result != null) _AnalysisCard(result: _result!),
                ],
              ),
            ),
          ),
        ),
      );

  Future<void> _submit() async {
    final sentence = _sentenceController.text.trim();
    if (sentence.isEmpty) {
      setState(() => _error = 'Hãy nhập một câu tiếng Trung cần kiểm tra.');
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
      _result = null;
    });
    try {
      final result = await widget.service.analyzeGrammar(
        sentence,
        context: _contextController.text.trim(),
      );
      if (mounted) setState(() => _result = result);
    } on StudentApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }
}

class _AnalysisCard extends StatelessWidget {
  const _AnalysisCard({required this.result});

  final GrammarAnalysisResult result;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(top: 18),
        child: Card(
          key: const Key('grammar-result'),
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    CircleAvatar(
                      backgroundColor: result.score >= 80
                          ? const Color(0xFFE4F4E9)
                          : const Color(0xFFFFE5DE),
                      child: Text(
                        result.score.toStringAsFixed(0),
                        style: const TextStyle(
                          color: AppTheme.jade,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(child: Text(result.feedback)),
                  ],
                ),
                const Divider(height: 30),
                const Text(
                  'Câu đề xuất',
                  style: TextStyle(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 8),
                SelectableText(
                  result.correctedSentence,
                  key: const Key('corrected-sentence'),
                  style: const TextStyle(
                    fontSize: 22,
                    color: AppTheme.jade,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const Divider(height: 30),
                Text(
                  result.errors.isEmpty
                      ? 'Không phát hiện lỗi cụ thể.'
                      : '${result.errors.length} lỗi cần chú ý',
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
                for (var index = 0; index < result.errors.length; index++)
                  _ErrorTile(index: index + 1, error: result.errors[index]),
              ],
            ),
          ),
        ),
      );
}

class _ErrorTile extends StatelessWidget {
  const _ErrorTile({required this.index, required this.error});

  final int index;
  final GrammarCorrectionError error;

  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.only(top: 10),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: const Color(0xFFFFF4EF),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Lỗi $index · ${error.position}',
              style: const TextStyle(
                color: AppTheme.red,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 6),
            Text('${error.original.isEmpty ? '∅' : error.original}  →  '
                '${error.suggestion.isEmpty ? '∅' : error.suggestion}'),
            const SizedBox(height: 4),
            Text(error.reason),
          ],
        ),
      );
}
