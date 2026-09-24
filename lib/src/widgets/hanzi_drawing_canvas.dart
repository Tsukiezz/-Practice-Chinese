import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

class _ImmediatePanGestureRecognizer extends PanGestureRecognizer {
  @override
  void addAllowedPointer(PointerDownEvent event) {
    super.addAllowedPointer(event);
    resolve(GestureDisposition.accepted);
  }
}

class HanziCanvasController extends ChangeNotifier {
  final List<List<Offset>> _strokes = [];

  bool get isEmpty => _strokes.isEmpty;
  int get strokeCount => _strokes.length;
  void restore(List<dynamic> strokes) {
    _strokes.clear();
    for (final stroke in strokes) {
      _strokes.add(
        (stroke as List)
            .map(
              (point) => Offset(
                (point['x'] as num).toDouble(),
                (point['y'] as num).toDouble(),
              ),
            )
            .toList(),
      );
    }
    notifyListeners();
  }

  List<List<Map<String, double>>> get payload => _strokes
      .map(
        (stroke) => stroke
            .map((point) => {'x': point.dx, 'y': point.dy})
            .toList(growable: false),
      )
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
    if (_strokes.isNotEmpty) {
      if (_strokes.last.length == 1) {
        // Ensure single-point dots (chấm nét 1, 2) are preserved
        final first = _strokes.last.first;
        _strokes.last.add(Offset(first.dx + 0.5, first.dy + 0.5));
      }
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

  Offset _normalize(Offset point, Size size) =>
      Offset(point.dx / size.width * 1024, point.dy / size.height * 1024);
}

class HanziDrawingCanvas extends StatelessWidget {
  const HanziDrawingCanvas({
    super.key,
    required this.controller,
    this.enabled = true,
    this.wrongStrokes = const {},
    this.onChanged,
    this.onDrawingStateChanged,
    this.canvasKey,
    this.maxWidth = 520,
  });

  final HanziCanvasController controller;
  final bool enabled;
  final Set<int> wrongStrokes;
  final VoidCallback? onChanged;
  final ValueChanged<bool>? onDrawingStateChanged;
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
            child: RawGestureDetector(
              key: canvasKey,
              behavior: HitTestBehavior.opaque,
              gestures: enabled
                  ? {
                      _ImmediatePanGestureRecognizer:
                          GestureRecognizerFactoryWithHandlers<
                              _ImmediatePanGestureRecognizer>(
                        () => _ImmediatePanGestureRecognizer(),
                        (_ImmediatePanGestureRecognizer instance) {
                          instance
                            ..onStart = (details) {
                              onDrawingStateChanged?.call(true);
                              controller.start(
                                details.localPosition,
                                box.biggest,
                              );
                              onChanged?.call();
                            }
                            ..onUpdate = (details) {
                              controller.update(
                                details.localPosition,
                                box.biggest,
                              );
                              onChanged?.call();
                            }
                            ..onEnd = (_) {
                              onDrawingStateChanged?.call(false);
                              controller.end();
                              onChanged?.call();
                            }
                            ..onCancel = () {
                              onDrawingStateChanged?.call(false);
                              controller.end();
                              onChanged?.call();
                            };
                        },
                      ),
                    }
                  : {},
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
      if (stroke.isEmpty) continue;
      ink.color = wrongStrokes.contains(index + 1)
          ? AppTheme.red
          : AppTheme.ink;
      if (stroke.length == 1) {
        final pt = Offset(
          stroke.first.dx / 1024 * size.width,
          stroke.first.dy / 1024 * size.height,
        );
        canvas.drawCircle(pt, 4.0, ink..style = PaintingStyle.fill);
        ink.style = PaintingStyle.stroke;
        continue;
      }
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
