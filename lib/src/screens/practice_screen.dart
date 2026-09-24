import 'dart:async';

import '../services/exam_draft_store.dart';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:audioplayers/audioplayers.dart';

import '../models/reading_exam.dart';
import '../services/reading_exam_service.dart';
import '../services/web_navigation.dart';
import '../services/pronunciation_service.dart';
import '../theme/app_theme.dart';
import '../widgets/common.dart';
import '../widgets/hanzi_drawing_canvas.dart';

class PracticeScreen extends StatefulWidget {
  const PracticeScreen({
    super.key,
    required this.repository,
    this.draftOwner,
    this.title = 'Test Đọc',
    this.eyebrow = 'Bài luyện · Kỹ năng đọc',
    this.skillLabel = 'ĐỌC',
    this.onBack,
  });

  final ReadingExamRepository repository;
  final int? draftOwner;
  final String title, eyebrow, skillLabel;
  final VoidCallback? onBack;

  @override
  State<PracticeScreen> createState() => _PracticeScreenState();
}

class _PracticeScreenState extends State<PracticeScreen> {
  final TextEditingController _textAnswerController = TextEditingController();
  final Map<String, dynamic> _answers = {};
  final Map<String, HanziCanvasController> _canvasControllers = {};

  Timer? _examTimer;
  int _remainingSeconds = 0;

  int _selectedHsk = 1;
  int _currentQuestion = 0;
  int _loadSequence = 0;
  bool _loading = true;
  bool _submitting = false;
  String? _loadError;
  String? _submitError;
  ReadingExam? _activeExam;
  ReadingResult? _result;
  List<ReadingExam> _exams = const [];

  @override
  void initState() {
    super.initState();
    _loadExams();
  }

  @override
  void dispose() {
    _examTimer?.cancel();
    _textAnswerController.dispose();
    for (final controller in _canvasControllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  void _startTimer(int durationMinutes) {
    _examTimer?.cancel();
    _remainingSeconds = (durationMinutes > 0 ? durationMinutes : 40) * 60;
    _examTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      if (_remainingSeconds <= 1) {
        timer.cancel();
        setState(() => _remainingSeconds = 0);
        _handleTimeUp();
      } else {
        setState(() => _remainingSeconds--);
      }
    });
  }

