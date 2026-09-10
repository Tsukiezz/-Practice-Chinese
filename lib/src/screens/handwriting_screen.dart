import 'dart:convert';

import 'package:flutter/material.dart';

import '../services/student_service.dart';
import '../theme/app_theme.dart';

enum _HandwritingMode { lookup, practice }

class HandwritingScreen extends StatefulWidget {
  const HandwritingScreen({super.key, required this.service, this.source});

  final StudentService service;
  final StudentResult? source;

  @override
  State<HandwritingScreen> createState() => _HandwritingScreenState();
}

class _HandwritingScreenState extends State<HandwritingScreen> {
  final _target = TextEditingController();
  final List<List<Offset>> _strokes = [];
  final Set<int> _savingWordIds = {};

  late _HandwritingMode _mode;
  bool _submitting = false;
  HandwritingGradeResult? _practiceResult;
  HandwritingRecognitionResult? _recognitionResult;
  String? _error;

  @override
  void initState() {
    super.initState();
    _mode = widget.source == null
        ? _HandwritingMode.lookup
        : _HandwritingMode.practice;
    if (widget.source != null) {
      try {
        _target.text = (jsonDecode(widget.source!.content)
                as Map<String, dynamic>)['target'] as String? ??
            '';
      } on Object {
        // Learner can enter a target if a legacy review payload has none.
      }
    }
  }

  @override
  void dispose() {
    _target.dispose();
    super.dispose();
  }

