import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class ScreenHeader extends StatelessWidget {
  const ScreenHeader({
    super.key,
    required this.eyebrow,
    required this.title,
    this.trailing,
    this.onBack,
    this.showBackButton,
  });

  final String eyebrow, title;
  final Widget? trailing;
  final VoidCallback? onBack;
  final bool? showBackButton;

  @override
  Widget build(BuildContext context) {
    final canPop = showBackButton ?? (onBack != null || Navigator.of(context).canPop());
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          if (canPop) ...[
            Material(
              color: Colors.transparent,
              child: InkWell(
                onTap: onBack ?? () => Navigator.of(context).maybePop(),
                borderRadius: BorderRadius.circular(12),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFFD4E2DA)),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF1B4D3E).withOpacity(0.06),
                        blurRadius: 6,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.arrow_back_rounded,
                        color: AppTheme.jade,
                        size: 18,
                      ),
                      SizedBox(width: 4),
                      Text(
                        'Quay lại',
                        style: TextStyle(
                          color: AppTheme.jade,
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                          decoration: TextDecoration.none,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(width: 10),
          ],
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  eyebrow.toUpperCase(),
                  style: const TextStyle(
                    color: AppTheme.jade,
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.2,
                    decoration: TextDecoration.none,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  title,
                  style: const TextStyle(
                    color: AppTheme.ink,
                    fontSize: 26,
                    fontWeight: FontWeight.w800,
                    letterSpacing: -0.5,
                    decoration: TextDecoration.none,
                  ),
                ),
              ],
            ),
          ),
          if (trailing != null) trailing!,
        ],
      ),
    );
  }
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
              decoration: TextDecoration.none,
              color: AppTheme.jade)));
}
