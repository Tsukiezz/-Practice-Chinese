import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../services/auth_service.dart';
import '../theme/app_theme.dart';

/// Official 4-color Google 'G' Logo
class GoogleLogo extends StatelessWidget {
  const GoogleLogo({super.key, this.size = 22});
  final double size;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: CustomPaint(
        painter: _GoogleLogoPainter(),
      ),
    );
  }
}

class _GoogleLogoPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final double w = size.width;
    final double h = size.height;
    final center = Offset(w / 2, h / 2);
    final radius = w / 2;

    // Paints for Google 4 brand colors
    final bluePaint = Paint()
      ..color = const Color(0xFF4285F4)
      ..style = PaintingStyle.fill;
    final redPaint = Paint()
      ..color = const Color(0xFFEA4335)
      ..style = PaintingStyle.fill;
    final yellowPaint = Paint()
      ..color = const Color(0xFFFBBC05)
      ..style = PaintingStyle.fill;
    final greenPaint = Paint()
      ..color = const Color(0xFF34A853)
      ..style = PaintingStyle.fill;

    // Draw stylized multi-colored Google 'G'
    final strokeWidth = w * 0.22;
    final ringPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.butt;

    final rect = Rect.fromCircle(center: center, radius: radius - strokeWidth / 2);

    // Blue arc & bar
    ringPaint.color = const Color(0xFF4285F4);
    canvas.drawArc(rect, -0.6, 1.2, false, ringPaint);

    // Green bottom arc
    ringPaint.color = const Color(0xFF34A853);
    canvas.drawArc(rect, 0.6, 1.3, false, ringPaint);

    // Yellow left arc
    ringPaint.color = const Color(0xFFFBBC05);
    canvas.drawArc(rect, 1.9, 1.3, false, ringPaint);

    // Red top arc
    ringPaint.color = const Color(0xFFEA4335);
    canvas.drawArc(rect, 3.2, 1.2, false, ringPaint);

    // Blue horizontal bar
    final barRect = RRect.fromRectAndRadius(
      Rect.fromLTRB(w * 0.45, h * 0.40, w * 0.95, h * 0.60),
      Radius.circular(w * 0.05),
    );
    canvas.drawRRect(barRect, bluePaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

/// Nút bấm Đăng nhập bằng Google tiêu chuẩn
class GoogleSignInButton extends StatelessWidget {
  const GoogleSignInButton({
    super.key,
    required this.baseUrl,
    this.authService,
    required this.onSuccess,
    this.label = 'Tiếp tục với Google',
  });

  final String baseUrl;
  final AuthService? authService;
  final VoidCallback onSuccess;
  final String label;

  static const primary = Color(0xFF1B4D3E);
  static const outline = Color(0xFF707974);

  Future<void> _handleTap(BuildContext context) async {
    final result = await showDialog<bool>(
      context: context,
      barrierDismissible: true,
      builder: (dialogCtx) => Theme(
        data: AppTheme.light,
        child: GoogleSignInDialog(
          baseUrl: baseUrl,
          authService: authService,
        ),
      ),
    );
    if (result == true) {
      onSuccess();
    }
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 52,
      child: OutlinedButton(
        onPressed: () => _handleTap(context),
        style: OutlinedButton.styleFrom(
          backgroundColor: Colors.white,
          foregroundColor: const Color(0xFF1F1F1F),
          side: BorderSide(color: outline.withValues(alpha: .35), width: 1.2),
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 16),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const GoogleLogo(size: 22),
            const SizedBox(width: 12),
            Text(
              label,
              style: const TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w700,
                color: Color(0xFF1F1F1F),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Hộp thoại hoàn tất đăng nhập Google cho phép khách hàng tự do chọn tên hiển thị của mình
class GoogleSignInDialog extends StatefulWidget {
  const GoogleSignInDialog({
    super.key,
    required this.baseUrl,
    this.authService,
    this.initialEmail,
    this.initialName,
  });

  final String baseUrl;
  final AuthService? authService;
  final String? initialEmail;
  final String? initialName;

  @override
  State<GoogleSignInDialog> createState() => _GoogleSignInDialogState();
}

class _GoogleSignInDialogState extends State<GoogleSignInDialog> {
  late final TextEditingController _emailController;
  late final TextEditingController _nameController;
  final _client = http.Client();

  bool _submitting = false;
  String? _error;
  bool _remember = true;

  static const primary = Color(0xFF1B4D3E);
  static const secondary = Color(0xFFE2C391);
  static const textColor = Color(0xFF191C1B);
  static const outline = Color(0xFF707974);

  @override
  void initState() {
    super.initState();
    _emailController = TextEditingController(text: widget.initialEmail ?? '');
    _nameController = TextEditingController(text: widget.initialName ?? '');

    _emailController.addListener(_onEmailChanged);
  }

  void _onEmailChanged() {
    // Nếu người dùng chưa gõ tên, tự động gợi ý tên từ email để người dùng tiện chỉnh sửa
    if (_nameController.text.trim().isEmpty) {
      final email = _emailController.text.trim();
      if (email.contains('@')) {
        final prefix = email.split('@').first;
        final formatted = prefix.replaceAll(RegExp(r'[._]'), ' ').trim();
        if (formatted.isNotEmpty) {
          final words = formatted.split(' ').map((w) => w.isNotEmpty ? '${w[0].toUpperCase()}${w.substring(1)}' : '').join(' ');
          setState(() {
            _nameController.text = words;
          });
        }
      }
    }
  }

  @override
  void dispose() {
    _emailController.removeListener(_onEmailChanged);
    _emailController.dispose();
    _nameController.dispose();
    _client.close();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_submitting) return;

    final email = _emailController.text.trim();
    final name = _nameController.text.trim();

    if (!RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(email)) {
      setState(() => _error = 'Vui lòng nhập địa chỉ email Google hợp lệ.');
      return;
    }

    if (name.isEmpty) {
      setState(() => _error = 'Vui lòng nhập tên bạn muốn hiển thị trên ứng dụng.');
      return;
    }

    setState(() {
      _submitting = true;
      _error = null;
    });

    try {
      final auth = widget.authService ?? await AuthService.load(_client);
      final user = await auth.loginWithGoogle(
        baseUrl: widget.baseUrl,
        email: email,
        name: name,
        remember: _remember,
      );

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('🎉 Chào mừng ${user.name} đã đăng nhập thành công!'),
          backgroundColor: primary,
          behavior: SnackBarBehavior.floating,
        ),
      );
      Navigator.pop(context, true);
    } on AuthException catch (err) {
      if (mounted) setState(() => _error = err.message);
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Không thể kết nối máy chủ. Vui lòng thử lại.');
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: Colors.white,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 480),
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 22),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Header với logo Google
              Row(
                children: [
                  Container(
                    width: 44,
                    height: 44,
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      shape: BoxShape.circle,
                      border: Border.all(color: outline.withValues(alpha: .2)),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: .04),
                          blurRadius: 8,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: const GoogleLogo(size: 24),
                  ),
                  const SizedBox(width: 14),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Đăng nhập với Google',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w800,
                            color: textColor,
                          ),
                        ),
                        SizedBox(height: 2),
                        Text(
                          'Kết nối tài khoản Google nhanh chóng & an toàn',
                          style: TextStyle(
                            fontSize: 12,
                            color: outline,
                          ),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    onPressed: _submitting ? null : () => Navigator.pop(context, false),
                    icon: const Icon(Icons.close_rounded, color: outline),
                  ),
                ],
              ),
              const SizedBox(height: 18),

              // Banner thông báo đặc quyền tự chọn tên
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFFE9F3ED),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: primary.withValues(alpha: .2)),
                ),
                child: const Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.badge_outlined, color: primary, size: 22),
                    SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Bạn có thể tự do đặt tên cho mình!',
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w700,
                              color: primary,
                            ),
                          ),
                          SizedBox(height: 2),
                          Text(
                            'Tên này sẽ hiển thị trên bảng xếp hạng, chứng chỉ bài thi và hồ sơ học tập của bạn.',
                            style: TextStyle(
                              fontSize: 11.5,
                              color: primary,
                              height: 1.35,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Input Email Google
              const Text(
                'Email Google của bạn (*)',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: textColor,
                ),
              ),
              const SizedBox(height: 6),
              TextField(
                controller: _emailController,
                enabled: !_submitting,
                keyboardType: TextInputType.emailAddress,
                style: const TextStyle(color: textColor, fontSize: 14.5),
                decoration: InputDecoration(
                  hintText: 'vidu@gmail.com',
                  hintStyle: TextStyle(color: outline.withValues(alpha: .6), fontSize: 14),
                  prefixIcon: const Icon(Icons.alternate_email_rounded, color: primary, size: 20),
                  filled: true,
                  fillColor: const Color(0xFFF9FAF8),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide(color: outline.withValues(alpha: .3)),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide(color: outline.withValues(alpha: .3)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: const BorderSide(color: primary, width: 1.5),
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Input Tên hiển thị (Khách tự chọn tên của mình)
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Tên hiển thị của bạn (*)',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: textColor,
                    ),
                  ),
                  Text(
                    'Khách tự chọn tên',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: primary.withValues(alpha: .85),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              TextField(
                controller: _nameController,
                enabled: !_submitting,
                maxLength: 60,
                textCapitalization: TextCapitalization.words,
                style: const TextStyle(color: textColor, fontSize: 15, fontWeight: FontWeight.w600),
                decoration: InputDecoration(
                  counterText: '',
                  hintText: 'Nhập tên bạn muốn dùng (VD: Minh Thư, Alex...)',
                  hintStyle: TextStyle(color: outline.withValues(alpha: .6), fontSize: 14),
                  prefixIcon: const Icon(Icons.person_outline_rounded, color: primary, size: 20),
                  filled: true,
                  fillColor: const Color(0xFFF9FAF8),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide(color: outline.withValues(alpha: .3)),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide(color: outline.withValues(alpha: .3)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: const BorderSide(color: primary, width: 1.5),
                  ),
                ),
              ),
              const SizedBox(height: 12),

              // Gợi ý tên nhanh
              Wrap(
                spacing: 6,
                runSpacing: 6,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  const Text('Gợi ý: ', style: TextStyle(fontSize: 11.5, color: outline)),
                  _buildNameChip('Tiểu Long'),
                  _buildNameChip('Bảo Nam'),
                  _buildNameChip('Minh Thư'),
                  _buildNameChip('Alex'),
                ],
              ),
              const SizedBox(height: 14),

              // Checkbox Ghi nhớ
              CheckboxListTile(
                value: _remember,
                activeColor: primary,
                contentPadding: EdgeInsets.zero,
                controlAffinity: ListTileControlAffinity.leading,
                dense: true,
                title: const Text(
                  'Ghi nhớ đăng nhập trên thiết bị này',
                  style: TextStyle(fontSize: 13, color: textColor),
                ),
                onChanged: _submitting ? null : (v) => setState(() => _remember = v ?? true),
              ),

              if (_error != null) ...[
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFDE8E8),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFFF98080)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline_rounded, color: Color(0xFFC81E1E), size: 18),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _error!,
                          style: const TextStyle(color: Color(0xFF9B1C1C), fontSize: 12.5),
                        ),
                      ),
                    ],
                  ),
                ),
              ],

              if (_submitting) ...[
                const SizedBox(height: 14),
                const LinearProgressIndicator(color: primary),
              ],

              const SizedBox(height: 18),

              // Action Buttons
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: _submitting ? null : () => Navigator.pop(context, false),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: textColor,
                        side: BorderSide(color: outline.withValues(alpha: .3)),
                        padding: const EdgeInsets.symmetric(vertical: 13),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      child: const Text('Hủy', style: TextStyle(fontWeight: FontWeight.w600)),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: ElevatedButton.icon(
                      onPressed: _submitting ? null : _submit,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: primary,
                        foregroundColor: Colors.white,
                        elevation: 0,
                        padding: const EdgeInsets.symmetric(vertical: 13),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      icon: const Icon(Icons.check_circle_outline_rounded, size: 18),
                      label: const Text(
                        'Xác nhận & Vào học',
                        style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildNameChip(String suggestion) {
    return InkWell(
      onTap: _submitting
          ? null
          : () {
              setState(() {
                _nameController.text = suggestion;
              });
            },
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: const Color(0xFFF4F6F4),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: outline.withValues(alpha: .2)),
        ),
        child: Text(
          suggestion,
          style: const TextStyle(fontSize: 11.5, color: primary, fontWeight: FontWeight.w600),
        ),
      ),
    );
  }
}
