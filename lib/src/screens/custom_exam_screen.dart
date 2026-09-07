import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';

import '../theme/app_theme.dart';
import '../widgets/common.dart';
import '../services/custom_exam_service.dart';

class CustomExamScreen extends StatefulWidget {
  const CustomExamScreen({super.key, required this.service});

  final CustomExamService service;

  @override
  State<CustomExamScreen> createState() => _CustomExamScreenState();
}

class _CustomExamScreenState extends State<CustomExamScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  String _section = 'listening';
  final List<CustomQuestion> _questions = [];
  int _nextQuestionNumber = 1;
  bool _saving = false;

  @override
  void dispose() {
    _titleController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Tạo đề luyện tập'),
        actions: [
          IconButton(
            onPressed: _saving ? null : _submit,
            icon: _saving
                ? const SizedBox.square(
                    dimension: 22,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.save_rounded),
            tooltip: 'Lưu đề',
          ),
        ],
      ),
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
            children: [
              TextFormField(
                controller: _titleController,
                enabled: !_saving,
                decoration: const InputDecoration(
                  labelText: 'Tên đề',
                  hintText: 'VD: HSK 1 - Nghe hiểu mẫu',
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) return 'Nhập tên đề';
                  return null;
                },
              ),
              const SizedBox(height: 14),
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(value: 'listening', label: Text('Nghe')),
                  ButtonSegment(value: 'reading', label: Text('Đọc')),
                ],
                selected: <String>{_section},
                onSelectionChanged: (Set<String> selection) {
                  setState(() {
                    _section = selection.first;
                  });
                },
              ),
              const SizedBox(height: 18),
              Row(
                children: [
                  Expanded(
                    child: Text(
                      _section == 'listening' ? 'Câu hỏi Nghe' : 'Câu hỏi Đọc',
                      style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
                    ),
                  ),
                  FilledButton.icon(
                    onPressed: _saving ? null : _addQuestion,
                    icon: const Icon(Icons.add_rounded, size: 18),
                    label: const Text('Thêm câu'),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              if (_questions.isEmpty)
                Card(
                  color: Colors.grey.shade50,
                  child: Padding(
                    padding: const EdgeInsets.all(18),
                    child: Text(
                      _section == 'listening'
                          ? 'Thêm câu hỏi Nghe. Mỗi câu cần audio URL, transcript và đáp án.'
                          : 'Thêm câu hỏi Đọc. Mỗi câu cần nội dung và đáp án.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.grey.shade600),
                    ),
                  ),
                )
              else
                ..._questions.asMap().entries.map(
                  (entry) => _QuestionCard(
                    number: entry.key + 1,
                    question: entry.value,
                    section: _section,
                    saving: _saving,
                    onUpdate: (question) {
                      setState(() {
                        _questions[entry.key] = question;
                      });
                    },
                    onDelete: () {
                      setState(() {
                        _questions.removeAt(entry.key);
                        _nextQuestionNumber--;
                      });
                    },
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  void _addQuestion() {
    setState(() {
      _questions.add(
        CustomQuestion(
          id: 'q$_nextQuestionNumber',
          prompt: '',
          options: const [''],
          answer: '',
          audioUrl: _section == 'listening' ? '' : '',
          transcript: _section == 'listening' ? '' : '',
        ),
      );
      _nextQuestionNumber++;
    });
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_questions.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Thêm ít nhất 1 câu hỏi')),
      );
      return;
    }

    for (final q in _questions) {
      if (q.prompt.trim().isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Câu ${_questions.indexOf(q) + 1} thiếu nội dung')),
        );
        return;
      }
      if (q.answer.trim().isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Câu ${_questions.indexOf(q) + 1} thiếu đáp án')),
        );
        return;
      }
      if (_section == 'listening' && q.audioUrl.trim().isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Câu ${_questions.indexOf(q) + 1} thiếu audio URL')),
        );
        return;
      }
    }

    setState(() => _saving = true);

    final exam = CustomExam(
      id: Uuid().v4(),
      title: _titleController.text.trim(),
      section: _section,
      questions: List.unmodifiable(_questions),
      createdAt: DateTime.now().millisecondsSinceEpoch ~/ 1000,
    );

    await widget.service.saveExam(exam);

    if (!mounted) return;
    setState(() => _saving = false);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Đã lưu đề thành công')),
    );
    Navigator.pop(context, true);
  }
}

