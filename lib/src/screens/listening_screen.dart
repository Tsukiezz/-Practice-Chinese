import 'package:flutter/material.dart';
import 'package:audioplayers/audioplayers.dart';

import '../theme/app_theme.dart';
import '../widgets/common.dart';
import '../services/listening_exam_service.dart';
import '../models/reading_exam.dart';

class ListeningScreen extends StatefulWidget {
  const ListeningScreen({super.key, required this.repository});

  final ListeningExamRepository repository;

  @override
  State<ListeningScreen> createState() => _ListeningScreenState();
}

class _ListeningScreenState extends State<ListeningScreen> {
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
  final AudioPlayer _audioPlayer = AudioPlayer();

  @override
  void initState() {
    super.initState();
    _loadExams();
  }

  @override
  void dispose() {
    _audioPlayer.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_result != null) return _buildResult();
    if (_activeExam != null) return _buildQuestion();
    return _buildExamList();
  }

  Widget _buildExamList() {
    return SafeArea(
      child: Column(
        children: [
          const ScreenHeader(
            eyebrow: 'Bài luyện · Kỹ năng nghe',
            title: 'Test Nghe',
            trailing: Icon(
              Icons.headphones_rounded,
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
          const Padding(
            padding: EdgeInsets.fromLTRB(20, 22, 20, 10),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    'Chọn một đề để bắt đầu',
                    style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
                  ),
                ),
                Text(
                  'NGHE',
                  style: TextStyle(
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
        key: Key('listening-loading'),
        child: CircularProgressIndicator(),
      );
    }
    if (_loadError != null) {
      return _MessageState(
        key: const Key('listening-error'),
        icon: Icons.cloud_off_rounded,
        title: 'Không tải được đề',
        message: _loadError!,
        actionLabel: 'Thử lại',
        onAction: _loadExams,
      );
    }
    if (_exams.isEmpty) {
      return _MessageState(
        key: const Key('empty-listening-state'),
        icon: Icons.headphones_rounded,
        title: 'Chưa có đề Nghe HSK $_selectedHsk',
        message: 'Đề cần được Admin phát hành trước khi học viên làm bài.',
      );
    }
    return RefreshIndicator(
      onRefresh: _loadExams,
      child: ListView.separated(
        key: const Key('listening-exam-list'),
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
    final answer = _answers[question.id] ?? '';
    final isLastQuestion = _currentQuestion == exam.questions.length - 1;

    return SafeArea(
      child: Column(
        children: [
          ScreenHeader(
            eyebrow: 'HSK ${exam.hsk} · ${exam.title}',
            title: 'Câu ${_currentQuestion + 1}',
            trailing: IconButton(
              key: const Key('close-listening'),
              tooltip: 'Thoát bài',
              onPressed: _submitting ? null : _confirmExit,
              icon: const Icon(Icons.close_rounded),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: ProgressLine(
              value: (_currentQuestion + 1) / exam.questions.length,
            ),
          ),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (question.audioUrl.isNotEmpty) ...[
                    _AudioPlayer(
                      url: question.audioUrl,
                      audioPlayer: _audioPlayer,
                    ),
                    const SizedBox(height: 22),
                  ],
                  Text(
                    question.prompt,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 19,
                      height: 1.55,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 22),
                  Text(
                    question.options.isEmpty
                        ? 'Nhập đáp án'
                        : 'Chọn một đáp án',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 12),
                  if (question.options.isEmpty)
                    TextField(
                      key: const Key('listening-text-answer'),
                      controller: _textAnswerController,
                      enabled: !_submitting,
                      maxLength: 5000,
                      minLines: 1,
                      maxLines: 4,
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
                            key: const Key('previous-listening-question'),
                            onPressed: _submitting ? null : _previousQuestion,
                            child: const Text('Câu trước'),
                          ),
                        ),
                        const SizedBox(width: 10),
                      ],
                      Expanded(
                        flex: 2,
                        child: FilledButton(
                          key: const Key('listening-question-action'),
                          onPressed: answer.trim().isEmpty || _submitting
                              ? null
                              : () => _handleQuestionAction(isLastQuestion),
                          child: _submitting
                              ? const SizedBox.square(
                                  dimension: 22,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white,
                                  ),
                                )
                              : Text(
                                  isLastQuestion ? 'Nộp bài' : 'Câu tiếp theo'),
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

  Widget _buildResult() {
    final result = _result!;
    final passed = result.score >= 80;
    return SafeArea(
      child: Column(
        children: [
          ScreenHeader(
            eyebrow: 'Kết quả đã được lưu',
            title: 'Bài Test Nghe',
            trailing: Icon(
              passed ? Icons.emoji_events_rounded : Icons.headphones_rounded,
              color: passed ? AppTheme.orange : AppTheme.jade,
            ),
          ),
          Expanded(
            child: ListView(
              key: const Key('listening-result'),
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
                      const Text('ĐIỂM',
                          style: TextStyle(fontWeight: FontWeight.w800)),
                      const SizedBox(height: 8),
                      Text(
                        passed
                            ? 'Bạn đã hoàn thành tốt bài nghe.'
                            : 'Bạn nên xem lại transcript và luyện thêm.',
                        textAlign: TextAlign.center,
                      ),
                      if (result.feedback.isNotEmpty) ...[
                        const SizedBox(height: 12),
                        Text(
                          result.feedback,
                          key: const Key('listening-feedback'),
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
                      (entry) => _ReviewCard(
                        number: entry.key + 1,
                        item: entry.value,
                      ),
                    ),
                const SizedBox(height: 10),
                FilledButton(
                  key: const Key('finish-listening-exam'),
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

  Future<void> _loadExams() async {
    final sequence = ++_loadSequence;
    setState(() {
      _loading = true;
      _loadError = null;
    });
    try {
      final exams = await widget.repository.fetchListeningExams(_selectedHsk);
      if (!mounted || sequence != _loadSequence) return;
      setState(() {
        _exams = exams;
        _loading = false;
      });
    } on ListeningApiException catch (error) {
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

  void _startExam(ReadingExam exam) {
    setState(() {
      _activeExam = exam;
      _result = null;
      _currentQuestion = 0;
      _answers.clear();
      _submitError = null;
      _textAnswerController.clear();
    });
  }

  Future<void> _submitExam() async {
    setState(() {
      _submitting = true;
      _submitError = null;
    });
    try {
      final result = await widget.repository.submitListeningExam(
        _activeExam!,
        Map.unmodifiable(_answers),
      );
      if (!mounted) return;
      setState(() {
        _result = result;
        _submitting = false;
      });
    } on ListeningApiException catch (error) {
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

  String _submissionMessage(ListeningApiException error) {
    return switch (error.statusCode) {
      404 => 'Đề không còn được phát hành. Hãy quay lại và tải danh sách mới.',
      409 => 'Đề vừa được cập nhật. Hãy quay lại và tải phiên bản mới.',
      422 => 'Bài làm chưa hợp lệ: ${error.message}',
      _ => error.message,
    };
  }

  Future<void> _confirmExit() async {
    await _audioPlayer.stop();
    if (!mounted) return;
    final shouldExit = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Thoát bài nghe?'),
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
    if (shouldExit == true) _returnToExamList();
  }

  void _returnToExamList() {
    _audioPlayer.stop();
    setState(() {
      _activeExam = null;
      _result = null;
      _currentQuestion = 0;
      _answers.clear();
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

  final Map<String, String> _answers = {};
  final TextEditingController _textAnswerController = TextEditingController();

  void _saveAnswer(String questionId, String value) {
    setState(() {
      _answers[questionId] = value;
      _submitError = null;
    });
  }

  void _previousQuestion() => _moveToQuestion(_currentQuestion - 1);

  void _moveToQuestion(int index) {
    setState(() {
      _currentQuestion = index;
      _submitError = null;
      final question = _activeExam!.questions[index];
      _textAnswerController.text = _answers[question.id] ?? '';
    });
  }

  void _handleQuestionAction(bool isLastQuestion) {
    if (isLastQuestion) {
      _submitExam();
    } else {
      _moveToQuestion(_currentQuestion + 1);
    }
  }
}

class _ExamCard extends StatelessWidget {
  const _ExamCard({required this.exam, required this.onTap});

  final ReadingExam exam;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        key: Key('listening-exam-${exam.id}'),
        onTap: onTap,
        borderRadius: BorderRadius.circular(20),
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Row(
            children: [
              const HanziAvatar('听', size: 58, color: Color(0xFFE9F3ED)),
              const SizedBox(width: 15),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'HSK ${exam.hsk}',
                      style: const TextStyle(
                        color: AppTheme.red,
                        fontSize: 10,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 5),
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

class _AudioPlayer extends StatefulWidget {
  const _AudioPlayer({
    required this.url,
    required this.audioPlayer,
  });

  final String url;
  final AudioPlayer audioPlayer;

  @override
  State<_AudioPlayer> createState() => _AudioPlayerState();
}

class _AudioPlayerState extends State<_AudioPlayer> {
  bool _playing = false;
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    widget.audioPlayer.onPlayerComplete.listen((_) {
      if (mounted) {
        setState(() => _playing = false);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      key: const Key('listening-audio-player'),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFFE9F3ED),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        children: [
          IconButton(
            onPressed: _loading
                ? null
                : () async {
                    if (_error != null) {
                      setState(() => _error = null);
                    }
                    setState(() {
                      _loading = true;
                    });
                    try {
                      if (_playing) {
                        await widget.audioPlayer.pause();
                        setState(() => _playing = false);
                      } else {
                        await widget.audioPlayer.play(UrlSource(widget.url));
                        setState(() => _playing = true);
                      }
                    } on Exception {
                      setState(() {
                        _error = 'Không thể phát audio.';
                        _playing = false;
                      });
                    } finally {
                      if (mounted) {
                        setState(() => _loading = false);
                      }
                    }
                  },
            icon: _loading
                ? const SizedBox.square(
                    dimension: 24,
                    child: CircularProgressIndicator(
                        strokeWidth: 2, color: AppTheme.jade),
                  )
                : Icon(
                    _playing ? Icons.pause_rounded : Icons.play_arrow_rounded,
                    color: AppTheme.jade,
                    size: 32,
                  ),
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _playing ? 'Đang phát...' : 'Nghe hội thoại mẫu',
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
                if (_error != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    _error!,
                    style: const TextStyle(color: AppTheme.red, fontSize: 12),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
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
        key: Key('listening-answer-$option'),
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
                    'Câu $number · ${item.isCorrect ? 'Đúng' : 'Chưa đúng'}',
                    style: const TextStyle(fontWeight: FontWeight.w800),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(item.prompt,
                style: const TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            Text('Bạn chọn: ${item.submittedAnswer}'),
            if (!item.isCorrect) Text('Đáp án đúng: ${item.answer}'),
            if (item.transcript.isNotEmpty) ...[
              const SizedBox(height: 10),
              const Text(
                'Transcript',
                style: TextStyle(fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 4),
              SelectableText(
                item.transcript,
                key: Key('listening-transcript-${item.id}'),
                style: const TextStyle(height: 1.5),
              ),
            ],
            if (item.explanation.isNotEmpty) ...[
              const SizedBox(height: 8),
              const Text(
                'Gemini giải thích',
                style: TextStyle(fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 4),
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
}

class _InlineError extends StatelessWidget {
  const _InlineError({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      key: const Key('listening-submit-error'),
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
      child: Padding(
        padding: const EdgeInsets.all(32),
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
