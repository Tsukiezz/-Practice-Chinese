import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../services/auth_service.dart';
import '../services/google_auth_service.dart';
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

    final bluePaint = Paint()
      ..color = const Color(0xFF4285F4)
      ..style = PaintingStyle.fill;
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

/// Nút bấm Đăng nhập bằng Google tiêu chuẩn kết nối trực tiếp với tài khoản Google
class GoogleSignInButton extends StatefulWidget {
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

  @override
  State<GoogleSignInButton> createState() => _GoogleSignInButtonState();
}

class _GoogleSignInButtonState extends State<GoogleSignInButton> {
  bool _connecting = false;
  static const primary = Color(0xFF1B4D3E);
  static const outline = Color(0xFF707974);

  Future<void> _handleTap() async {
    if (_connecting) return;
    setState(() => _connecting = true);

    try {
      final auth = widget.authService ?? await AuthService.load(http.Client());
      final config = await auth.fetchGoogleConfig(widget.baseUrl);
      String clientId = (config['client_id'] ?? '').toString().trim();

      // Nếu chưa có Google Client ID, mở hộp thoại hướng dẫn / nhập nhanh Client ID
      if (clientId.isEmpty) {
        if (!mounted) return;
        final enteredClientId = await showDialog<String>(
          context: context,
          barrierDismissible: true,
          builder: (ctx) => const Theme(
            data: AppTheme.light,
            child: _GoogleClientIdDialog(),
          ),
        );

        if (enteredClientId == null || enteredClientId.trim().isEmpty) {
          setState(() => _connecting = false);
          return;
        }
        clientId = enteredClientId.trim();
      }

      // Kích hoạt popup đăng nhập thực tế của Google (accounts.google.com)
      final googleResult = await triggerGoogleWebSignIn(clientId);

      if (!mounted) return;

      if (!googleResult.success) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(googleResult.error ?? 'Đăng nhập Google đã bị hủy.'),
            backgroundColor: const Color(0xFF991B1B),
            behavior: SnackBarBehavior.floating,
          ),
        );
        setState(() => _connecting = false);
        return;
      }

      // Khi Google đã xác nhận danh tính thành công:
      // Mở hộp thoại cho khách tự do chọn tên hiển thị của mình
      final completed = await showDialog<bool>(
        context: context,
        barrierDismissible: false,
        builder: (ctx) => Theme(
          data: AppTheme.light,
          child: GoogleNameSelectionDialog(
            baseUrl: widget.baseUrl,
            authService: widget.authService,
            googleEmail: googleResult.email,
            suggestedName: googleResult.name,
            avatar: googleResult.avatar,
            accessToken: googleResult.accessToken,
            googleId: googleResult.googleId,
          ),
        ),
      );

      if (completed == true) {
        widget.onSuccess();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Lỗi kết nối Google: $e'),
            backgroundColor: const Color(0xFF991B1B),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _connecting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 52,
      child: OutlinedButton(
        onPressed: _connecting ? null : _handleTap,
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
        child: _connecting
            ? const SizedBox(
                width: 22,
                height: 22,
                child: CircularProgressIndicator(
                  strokeWidth: 2.2,
                  valueColor: AlwaysStoppedAnimation<Color>(primary),
                ),
              )
            : Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const GoogleLogo(size: 22),
                  const SizedBox(width: 12),
                  Text(
                    widget.label,
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

/// Hộp thoại cấu hình Google Client ID nếu môi trường chưa cài đặt
class _GoogleClientIdDialog extends StatefulWidget {
  const _GoogleClientIdDialog();

  @override
  State<_GoogleClientIdDialog> createState() => _GoogleClientIdDialogState();
}

class _GoogleClientIdDialogState extends State<_GoogleClientIdDialog> {
  final _ctrl = TextEditingController();
  static const primary = Color(0xFF1B4D3E);
  static const textColor = Color(0xFF191C1B);
  static const outline = Color(0xFF707974);

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 460),
        child: Padding(
          padding: const EdgeInsets.all(22),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  const GoogleLogo(size: 24),
                  const SizedBox(width: 12),
                  const Expanded(
                    child: Text(
                      'Kết nối Google OAuth 2.0',
                      style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800, color: textColor),
                    ),
                  ),
                  IconButton(
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(Icons.close_rounded, color: outline),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFFFEF3C7),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFFF59E0B).withValues(alpha: .4)),
                ),
                child: const Text(
                  'Hệ thống chưa tìm thấy biến GOOGLE_CLIENT_ID trên máy chủ. Bạn có thể nhập Google Client ID tại đây để kết nối với Google ngay lập tức:',
                  style: TextStyle(fontSize: 13, color: Color(0xFF92400E), height: 1.4),
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                'Google Client ID (Web Application)',
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: textColor),
              ),
              const SizedBox(height: 6),
              TextField(
                controller: _ctrl,
                style: const TextStyle(fontSize: 13.5, color: textColor),
                decoration: InputDecoration(
                  hintText: 'xxxxxx.apps.googleusercontent.com',
                  hintStyle: TextStyle(color: outline.withValues(alpha: .6), fontSize: 13),
                  filled: true,
                  fillColor: const Color(0xFFF9FAF8),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
              const SizedBox(height: 18),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('Hủy'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: primary, foregroundColor: Colors.white),
                      onPressed: () {
                        if (_ctrl.text.trim().isNotEmpty) {
                          Navigator.pop(context, _ctrl.text.trim());
                        }
                      },
                      child: const Text('Mở popup Google'),
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
}

/// Hộp thoại SAU KHI GOOGLE ĐÃ XÁC THỰC DANH TÍNH:
/// Cho phép khách hàng tự do chọn/đổi tên hiển thị của mình trên HanziGo
class GoogleNameSelectionDialog extends StatefulWidget {
  const GoogleNameSelectionDialog({
    super.key,
    required this.baseUrl,
    this.authService,
    required this.googleEmail,
    required this.suggestedName,
    this.avatar,
    this.accessToken,
    this.googleId,
  });

  final String baseUrl;
  final AuthService? authService;
  final String googleEmail;
  final String suggestedName;
  final String? avatar;
  final String? accessToken;
  final String? googleId;

  @override
  State<GoogleNameSelectionDialog> createState() => _GoogleNameSelectionDialogState();
}

class _GoogleNameSelectionDialogState extends State<GoogleNameSelectionDialog> {
  late final TextEditingController _nameController;
  final _client = http.Client();
  bool _submitting = false;
  String? _error;
  bool _remember = true;

  static const primary = Color(0xFF1B4D3E);
  static const textColor = Color(0xFF191C1B);
  static const outline = Color(0xFF707974);

  @override
  void initState() {
    super.initState();
    // Tự động điền tên nhận được từ Google nhưng cho khách toàn quyền chỉnh sửa
    _nameController = TextEditingController(text: widget.suggestedName);
  }

  @override
  void dispose() {
    _nameController.dispose();
    _client.close();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_submitting) return;

    final chosenName = _nameController.text.trim();
    if (chosenName.isEmpty) {
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
        email: widget.googleEmail,
        name: chosenName,
        accessToken: widget.accessToken,
        avatar: widget.avatar,
        googleId: widget.googleId,
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
              // Header với logo Google và xác nhận tài khoản
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
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Google đã xác nhận danh tính',
                          style: TextStyle(
                            fontSize: 17,
                            fontWeight: FontWeight.w800,
                            color: textColor,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          widget.googleEmail,
                          style: const TextStyle(
                            fontSize: 12.5,
                            fontWeight: FontWeight.w600,
                            color: primary,
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
              const SizedBox(height: 16),

              // Banner xác nhận từ Google và quyền tự chọn tên
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFFE9F3ED),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: primary.withValues(alpha: .2)),
                ),
                child: const Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.verified_user_rounded, color: primary, size: 22),
                    SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Bạn được tự do chọn tên của mình!',
                            style: TextStyle(
                              fontSize: 13.5,
                              fontWeight: FontWeight.w700,
                              color: primary,
                            ),
                          ),
                          SizedBox(height: 3),
                          Text(
                            'Bên Google đã xác nhận quyền đăng nhập. Hãy chọn tên bạn muốn hiển thị trên chứng chỉ bài thi, bảng xếp hạng và hồ sơ học tập.',
                            style: TextStyle(
                              fontSize: 12,
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

              // Trường nhập tên hiển thị tự chọn
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
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: primary.withValues(alpha: .08),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Text(
                      'Khách tự chọn tên',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: primary,
                      ),
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
                  hintText: 'Nhập tên hiển thị bạn muốn...',
                  hintStyle: TextStyle(color: outline.withValues(alpha: .6), fontSize: 14),
                  prefixIcon: const Icon(Icons.badge_outlined, color: primary, size: 20),
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

              // Ghi nhớ đăng nhập
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
