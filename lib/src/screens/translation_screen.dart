import 'package:flutter/material.dart';

import '../services/student_service.dart';
import '../theme/app_theme.dart';
import '../widgets/mini_chinese_keyboard.dart';

class TranslationScreen extends StatefulWidget {
  const TranslationScreen({
    super.key,
    required this.service,
    this.guest = false,
  });

  final StudentService service;
  final bool guest;

  @override
  State<TranslationScreen> createState() => _TranslationScreenState();
}

class _TranslationScreenState extends State<TranslationScreen> {
  final _sentenceController = TextEditingController();
  final _contextController = TextEditingController();

  bool _loading = false;
  String? _error;
  GrammarAnalysisResult? _result;
  final _translationText = TextEditingController();
  String _source = 'zh', _target = 'vi';
  String? _translation;
  bool _showMiniKeyboard = false;
  String _activeInput = 'translation'; // 'translation' or 'sentence'
  static const _languages = {
    'zh': 'Tiếng Trung',
    'vi': 'Tiếng Việt',
  };

  @override
  void dispose() {
    _sentenceController.dispose();
    _translationText.dispose();
    _contextController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      title: const Text('Dịch & sửa câu'),
      actions: [
        IconButton(
          icon: Icon(_showMiniKeyboard ? Icons.keyboard_hide_outlined : Icons.keyboard_alt_outlined),
          tooltip: _showMiniKeyboard ? 'Ẩn bàn phím tiếng Trung' : 'Mở bàn phím tiếng Trung mini',
          onPressed: () => setState(() => _showMiniKeyboard = !_showMiniKeyboard),
        ),
      ],
    ),
    bottomNavigationBar: _showMiniKeyboard
        ? MiniChineseKeyboard(
            controller: _activeInput == 'translation' ? _translationText : _sentenceController,
            targetLabel: _activeInput == 'translation' ? 'Văn bản dịch' : 'Câu tiếng Trung',
            onClose: () => setState(() => _showMiniKeyboard = false),
          )
        : null,
    body: SafeArea(
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 820),
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Dịch đoạn văn',
                    style: TextStyle(fontSize: 23, fontWeight: FontWeight.w800),
                  ),
                  OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      visualDensity: VisualDensity.compact,
                    ),
                    icon: Icon(
                      _showMiniKeyboard && _activeInput == 'translation'
                          ? Icons.keyboard_hide_outlined
                          : Icons.keyboard_alt_outlined,
                      size: 16,
                      color: AppTheme.jade,
                    ),
                    label: Text(
                      _showMiniKeyboard && _activeInput == 'translation'
                          ? 'Đóng phím'
                          : 'Phím tiếng Trung',
                      style: const TextStyle(fontSize: 12, color: AppTheme.jade),
                    ),
                    onPressed: () => setState(() {
                      if (_showMiniKeyboard && _activeInput == 'translation') {
                        _showMiniKeyboard = false;
                      } else {
                        _showMiniKeyboard = true;
                        _activeInput = 'translation';
                      }
                    }),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _source,
                      decoration: const InputDecoration(
                        labelText: 'Ngôn ngữ nguồn',
                      ),
                      items: _languages.entries
                          .map(
                            (e) => DropdownMenuItem(
                              value: e.key,
                              child: Text(e.value),
                            ),
                          )
                          .toList(),
                      onChanged: _loading
                          ? null
                          : (v) => setState(() => _source = v!),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _target,
                      decoration: const InputDecoration(
                        labelText: 'Ngôn ngữ đích',
                      ),
                      items: _languages.entries
                          .map(
                            (e) => DropdownMenuItem(
                              value: e.key,
                              child: Text(e.value),
                            ),
                          )
                          .toList(),
                      onChanged: _loading
                          ? null
                          : (v) => setState(() => _target = v!),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              TextField(
                controller: _translationText,
                maxLength: 5000,
                minLines: 3,
                maxLines: 8,
                decoration: const InputDecoration(
                  labelText: 'Văn bản cần dịch',
                  hintText: 'Nhập hoặc bấm "Phím tiếng Trung" bên trên để gõ chữ Hán, Pinyin...',
                  alignLabelWithHint: true,
                ),
                enabled: !_loading,
                onTap: () => setState(() => _activeInput = 'translation'),
              ),
              FilledButton.icon(
                onPressed: _loading ? null : _translate,
                icon: const Icon(Icons.translate),
                label: const Text('Dịch văn bản'),
              ),
              if (_translation != null)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 20),
                  child: SelectableText(
                    _translation!,
                    style: const TextStyle(fontSize: 17, height: 1.6),
                  ),
                ),
              const Divider(height: 36),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Kiểm tra ngữ pháp & sửa câu',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                  ),
                  OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      visualDensity: VisualDensity.compact,
                    ),
                    icon: Icon(
                      _showMiniKeyboard && _activeInput == 'sentence'
                          ? Icons.keyboard_hide_outlined
                          : Icons.keyboard_alt_outlined,
                      size: 16,
                      color: AppTheme.jade,
                    ),
                    label: Text(
                      _showMiniKeyboard && _activeInput == 'sentence'
                          ? 'Đóng phím'
                          : 'Phím tiếng Trung',
                      style: const TextStyle(fontSize: 12, color: AppTheme.jade),
                    ),
                    onPressed: () => setState(() {
                      if (_showMiniKeyboard && _activeInput == 'sentence') {
                        _showMiniKeyboard = false;
                      } else {
                        _showMiniKeyboard = true;
                        _activeInput = 'sentence';
                      }
                    }),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              const Text(
                'Nhập câu tiếng Trung để xem lỗi ngữ pháp và gợi ý sửa.',
                style: TextStyle(color: Colors.grey, fontSize: 13),
              ),
              const SizedBox(height: 14),
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
                onTap: () => setState(() => _activeInput = 'sentence'),
              ),
              const SizedBox(height: 10),
              if (!widget.guest)
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
        guest: widget.guest,
      );
      if (mounted) setState(() => _result = result);
    } on StudentApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _translate() async {
    if (_translationText.text.trim().isEmpty) {
      setState(() => _error = 'Hãy nhập văn bản cần dịch.');
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
      _translation = null;
    });
    try {
      final result = await widget.service.translateText(
        _translationText.text,
        _source,
        _target,
      );
      if (mounted) setState(() => _translation = result);
    } on StudentApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
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
        Text(
          '${error.original.isEmpty ? '∅' : error.original}  →  '
          '${error.suggestion.isEmpty ? '∅' : error.suggestion}',
        ),
        const SizedBox(height: 4),
        Text(error.reason),
      ],
    ),
  );
}