  bool get _isLookup => _mode == _HandwritingMode.lookup;

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: Text(widget.source == null
              ? 'Viết tay chữ Hán'
              : 'Viết lại chữ dưới 80 điểm'),
        ),
        body: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 760),
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  if (widget.source == null) ...[
                    SegmentedButton<_HandwritingMode>(
                      key: const Key('handwriting-mode'),
                      segments: const [
                        ButtonSegment(
                          value: _HandwritingMode.lookup,
                          icon: Icon(Icons.search),
                          label: Text('Tra từ'),
                        ),
                        ButtonSegment(
                          value: _HandwritingMode.practice,
                          icon: Icon(Icons.school_outlined),
                          label: Text('Luyện nét'),
                        ),
                      ],
                      selected: {_mode},
                      onSelectionChanged: _submitting
                          ? null
                          : (selection) => _changeMode(selection.single),
                    ),
                    const SizedBox(height: 16),
                  ],
                  Text(
                    _isLookup
                        ? 'Viết một chữ Hán vào ô bên dưới để nhận dạng và tra từ.'
                        : 'Nhập một chữ Hán, sau đó viết đúng thứ tự nét để chấm offline.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.grey.shade700),
                  ),
                  if (!_isLookup) ...[
                    const SizedBox(height: 12),
                    TextField(
                      key: const Key('handwriting-target'),
                      controller: _target,
                      enabled: !_submitting && widget.source == null,
                      maxLength: 1,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 32,
                        fontWeight: FontWeight.w800,
                      ),
                      decoration: const InputDecoration(
                        labelText: 'Chữ cần viết',
                        hintText: 'Ví dụ: 你',
                      ),
                    ),
                  ],
                  const SizedBox(height: 8),
                  Center(
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 520),
                      child: AspectRatio(
                        aspectRatio: 1,
                        child: LayoutBuilder(
                          builder: (_, box) => MouseRegion(
                            cursor: SystemMouseCursors.precise,
                            child: GestureDetector(
                              key: const Key('handwriting-canvas'),
                              behavior: HitTestBehavior.opaque,
                              onPanStart: _submitting
                                  ? null
                                  : (details) => setState(() {
                                        _strokes.add([
                                          _normalize(
                                            details.localPosition,
                                            box.biggest,
                                          ),
                                        ]);
                                        _clearResults();
                                      }),
                              onPanUpdate: _submitting
                                  ? null
                                  : (details) => setState(() {
                                        final point = _normalize(
                                          details.localPosition,
                                          box.biggest,
                                        );
                                        if (point.dx >= 0 &&
                                            point.dy >= 0 &&
                                            point.dx <= 1024 &&
                                            point.dy <= 1024) {
                                          _strokes.last.add(point);
                                        }
                                      }),
                              onPanEnd: _submitting
                                  ? null
                                  : (_) => setState(() {
                                        if (_strokes.isNotEmpty &&
                                            _strokes.last.length < 2) {
                                          _strokes.removeLast();
                                        }
                                      }),
                              child: Semantics(
                                label: _practiceResult
                                            ?.wrongStrokes.isNotEmpty ==
                                        true
                                    ? 'Nét sai được tô đỏ: ${_practiceResult!.wrongStrokes.join(', ')}'
                                    : null,
                                child: CustomPaint(
                                  // Draw above the white Container. A normal
                                  // painter is rendered behind its child.
                                  foregroundPainter: _HanziPainter(
                                    _strokes,
                                    wrongStrokes:
                                        _practiceResult?.wrongStrokes.toSet() ??
                                            const {},
                                  ),
                                  child: Container(
                                    decoration: BoxDecoration(
                                      color: Colors.white,
                                      border: Border.all(
                                          color: AppTheme.jade, width: 2),
                                      borderRadius: BorderRadius.circular(18),
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                  const Padding(
                    padding: EdgeInsets.only(top: 8),
                    child: Text(
                      'Giữ chuột và kéo trên ô vuông (hoặc dùng ngón tay) để viết từng nét.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.grey),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _submitting || _strokes.isEmpty
                              ? null
                              : () => setState(() {
                                    _strokes.removeLast();
                                    _clearResults();
                                  }),
                          icon: const Icon(Icons.undo),
                          label: const Text('Hoàn tác nét'),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _submitting || _strokes.isEmpty
                              ? null
                              : () => setState(() {
                                    _strokes.clear();
                                    _clearResults();
                                  }),
                          icon: const Icon(Icons.delete_outline),
                          label: const Text('Viết lại'),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  FilledButton.icon(
                    key: const Key('submit-handwriting'),
                    onPressed: _submitting ? null : _submit,
                    icon: _submitting
                        ? const SizedBox.square(
                            dimension: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : Icon(_isLookup ? Icons.search : Icons.auto_awesome),
                    label: Text(_isLookup
                        ? 'Nhận dạng & tra từ'
                        : 'Chấm thứ tự nét offline'),
                  ),
                  if (_error != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 12),
                      child: Text(
                        _error!,
                        key: const Key('handwriting-error'),
                        style: const TextStyle(color: AppTheme.red),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  if (_recognitionResult != null)
                    _RecognitionCard(
                      result: _recognitionResult!,
                      savingWordIds: _savingWordIds,
                      onSaveWord: _saveWord,
                    ),
                  if (_practiceResult != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 16),
                      child: Card(
                        color: _practiceResult!.score >= 80
                            ? const Color(0xFFE4F4E9)
                            : const Color(0xFFFFF1E8),
                        child: Padding(
                          padding: const EdgeInsets.all(18),
                          child: Column(
                            children: [
                              Text(
                                '${_practiceResult!.score.toStringAsFixed(0)} điểm',
                                style: const TextStyle(
                                  fontSize: 28,
                                  fontWeight: FontWeight.w900,
                                  color: AppTheme.jade,
                                ),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                _practiceResult!.feedback,
                                textAlign: TextAlign.center,
                              ),
                              const SizedBox(height: 14),
                              Wrap(
                                alignment: WrapAlignment.center,
                                spacing: 8,
                                runSpacing: 8,
                                children: [
                                  _ScoreChip(
                                    label: 'Số nét 30%',
                                    score: _practiceResult!.countScore,
                                  ),
                                  _ScoreChip(
                                    label: 'Dáng, vị trí & thứ tự 40%',
                                    score: _practiceResult!.orderPositionScore,
                                  ),
                                  _ScoreChip(
                                    label: 'Hướng nét 30%',
                                    score: _practiceResult!.directionScore,
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
      );

  void _changeMode(_HandwritingMode mode) {
    setState(() {
      _mode = mode;
      _strokes.clear();
      _clearResults();
    });
  }

  void _clearResults() {
    _practiceResult = null;
    _recognitionResult = null;
    _error = null;
  }

  Offset _normalize(Offset point, Size size) => Offset(
        point.dx / size.width * 1024,
        point.dy / size.height * 1024,
      );

  List<List<Map<String, double>>> _strokePayload() => _strokes
      .map((stroke) => stroke
          .map((point) => {'x': point.dx, 'y': point.dy})
          .toList(growable: false))
      .toList(growable: false);

  Future<void> _submit() async {
    final target = _target.text.trim();
    if (_strokes.isEmpty || (!_isLookup && target.isEmpty)) {
      setState(() => _error = _isLookup
          ? 'Hãy viết ít nhất một nét trước khi nhận dạng.'
          : 'Hãy nhập chữ và viết ít nhất một nét.');
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      if (_isLookup) {
        final result =
            await widget.service.recognizeHandwriting(_strokePayload());
        if (!mounted) return;
        setState(() => _recognitionResult = result);
      } else {
        final result = await widget.service.submitHandwriting(
          target,
          _strokePayload(),
          sourceResultId: widget.source?.id,
        );
        if (!mounted) return;
        setState(() => _practiceResult = result);
      }
    } on StudentApiException catch (error) {
      if (!mounted) return;
      setState(() => _error = error.message);
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  Future<void> _saveWord(VocabularyEntry word) async {
    if (_savingWordIds.contains(word.id)) return;
    setState(() => _savingWordIds.add(word.id));
    try {
      await widget.service.recordDictionaryLookup(
        word,
        'Viết tay: ${_recognitionResult?.recognizedHanzi ?? word.hanzi}',
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Đã lưu ${word.hanzi} vào lịch sử tra từ.')),
      );
    } on StudentApiException catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.message)),
      );
    } finally {
      if (mounted) setState(() => _savingWordIds.remove(word.id));
    }
  }
}

class _RecognitionCard extends StatelessWidget {
  const _RecognitionCard({
    required this.result,
    required this.savingWordIds,
    required this.onSaveWord,
  });

  final HandwritingRecognitionResult result;
  final Set<int> savingWordIds;
  final Future<void> Function(VocabularyEntry) onSaveWord;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(top: 16),
        child: Card(
          key: const Key('handwriting-recognition-result'),
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      result.recognizedHanzi,
                      style: const TextStyle(
                        fontSize: 52,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.jade,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Kết quả gần nhất',
                            style: TextStyle(fontWeight: FontWeight.w800),
                          ),
                          Text(
                            '${result.score.toStringAsFixed(0)}% tin cậy',
                            style: const TextStyle(color: AppTheme.red),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(result.feedback),
                const Divider(height: 28),
                const Text(
                  'Ứng viên và từ tương ứng',
                  style: TextStyle(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 8),
                for (final candidate in result.candidates)
                  _CandidateSection(
                    candidate: candidate,
                    savingWordIds: savingWordIds,
                    onSaveWord: onSaveWord,
                  ),
              ],
            ),
          ),
        ),
      );
}

class _CandidateSection extends StatelessWidget {
  const _CandidateSection({
    required this.candidate,
    required this.savingWordIds,
    required this.onSaveWord,
  });

  final HandwritingCandidate candidate;
  final Set<int> savingWordIds;
  final Future<void> Function(VocabularyEntry) onSaveWord;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: Material(
          color: const Color(0xFFF7F4EF),
          borderRadius: BorderRadius.circular(14),
          child: Column(
            children: [
              ListTile(
                dense: true,
                title: Text(
                  candidate.hanzi,
                  style: const TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                trailing: Text(
                  '${candidate.confidence.toStringAsFixed(0)}%',
                  style: const TextStyle(
                    color: AppTheme.jade,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              if (candidate.words.isEmpty)
                const Padding(
                  padding: EdgeInsets.fromLTRB(16, 0, 16, 14),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      'Chưa có từ tương ứng trong kho từ vựng.',
                      style: TextStyle(color: Colors.grey),
                    ),
                  ),
                )
              else
                for (final word in candidate.words)
                  ListTile(
                    key: Key('handwriting-word-${word.id}'),
                    dense: true,
                    title: Text('${word.hanzi} · ${word.pinyin}'),
                    subtitle: Text(word.meaning),
                    trailing: savingWordIds.contains(word.id)
                        ? const SizedBox.square(
                            dimension: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.bookmark_add_outlined),
                    onTap: savingWordIds.contains(word.id)
                        ? null
                        : () => onSaveWord(word),
                  ),
            ],
          ),
        ),
      );
}

class _ScoreChip extends StatelessWidget {
  const _ScoreChip({required this.label, required this.score});

  final String label;
  final double score;

  @override
  Widget build(BuildContext context) => Chip(
        label: Text('$label: ${score.toStringAsFixed(0)}'),
        side: BorderSide(color: AppTheme.jade.withValues(alpha: 0.3)),
        backgroundColor: Colors.white.withValues(alpha: 0.75),
      );
}

class _HanziPainter extends CustomPainter {
  const _HanziPainter(this.strokes, {this.wrongStrokes = const {}});

  final List<List<Offset>> strokes;
  final Set<int> wrongStrokes;

  @override
  void paint(Canvas canvas, Size size) {
    final guide = Paint()
      ..color = const Color(0xFFE6DED5)
      ..strokeWidth = 1;
    canvas.drawLine(
      Offset(size.width / 2, 0),
      Offset(size.width / 2, size.height),
      guide,
    );
    canvas.drawLine(
      Offset(0, size.height / 2),
      Offset(size.width, size.height / 2),
      guide,
    );
    final ink = Paint()
      ..strokeWidth = 7
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round
      ..style = PaintingStyle.stroke;
    for (var index = 0; index < strokes.length; index++) {
      final stroke = strokes[index];
      if (stroke.length < 2) continue;
      ink.color =
          wrongStrokes.contains(index + 1) ? AppTheme.red : AppTheme.ink;
      final path = Path()
        ..moveTo(
          stroke.first.dx / 1024 * size.width,
          stroke.first.dy / 1024 * size.height,
        );
      for (final point in stroke.skip(1)) {
        path.lineTo(
          point.dx / 1024 * size.width,
          point.dy / 1024 * size.height,
        );
      }
      canvas.drawPath(path, ink);
    }
  }

  @override
  bool shouldRepaint(covariant _HanziPainter oldDelegate) => true;
}
