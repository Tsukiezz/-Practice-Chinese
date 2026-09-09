import 'dart:convert';
import 'package:flutter/material.dart';
import '../services/student_service.dart';
import '../theme/app_theme.dart';

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
  bool _submitting = false;
  StudentResult? _result;
  String? _error;

  @override
  void initState() {
    super.initState();
    if (widget.source != null) {
      try {
        _target.text = (jsonDecode(widget.source!.content)
                as Map<String, dynamic>)['target'] as String? ??
            '';
      } on Object {
        /* Learner can enter a target if the legacy payload has none. */
      }
    }
  }

  @override
  void dispose() {
    _target.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
            title: Text(widget.source == null
                ? 'Luyện viết chữ Hán'
                : 'Viết lại chữ dưới 80')),
        body: SafeArea(
            child: ListView(padding: const EdgeInsets.all(20), children: [
          TextField(
            key: const Key('handwriting-target'),
            controller: _target,
            enabled: !_submitting && widget.source == null,
            maxLength: 4,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 32, fontWeight: FontWeight.w800),
            decoration: const InputDecoration(
                labelText: 'Chữ cần viết', hintText: 'Ví dụ: 你'),
          ),
          AspectRatio(
              aspectRatio: 1,
              child: LayoutBuilder(
                  builder: (_, box) => GestureDetector(
                        key: const Key('handwriting-canvas'),
                        onPanStart: _submitting
                            ? null
                            : (d) => setState(() {
                                  _strokes.add([
                                    _normalize(d.localPosition, box.biggest)
                                  ]);
                                  _result = null;
                                  _error = null;
                                }),
                        onPanUpdate: _submitting
                            ? null
                            : (d) => setState(() {
                                  final p =
                                      _normalize(d.localPosition, box.biggest);
                                  if (p.dx >= 0 &&
                                      p.dy >= 0 &&
                                      p.dx <= 1024 &&
                                      p.dy <= 1024) {
                                    _strokes.last.add(p);
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
                        child: CustomPaint(
                          painter: _HanziPainter(_strokes),
                          child: Container(
                              decoration: BoxDecoration(
                            color: Colors.white,
                            border: Border.all(color: AppTheme.jade, width: 2),
                            borderRadius: BorderRadius.circular(18),
                          )),
                        ),
                      ))),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(
                child: OutlinedButton.icon(
              onPressed: _submitting || _strokes.isEmpty
                  ? null
                  : () => setState(() => _strokes.removeLast()),
              icon: const Icon(Icons.undo),
              label: const Text('Hoàn tác nét'),
            )),
            const SizedBox(width: 10),
            Expanded(
                child: OutlinedButton.icon(
              onPressed: _submitting || _strokes.isEmpty
                  ? null
                  : () => setState(_strokes.clear),
              icon: const Icon(Icons.delete_outline),
              label: const Text('Viết lại'),
            )),
          ]),
          const SizedBox(height: 12),
          FilledButton.icon(
            key: const Key('submit-handwriting'),
            onPressed: _submitting ? null : _submit,
            icon: _submitting
                ? const SizedBox.square(
                    dimension: 20,
                    child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.auto_awesome),
            label: const Text('Gửi Gemini chấm nét'),
          ),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: Text(_error!,
                  style: const TextStyle(color: AppTheme.red),
                  textAlign: TextAlign.center),
            ),
          if (_result != null)
            Padding(
              padding: const EdgeInsets.only(top: 16),
              child: Card(
                  color: _result!.score >= 80
                      ? const Color(0xFFE4F4E9)
                      : const Color(0xFFFFF1E8),
                  child: Padding(
                      padding: const EdgeInsets.all(18),
                      child: Column(children: [
                        Text('${_result!.score.toStringAsFixed(0)} điểm',
                            style: const TextStyle(
                                fontSize: 28,
                                fontWeight: FontWeight.w900,
                                color: AppTheme.jade)),
                        const SizedBox(height: 8),
                        Text(_result!.feedback, textAlign: TextAlign.center),
                      ]))),
            ),
        ])),
      );

  Offset _normalize(Offset p, Size size) =>
      Offset(p.dx / size.width * 1024, p.dy / size.height * 1024);

  Future<void> _submit() async {
    final target = _target.text.trim();
    if (target.isEmpty || _strokes.isEmpty) {
      setState(() => _error = 'Hãy nhập chữ và viết ít nhất một nét.');
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    final payload = _strokes
        .map((s) => s.map((p) => {'x': p.dx, 'y': p.dy}).toList())
        .toList();
    try {
      final result = await widget.service.submitHandwriting(target, payload,
          sourceResultId: widget.source?.id);
      if (!mounted) return;
      setState(() {
        _result = result;
        _submitting = false;
      });
    } on StudentApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.message;
        _submitting = false;
      });
    }
  }
}

class _HanziPainter extends CustomPainter {
  const _HanziPainter(this.strokes);
  final List<List<Offset>> strokes;
  @override
  void paint(Canvas canvas, Size size) {
    final guide = Paint()
      ..color = const Color(0xFFE6DED5)
      ..strokeWidth = 1;
    canvas.drawLine(
        Offset(size.width / 2, 0), Offset(size.width / 2, size.height), guide);
    canvas.drawLine(
        Offset(0, size.height / 2), Offset(size.width, size.height / 2), guide);
    final ink = Paint()
      ..color = AppTheme.ink
      ..strokeWidth = 7
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round
      ..style = PaintingStyle.stroke;
    for (final stroke in strokes) {
      if (stroke.length < 2) continue;
      final path = Path()
        ..moveTo(stroke.first.dx / 1024 * size.width,
            stroke.first.dy / 1024 * size.height);
      for (final p in stroke.skip(1)) {
        path.lineTo(p.dx / 1024 * size.width, p.dy / 1024 * size.height);
      }
      canvas.drawPath(path, ink);
    }
  }

  @override
  bool shouldRepaint(covariant _HanziPainter oldDelegate) => true;
}