class _QuestionCard extends StatefulWidget {
  const _QuestionCard({
    required this.number,
    required this.question,
    required this.section,
    required this.saving,
    required this.onUpdate,
    required this.onDelete,
  });

  final int number;
  final CustomQuestion question;
  final String section;
  final bool saving;
  final void Function(CustomQuestion) onUpdate;
  final VoidCallback onDelete;

  @override
  State<_QuestionCard> createState() => _QuestionCardState();
}

class _QuestionCardState extends State<_QuestionCard> {
  late final TextEditingController _promptController;
  late final TextEditingController _answerController;
  late final TextEditingController _audioUrlController;
  late final TextEditingController _transcriptController;
  final List<TextEditingController> _optionControllers = [];

  @override
  void initState() {
    super.initState();
    _promptController = TextEditingController(text: widget.question.prompt);
    _answerController = TextEditingController(text: widget.question.answer);
    _audioUrlController = TextEditingController(text: widget.question.audioUrl);
    _transcriptController = TextEditingController(text: widget.question.transcript);
    _optionControllers
      ..clear()
      ..addAll(widget.question.options.map((o) => TextEditingController(text: o)));
    if (_optionControllers.isEmpty || _optionControllers[0].text.isEmpty) {
      _optionControllers.add(TextEditingController());
    }
  }

  @override
  void dispose() {
    _promptController.dispose();
    _answerController.dispose();
    _audioUrlController.dispose();
    _transcriptController.dispose();
    for (final c in _optionControllers) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Câu ${widget.number}',
                    style: const TextStyle(fontWeight: FontWeight.w800),
                  ),
                ),
                IconButton(
                  onPressed: widget.onDelete,
                  icon: const Icon(Icons.delete_outline_rounded, color: AppTheme.red),
                  tooltip: 'Xóa câu',
                ),
              ],
            ),
            const SizedBox(height: 8),
            TextFormField(
              controller: _promptController,
              enabled: !widget.saving,
              decoration: const InputDecoration(labelText: 'Nội dung câu hỏi'),
              maxLines: 3,
              onChanged: (_) => _update(),
            ),
            const SizedBox(height: 10),
            TextFormField(
              controller: _answerController,
              enabled: !widget.saving,
              decoration: const InputDecoration(labelText: 'Đáp án đúng'),
              onChanged: (_) => _update(),
            ),
            const SizedBox(height: 10),
            ...List.generate(_optionControllers.length, (index) {
              final controller = _optionControllers[index];
              return Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: controller,
                        enabled: !widget.saving,
                        decoration: InputDecoration(labelText: 'Đáp án ${index + 1}'),
                        onChanged: (_) => _update(),
                      ),
                    ),
                    if (_optionControllers.length > 1)
                      IconButton(
                        onPressed: () {
                          setState(() {
                            controller.dispose();
                            _optionControllers.removeAt(index);
                            _update();
                          });
                        },
                        icon: const Icon(Icons.remove_circle_outline_rounded, color: AppTheme.red),
                      ),
                  ],
                ),
              );
            }),
            TextButton.icon(
              onPressed: widget.saving
                  ? null
                  : () {
                      setState(() {
                        _optionControllers.add(TextEditingController());
                        _update();
                      });
                    },
              icon: const Icon(Icons.add_rounded, size: 18),
              label: const Text('Thêm đáp án'),
            ),
            const SizedBox(height: 10),
            if (widget.section == 'listening') ...[
              TextFormField(
                controller: _audioUrlController,
                enabled: !widget.saving,
                decoration: const InputDecoration(labelText: 'Audio URL'),
                onChanged: (_) => _update(),
              ),
              const SizedBox(height: 10),
              TextFormField(
                controller: _transcriptController,
                enabled: !widget.saving,
                decoration: const InputDecoration(labelText: 'Transcript'),
                maxLines: 3,
                onChanged: (_) => _update(),
              ),
            ],
          ],
        ),
      ),
    );
  }

  void _update() {
    widget.onUpdate(
      CustomQuestion(
        id: widget.question.id,
        prompt: _promptController.text,
        options: _optionControllers.map((c) => c.text).toList(growable: false),
        answer: _answerController.text,
        audioUrl: _audioUrlController.text,
        transcript: _transcriptController.text,
      ),
    );
  }
}
