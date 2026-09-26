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
    this.guideStrokes,
    this.visibleGuideStrokeCount,
    this.activeGuideStrokeIndex,
    this.showStrokeNumbers = false,
    this.onChanged,
    this.onDrawingStateChanged,
    this.canvasKey,
    this.maxWidth = 520,
  });

  final HanziCanvasController controller;
  final bool enabled;
  final Set<int> wrongStrokes;
  final List<List<Offset>>? guideStrokes;
  final int? visibleGuideStrokeCount;
  final int? activeGuideStrokeIndex;
  final bool showStrokeNumbers;
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
                    guideStrokes: guideStrokes,
                    visibleGuideStrokeCount: visibleGuideStrokeCount,
                    activeGuideStrokeIndex: activeGuideStrokeIndex,
                    showStrokeNumbers: showStrokeNumbers,
                  ),
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.white,
                      border: Border.all(color: AppTheme.jade, width: 2.5),
                      borderRadius: BorderRadius.circular(18),
                      boxShadow: const [
                        BoxShadow(
                          color: Color(0x12000000),
                          blurRadius: 12,
                          offset: Offset(0, 4),
                        ),
                      ],
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
  const _HanziPainter(
    this.strokes, {
    this.wrongStrokes = const {},
    this.guideStrokes,
    this.visibleGuideStrokeCount,
    this.activeGuideStrokeIndex,
    this.showStrokeNumbers = false,
  });

  final List<List<Offset>> strokes;
  final Set<int> wrongStrokes;
  final List<List<Offset>>? guideStrokes;
  final int? visibleGuideStrokeCount;
  final int? activeGuideStrokeIndex;
  final bool showStrokeNumbers;

  @override
  void paint(Canvas canvas, Size size) {
    // 1. Calligraphy rice-grid (米字格) guidelines
    final crossPaint = Paint()
      ..color = const Color(0xFFE2D8CC)
      ..strokeWidth = 1.2;
    canvas.drawLine(
      Offset(size.width / 2, 0),
      Offset(size.width / 2, size.height),
      crossPaint,
    );
    canvas.drawLine(
      Offset(0, size.height / 2),
      Offset(size.width, size.height / 2),
      crossPaint,
    );

    final diagPaint = Paint()
      ..color = const Color(0xFFEEE6DC)
      ..strokeWidth = 0.8;
    canvas.drawLine(Offset.zero, Offset(size.width, size.height), diagPaint);
    canvas.drawLine(Offset(size.width, 0), Offset(0, size.height), diagPaint);

    // 2. Stroke guidance (Ghost / animated step-by-step strokes)
    if (guideStrokes != null && guideStrokes!.isNotEmpty) {
      final totalGuide = guideStrokes!.length;
      final limit = visibleGuideStrokeCount == null
          ? totalGuide
          : visibleGuideStrokeCount!.clamp(0, totalGuide);

      final guidePaint = Paint()
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round
        ..style = PaintingStyle.stroke;

      for (var i = 0; i < limit; i++) {
        final gStroke = guideStrokes![i];
        if (gStroke.isEmpty) continue;
        final isActive = (activeGuideStrokeIndex == i);

        if (isActive) {
          guidePaint
            ..color = const Color(0xFFE65100)
            ..strokeWidth = 9.0;
        } else {
          guidePaint
            ..color = const Color(0x38176B50)
            ..strokeWidth = 6.5;
        }

        if (gStroke.length == 1) {
          final pt = Offset(
            gStroke.first.dx / 1024 * size.width,
            gStroke.first.dy / 1024 * size.height,
          );
          canvas.drawCircle(pt, isActive ? 5.5 : 4.0, guidePaint..style = PaintingStyle.fill);
          guidePaint.style = PaintingStyle.stroke;
        } else {
          final path = Path()
            ..moveTo(
              gStroke.first.dx / 1024 * size.width,
              gStroke.first.dy / 1024 * size.height,
            );
          for (final pt in gStroke.skip(1)) {
            path.lineTo(
              pt.dx / 1024 * size.width,
              pt.dy / 1024 * size.height,
            );
          }
          canvas.drawPath(path, guidePaint);
        }

        // Show starting point badge if active or numbers enabled
        if (showStrokeNumbers || isActive) {
          final startPt = Offset(
            gStroke.first.dx / 1024 * size.width,
            gStroke.first.dy / 1024 * size.height,
          );
          final badgePaint = Paint()
            ..color = isActive ? const Color(0xFFE65100) : const Color(0xFF176B50)
            ..style = PaintingStyle.fill;
          canvas.drawCircle(startPt, 8.5, badgePaint);

          final textPainter = TextPainter(
            text: TextSpan(
              text: '${i + 1}',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 10,
                fontWeight: FontWeight.bold,
              ),
            ),
            textDirection: TextDirection.ltr,
          )..layout();
          textPainter.paint(
            canvas,
            Offset(
              startPt.dx - textPainter.width / 2,
              startPt.dy - textPainter.height / 2,
            ),
          );
        }
      }
    }

    // 3. User's drawn strokes
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
