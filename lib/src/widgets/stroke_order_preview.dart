import 'package:flutter/material.dart';

/// Animated preview uses the same 0..1024 stroke coordinates as grading.
class StrokeOrderPreview extends StatefulWidget {
  const StrokeOrderPreview(
      {super.key, required this.character, required this.strokes});
  final String character;
  final List<List<Offset>> strokes;
  @override
  State<StrokeOrderPreview> createState() => _StrokeOrderPreviewState();
}

class _StrokeOrderPreviewState extends State<StrokeOrderPreview>
    with SingleTickerProviderStateMixin {
  late final AnimationController _animation = AnimationController(vsync: this);
  void _restart() {
    _animation.duration = Duration(seconds: widget.strokes.length + 3);
    _animation.repeat(period: _animation.duration);
  }

  @override
  void initState() {
    super.initState();
    _restart();
  }

  @override
  void didUpdateWidget(StrokeOrderPreview oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.character != widget.character ||
        oldWidget.strokes != widget.strokes) {
      _animation.reset();
      _restart();
    }
  }

  @override
  void dispose() {
    _animation.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Semantics(
        label: 'Stroke order: ${widget.character}',
        child: AspectRatio(
            aspectRatio: 1,
            child: CustomPaint(
              painter: StrokeOrderPainter(
                  _animation, Theme.of(context).colorScheme, widget.strokes),
            )),
      );
}

class StrokeOrderPainter extends CustomPainter {
  StrokeOrderPainter(this.animation, this.colors, this.strokes)
      : super(repaint: animation);
  final Animation<double> animation;
  final ColorScheme colors;
  final List<List<Offset>> strokes;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawRRect(
        RRect.fromRectAndRadius(Offset.zero & size, const Radius.circular(16)),
        Paint()..color = colors.surfaceContainerLow);
    canvas.save();
    canvas.scale(size.width / 1024, size.height / 1024);
    final grid = Paint()
      ..color = colors.outlineVariant
      ..strokeWidth = 3;
    canvas.drawLine(const Offset(512, 0), const Offset(512, 1024), grid);
    canvas.drawLine(const Offset(0, 512), const Offset(1024, 512), grid);
    canvas.drawLine(Offset.zero, const Offset(1024, 1024), grid);
    canvas.drawLine(const Offset(1024, 0), const Offset(0, 1024), grid);
    final ink = Paint()
      ..color = colors.primary
      ..strokeWidth = 28
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    // One second per stroke, two seconds holding, one blank before restart.
    final elapsed = animation.value * (strokes.length + 3);
    if (elapsed < strokes.length + 2) {
      for (var i = 0; i < strokes.length; i++) {
        final fraction = (elapsed - i).clamp(0.0, 1.0);
        if (fraction <= 0) continue;
        final stroke = strokes[i];
        final path = Path()..moveTo(stroke.first.dx, stroke.first.dy);
        for (final point in stroke.skip(1)) {
          path.lineTo(point.dx, point.dy);
        }
        if (stroke.length < 2) continue;
        final metrics = path.computeMetrics().toList();
        if (metrics.isEmpty) continue;
        final metric = metrics.first;
        canvas.drawPath(metric.extractPath(0, metric.length * fraction), ink);
      }
    }
    canvas.restore();
  }

  @override
  bool shouldRepaint(StrokeOrderPainter oldDelegate) =>
      oldDelegate.colors != colors ||
      oldDelegate.animation != animation ||
      oldDelegate.strokes != strokes;
}
