import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

class HanziCanvasController extends ChangeNotifier {
  final List<List<Offset>> _strokes = [];

  bool get isEmpty => _strokes.isEmpty;
  int get strokeCount => _strokes.length;

  List<List<Map<String, double>>> get payload => _strokes
      .map((stroke) => stroke
          .map((point) => {'x': point.dx, 'y': point.dy})
          .toList(growable: false))
      .toList(growable: false);

  void start(Offset point, Size size) {
    _strokes.add([_normalize(point, size)]);
    notifyListeners();
  }

  void update(Offset point, Size size) {
    if (_strokes.isEmpty) return;
    final normalized = _normalize(point, size);
    if (normalized.dx >= 0 &&
        normalized.dy >= 0 &&
        normalized.dx <= 1024 &&
        normalized.dy <= 1024) {
      _strokes.last.add(normalized);
      notifyListeners();
    }
  }

  void end() {
    if (_strokes.isNotEmpty && _strokes.last.length < 2) {
      _strokes.removeLast();
    }
    notifyListeners();
  }

  void undo() {
    if (_strokes.isEmpty) return;
    _strokes.removeLast();
    notifyListeners();
  }

  void clear() {
    if (_strokes.isEmpty) return;
    _strokes.clear();
    notifyListeners();
  }

  Offset _normalize(Offset point, Size size) => Offset(
        point.dx / size.width * 1024,
        point.dy / size.height * 1024,
      );
}

class HanziDrawingCanvas extends StatelessWidget {
  const HanziDrawingCanvas({
    super.key,
    required this.controller,
    this.enabled = true,
    this.wrongStrokes = const {},
    this.onChanged,
    this.canvasKey,
    this.maxWidth = 520,
  });

  final HanziCanvasController controller;
  final bool enabled;
  final Set<int> wrongStrokes;
  final VoidCallback? onChanged;
  final Key? canvasKey;
  final double maxWidth;

  @override
  Widget build(BuildContext context) => Center(
        child: ConstrainedBox(
          constraints: BoxConstraints(maxWidth: maxWidth),
          child: AspectRatio(
            aspectRatio: 1,
            child: LayoutBuilder(
              builder: (_, box) => MouseRegion(
                cursor: enabled
                    ? SystemMouseCursors.precise
                    : SystemMouseCursors.forbidden,
                child: GestureDetector(
                  key: canvasKey,
                  behavior: HitTestBehavior.opaque,
                  onPanStart: enabled
                      ? (details) {
                          controller.start(details.localPosition, box.biggest);
                          onChanged?.call();
                        }
                      : null,
                  onPanUpdate: enabled
                      ? (details) {
                          controller.update(details.localPosition, box.biggest);
                          onChanged?.call();
                        }
                      : null,
                  onPanEnd: enabled
                      ? (_) {
                          controller.end();
                          onChanged?.call();
                        }
                      : null,
                  child: AnimatedBuilder(
                    animation: controller,
                    builder: (_, __) => CustomPaint(
                      foregroundPainter: _HanziPainter(
                        controller._strokes,
                        wrongStrokes: wrongStrokes,
                      ),
                      child: Container(
                        decoration: BoxDecoration(
                          color: Colors.white,
                          border: Border.all(color: AppTheme.jade, width: 2),
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
