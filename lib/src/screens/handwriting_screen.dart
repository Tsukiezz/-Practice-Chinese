import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';

import '../services/student_service.dart';
import '../theme/app_theme.dart';
import '../widgets/hanzi_drawing_canvas.dart';

enum _HandwritingMode { lookup, practice }

class HandwritingScreen extends StatefulWidget {
  const HandwritingScreen({
    super.key,
    required this.service,
    this.source,
    this.guest = false,
  });

  final StudentService service;
  final StudentResult? source;
  final bool guest;

  @override
  State<HandwritingScreen> createState() => _HandwritingScreenState();
}

class _HandwritingScreenState extends State<HandwritingScreen> {
  final _target = TextEditingController();
  final _searchController = TextEditingController();
  final _canvasController = HanziCanvasController();
  final Set<int> _savingWordIds = {};

  late _HandwritingMode _mode;
  bool _submitting = false;
  bool _isDrawing = false;
  HandwritingGradeResult? _practiceResult;
  HandwritingRecognitionResult? _recognitionResult;
  String? _error;

  // Search & Stroke-by-stroke guidance state
  List<VocabularyEntry> _searchResults = [];
  bool _searching = false;
  bool _showSearchResults = false;
  Timer? _searchDebounce;

  HanziStrokeGuide? _strokeGuide;
  bool _loadingStrokeGuide = false;
  int _activeGuideStrokeIndex = 0;
  bool _isPlayingAnimation = false;
  Timer? _animationTimer;
  bool _showGhostStrokes = true;
  bool _showStrokeNumbers = true;

  static const _popularChars = [
    '你', '好', '学', '爱', '我', '中', '国', '生', '人', '水', '大', '天'
  ];

  @override
  void initState() {
    super.initState();
    _mode = widget.source == null
        ? _HandwritingMode.lookup
        : _HandwritingMode.practice;
    if (widget.source != null) {
      try {
        final initialTarget =
            (jsonDecode(widget.source!.content)
                    as Map<String, dynamic>)['target']
                as String? ??
            '';
        _target.text = initialTarget;
        if (initialTarget.isNotEmpty) {
          _loadStrokeGuide(initialTarget);
        }
      } on Object {
        // Learner can enter a target if a legacy review payload has none.
      }
    } else {
      _target.text = '你';
      _loadStrokeGuide('你');
    }
  }

  @override
  void dispose() {
    _target.dispose();
    _searchController.dispose();
    _canvasController.dispose();
    _searchDebounce?.cancel();
    _animationTimer?.cancel();
    super.dispose();
  }