  void _handleTimeUp() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Text('Hết giờ làm bài!'),
        content: const Text(
          'Thời gian làm bài đã kết thúc. Hệ thống đang tự động nộp bài của bạn.',
        ),
        actions: [
          FilledButton(
            onPressed: () {
              Navigator.pop(context);
              _submitExam();
            },
            child: const Text('Xem kết quả'),
          ),
        ],
      ),
    );
  }

  String _formattedTimer() {
    final minutes = _remainingSeconds ~/ 60;
    final seconds = _remainingSeconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }

  Widget _buildHeaderChip(String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.18),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withOpacity(0.2)),
      ),
      child: Text(
        label,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 11,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }



  @override
  Widget build(BuildContext context) {
    Widget content;
    if (_result != null) {
      content = _buildResult();
    } else if (_activeExam != null) {
      content = _buildQuestion();
    } else {
      content = _buildExamList();
    }
    return Scaffold(
      backgroundColor: const Color(0xFFF7F9F8),
      body: content,
    );
  }

  Widget _buildExamList() {
    return SafeArea(
      child: Column(
        children: [
          ScreenHeader(
            eyebrow: widget.eyebrow,
            title: widget.title,
            showBackButton: widget.onBack != null || Navigator.of(context).canPop(),
            onBack: widget.onBack ?? (Navigator.of(context).canPop() ? () => Navigator.of(context).pop() : null),
            trailing: const Icon(
              Icons.chrome_reader_mode_outlined,
              color: AppTheme.jade,
            ),
          ),
          SizedBox(
            height: 48,
            child: ListView.separated(
              key: const Key('hsk-filter'),
              padding: const EdgeInsets.symmetric(horizontal: 20),
              scrollDirection: Axis.horizontal,
              itemCount: 6,
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemBuilder: (context, index) {
                final hsk = index + 1;
                return ChoiceChip(
                  key: Key('hsk-$hsk'),
                  label: Text('HSK $hsk'),
                  selected: _selectedHsk == hsk,
                  onSelected: (_) => _selectHsk(hsk),
                  selectedColor: const Color(0xFFFFE7DC),
                  side: BorderSide.none,
                  labelStyle: TextStyle(
                    color: _selectedHsk == hsk
                        ? AppTheme.red
                        : Colors.grey.shade700,
                    fontWeight: FontWeight.w700,
                  ),
                );
              },
            ),
          ),
          if (widget.title == 'Test Đọc')
            Container(
              margin: const EdgeInsets.fromLTRB(20, 16, 20, 0),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF163F35), Color(0xFF2D6A4F)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(18),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF163F35).withOpacity(0.18),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.mic_rounded, color: Color(0xFFE2C391), size: 28),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Luyện đọc phát âm AI',
                          style: TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w800,
                            fontSize: 15,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          'Thu âm micro, AI chấm % chính xác & sửa lỗi',
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.85),
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                  FilledButton(
                    style: FilledButton.styleFrom(
                      backgroundColor: const Color(0xFFEAD8B3),
                      foregroundColor: const Color(0xFF163F35),
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                      textStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
                    ),
                    onPressed: () {
                      if (kIsWeb) {
                        openReading('');
                      }
                    },
                    child: const Text('Bắt đầu'),
                  ),
                ],
              ),
            ),
          if (widget.title == 'Test Tổng hợp')
            Container(
              margin: const EdgeInsets.fromLTRB(20, 16, 20, 0),
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF1B3B36), Color(0xFF2C5E55)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF1B3B36).withOpacity(0.2),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.15),
                          borderRadius: BorderRadius.circular(14),
                        ),
                        child: const Icon(
                          Icons.fact_check_rounded,
                          color: Color(0xFFE2C391),
                          size: 26,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Đề thi Tổng hợp HSK $_selectedHsk (40 câu)',
                              style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.w800,
                                fontSize: 16,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              'Mô phỏng thi thực tế: Nghe · Đọc · Cấu trúc & Viết',
                              style: TextStyle(
                                color: Colors.white.withOpacity(0.85),
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    runSpacing: 6,
                    children: [
                      _buildHeaderChip('⏱️ 40 phút'),
                      _buildHeaderChip('🎯 40 câu / 100 điểm'),
                      _buildHeaderChip('🤖 AI Chấm điểm & Sửa lỗi'),
                    ],
                  ),
                ],
              ),
            ),
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 18, 20, 10),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    widget.title == 'Test Tổng hợp'
                        ? 'Đề thi Tổng hợp HSK $_selectedHsk chuẩn khảo thí'
                        : 'Đề thi ${widget.title} do Admin phát hành',
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
                  ),
                ),
                Text(
                  widget.skillLabel,
                  style: const TextStyle(
                    color: AppTheme.red,
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ],
            ),
          ),
          Expanded(child: _buildExamListBody()),

        ],
      ),
    );
  }

  Widget _buildExamListBody() {
    if (_loading) {
      return const Center(
        key: Key('exam-loading'),
        child: CircularProgressIndicator(),
      );
    }
    if (_loadError != null) {
      return _MessageState(
        key: const Key('exam-error'),
        icon: Icons.cloud_off_rounded,
        title: 'Không tải được đề',
        message: _loadError!,
        actionLabel: 'Thử lại',
        onAction: _loadExams,
      );
    }
    if (_exams.isEmpty) {
      return _MessageState(
        key: const Key('empty-exam-state'),
        icon: Icons.menu_book_outlined,
        title: widget.title == 'Test Đọc'
            ? 'Chưa có đề Đọc HSK $_selectedHsk'
            : 'Chưa có ${widget.title} HSK $_selectedHsk',
        message: widget.title == 'Test Đọc'
            ? 'Hãy bấm "Luyện đọc phát âm AI" ở trên để thu âm qua micro và nhận AI chấm điểm trực tiếp theo từ vựng và chủ đề.'
            : 'Đề cần được Admin phát hành trước khi học viên làm bài.',
        actionLabel: widget.title == 'Test Đọc' && kIsWeb ? 'Mở Luyện Đọc AI' : null,
        onAction: widget.title == 'Test Đọc' && kIsWeb ? () => openReading('') : null,
      );
    }
    return RefreshIndicator(
      onRefresh: _loadExams,
      child: ListView.separated(
        key: const Key('reading-exam-list'),
        padding: const EdgeInsets.fromLTRB(20, 4, 20, 24),
        itemCount: _exams.length,
        separatorBuilder: (_, __) => const SizedBox(height: 12),
        itemBuilder: (context, index) => _ExamCard(
          exam: _exams[index],
          onTap: () => _startExam(_exams[index]),
        ),
      ),
    );
  }

  Widget _buildQuestion() {
    final exam = _activeExam!;
    final question = exam.questions[_currentQuestion];
    final answer = _answers[question.id];
    final isLastQuestion = _currentQuestion == exam.questions.length - 1;

    return SafeArea(
      child: Column(
        children: [
          ScreenHeader(
            eyebrow: 'HSK ${exam.hsk} · ${exam.title}',
            title: 'Câu ${_currentQuestion + 1}/${exam.questions.length}',
            showBackButton: true,
            onBack: _submitting ? null : _confirmExit,
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (exam.durationMinutes > 0) ...[
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    decoration: BoxDecoration(
                      color: _remainingSeconds < 300
                          ? const Color(0xFFFFECE5)
                          : const Color(0xFFE9F3ED),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: _remainingSeconds < 300
                            ? AppTheme.red
                            : AppTheme.jade,
                      ),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.timer_outlined,
                          size: 15,
                          color: _remainingSeconds < 300
                              ? AppTheme.red
                              : AppTheme.jade,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          _formattedTimer(),
                          style: TextStyle(
                            fontWeight: FontWeight.w800,
                            fontSize: 12,
                            color: _remainingSeconds < 300
                                ? AppTheme.red
                                : AppTheme.jade,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 4),
                ],
                IconButton(
                  tooltip: 'Bảng câu hỏi',
                  onPressed: _openQuestionPalette,
                  icon: const Icon(Icons.grid_view_rounded, color: AppTheme.jade),
                ),
                IconButton(
                  key: const Key('close-exam'),
                  tooltip: 'Thoát bài',
                  onPressed: _submitting ? null : _confirmExit,
                  icon: const Icon(Icons.close_rounded),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: ProgressLine(
              value: (_currentQuestion + 1) / exam.questions.length,
            ),
          ),
          const SizedBox(height: 10),
          SizedBox(
            height: 38,
            child: ListView.separated(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              scrollDirection: Axis.horizontal,
              itemCount: exam.questions.length,
              separatorBuilder: (_, __) => const SizedBox(width: 6),
              itemBuilder: (context, index) {
                final q = exam.questions[index];
                final isCurrent = index == _currentQuestion;
                final isDone = _hasAnswer(q);
                return InkWell(
                  onTap: _submitting ? null : () => _moveToQuestion(index),
                  borderRadius: BorderRadius.circular(10),
                  child: Container(
                    width: 38,
                    height: 38,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: isCurrent
                          ? const Color(0xFFFFECE5)
                          : (isDone ? const Color(0xFFE4F4E9) : const Color(0xFFF1F3F4)),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: isCurrent
                            ? AppTheme.red
                            : (isDone ? AppTheme.jade : Colors.transparent),
                        width: isCurrent ? 2 : 1,
                      ),
                    ),
                    child: Text(
                      '${index + 1}',
                      style: TextStyle(
                        color: isCurrent
                            ? AppTheme.red
                            : (isDone ? const Color(0xFF1D5C42) : Colors.black87),
                        fontWeight: isCurrent || isDone ? FontWeight.w800 : FontWeight.w600,
                        fontSize: 12,
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: 6),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      _buildSectionBadge(question.section),
                      Text(
                        '${_currentQuestion + 1}/${exam.questions.length}',
                        textAlign: TextAlign.right,
                        style: const TextStyle(
                          color: AppTheme.red,
                          fontSize: 12,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Container(
                    key: const Key('reading-prompt'),
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE9F3ED),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text(
                          question.prompt,
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                            fontSize: 19,
                            height: 1.55,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        if (question.prompt.trim().isNotEmpty) ...[
                          const SizedBox(height: 10),
                          Align(
                            alignment: Alignment.centerRight,
                            child: IconButton.filledTonal(
                              tooltip: 'Nghe phát âm',
                              icon: const Icon(Icons.volume_up_rounded, size: 20, color: AppTheme.jade),
                              onPressed: () => PronunciationService.playWord(question.prompt),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                  if (question.section == 'listening' &&
                      question.audioUrl.isNotEmpty) ...[
                    const SizedBox(height: 14),
                    _ExamAudioPlayer(url: question.audioUrl),
                  ],
                  const SizedBox(height: 22),
                  Text(
                    question.questionType == 'hanzi_canvas'
                        ? 'Viết chữ Hán'
                        : question.questionType == 'essay'
                        ? 'Viết đoạn văn'
                        : question.options.isEmpty
                        ? 'Nhập đáp án'
                        : 'Chọn một đáp án',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 12),
                  if (question.questionType == 'hanzi_canvas')
                    _buildCanvasAnswer(question)
                  else if (question.questionType == 'essay')
                    TextField(
                      key: const Key('essay-answer'),
                      controller: _textAnswerController,
                      enabled: !_submitting,
                      maxLength: 500,
                      minLines: 8,
                      maxLines: 12,
                      decoration: const InputDecoration(
                        hintText:
                            'Nhập đoạn văn tiếng Trung (tối đa 500 ký tự)',
                        border: OutlineInputBorder(),
                      ),
                      onChanged: (value) => _saveAnswer(question.id, {
                        'kind': 'essay',
                        'text': value,
                      }),
                    )
                  else if (question.questionType == 'sentence_order')
                    _buildSentenceOrder(question)
                  else if (question.options.isEmpty)
                    TextField(
                      key: const Key('text-answer'),
                      controller: _textAnswerController,
                      enabled: !_submitting,
                      maxLength: 5000,
                      minLines: 1,
                      maxLines: question.section == 'writing' ? 10 : 4,
                      textInputAction: TextInputAction.done,
                      decoration: const InputDecoration(
                        hintText: 'Nhập câu trả lời của bạn',
                        border: OutlineInputBorder(),
                      ),
                      onChanged: (value) => _saveAnswer(question.id, value),
                    )
                  else
                    ...question.options.map(
                      (option) => _AnswerOption(
                        option: option,
                        selected: answer == option,
                        enabled: !_submitting,
                        onTap: () => _saveAnswer(question.id, option),
                      ),
                    ),
                  if (_submitError != null) ...[
                    const SizedBox(height: 8),
                    _InlineError(message: _submitError!),
                  ],
                  const SizedBox(height: 18),
                  Row(
                    children: [
                      if (_currentQuestion > 0) ...[
                        Expanded(
                          child: OutlinedButton(
                            key: const Key('previous-question'),
                            onPressed: _submitting ? null : _previousQuestion,
                            child: const Text('Câu trước'),
                          ),
                        ),
                        const SizedBox(width: 8),
                      ],
                      IconButton.outlined(
                        tooltip: 'Bảng câu hỏi',
                        onPressed: _openQuestionPalette,
                        icon: const Icon(Icons.grid_view_rounded),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        flex: 2,
                        child: FilledButton(
                          key: const Key('question-action'),
                          onPressed: _submitting
                              ? null
                              : (!isLastQuestion || _hasAnswer(question)
                                  ? () => _handleQuestionAction(isLastQuestion)
                                  : null),
                          child: _submitting

                              ? const SizedBox.square(
                                  dimension: 22,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white,
                                  ),
                                )
                              : Text(
                                  isLastQuestion ? 'Nộp bài' : 'Câu tiếp theo',
                                ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionBadge(String section) {
    final (icon, label, color) = switch (section) {
      'listening' => (Icons.headset_rounded, 'Phần 1: Nghe hiểu', const Color(0xFF1D5C42)),
      'writing' => (Icons.edit_note_rounded, 'Phần 3: Cấu trúc & Viết', const Color(0xFFC04B3E)),
      _ => (Icons.menu_book_rounded, 'Phần 2: Đọc hiểu', const Color(0xFF20639B)),
    };

    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: color.withOpacity(0.3)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 14, color: color),
            const SizedBox(width: 5),
            Text(
              label,
              style: TextStyle(
                color: color,
                fontWeight: FontWeight.w800,
                fontSize: 11,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildResult() {

    final result = _result!;
    final passed = result.score >= 80;
    return SafeArea(
      child: Column(
        children: [
          ScreenHeader(
            eyebrow: 'Kết quả đã được lưu',
            title: widget.title,
            showBackButton: true,
            onBack: _returnToExamList,
            trailing: Icon(
              passed ? Icons.emoji_events_rounded : Icons.auto_stories_rounded,
              color: passed ? AppTheme.orange : AppTheme.jade,
            ),
          ),
          Expanded(
            child: ListView(
              key: const Key('reading-result'),
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
              children: [
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: passed
                        ? const Color(0xFFE4F4E9)
                        : const Color(0xFFFFF1E8),
                    borderRadius: BorderRadius.circular(24),
                  ),
                  child: Column(
                    children: [
                      Text(
                        _formatScore(result.score),
                        style: const TextStyle(
                          color: AppTheme.jade,
                          fontSize: 42,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      const Text(
                        'ĐIỂM',
                        style: TextStyle(fontWeight: FontWeight.w800),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        passed
                            ? 'Bạn đã hoàn thành tốt bài luyện.'
                            : 'Bạn nên xem lại lời giải và luyện thêm.',
                        textAlign: TextAlign.center,
                      ),
                      if (result.feedback.isNotEmpty) ...[
                        const SizedBox(height: 12),
                        Text(
                          result.feedback,
                          key: const Key('ai-feedback'),
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                            color: AppTheme.ink,
                            height: 1.4,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                const Padding(
                  padding: EdgeInsets.only(top: 24, bottom: 10),
                  child: Text(
                    'Xem lại đáp án',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                  ),
                ),
                ...result.reviewItems.asMap().entries.map(
                  (entry) =>
                      _ReviewCard(number: entry.key + 1, item: entry.value),
                ),
                const SizedBox(height: 10),
                FilledButton(
                  key: const Key('finish-exam'),
                  onPressed: _returnToExamList,
                  child: const Text('Về danh sách đề'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCanvasAnswer(ReadingQuestion question) {
    final controller = _canvasControllers.putIfAbsent(question.id, () {
      final restored = HanziCanvasController();
      final saved = _answers[question.id];
      if (saved is Map && saved['strokes'] is List) {
        restored.restore(saved['strokes'] as List);
      }
      return restored;
    });
    return Column(
      children: [
        HanziDrawingCanvas(
          key: const Key('exam-hanzi-canvas'),
          controller: controller,
          enabled: !_submitting,
          maxWidth: 430,
          onChanged: () => _saveAnswer(question.id, {
            'kind': 'hanzi_canvas',
            'strokes': controller.payload,
          }),
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                key: const Key('undo-exam-stroke'),
                onPressed: _submitting || controller.isEmpty
                    ? null
                    : () {
                        controller.undo();
                        _saveAnswer(question.id, {
                          'kind': 'hanzi_canvas',
                          'strokes': controller.payload,
                        });
                      },
                icon: const Icon(Icons.undo_rounded),
                label: const Text('Hoàn tác nét'),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: OutlinedButton.icon(
                key: const Key('clear-exam-canvas'),
                onPressed: _submitting || controller.isEmpty
                    ? null
                    : () {
                        controller.clear();
                        _saveAnswer(question.id, {
                          'kind': 'hanzi_canvas',
                          'strokes': controller.payload,
                        });
                      },
                icon: const Icon(Icons.delete_outline_rounded),
                label: const Text('Viết lại'),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildSentenceOrder(ReadingQuestion question) {
    final answer = _answers[question.id];
    final selected = answer is String && answer.isNotEmpty
        ? answer.split(' ')
        : <String>[];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Chạm các cụm từ theo đúng thứ tự. Chạm từ đã chọn để bỏ.'),
        const SizedBox(height: 16),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: selected
              .map(
                (word) => InputChip(
                  label: Text(word),
                  onDeleted: _submitting
                      ? null
                      : () {
                          selected.remove(word);
                          _saveAnswer(question.id, selected.join(' '));
                        },
                ),
              )
              .toList(),
        ),
        const Divider(height: 32),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: question.options
              .where((word) => !selected.contains(word))
              .map(
                (word) => ActionChip(
                  label: Text(word),
                  onPressed: _submitting
                      ? null
                      : () {
                          selected.add(word);
                          _saveAnswer(question.id, selected.join(' '));
                        },
                ),
              )
              .toList(),
        ),
      ],
    );
  }

  Future<void> _loadExams() async {
    final sequence = ++_loadSequence;
    setState(() {
      _loading = true;
      _loadError = null;
    });
    try {
      final exams = await widget.repository.fetchReadingExams(_selectedHsk);
      if (!mounted || sequence != _loadSequence) return;
      setState(() {
        _exams = exams;
        _loading = false;
      });
    } on ReadingApiException catch (error) {
      if (!mounted || sequence != _loadSequence) return;
      setState(() {
        _exams = const [];
        _loadError = error.message;
        _loading = false;
      });
    } on Exception {
      if (!mounted || sequence != _loadSequence) return;
      setState(() {
        _exams = const [];
        _loadError = 'Không tải được dữ liệu đề. Hãy thử lại.';
        _loading = false;
      });
    }
  }

  void _selectHsk(int hsk) {
    if (_selectedHsk == hsk) return;
    setState(() => _selectedHsk = hsk);
    _loadExams();
  }

  void _startExam(ReadingExam exam) async {
    _startTimer(exam.durationMinutes);
    final restored = await ExamDraftStore.read(
      widget.draftOwner,
      'reading',
      exam.id,
      exam.version,
    );
    if (!mounted) return;
    setState(() {
      _activeExam = exam;
      _result = null;
      _currentQuestion = 0;
      _answers.clear();
      _answers.addAll(restored);
      _clearCanvasControllers();
      _submitError = null;
      final first = exam.questions.first;
      final answer = _answers[first.id];
      _textAnswerController.text = answer is String
          ? answer
          : (answer is Map ? (answer['text'] as String? ?? '') : '');
    });
  }

  void _saveAnswer(String questionId, dynamic value) {
    setState(() {
      _answers[questionId] = value;
      final exam = _activeExam;
      if (exam != null) {
        ExamDraftStore.save(
          widget.draftOwner,
          'reading',
          exam.id,
          exam.version,
          Map<String, dynamic>.from(_answers),
        ).catchError((Object error) {
          if (mounted) {
            setState(
              () => _submitError = 'Không lưu được bản nháp trên thiết bị. Đừng đóng trang trước khi nộp bài.',
            );
          }
        });
      }
      _submitError = null;
    });
  }

  void _handleQuestionAction(bool isLastQuestion) {
    if (isLastQuestion) {
      _submitExam();
    } else {
      _moveToQuestion(_currentQuestion + 1);
    }
  }

  void _previousQuestion() => _moveToQuestion(_currentQuestion - 1);

  void _moveToQuestion(int index) {
    setState(() {
      _currentQuestion = index;
      _submitError = null;
      final question = _activeExam!.questions[index];
      final answer = _answers[question.id];
      _textAnswerController.text = question.questionType == 'essay'
          ? ((answer as Map?)?['text'] as String? ?? '')
          : (answer is String ? answer : '');
    });
  }

  void _openQuestionPalette() {
    final exam = _activeExam;
    if (exam == null) return;
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => _QuestionPaletteSheet(
        exam: exam,
        currentQuestion: _currentQuestion,
        answers: _answers,
        hasAnswer: _hasAnswer,
        onSelectQuestion: (index) {
          Navigator.pop(context);
          _moveToQuestion(index);
        },
        onSubmitExam: () {
          Navigator.pop(context);
          _confirmSubmit();
        },
      ),
    );
  }

  Future<void> _confirmSubmit() async {
    final exam = _activeExam;
    if (exam == null) return;
    final total = exam.questions.length;
    final answered = exam.questions.where((q) => _hasAnswer(q)).length;
    final unanswered = total - answered;

    final shouldSubmit = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Xác nhận nộp bài?'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Bạn đã hoàn thành: $answered/$total câu.'),
            if (unanswered > 0) ...[
              const SizedBox(height: 10),
              Text(
                'Còn $unanswered câu chưa trả lời. Các câu chưa trả lời sẽ được tính 0 điểm.',
                style: const TextStyle(color: AppTheme.red, fontWeight: FontWeight.w600),
              ),
            ],
            const SizedBox(height: 12),
            const Text('Bạn có chắc chắn muốn nộp bài ngay bây giờ?'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Làm tiếp'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Nộp bài ngay'),
          ),
        ],
      ),
    );

    if (shouldSubmit == true) {
      _submitExam();
    }
  }

  Future<void> _submitExam() async {
    _examTimer?.cancel();
    setState(() {
      _submitting = true;
      _submitError = null;
    });
    try {
      // Default unanswered questions to empty string so backend receives all IDs
      final answersToSubmit = Map<String, dynamic>.from(_answers);
      if (_activeExam != null) {
        for (final q in _activeExam!.questions) {
          if (!answersToSubmit.containsKey(q.id) || answersToSubmit[q.id] == null) {
            answersToSubmit[q.id] = '';
          }
        }
      }
      final result = await widget.repository.submitReadingExam(
        _activeExam!,
        Map.unmodifiable(answersToSubmit),
      );
      try {
        await ExamDraftStore.clear(
          widget.draftOwner,
          'reading',
          _activeExam!.id,
          _activeExam!.version,
        );
      } on Exception {
        /* The server has already saved the submitted result. */
      }
      if (!mounted) return;
      setState(() {
        _result = result;
        _submitting = false;
      });
    } on ReadingApiException catch (error) {
      if (!mounted) return;
      setState(() {
        _submitting = false;
        _submitError = _submissionMessage(error);
      });
    } on Exception {
      if (!mounted) return;
      setState(() {
        _submitting = false;
        _submitError = 'Không thể nộp bài. Hãy kiểm tra mạng và thử lại.';
      });
    }
  }

  String _submissionMessage(ReadingApiException error) {
    return switch (error.statusCode) {
      404 => 'Đề không còn được phát hành. Hãy quay lại và tải danh sách mới.',
      409 => 'Đề vừa được cập nhật. Hãy quay lại và tải phiên bản mới.',
      422 => 'Bài làm chưa hợp lệ: ${error.message}',
      _ => error.message,
    };
  }

  Future<void> _confirmExit() async {
    final shouldExit = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Thoát ${widget.title.toLowerCase()}?'),
        content: const Text('Các đáp án chưa nộp sẽ bị xóa.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Tiếp tục làm'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Thoát bài'),
          ),
        ],
      ),
    );
    if (shouldExit == true) {
      _examTimer?.cancel();
      _returnToExamList();
    }
  }


  void _returnToExamList() {
    setState(() {
      _activeExam = null;
      _result = null;
      _currentQuestion = 0;
      _answers.clear();
      _clearCanvasControllers();
      _submitError = null;
      _textAnswerController.clear();
    });
    _loadExams();
  }

  String _formatScore(double score) {
    return score == score.roundToDouble()
        ? score.toInt().toString()
        : score.toStringAsFixed(1);
  }

  bool _hasAnswer(ReadingQuestion question) {
    final answer = _answers[question.id];
    if (question.questionType == 'sentence_order') {
      return answer is String &&
          answer.split(' ').length == question.options.length;
    }
    if (question.questionType == 'hanzi_canvas') {
      return answer is Map &&
          answer['strokes'] is List &&
          (answer['strokes'] as List).isNotEmpty;
    }
    if (question.questionType == 'essay') {
      return answer is Map &&
          (answer['text'] as String? ?? '').trim().isNotEmpty;
    }
    return answer is String && answer.trim().isNotEmpty;
  }

  void _clearCanvasControllers() {
    for (final controller in _canvasControllers.values) {
      controller.dispose();
    }
    _canvasControllers.clear();
  }
}

class _ExamAudioPlayer extends StatefulWidget {
  const _ExamAudioPlayer({required this.url});

  final String url;

  @override
  State<_ExamAudioPlayer> createState() => _ExamAudioPlayerState();
}

class _ExamAudioPlayerState extends State<_ExamAudioPlayer> {
  final AudioPlayer _player = AudioPlayer();
  bool _playing = false;
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _player.onPlayerComplete.listen((_) {
      if (mounted) setState(() => _playing = false);
    });
  }

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }

  Future<void> _toggle() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      if (_playing) {
        await _player.pause();
      } else {
        await _player.play(UrlSource(widget.url));
      }
      if (mounted) setState(() => _playing = !_playing);
    } on Exception {
      if (mounted) {
        setState(() => _error = 'Không phát được audio. Hãy kiểm tra mạng.');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(12),
    decoration: BoxDecoration(
      color: const Color(0xFFFFF1E8),
      borderRadius: BorderRadius.circular(16),
    ),
    child: Column(
      children: [
        Row(
          children: [
            IconButton.filled(
              key: const Key('comprehensive-audio'),
              onPressed: _busy ? null : _toggle,
              icon: _busy
                  ? const SizedBox.square(
                      dimension: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Icon(_playing ? Icons.pause : Icons.play_arrow),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                _playing ? 'Đang phát hội thoại...' : 'Nghe hội thoại',
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
            ),
          ],
        ),
        if (_error != null)
          Text(_error!, style: const TextStyle(color: AppTheme.red)),
      ],
    ),
  );
}

class _ExamCard extends StatelessWidget {
  const _ExamCard({required this.exam, required this.onTap});

  final ReadingExam exam;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final isComprehensive = exam.questions.length >= 40 ||
        exam.questions.map((q) => q.section).toSet().length > 1;

    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: InkWell(
        key: Key('exam-${exam.id}'),
        onTap: onTap,
        borderRadius: BorderRadius.circular(20),
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Row(
            children: [
              HanziAvatar(
                isComprehensive ? '全' : '读',
                size: 58,
                color: isComprehensive
                    ? const Color(0xFFE2F0D9)
                    : const Color(0xFFE9F3ED),
              ),
              const SizedBox(width: 15),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 7,
                            vertical: 2,
                          ),
                          decoration: BoxDecoration(
                            color: const Color(0xFFFFECE5),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            'HSK ${exam.hsk}',
                            style: const TextStyle(
                              color: AppTheme.red,
                              fontSize: 10,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ),
                        if (isComprehensive) ...[
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 7,
                              vertical: 2,
                            ),
                            decoration: BoxDecoration(
                              color: const Color(0xFFE9F3ED),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: const Text(
                              'Đề thi Tổng hợp 3 phần',
                              style: TextStyle(
                                color: AppTheme.jade,
                                fontSize: 10,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                      exam.title,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Icon(
                          Icons.help_outline_rounded,
                          size: 15,
                          color: Colors.grey,
                        ),
                        Text(
                          ' ${exam.questions.length} câu',
                          style: const TextStyle(
                            color: Colors.grey,
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(width: 14),
                        const Icon(
                          Icons.schedule_rounded,
                          size: 15,
                          color: Colors.grey,
                        ),
                        Text(
                          ' ${exam.durationMinutes} phút',
                          style: const TextStyle(
                            color: Colors.grey,
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right_rounded, color: Colors.grey),
            ],
          ),
        ),
      ),
    );
  }
}

class _QuestionPaletteSheet extends StatelessWidget {
  const _QuestionPaletteSheet({
    required this.exam,
    required this.currentQuestion,
    required this.answers,
    required this.hasAnswer,
    required this.onSelectQuestion,
    required this.onSubmitExam,
  });

  final ReadingExam exam;
  final int currentQuestion;
  final Map<String, dynamic> answers;
  final bool Function(ReadingQuestion) hasAnswer;
  final ValueChanged<int> onSelectQuestion;
  final VoidCallback onSubmitExam;

  @override
  Widget build(BuildContext context) {
    final total = exam.questions.length;
    final answered = exam.questions.where((q) => hasAnswer(q)).length;

    final listening = <int>[];
    final reading = <int>[];
    final writing = <int>[];

    for (int i = 0; i < exam.questions.length; i++) {
      final s = exam.questions[i].section;
      if (s == 'listening') {
        listening.add(i);
      } else if (s == 'writing') {
        writing.add(i);
      } else {
        reading.add(i);
      }
    }

    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.8,
      ),
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey.shade300,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              const Icon(Icons.grid_view_rounded, color: AppTheme.jade),
              const SizedBox(width: 8),
              const Text(
                'Bảng câu hỏi đề thi',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFFE4F4E9),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  'Đã làm $answered/$total',
                  style: const TextStyle(
                    color: AppTheme.jade,
                    fontWeight: FontWeight.w800,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          const Divider(height: 1),
          const SizedBox(height: 8),
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (listening.isNotEmpty)
                    _buildSectionGroup('🎧 Phần 1: Nghe hiểu (${listening.length} câu)', listening),
                  if (reading.isNotEmpty)
                    _buildSectionGroup('📖 Phần 2: Đọc hiểu (${reading.length} câu)', reading),
                  if (writing.isNotEmpty)
                    _buildSectionGroup('✍️ Phần 3: Cấu trúc & Viết (${writing.length} câu)', writing),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            style: FilledButton.styleFrom(
              backgroundColor: AppTheme.jade,
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
            onPressed: onSubmitExam,
            icon: const Icon(Icons.check_circle_outline_rounded),
            label: Text('Nộp bài ngay ($answered/$total câu)'),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionGroup(String title, List<int> indices) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Text(
            title,
            style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 13, color: Colors.black87),
          ),
        ),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: indices.map((idx) {
            final q = exam.questions[idx];
            final isCurrent = idx == currentQuestion;
            final isDone = hasAnswer(q);

            return InkWell(
              onTap: () => onSelectQuestion(idx),
              borderRadius: BorderRadius.circular(10),
              child: Container(
                width: 44,
                height: 44,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: isCurrent
                      ? const Color(0xFFFFECE5)
                      : (isDone ? const Color(0xFFE4F4E9) : const Color(0xFFF5F5F5)),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: isCurrent
                        ? AppTheme.red
                        : (isDone ? AppTheme.jade : Colors.grey.shade300),
                    width: isCurrent ? 2 : 1,
                  ),
                ),
                child: Text(
                  '${idx + 1}',
                  style: TextStyle(
                    fontWeight: isCurrent || isDone ? FontWeight.w800 : FontWeight.w600,
                    color: isCurrent
                        ? AppTheme.red
                        : (isDone ? const Color(0xFF1D5C42) : Colors.black87),
                    fontSize: 13,
                  ),
                ),
              ),
            );
          }).toList(),
        ),
        const SizedBox(height: 12),
      ],
    );
  }
}


class _AnswerOption extends StatelessWidget {
  const _AnswerOption({
    required this.option,
    required this.selected,
    required this.enabled,
    required this.onTap,
  });

  final String option;
  final bool selected;
  final bool enabled;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        key: Key('answer-$option'),
        onTap: enabled ? onTap : null,
        borderRadius: BorderRadius.circular(16),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          width: double.infinity,
          constraints: const BoxConstraints(minHeight: 56),
          padding: const EdgeInsets.symmetric(horizontal: 17, vertical: 15),
          decoration: BoxDecoration(
            color: selected ? const Color(0xFFFFEEE5) : Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: selected ? AppTheme.red : const Color(0xFFF0E8DE),
              width: selected ? 1.5 : 1,
            ),
          ),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  option,
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
              ),
              if (selected)
                const Icon(Icons.radio_button_checked, color: AppTheme.red),
            ],
          ),
        ),
      ),
    );
  }
}

class _ReviewCard extends StatelessWidget {
  const _ReviewCard({required this.number, required this.item});

  final int number;
  final ReadingReviewItem item;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  item.isCorrect ? Icons.check_circle : Icons.cancel,
                  color: item.isCorrect ? AppTheme.jade : AppTheme.red,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Câu $number · ${item.score != null
                        ? '${_score(item.score!)} điểm'
                        : item.isCorrect
                        ? 'Đúng'
                        : 'Chưa đúng'}',
                    style: const TextStyle(fontWeight: FontWeight.w800),
                  ),
                ),
                IconButton(
                  tooltip: 'Nghe phát âm',
                  icon: const Icon(Icons.volume_up_rounded, size: 20, color: AppTheme.jade),
                  onPressed: () => PronunciationService.playWord(item.prompt),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              item.prompt,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 8),
            Text(
              item.questionType == 'hanzi_canvas'
                  ? item.submittedAnswer
                  : 'Bạn trả lời: ${item.submittedAnswer}',
            ),
            if (item.questionType == 'hanzi_canvas')
              Text('Chữ cần viết: ${item.answer}')
            else if (item.questionType == 'essay')
              Text('Rubric: ${item.answer}')
            else if (!item.isCorrect)
              Text('Đáp án đúng: ${item.answer}'),
            if (item.explanation.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                item.explanation,
                style: const TextStyle(color: Colors.grey, height: 1.4),
              ),
            ],
          ],
        ),
      ),
    );
  }

  String _score(double score) => score == score.roundToDouble()
      ? score.toInt().toString()
      : score.toStringAsFixed(1);
}

class _InlineError extends StatelessWidget {
  const _InlineError({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      key: const Key('submit-error'),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFFFE5E1),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.error_outline_rounded, color: AppTheme.red),
          const SizedBox(width: 9),
          Expanded(child: Text(message)),
        ],
      ),
    );
  }
}

class _MessageState extends StatelessWidget {
  const _MessageState({
    super.key,
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
