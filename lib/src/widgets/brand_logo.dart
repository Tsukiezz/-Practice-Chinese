import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

/// Reusable, fail-safe brand logo for HanziGo.
/// Automatically handles web asset paths, root URL caching, and clean circular clipping.
class BrandLogo extends StatelessWidget {
  final double size;
  final BoxFit fit;
  final VoidCallback? onTap;

  const BrandLogo({
    super.key,
    this.size = 40,
    this.fit = BoxFit.contain,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    Widget imageWidget;

    if (kIsWeb) {
      // On Web, use direct root URL first for instantaneous native browser rendering & HTTP caching
      imageWidget = Image.network(
        '/logo.png',
        width: size,
        height: size,
        fit: fit,
        errorBuilder: (context, error, stackTrace) {
          return Image.asset(
            'assets/images/logo.png',
            width: size,
            height: size,
            fit: fit,
            errorBuilder: (context2, error2, stackTrace2) {
              return Image.network(
                '/admin/assets/logo.png',
                width: size,
                height: size,
                fit: fit,
                errorBuilder: (context3, error3, stackTrace3) {
                  return Container(
                    width: size,
                    height: size,
                    decoration: const BoxDecoration(
                      color: Color(0xFF153E35),
                      shape: BoxShape.circle,
                    ),
                    child: Center(
                      child: Text(
                        'H',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: size * 0.45,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  );
                },
              );
            },
          );
        },
      );
    } else {
      // On Mobile / Desktop, use standard Flutter AssetBundle
      imageWidget = Image.asset(
        'assets/images/logo.png',
        width: size,
        height: size,
        fit: fit,
        errorBuilder: (context, error, stackTrace) {
          return Container(
            width: size,
            height: size,
            decoration: const BoxDecoration(
              color: Color(0xFF153E35),
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Text(
                'H',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: size * 0.45,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          );
        },
      );
    }

    final content = ClipOval(
      child: SizedBox(
        width: size,
        height: size,
        child: imageWidget,
      ),
    );

    if (onTap != null) {
      return GestureDetector(
        onTap: onTap,
        child: content,
      );
    }
    return content;
  }
}
