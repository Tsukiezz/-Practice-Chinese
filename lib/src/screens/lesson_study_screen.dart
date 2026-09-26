import 'package:flutter/material.dart';

import '../services/student_service.dart';
import '../services/pronunciation_service.dart';
import '../theme/app_theme.dart';

class LessonStudyScreen extends StatefulWidget {
  const LessonStudyScreen({
    super.key,
    required this.service,
    required this.lessonId,
    this.initialStage = 0,
  });
  final StudentService service;
  final String lessonId;
  final int initialStage;

  @override
  State<LessonStudyScreen> createState() => _LessonStudyScreenState();
}

class _LessonStudyScreenState extends State<LessonStudyScreen> {
  late Future<Map<String, dynamic>> _future;
  final _scroll = ScrollController();
  final Map<String, int> _answers = {};
  Map<String, dynamic>? _result;
  String? _error;
  late int _step;
  bool _busy = false, _translation = false;
  static const _steps = ['Từ vựng', 'Mẫu câu', 'Đọc hiểu', 'Luyện tập'];

  @override
  void initState() {
    super.initState();
    _step = widget.initialStage >= 4 ? 0 : widget.initialStage.clamp(0, 3);
    _future = widget.service.fetchLesson(widget.lessonId);
  }

  @override
  void dispose() {
    _scroll.dispose();
    super.dispose();
  }

  void _go(int step) {
    setState(() {
      _step = step;
      _error = null;
    });
    if (_scroll.hasClients) _scroll.jumpTo(0);
  }

