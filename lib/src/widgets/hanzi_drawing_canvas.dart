import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';

import '../theme/app_theme.dart';
import '../services/benefits_service.dart';

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

  List<List<Map<String, double>>> get payload => _strokes.map((stroke) {
    final points = stroke.length > 512
        ? List<Offset>.generate(512, (i) => stroke[(i * (stroke.length - 1) / 511).round()])
        : stroke;
    return points.map((point) => {
      'x': point.dx.clamp(0.0, 1024.0).toDouble(),
      'y': point.dy.clamp(0.0, 1024.0).toDouble(),
    }).toList(growable: false);
  }).toList(growable: false);

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

  bool autoFit({double targetPadding = 90.0}) {
    if (_strokes.isEmpty) return false;
    double minX = double.infinity;
    double maxX = -double.infinity;
    double minY = double.infinity;
    double maxY = -double.infinity;
    bool hasPoints = false;

    for (final stroke in _strokes) {
      for (final pt in stroke) {
        hasPoints = true;
        if (pt.dx < minX) minX = pt.dx;
        if (pt.dx > maxX) maxX = pt.dx;
        if (pt.dy < minY) minY = pt.dy;
        if (pt.dy > maxY) maxY = pt.dy;
      }
    }
    if (!hasPoints) return false;

    final width = maxX - minX;
    final height = maxY - minY;
    final dim = width > height ? width : height;
    if (dim < 8.0) return false;

    final availableDim = 1024.0 - 2 * targetPadding;
    final scale = availableDim / dim;
    final centerX = (minX + maxX) / 2;
    final centerY = (minY + maxY) / 2;

    for (var i = 0; i < _strokes.length; i++) {
      _strokes[i] = _strokes[i].map((pt) {
        final newX = (pt.dx - centerX) * scale + 512.0;
        final newY = (pt.dy - centerY) * scale + 512.0;
        return Offset(
          newX.clamp(0.0, 1024.0),
          newY.clamp(0.0, 1024.0),
        );
      }).toList();
    }
    notifyListeners();
    return true;
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

  static final ValueNotifier<Color> selectedInkColor = ValueNotifier<Color>(const Color(0xFF24332E));

  static const Map<String, String> _brushStyles = {
    'default': 'Tiêu chuẩn',
    'brush': 'Bút lông',
    'ink': 'Bút máy',
    'calligraphy': 'Thư pháp',
    'pencil': 'Bút chì',
    'marker': 'Bút dạ',
    'feather': 'Lông vũ',
  };

  static const List<Map<String, dynamic>> _inkColors = [
    {'id': 'ink', 'name': 'Mực đen', 'color': Color(0xFF24332E)},
    {'id': 'vermilion', 'name': 'Chu sa đỏ', 'color': Color(0xFFC62828)},
    {'id': 'jade', 'name': 'Xanh ngọc', 'color': Color(0xFF163F35)},
    {'id': 'sapphire', 'name': 'Lam ngọc', 'color': Color(0xFF1565C0)},
    {'id': 'gold', 'name': 'Hoàng kim', 'color': Color(0xFFD4AF37)},
    {'id': 'purple', 'name': 'Tím Tử Cấm', 'color': Color(0xFF6A1B9A)},
    {'id': 'pastelGreen', 'name': 'Xanh Pastel', 'color': Color(0xFF4E8752)},
    {'id': 'blossom', 'name': 'Hồng đào', 'color': Color(0xFFD81B60)},
    {'id': 'ocean', 'name': 'Xanh đại dương', 'color': Color(0xFF006064)},
    {'id': 'turquoise', 'name': 'Xanh ngọc lam', 'color': Color(0xFF00838F)},
    {'id': 'forest', 'name': 'Xanh rừng', 'color': Color(0xFF2E7D32)},
    {'id': 'olive', 'name': 'Xanh ô liu', 'color': Color(0xFF667C20)},
    {'id': 'indigo', 'name': 'Chàm', 'color': Color(0xFF303F9F)},
    {'id': 'lavender', 'name': 'Tím oải hương', 'color': Color(0xFF9575CD)},
    {'id': 'plum', 'name': 'Tím mận', 'color': Color(0xFF880E4F)},
    {'id': 'coral', 'name': 'Cam san hô', 'color': Color(0xFFE76F51)},
    {'id': 'amber', 'name': 'Hổ phách', 'color': Color(0xFFB76A00)},
    {'id': 'terracotta', 'name': 'Nâu đất', 'color': Color(0xFF9C4933)},
    {'id': 'coffee', 'name': 'Nâu cà phê', 'color': Color(0xFF5D4037)},
    {'id': 'slate', 'name': 'Xám đá', 'color': Color(0xFF546E7A)},
  ];

  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: Listenable.merge([BenefitsService.instance, selectedInkColor]),
    builder: (context, _) => Column(mainAxisSize: MainAxisSize.min, children: [
      if (enabled)
        Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: Row(children: [
            Expanded(child: OutlinedButton.icon(
              key: const Key('choose-brush'),
              onPressed: () => _chooseBrush(context),
              icon: const Icon(Icons.brush_outlined, size: 18),
              label: Text(_brushStyles[BenefitsService.instance.brush] ?? 'Chọn cọ',
                overflow: TextOverflow.ellipsis),
            )),
            const SizedBox(width: 8),
            Expanded(child: OutlinedButton.icon(
              key: const Key('choose-ink'),
              onPressed: () => _chooseInk(context),
              icon: Icon(Icons.circle, color: BenefitsService.instance.isPremium
                ? selectedInkColor.value : const Color(0xFF24332E), size: 18),
              label: const Text('Màu mực ▾'),
            )),
          ]),
        ),
      _canvas(context),
    ]),
  );

  Future<void> _chooseBrush(BuildContext context) async {
    final selected = await showDialog<String>(
      context: context,
      builder: (dialogContext) => SimpleDialog(
        title: const Text('Chọn cọ viết tay'),
        children: [
          for (final entry in _brushStyles.entries)
            SimpleDialogOption(
              onPressed: () => Navigator.pop(dialogContext, entry.key),
              child: ListTile(
                contentPadding: EdgeInsets.zero,
                leading: Icon(entry.key != 'default' && !BenefitsService.instance.isPremium
                    ? Icons.lock_outline : Icons.brush_outlined),
                title: Text(entry.value),
                trailing: BenefitsService.instance.brush == entry.key
                    ? const Icon(Icons.check) : null,
              ),
            ),
        ],
      ),
    );
    if (selected == null) return;
    try {
      await BenefitsService.instance.select(brush: selected);
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
      }
    }
  }

  Future<void> _chooseInk(BuildContext context) async {
    final selected = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Chọn màu mực'),
        content: SizedBox(
          width: 320,
          child: SingleChildScrollView(
            child: Wrap(spacing: 8, runSpacing: 8, children: [
              for (final item in _inkColors)
                Tooltip(
                  message: '${item['name']}${item['id'] != 'ink' && !BenefitsService.instance.isPremium ? ' (Premium)' : ''}',
                  child: Semantics(
                    button: true, label: item['name'] as String,
                    child: InkWell(
                      onTap: () => Navigator.pop(dialogContext, item),
                      borderRadius: BorderRadius.circular(24),
                      child: CircleAvatar(
                        radius: 24, backgroundColor: item['color'] as Color,
                        child: item['id'] != 'ink' && !BenefitsService.instance.isPremium
                            ? const Icon(Icons.lock_outline, color: Colors.white, size: 18)
                            : selectedInkColor.value == item['color']
                                ? const Icon(Icons.check, color: Colors.white) : null,
                      ),
                    ),
                  ),
                ),
            ]),
          ),
        ),
        actions: [TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Đóng'))],
      ),
    );
    if (selected == null || !context.mounted) return;
    if (selected['id'] != 'ink' && !BenefitsService.instance.isPremium) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Màu mực mở rộng dành cho HanziGo Premium.'),
      ));
      return;
    }
    selectedInkColor.value = selected['color'] as Color;
  }

  Widget _canvas(BuildContext context) => Center(
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
                    brush: BenefitsService.instance.brush,
                    inkColor: BenefitsService.instance.isPremium
                        ? selectedInkColor.value : const Color(0xFF24332E),
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
    this.brush = 'default',
    this.inkColor = const Color(0xFF24332E),
    this.wrongStrokes = const {},
    this.guideStrokes,
    this.visibleGuideStrokeCount,
    this.activeGuideStrokeIndex,
    this.showStrokeNumbers = false,
  });

  final List<List<Offset>> strokes;
  final String brush;
  final Color inkColor;
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
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round
      ..style = PaintingStyle.stroke;

    for (var index = 0; index < strokes.length; index++) {
      final stroke = strokes[index];
      if (stroke.isEmpty) continue;
      ink.color = wrongStrokes.contains(index + 1)
          ? AppTheme.red
          : inkColor;
      if (stroke.length == 1) {
        final pt = Offset(
          stroke.first.dx / 1024 * size.width,
          stroke.first.dy / 1024 * size.height,
        );
        canvas.drawCircle(pt, brush == 'marker' ? 5.5 : (brush == 'pencil' || brush == 'ink' ? 2.5 : 4.0), ink..style = PaintingStyle.fill);
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
      if (brush == 'brush') {
        for (var i = 1; i < stroke.length; i++) {
          final from = Offset(stroke[i - 1].dx / 1024 * size.width, stroke[i - 1].dy / 1024 * size.height);
          final to = Offset(stroke[i].dx / 1024 * size.width, stroke[i].dy / 1024 * size.height);
          final t = i / stroke.length;
          ink.strokeWidth = 3 + 9 * (1 - (2 * t - 1).abs());
          ink.strokeCap = StrokeCap.round;
          canvas.drawLine(from, to, ink);
        }
      } else if (brush == 'calligraphy') {
        for (var i = 1; i < stroke.length; i++) {
          final from = Offset(stroke[i - 1].dx / 1024 * size.width, stroke[i - 1].dy / 1024 * size.height);
          final to = Offset(stroke[i].dx / 1024 * size.width, stroke[i].dy / 1024 * size.height);
          ink.strokeWidth = 4 + 7 * ((to.dx - from.dx).abs() / ((to - from).distance + .1)).clamp(0.0, 1.0);
          ink.strokeCap = StrokeCap.square;
          canvas.drawLine(from, to, ink);
        }
      } else if (brush == 'feather') {
        for (var i = 1; i < stroke.length; i++) {
          final from = Offset(stroke[i - 1].dx / 1024 * size.width, stroke[i - 1].dy / 1024 * size.height);
          final to = Offset(stroke[i].dx / 1024 * size.width, stroke[i].dy / 1024 * size.height);
          final t = i / stroke.length;
          ink.strokeWidth = 1.8 + 5.5 * (1 - t);
          ink.strokeCap = StrokeCap.round;
          canvas.drawLine(from, to, ink);
        }
      } else if (brush == 'pencil') {
        ink.strokeWidth = 2.8;
        ink.strokeCap = StrokeCap.round;
        canvas.drawPath(path, ink);
      } else if (brush == 'marker') {
        ink.strokeWidth = 10.5;
        ink.strokeCap = StrokeCap.square;
        canvas.drawPath(path, ink);
      } else if (brush == 'ink') {
        ink.strokeWidth = 3.5;
        ink.strokeCap = StrokeCap.round;
        canvas.drawPath(path, ink);
      } else {
        ink.strokeWidth = 6.5;
        ink.strokeCap = StrokeCap.round;
        canvas.drawPath(path, ink);
      }
    }
  }

  @override
  bool shouldRepaint(covariant _HanziPainter oldDelegate) => true;
}
