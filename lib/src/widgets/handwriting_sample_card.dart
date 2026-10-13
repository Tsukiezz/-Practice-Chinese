import 'package:flutter/material.dart';

/// Local stroke medians for the single featured sample, from Make Me a Hanzi.
/// Same data as backend/data/stroke_data/4f60.json (see backend/data/MAKEMEAHANZI-COPYING.txt and MAKEMEAHANZI-APL.txt).
final _sampleStrokes = <List<Offset>>[
  [
    Offset(317, 88),
    Offset(342, 114),
    Offset(353, 141),
    Offset(303, 237),
    Offset(249, 323),
    Offset(181, 415),
    Offset(93, 514),
    Offset(68, 533)
  ],
  [
    Offset(273, 342),
    Offset(274, 375),
    Offset(285, 405),
    Offset(284, 459),
    Offset(273, 657),
    Offset(256, 777),
    Offset(260, 859)
  ],
  [
    Offset(556, 72),
    Offset(574, 83),
    Offset(595, 117),
    Offset(584, 154),
    Offset(539, 260),
    Offset(481, 369),
    Offset(428, 447),
    Offset(406, 469)
  ],
  [
    Offset(513, 368),
    Offset(704, 315),
    Offset(796, 303),
    Offset(813, 315),
    Offset(827, 337),
    Offset(798, 381),
    Offset(746, 440)
  ],
  [
    Offset(586, 437),
    Offset(615, 462),
    Offset(632, 488),
    Offset(627, 827),
    Offset(616, 859),
    Offset(604, 870),
    Offset(558, 853),
    Offset(490, 815)
  ],
  [Offset(455, 584), Offset(437, 657), Offset(397, 749)],
  [
    Offset(742, 574),
    Offset(812, 635),
    Offset(856, 684),
    Offset(871, 710),
    Offset(878, 746)
  ]
];

class HandwritingSampleCard extends StatefulWidget {
  const HandwritingSampleCard(
      {super.key, required this.onPractice, this.active = true});
  final VoidCallback? onPractice;
  final bool active;

  @override
  State<HandwritingSampleCard> createState() => _HandwritingSampleCardState();
}

class _HandwritingSampleCardState extends State<HandwritingSampleCard>
    with SingleTickerProviderStateMixin {
  late final AnimationController _animation = AnimationController(
    vsync: this,
    duration: const Duration(seconds: 10),
  );

  @override
  void initState() {
    super.initState();
    if (widget.active) _animation.repeat();
  }

  @override
  void didUpdateWidget(HandwritingSampleCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.active != oldWidget.active) {
      if (widget.active) {
        _animation.repeat();
      } else {
        _animation.stop();
      }
    }
  }

  @override
  void dispose() {
    _animation.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Card(
      margin: EdgeInsets.zero,
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        key: const Key('home-handwriting-sample'),
        onTap: widget.onPractice,
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Mẫu chữ viết',
                  style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              const Text('Xem từng nét, tự tay viết chữ Hán.'),
              const SizedBox(height: 16),
              Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 240),
                  child: AspectRatio(
                    aspectRatio: 1,
                    child: Semantics(
                      label: 'Mẫu chữ 你, 7 nét, tự động vẽ lặp lại',
                      child: CustomPaint(
                        painter: _SamplePainter(_animation, colors),
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 12),
              const Center(child: Text('你 · nǐ · Bạn · 7 nét')),
              const SizedBox(height: 12),
              Center(
                  child: FilledButton.icon(
                onPressed: widget.onPractice,
                icon: const Icon(Icons.draw_rounded),
                label: const Text('Luyện viết chữ này'),
              )),
            ],
          ),
        ),
      ),
    );
  }
}

class _SamplePainter extends CustomPainter {
  _SamplePainter(this.animation, this.colors) : super(repaint: animation);
  final Animation<double> animation;
  final ColorScheme colors;

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
    // Seven drawing seconds, two seconds holding, one second blank before restart.
    final elapsed = animation.value * 10;
    if (elapsed < 9) {
      for (var i = 0; i < _sampleStrokes.length; i++) {
        final fraction = (elapsed - i).clamp(0.0, 1.0);
        if (fraction <= 0) continue;
        final stroke = _sampleStrokes[i];
        final path = Path()..moveTo(stroke.first.dx, stroke.first.dy);
        for (final point in stroke.skip(1)) {
          path.lineTo(point.dx, point.dy);
        }
        final metric = path.computeMetrics().first;
        canvas.drawPath(metric.extractPath(0, metric.length * fraction), ink);
      }
    }
    canvas.restore();
  }

  @override
  bool shouldRepaint(_SamplePainter oldDelegate) =>
      oldDelegate.colors != colors || oldDelegate.animation != animation;
}