  Future<void> _next(Map<String, dynamic> lesson) async {
    if (_busy) return;
    if (_step == 3 && _result != null) {
      Navigator.pop(context);
      return;
    }
    if (_step == 3 && _answers.length != (lesson['questions'] as List).length) {
      setState(
        () => _error = 'Bạn cần chọn một đáp án cho mỗi câu trước khi nộp.',
      );
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      if (_step < 3) {
        await widget.service.saveLessonStage(widget.lessonId, _step + 1);
        if (!mounted) return;
        _go(_step + 1);
      } else {
        final result = await widget.service.submitLesson(
          widget.lessonId,
          _answers,
        );
        if (!mounted) return;
        setState(() => _result = result);
        if (_scroll.hasClients) _scroll.jumpTo(0);
      }
    } catch (e) {
      if (mounted) setState(() => _error = 'Chưa lưu được. ${e.toString()}');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => PopScope(
        canPop: !_busy,
        child: Scaffold(
          appBar: AppBar(title: const Text('Bài học của bạn')),
          body: FutureBuilder<Map<String, dynamic>>(
            future: _future,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          'Chưa tải được bài học.\n${snapshot.error}',
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 12),
                        FilledButton(
                          onPressed: () => setState(
                            () => _future = widget.service.fetchLesson(
                              widget.lessonId,
                            ),
                          ),
                          child: const Text('Thử lại'),
                        ),
                      ],
                    ),
                  ),
                );
              }
              final lesson = snapshot.requireData;
              return SafeArea(
                top: false,
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 820),
                    child: Column(
                      children: [
                        Padding(
                          padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
                          child: SingleChildScrollView(
                            scrollDirection: Axis.horizontal,
                            child: Row(
                              children: List.generate(
                                4,
                                (i) => Padding(
                                  padding: const EdgeInsets.only(right: 8),
                                  child: ChoiceChip(
                                    key: ValueKey('lesson-step-$i'),
                                    label: Text('${i + 1}. ${_steps[i]}'),
                                    selected: _step == i,
                                    onSelected: _busy ? null : (_) => _go(i),
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ),
                        Expanded(
                          child: ListView(
                            controller: _scroll,
                            padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
                            children: [
                              Text(
                                'HSK ${lesson['hsk']} · Bài ${lesson['order']}/8 · ${lesson['minutes']} phút',
                                style: const TextStyle(
                                  color: AppTheme.jade,
                                  fontWeight: FontWeight.w700,
                                  fontSize: 12,
                                ),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                lesson['title'] as String,
                                style: const TextStyle(
                                  fontSize: 26,
                                  fontWeight: FontWeight.w800,
                                  height: 1.3,
                                ),
                              ),
                              const SizedBox(height: 12),
                              Text(
                                lesson['objective'] as String,
                                style: const TextStyle(height: 1.6),
                              ),
                              const SizedBox(height: 24),
                              if (_step == 0) ..._vocabulary(lesson),
                              if (_step == 1) ..._grammar(lesson),
                              if (_step == 2) ..._reading(lesson),
                              if (_step == 3) ..._quiz(lesson),
                            ],
                          ),
                        ),
                        if (_error != null)
                          Padding(
                            padding: const EdgeInsets.fromLTRB(20, 8, 20, 0),
                            child: Text(
                              _error!,
                              style: const TextStyle(color: AppTheme.red),
                              maxLines: 3,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Row(
                                children: [
                                  if (_step > 0) ...[
                                    IconButton(
                                      tooltip: 'Bước trước',
                                      onPressed:
                                          _busy ? null : () => _go(_step - 1),
                                      icon: const Icon(Icons.arrow_back),
                                    ),
                                    const SizedBox(width: 8),
                                  ],
                                  Expanded(
                                    child: FilledButton.icon(
                                      key: const ValueKey('lesson-next'),
                                      onPressed:
                                          _busy ? null : () => _next(lesson),
                                      icon: _busy
                                          ? const SizedBox(
                                              width: 18,
                                              height: 18,
                                              child: CircularProgressIndicator(
                                                strokeWidth: 2,
                                              ),
                                            )
                                          : Icon(
                                              _step == 3
                                                  ? Icons.check_rounded
                                                  : Icons.arrow_forward,
                                            ),
                                      label: Text(
                                        _busy
                                            ? 'Đang lưu…'
                                            : _step < 3
                                                ? 'Tiếp tục · ${_steps[_step + 1]}'
                                                : _result == null
                                                    ? 'Nộp bài · ${_answers.length}/4 câu'
                                                    : 'Về lộ trình',
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 6),
                              const Text(
                                'Tiến độ lưu theo tài khoản khi bạn bấm Tiếp tục hoặc Nộp bài.',
                                style:
                                    TextStyle(fontSize: 11, color: Colors.grey),
                                textAlign: TextAlign.center,
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      );

  Widget _heading(String title) => Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Text(
          title,
          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
        ),
      );

  Widget _panel(List<Widget> children, {Color? color}) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final defaultBg = isDark ? const Color(0xFF1A2924) : Colors.white;
    Color bg;
    if (color == const Color(0xFFE6F0EB)) {
      bg = isDark ? const Color(0xFF1E322A) : const Color(0xFFE6F0EB);
    } else {
      bg = color ?? defaultBg;
    }
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(18),
        border: isDark ? Border.all(color: const Color(0xFF283B34)) : null,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: children,
      ),
    );
  }

  List<Widget> _vocabulary(Map<String, dynamic> lesson) => [
        _heading('01 · Từ vựng trọng tâm'),
        const Text(
          'Đọc chữ Hán, đối chiếu pinyin và nghĩa. Tự nói một câu ngắn với mỗi từ.',
          style: TextStyle(height: 1.6),
        ),
        const SizedBox(height: 16),
        for (final word
            in (lesson['vocabulary'] as List).cast<Map<String, dynamic>>())
          _panel([
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: SelectableText(
                    word['hanzi'] as String,
                    style: const TextStyle(
                      fontSize: 30,
                      color: AppTheme.jade,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                IconButton.filledTonal(
                  tooltip: 'Nghe phát âm',
                  icon: const Icon(Icons.volume_up_rounded, color: AppTheme.jade),
                  onPressed: () => PronunciationService.playWord(
                    word['hanzi'] as String,
                    baseUrl: widget.service.baseUrl,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              word['pinyin'] as String,
              style: const TextStyle(fontSize: 16, color: AppTheme.red),
            ),
            const SizedBox(height: 6),
            Text(
              word['meaning'] as String,
              style: const TextStyle(fontSize: 16, height: 1.5),
            ),
            if (word['hsk'] == null ||
                (word['hsk'] as int) > (lesson['hsk'] as int)) ...[
              const SizedBox(height: 8),
              const Text(
                'Từ / cụm từ mở rộng theo ngữ cảnh bài',
                style: TextStyle(fontSize: 11, color: Colors.grey),
              ),
            ],
          ]),
        if (lesson['hsk'] == 1)
          _panel([
            const Text(
              'Gợi ý đọc pinyin',
              style: TextStyle(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 8),
            const Text(
              'ā: cao và ngang · á: đi lên · ǎ: hạ rồi lên khi đọc riêng · à: đi xuống. Âm không có dấu thường đọc nhẹ. Khi nói trong câu, thanh điệu có thể biến đổi; hãy đọc chậm và chú ý cụm từ.',
              style: TextStyle(height: 1.6),
            ),
          ], color: const Color(0xFFE6F0EB)),
      ];

  List<Widget> _grammar(Map<String, dynamic> lesson) {
    final grammar = lesson['grammar'] as Map<String, dynamic>;
    final example = grammar['example'] as Map<String, dynamic>;
    return [
      _heading('02 · Mẫu câu và cách dùng'),
      _panel([
        Text(
          grammar['pattern'] as String,
          style: const TextStyle(
            fontSize: 21,
            fontWeight: FontWeight.w700,
            color: AppTheme.jade,
            height: 1.5,
          ),
        ),
        const SizedBox(height: 12),
        Text(
          grammar['note'] as String,
          style: const TextStyle(fontSize: 16, height: 1.8),
        ),
      ], color: const Color(0xFFE6F0EB)),
      _panel([
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'VÍ DỤ',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
                color: AppTheme.jade,
              ),
            ),
            IconButton(
              tooltip: 'Nghe câu mẫu',
              icon: const Icon(Icons.volume_up_rounded, size: 20, color: AppTheme.jade),
              onPressed: () => PronunciationService.playWord(
                example['hanzi'] as String,
                baseUrl: widget.service.baseUrl,
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        SelectableText(
          example['hanzi'] as String,
          style: const TextStyle(fontSize: 25, height: 1.7),
        ),
        const SizedBox(height: 8),
        Text(
          example['pinyin'] as String,
          style: const TextStyle(color: AppTheme.red, height: 1.7),
        ),
        const SizedBox(height: 8),
        Text(
          example['meaning'] as String,
          style: const TextStyle(fontSize: 16, height: 1.7),
        ),
      ]),
      _panel([
        const Text(
          'Tự vận dụng',
          style: TextStyle(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 8),
        Text(lesson['task'] as String, style: const TextStyle(height: 1.7)),
        const SizedBox(height: 8),
        const Text(
          'Tự nói hoặc viết vào sổ. Phần này không chấm điểm tự động.',
          style: TextStyle(fontSize: 12, color: Colors.grey),
        ),
      ]),
    ];
  }

  List<Widget> _reading(Map<String, dynamic> lesson) {
    final reading = lesson['reading'] as Map<String, dynamic>;
    return [
      _heading('03 · Đọc và hiểu trong ngữ cảnh'),
      const Text(
        'Đọc một lượt để nắm ý chính. Sau đó tìm ai, làm gì, vì sao và đối chiếu bản dịch nếu cần.',
        style: TextStyle(height: 1.6),
      ),
      const SizedBox(height: 16),
      _panel([
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: SelectableText(
                reading['hanzi'] as String,
                style: const TextStyle(fontSize: 23, height: 1.9),
              ),
            ),
            IconButton.filledTonal(
              tooltip: 'Nghe bài đọc',
              icon: const Icon(Icons.volume_up_rounded, color: AppTheme.jade),
              onPressed: () => PronunciationService.playWord(
                reading['hanzi'] as String,
                baseUrl: widget.service.baseUrl,
              ),
            ),
          ],
        ),
      ]),
      Align(
        alignment: Alignment.centerLeft,
        child: TextButton.icon(
          onPressed: () => setState(() => _translation = !_translation),
          icon: Icon(
            _translation ? Icons.visibility_off_outlined : Icons.translate,
          ),
          label: Text(_translation ? 'Ẩn bản dịch' : 'Xem bản dịch tiếng Việt'),
        ),
      ),
      if (_translation)
        _panel([
          Text(
            reading['meaning'] as String,
            style: const TextStyle(fontSize: 16, height: 1.8),
          ),
        ], color: const Color(0xFFE6F0EB)),
      const SizedBox(height: 12),
      _heading('Tự kiểm tra trước khi làm bài'),
      const Text(
        '• Chủ đề chính của đoạn là gì?\n• Câu nào giúp bạn nhận ra ý chính?\n• Bạn có thể kể lại bằng lời của mình không?',
        style: TextStyle(height: 1.9),
      ),
    ];
  }

  List<Widget> _quiz(Map<String, dynamic> lesson) {
    final questions =
        (lesson['questions'] as List).cast<Map<String, dynamic>>();
    final review = {
      for (final r in (_result?['review'] as List? ?? []))
        r['id'] as String: r as Map<String, dynamic>,
    };
    return [
      _heading('04 · Luyện tập và ghi nhớ'),
      if (_result == null) ...[
        const Text(
          'Chọn một đáp án cho mỗi câu. Đúng ít nhất 3/4 câu để hoàn thành bài. Bạn có thể mở lại các bước để ôn trước khi nộp.',
          style: TextStyle(height: 1.6),
        ),
        const SizedBox(height: 8),
        const Text(
          'Nếu thoát trước khi nộp, các lựa chọn của lần làm này chưa được lưu.',
          style: TextStyle(fontSize: 12, color: Colors.grey),
        ),
      ] else
        _panel([
          Icon(
            _result!['passed'] == true
                ? Icons.verified_outlined
                : Icons.auto_stories_outlined,
            color: AppTheme.jade,
            size: 36,
          ),
          const SizedBox(height: 8),
          Text(
            '${_result!['score']}% · ${_result!['passed'] == true ? 'Đã hoàn thành bài' : 'Cùng ôn thêm nhé'}',
            style: const TextStyle(fontSize: 23, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 8),
          Text(
            'Điểm tốt nhất: ${(_result!['progress'] as Map)['best_score']}%. Xem lời giải bên dưới rồi thử lại để nhớ lâu hơn.',
            style: const TextStyle(height: 1.6),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: () {
              setState(() {
                _result = null;
                _answers.clear();
              });
              if (_scroll.hasClients) _scroll.jumpTo(0);
            },
            icon: const Icon(Icons.replay),
            label: const Text('Làm lại câu hỏi'),
          ),
        ], color: const Color(0xFFE6F0EB)),
      const SizedBox(height: 12),
      ExpansionTile(
        tilePadding: EdgeInsets.zero,
        title: const Text('Xem lại đoạn đọc'),
        children: [
          Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: Text(
              (lesson['reading'] as Map)['hanzi'] as String,
              style: const TextStyle(fontSize: 20, height: 1.8),
            ),
          ),
        ],
      ),
      const SizedBox(height: 12),
      for (var i = 0; i < questions.length; i++)
        _panel([
          Text(
            'Câu ${i + 1} · ${questions[i]['kind'] == 'grammar' ? 'Mẫu câu' : questions[i]['kind'] == 'reading' ? 'Đọc hiểu' : 'Từ vựng'}',
            style: const TextStyle(
              fontSize: 12,
              color: AppTheme.jade,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            questions[i]['prompt'] as String,
            style: const TextStyle(
              fontSize: 18,
              height: 1.6,
              fontWeight: FontWeight.w600,
            ),
          ),
          for (var option = 0;
              option < (questions[i]['options'] as List).length;
              option++)
            Builder(
              builder: (context) {
                final isDark = Theme.of(context).brightness == Brightness.dark;
                final isSelected = _answers[questions[i]['id']] == option;
                return Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Semantics(
                    selected: isSelected,
                    child: OutlinedButton(
                      key: ValueKey('answer-${questions[i]['id']}-$option'),
                      style: OutlinedButton.styleFrom(
                        alignment: Alignment.centerLeft,
                        padding: const EdgeInsets.all(14),
                        foregroundColor: isDark ? const Color(0xFFE2ECE7) : AppTheme.ink,
                        disabledForegroundColor: isDark ? const Color(0xFFE2ECE7) : AppTheme.ink,
                        backgroundColor: isSelected
                            ? (isDark ? const Color(0xFF1E3A2F) : const Color(0xFFE6F0EB))
                            : (isDark ? const Color(0xFF1A2924) : Colors.white),
                        side: BorderSide(
                          color: isSelected
                              ? AppTheme.jade
                              : (isDark ? const Color(0xFF283B34) : const Color(0xFFDBE1DC)),
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      onPressed: _busy || _result != null
                          ? null
                          : () => setState(() {
                                _answers[questions[i]['id'] as String] = option;
                                _error = null;
                              }),
                      child: Row(
                        children: [
                          Container(
                            width: 28,
                            height: 28,
                            alignment: Alignment.center,
                            decoration: BoxDecoration(
                              color: isSelected
                                  ? AppTheme.jade
                                  : (isDark ? const Color(0xFF263A31) : const Color(0xFFE9F3ED)),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              String.fromCharCode(65 + option),
                              style: TextStyle(
                                color: isSelected
                                    ? Colors.white
                                    : (isDark ? const Color(0xFF4DB697) : AppTheme.jade),
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              (questions[i]['options'] as List)[option] as String,
                              style: const TextStyle(fontWeight: FontWeight.w600),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          if (review[questions[i]['id']] != null) ...[
            const SizedBox(height: 8),
            Text(
              review[questions[i]['id']]!['correct'] == true
                  ? 'Chính xác'
                  : 'Đáp án đúng: ${(questions[i]['options'] as List)[review[questions[i]['id']]!['answer'] as int]}',
              style: TextStyle(
                fontWeight: FontWeight.w700,
                color: review[questions[i]['id']]!['correct'] == true
                    ? AppTheme.jade
                    : AppTheme.red,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              review[questions[i]['id']]!['explanation'] as String,
              style: const TextStyle(height: 1.7),
            ),
          ],
        ]),
    ];
  }
}
