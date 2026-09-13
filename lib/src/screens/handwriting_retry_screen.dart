import 'package:flutter/material.dart';

import '../services/student_service.dart';
import '../theme/app_theme.dart';
import '../widgets/hanzi_drawing_canvas.dart';

class HandwritingRetryScreen extends StatefulWidget {
  const HandwritingRetryScreen({super.key, required this.service});

  final StudentService service;

  @override
  State<HandwritingRetryScreen> createState() => _HandwritingRetryScreenState();
}

class _HandwritingRetryScreenState extends State<HandwritingRetryScreen> {
  final HanziCanvasController _canvasController = HanziCanvasController();
  final Set<String> _selected = {};

  List<HandwritingRetryItem> _items = const [];
  List<String> _session = const [];
  int _currentIndex = 0;
  bool _loading = true;
  bool _submitting = false;
  String? _error;
  HandwritingGradeResult? _result;

  bool get _inSession => _session.isNotEmpty;
  String get _currentHanzi => _session[_currentIndex];

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _canvasController.dispose();
    super.dispose();
  }

  Future<void> _load({bool showLoading = true}) async {
    if (showLoading) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }
    try {
      final items = await widget.service.fetchHandwritingRetryItems();
      if (!mounted) return;
      setState(() {
        _items = items;
        _selected.removeWhere(
          (hanzi) => !items.any((item) => item.hanzi == hanzi),
        );
        _loading = false;
      });
    } on StudentApiException catch (error) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = error.message;
      });
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          leading: _inSession
              ? IconButton(
                  tooltip: 'Về danh sách',
                  onPressed: _submitting ? null : _finishSession,
                  icon: const Icon(Icons.arrow_back),
                )
              : null,
          title: Text(_inSession
              ? 'Luyện ${_currentIndex + 1}/${_session.length}'
              : 'Luyện lại chữ dưới 80'),
        ),
        body: SafeArea(
          child: _inSession ? _buildPractice() : _buildList(),
        ),
      );

  Widget _buildList() {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return _Message(
        title: 'Không tải được danh sách',
        message: _error!,
        action: _load,
      );
    }
    if (_items.isEmpty) {
      return _Message(
        key: const Key('retry-empty'),
        title: 'Đã hoàn thành',
        message: 'Không còn chữ nào có lần luyện gần nhất dưới 80 điểm.',
        action: _load,
      );
    }
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 12),
          child: Text(
            'Chọn một hoặc nhiều chữ. Danh sách dùng điểm lần luyện gần nhất '
            'và được xếp từ thấp lên cao.',
            style: TextStyle(color: Colors.grey.shade700),
          ),
        ),
        Expanded(
          child: RefreshIndicator(
            onRefresh: _load,
            child: ListView.builder(
              key: const Key('handwriting-retry-list'),
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 100),
              itemCount: _items.length,
              itemBuilder: (_, index) {
                final item = _items[index];
                return Card(
                  child: CheckboxListTile(
                    key: Key('retry-${item.hanzi}'),
                    value: _selected.contains(item.hanzi),
                    onChanged: (checked) => setState(() {
                      if (checked == true) {
                        _selected.add(item.hanzi);
                      } else {
                        _selected.remove(item.hanzi);
                      }
                    }),
                    secondary: CircleAvatar(
                      backgroundColor: const Color(0xFFFFEBDD),
                      child: Text(
                        item.hanzi,
                        style: const TextStyle(
                          color: AppTheme.jade,
                          fontSize: 25,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                    title: Text(
                      '${item.latestScore.toStringAsFixed(0)} điểm',
                      style: const TextStyle(fontWeight: FontWeight.w800),
                    ),
                    subtitle: Text('Đã luyện ${item.attempts} lần'),
                  ),
                );
              },
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              key: const Key('start-retry-session'),
              onPressed: _selected.isEmpty ? null : _startSession,
              icon: const Icon(Icons.play_arrow_rounded),
              label: Text('Luyện ${_selected.length} chữ đã chọn'),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildPractice() => Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 680),
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              const Text(
                'Viết đúng thứ tự, vị trí và hướng nét',
                textAlign: TextAlign.center,
              ),
              Text(
                _currentHanzi,
                key: const Key('retry-current-hanzi'),
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: AppTheme.jade,
                  fontSize: 62,
                  fontWeight: FontWeight.w900,
                ),
              ),
              HanziDrawingCanvas(
                key: const Key('retry-canvas'),
                controller: _canvasController,
                enabled: !_submitting,
                wrongStrokes: _result?.wrongStrokes.toSet() ?? const {},
                onChanged: () => setState(() {
                  _result = null;
                  _error = null;
                }),
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _submitting || _canvasController.isEmpty
                          ? null
                          : () => setState(() {
                                _canvasController.undo();
                                _result = null;
                              }),
                      icon: const Icon(Icons.undo),
                      label: const Text('Hoàn tác'),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _submitting || _canvasController.isEmpty
                          ? null
                          : () => setState(() {
                                _canvasController.clear();
                                _result = null;
                              }),
                      icon: const Icon(Icons.delete_outline),
                      label: const Text('Viết lại'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              FilledButton.icon(
                key: const Key('submit-retry'),
                onPressed: _submitting ? null : _submit,
                icon: _submitting
                    ? const SizedBox.square(
                        dimension: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.task_alt),
                label: const Text('Chấm nét offline'),
              ),
              if (_result != null) ...[
                const SizedBox(height: 12),
                Card(
                  color: _result!.score >= 80
                      ? const Color(0xFFE4F4E9)
                      : const Color(0xFFFFF1E8),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      children: [
                        Text(
                          '${_result!.score.toStringAsFixed(0)} điểm',
                          style: const TextStyle(
                            color: AppTheme.jade,
                            fontSize: 28,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                        Text(_result!.feedback, textAlign: TextAlign.center),
                      ],
                    ),
                  ),
                ),
              ],
              if (_error != null) ...[
                const SizedBox(height: 10),
                Text(
                  _error!,
                  key: const Key('retry-error'),
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: AppTheme.red),
                ),
              ],
              if (_session.length > 1) ...[
                const SizedBox(height: 8),
                TextButton(
                  onPressed: _submitting ? null : _skip,
                  child: const Text('Để sau, chuyển sang chữ tiếp theo'),
                ),
              ],
            ],
          ),
        ),
      );

  void _startSession() {
    setState(() {
      _session = _items
          .where((item) => _selected.contains(item.hanzi))
          .map((item) => item.hanzi)
          .toList(growable: false);
      _currentIndex = 0;
      _result = null;
      _error = null;
      _canvasController.clear();
    });
  }

  Future<void> _submit() async {
    if (_canvasController.isEmpty) {
      setState(() => _error = 'Hãy viết ít nhất một nét trước khi chấm.');
      return;
    }
    final hanzi = _currentHanzi;
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      final result = await widget.service.submitHandwriting(
        hanzi,
        _canvasController.payload,
      );
      if (!mounted) return;
      setState(() => _result = result);
      if (result.score >= 80) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Hoàn thành chữ $hanzi với ${result.score.toStringAsFixed(0)} điểm.',
            ),
          ),
        );
        await _load(showLoading: false);
        if (!mounted) return;
        _advance();
      }
    } on StudentApiException catch (error) {
      if (!mounted) return;
      setState(() => _error = error.message);
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  void _skip() => _advance();

  void _advance() {
    if (_currentIndex + 1 >= _session.length) {
      _finishSession();
      return;
    }
    setState(() {
      _currentIndex += 1;
      _canvasController.clear();
      _result = null;
      _error = null;
    });
  }

  void _finishSession() {
    setState(() {
      _session = const [];
      _currentIndex = 0;
      _canvasController.clear();
      _result = null;
      _error = null;
    });
    _load(showLoading: false);
  }
}

class _Message extends StatelessWidget {
  const _Message({
    super.key,
    required this.title,
    required this.message,
    required this.action,
  });

  final String title;
  final String message;
  final Future<void> Function({bool showLoading}) action;

  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.task_alt, size: 56, color: AppTheme.jade),
              const SizedBox(height: 10),
              Text(
                title,
                style: const TextStyle(fontWeight: FontWeight.w900),
              ),
              const SizedBox(height: 6),
              Text(message, textAlign: TextAlign.center),
              const SizedBox(height: 14),
              OutlinedButton(
                onPressed: action,
                child: const Text('Làm mới'),
              ),
            ],
          ),
        ),
      );
}