  bool get _isLookup => _mode == _HandwritingMode.lookup;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Scaffold(
    appBar: AppBar(
      title: Text(
        widget.source == null
            ? 'Viết tay chữ Hán'
            : 'Viết lại chữ dưới 80 điểm',
      ),
      actions: [
        if (_isLookup)
          TextButton.icon(
            key: const Key('switch-to-keyboard'),
            onPressed: () => Navigator.pop(context, 'focus_keyboard'),
            icon: const Icon(Icons.keyboard),
            label: const Text('Gõ phím'),
          ),
      ],
    ),
    body: SafeArea(
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 760),
          child: ListView(
            padding: const EdgeInsets.all(20),
            physics: _isDrawing
                ? const NeverScrollableScrollPhysics()
                : const ClampingScrollPhysics(),
            children: [
              if (widget.source == null && !widget.guest) ...[
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
                    : 'Tìm từ vựng cần viết, xem hướng dẫn từng nét và luyện viết đúng chuẩn.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: isDark ? const Color(0xFF90A89D) : Colors.grey.shade700,
                ),
              ),

              if (_isLookup) ...[
                const SizedBox(height: 8),
                Center(
                  child: OutlinedButton.icon(
                    key: const Key('switch-to-keyboard-btn'),
                    onPressed: () => Navigator.pop(context, 'focus_keyboard'),
                    icon: const Icon(Icons.keyboard_alt_outlined),
                    label: const Text('Chuyển sang gõ bàn phím'),
                  ),
                ),
              ],
              if (!_isLookup) ...[
                const SizedBox(height: 12),
                // 1. Search Box with Live Auto-complete
                TextField(
                  controller: _searchController,
                  onChanged: _onSearchChanged,
                  decoration: InputDecoration(
                    labelText: 'Tìm từ vựng muốn viết',
                    hintText: 'Nhập chữ Hán, Pinyin hoặc nghĩa (VD: bạn, nǐ, 你, học...)',
                    prefixIcon: const Icon(Icons.search),
                    suffixIcon: _searching
                        ? const Padding(
                            padding: EdgeInsets.all(12),
                            child: SizedBox.square(
                              dimension: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                          )
                        : _searchController.text.isNotEmpty
                            ? IconButton(
                                icon: const Icon(Icons.clear),
                                onPressed: () {
                                  _searchController.clear();
                                  setState(() {
                                    _showSearchResults = false;
                                    _searchResults = [];
                                  });
                                },
                              )
                            : null,
                  ),
                ),
                if (_showSearchResults && _searchResults.isNotEmpty) ...[
                  const SizedBox(height: 6),
                  Card(
                    elevation: 4,
                    color: isDark ? const Color(0xFF1E3029) : Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                      side: BorderSide(color: AppTheme.jade.withValues(alpha: 0.3)),
                    ),
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxHeight: 220),
                      child: ListView.separated(
                        shrinkWrap: true,
                        padding: const EdgeInsets.symmetric(vertical: 4),
                        itemCount: _searchResults.length,
                        separatorBuilder: (_, __) => const Divider(height: 1),
                        itemBuilder: (_, index) {
                          final item = _searchResults[index];
                          return ListTile(
                            dense: true,
                            leading: Text(
                              item.hanzi,
                              style: const TextStyle(
                                fontSize: 22,
                                fontWeight: FontWeight.bold,
                                color: AppTheme.jade,
                              ),
                            ),
                            title: Text('${item.pinyin} • ${item.meaning}'),
                            trailing: Chip(
                              label: Text('HSK ${item.hsk}'),
                              padding: EdgeInsets.zero,
                              labelStyle: const TextStyle(fontSize: 10),
                            ),
                            onTap: () => _selectChar(
                              item.hanzi,
                              pinyin: item.pinyin,
                              meaning: item.meaning,
                              hsk: item.hsk,
                            ),
                          );
                        },
                      ),
                    ),
                  ),
                ],
                const SizedBox(height: 10),
                // 2. Quick Popular Character Chips
                Wrap(
                  crossAxisAlignment: WrapCrossAlignment.center,
                  spacing: 6,
                  runSpacing: 6,
                  children: [
                    Text(
                      'Gợi ý:',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: isDark ? const Color(0xFF90A89D) : Colors.grey.shade700,
                      ),
                    ),
                    for (final ch in _popularChars)
                      ActionChip(
                        label: Text(ch),
                        padding: const EdgeInsets.symmetric(horizontal: 4),
                        labelStyle: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: _target.text == ch ? Colors.white : (isDark ? Colors.white : AppTheme.jade),
                        ),
                        backgroundColor: _target.text == ch
                            ? AppTheme.jade
                            : (isDark ? const Color(0xFF1A3328) : const Color(0xFFEBF5EE)),
                        side: BorderSide(
                          color: _target.text == ch ? AppTheme.jade : AppTheme.jade.withValues(alpha: 0.25),
                        ),
                        onPressed: () => _selectChar(ch),
                      ),
                  ],
                ),
                const SizedBox(height: 12),
                // 3. Current Selected Character Info Card
                Card(
                  color: isDark ? const Color(0xFF1C2C24) : const Color(0xFFF4F8F4),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                    side: BorderSide(color: AppTheme.jade.withValues(alpha: 0.25)),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    child: Row(
                      children: [
                        Container(
                          width: 58,
                          height: 58,
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            color: isDark ? const Color(0xFF122019) : Colors.white,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: AppTheme.jade, width: 1.5),
                          ),
                          child: Text(
                            _target.text.isEmpty ? '?' : _target.text,
                            style: const TextStyle(
                              fontSize: 34,
                              fontWeight: FontWeight.bold,
                              color: AppTheme.jade,
                            ),
                          ),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Text(
                                    _strokeGuide?.pinyin.isNotEmpty == true
                                        ? _strokeGuide!.pinyin
                                        : 'Chữ cần viết',
                                    style: const TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  if (_strokeGuide != null && _strokeGuide!.hsk > 0) ...[
                                    const SizedBox(width: 8),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                      decoration: BoxDecoration(
                                        color: AppTheme.jade.withValues(alpha: 0.15),
                                        borderRadius: BorderRadius.circular(6),
                                      ),
                                      child: Text(
                                        'HSK ${_strokeGuide!.hsk}',
                                        style: const TextStyle(
                                          fontSize: 11,
                                          fontWeight: FontWeight.bold,
                                          color: AppTheme.jade,
                                        ),
                                      ),
                                    ),
                                  ],
                                ],
                              ),
                              const SizedBox(height: 3),
                              Text(
                                _strokeGuide?.meaning.isNotEmpty == true
                                    ? _strokeGuide!.meaning
                                    : (_loadingStrokeGuide
                                        ? 'Đang tải thông tin nét...'
                                        : 'Nhấn vào các nút bên dưới để xem hướng dẫn viết từng nét'),
                                style: TextStyle(
                                  fontSize: 13,
                                  color: isDark ? const Color(0xFFA0B4AA) : Colors.grey.shade700,
                                ),
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ],
                          ),
                        ),
                        if (_strokeGuide != null)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                            decoration: BoxDecoration(
                              color: AppTheme.jade,
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Text(
                              '${_strokeGuide!.totalStrokes} nét',
                              style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 10),
                // 4. Interactive Stroke Guidance Bar & Player
                if (_strokeGuide != null && _strokeGuide!.strokes.isNotEmpty) ...[
                  Card(
                    color: isDark ? const Color(0xFF1E2F26) : Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                      side: BorderSide(color: AppTheme.jade.withValues(alpha: 0.2)),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Row(
                                children: [
                                  const Icon(Icons.school, size: 18, color: AppTheme.jade),
                                  const SizedBox(width: 6),
                                  Text(
                                    'Hướng dẫn nét:',
                                    style: TextStyle(
                                      fontSize: 13,
                                      fontWeight: FontWeight.bold,
                                      color: isDark ? Colors.white : const Color(0xFF153E35),
                                    ),
                                  ),
                                ],
                              ),
                              Row(
                                children: [
                                  FilterChip(
                                    label: const Text('Nét mờ'),
                                    selected: _showGhostStrokes,
                                    padding: EdgeInsets.zero,
                                    labelStyle: const TextStyle(fontSize: 11),
                                    onSelected: (val) => setState(() => _showGhostStrokes = val),
                                  ),
                                  const SizedBox(width: 6),
                                  FilterChip(
                                    label: const Text('Số nét 1..N'),
                                    selected: _showStrokeNumbers,
                                    padding: EdgeInsets.zero,
                                    labelStyle: const TextStyle(fontSize: 11),
                                    onSelected: (val) => setState(() => _showStrokeNumbers = val),
                                  ),
                                ],
                              ),
                            ],
                          ),
                          const Divider(height: 16),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                            children: [
                              IconButton.outlined(
                                icon: const Icon(Icons.replay),
                                tooltip: 'Về nét 1',
                                onPressed: _resetGuide,
                              ),
                              IconButton.outlined(
                                icon: const Icon(Icons.skip_previous),
                                tooltip: 'Nét trước',
                                onPressed: _prevStroke,
                              ),
                              FilledButton.tonalIcon(
                                onPressed: _togglePlayAnimation,
                                icon: Icon(_isPlayingAnimation ? Icons.pause : Icons.play_arrow),
                                label: Text(_isPlayingAnimation ? 'Tạm dừng' : 'Tự động phát'),
                              ),
                              IconButton.outlined(
                                icon: const Icon(Icons.skip_next),
                                tooltip: 'Nét tiếp theo',
                                onPressed: _nextStroke,
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                decoration: BoxDecoration(
                                  color: const Color(0xFFE65100).withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(10),
                                  border: Border.all(color: const Color(0xFFE65100).withValues(alpha: 0.4)),
                                ),
                                child: Text(
                                  'Nét ${_activeGuideStrokeIndex + 1}/${_strokeGuide!.totalStrokes}',
                                  style: const TextStyle(
                                    color: Color(0xFFE65100),
                                    fontWeight: FontWeight.bold,
                                    fontSize: 13,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                ],
              ],
              const SizedBox(height: 8),
              Semantics(
                label: _practiceResult?.wrongStrokes.isNotEmpty == true
                    ? 'Nét sai được tô đỏ: ${_practiceResult!.wrongStrokes.join(', ')}'
                    : null,
                child: HanziDrawingCanvas(
                  controller: _canvasController,
                  enabled: !_submitting,
                  wrongStrokes:
                      _practiceResult?.wrongStrokes.toSet() ?? const {},
                  guideStrokes: !_isLookup && _showGhostStrokes && _strokeGuide != null
                      ? _strokeGuide!.strokes
                      : null,
                  visibleGuideStrokeCount: _isPlayingAnimation || _activeGuideStrokeIndex > 0
                      ? _activeGuideStrokeIndex + 1
                      : null,
                  activeGuideStrokeIndex: !_isLookup && _strokeGuide != null && _strokeGuide!.strokes.isNotEmpty
                      ? _activeGuideStrokeIndex
                      : null,
                  showStrokeNumbers: !_isLookup && _showStrokeNumbers && _strokeGuide != null,
                  canvasKey: const Key('handwriting-canvas'),
                  onChanged: () => setState(_clearResults),
                  onDrawingStateChanged: (drawing) {
                    if (_isDrawing != drawing) {
                      setState(() => _isDrawing = drawing);
                    }
                  },
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
                      onPressed: _submitting || _canvasController.isEmpty
                          ? null
                          : () => setState(() {
                              _canvasController.undo();
                              _clearResults();
                            }),
                      icon: const Icon(Icons.undo),
                      label: const Text('Hoàn tác nét'),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _submitting || _canvasController.isEmpty
                          ? null
                          : () => setState(() {
                              _canvasController.clear();
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
                label: Text(
                  _isLookup ? 'Nhận dạng & tra từ' : 'Chấm thứ tự nét offline',
                ),
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
                        ? (isDark ? const Color(0xFF1E3228) : const Color(0xFFE4F4E9))
                        : (isDark ? const Color(0xFF382320) : const Color(0xFFFFF1E8)),
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
  }


  void _changeMode(_HandwritingMode mode) {
    setState(() {
      _mode = mode;
      _canvasController.clear();
      _clearResults();
      _stopAnimation();
    });
    if (mode == _HandwritingMode.practice && _strokeGuide == null) {
      if (_target.text.isEmpty) {
        _target.text = '你';
      }
      _loadStrokeGuide(_target.text);
    }
  }

  void _onSearchChanged(String query) {
    _searchDebounce?.cancel();
    if (query.trim().isEmpty) {
      setState(() {
        _searchResults = [];
        _showSearchResults = false;
      });
      return;
    }
    _searchDebounce = Timer(const Duration(milliseconds: 300), () async {
      if (!mounted) return;
      setState(() => _searching = true);
      try {
        final list = await widget.service.fetchVocabulary(search: query.trim());
        if (!mounted) return;
        setState(() {
          _searchResults = list.take(15).toList();
          _showSearchResults = true;
          _searching = false;
        });
      } catch (_) {
        if (!mounted) return;
        setState(() => _searching = false);
      }
    });
  }

  void _selectChar(String char, {String? pinyin, String? meaning, int? hsk}) {
    if (char.trim().isEmpty) return;
    final single = char.trim().characters.first;
    _target.text = single;
    _searchController.clear();
    setState(() {
      _showSearchResults = false;
      _searchResults = [];
      _clearResults();
      _canvasController.clear();
    });
    _stopAnimation();
    _loadStrokeGuide(single);
  }

  Future<void> _loadStrokeGuide(String char) async {
    final clean = char.trim();
    if (clean.isEmpty) return;
    final single = clean.characters.first;
    setState(() {
      _loadingStrokeGuide = true;
      _strokeGuide = null;
      _activeGuideStrokeIndex = 0;
    });
    try {
      final guide = await widget.service.fetchStrokeGuide(single);
      if (!mounted) return;
      setState(() {
        _strokeGuide = guide;
        _loadingStrokeGuide = false;
        _activeGuideStrokeIndex = 0;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _loadingStrokeGuide = false);
    }
  }

  void _togglePlayAnimation() {
    if (_isPlayingAnimation) {
      _stopAnimation();
    } else {
      _startAnimation();
    }
  }

  void _startAnimation() {
    if (_strokeGuide == null || _strokeGuide!.strokes.isEmpty) return;
    _stopAnimation();
    setState(() {
      _isPlayingAnimation = true;
      _activeGuideStrokeIndex = 0;
    });
    _animationTimer = Timer.periodic(const Duration(milliseconds: 800), (timer) {
      if (!mounted || _strokeGuide == null) {
        timer.cancel();
        return;
      }
      if (_activeGuideStrokeIndex < _strokeGuide!.strokes.length - 1) {
        setState(() => _activeGuideStrokeIndex++);
      } else {
        _stopAnimation();
      }
    });
  }

  void _stopAnimation() {
    _animationTimer?.cancel();
    _animationTimer = null;
    if (_isPlayingAnimation) {
      setState(() => _isPlayingAnimation = false);
    }
  }

  void _nextStroke() {
    _stopAnimation();
    if (_strokeGuide == null || _strokeGuide!.strokes.isEmpty) return;
    if (_activeGuideStrokeIndex < _strokeGuide!.strokes.length - 1) {
      setState(() => _activeGuideStrokeIndex++);
    }
  }

  void _prevStroke() {
    _stopAnimation();
    if (_strokeGuide == null || _strokeGuide!.strokes.isEmpty) return;
    if (_activeGuideStrokeIndex > 0) {
      setState(() => _activeGuideStrokeIndex--);
    }
  }

  void _resetGuide() {
    _stopAnimation();
    setState(() => _activeGuideStrokeIndex = 0);
  }

  void _clearResults() {
    _practiceResult = null;
    _recognitionResult = null;
    _error = null;
  }

  Future<void> _submit() async {
    final target = _target.text.trim();
    if (_canvasController.isEmpty || (!_isLookup && target.isEmpty)) {
      setState(
        () => _error = _isLookup
            ? 'Hãy viết ít nhất một nét trước khi nhận dạng.'
            : 'Hãy nhập chữ và viết ít nhất một nét.',
      );
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      if (_isLookup) {
        final result = await widget.service.recognizeHandwriting(
          _canvasController.payload,
          guest: widget.guest,
        );
        if (!mounted) return;
        setState(() => _recognitionResult = result);
      } else {
        final result = await widget.service.submitHandwriting(
          target,
          _canvasController.payload,
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
    if (widget.guest) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Đăng nhập để lưu từ vựng.')),
      );
      return;
    }
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
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(error.message)));
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
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Material(
        color: isDark ? const Color(0xFF1E3029) : const Color(0xFFF7F4EF),
        borderRadius: BorderRadius.circular(14),
        child: Column(

        children: [
          ListTile(
            dense: true,
            title: Text(
              candidate.hanzi,
              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800),
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
}

class _ScoreChip extends StatelessWidget {
  const _ScoreChip({required this.label, required this.score});

  final String label;
  final double score;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Chip(
      label: Text('$label: ${score.toStringAsFixed(0)}'),
      side: BorderSide(color: AppTheme.jade.withValues(alpha: 0.3)),
      backgroundColor: isDark
          ? const Color(0xFF1E3228)
          : Colors.white.withValues(alpha: 0.75),
    );
  }
}

