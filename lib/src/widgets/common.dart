import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class ScreenHeader extends StatelessWidget {
  const ScreenHeader(
      {super.key, required this.eyebrow, required this.title, this.trailing});
  final String eyebrow, title;
  final Widget? trailing;
  @override
  Widget build(BuildContext context) => Padding(
      padding: const EdgeInsets.fromLTRB(20, 18, 20, 12),
      child: Row(children: [
        Expanded(
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(eyebrow.toUpperCase(),
              style: const TextStyle(
                  color: AppTheme.jade,
                  fontSize: 10,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1.5)),
          const SizedBox(height: 5),
          Text(title,
              style: const TextStyle(
                  color: AppTheme.ink,
                  fontSize: 28,
                  fontWeight: FontWeight.w800))
        ])),
        if (trailing != null) trailing!
      ]));
}

class ProgressLine extends StatelessWidget {
  const ProgressLine({super.key, required this.value});
  final double value;
  @override
  Widget build(BuildContext context) => ClipRRect(
      borderRadius: BorderRadius.circular(9),
      child: LinearProgressIndicator(
          value: value,
          minHeight: 6,
          backgroundColor: const Color(0xFFF0ECE5),
          color: AppTheme.red));
}

class HanziAvatar extends StatelessWidget {
  const HanziAvatar(this.text,
      {super.key, this.size = 52, this.color = const Color(0xFFE9F3ED)});
  final String text;
  final double size;
  final Color color;
  @override
  Widget build(BuildContext context) => Container(
      width: size,
      height: size,
      alignment: Alignment.center,
      decoration: BoxDecoration(
          color: color, borderRadius: BorderRadius.circular(size * .3)),
      child: Text(text,
          style: TextStyle(
              fontSize: size * .5,
              fontWeight: FontWeight.w700,
              color: AppTheme.jade)));
}
