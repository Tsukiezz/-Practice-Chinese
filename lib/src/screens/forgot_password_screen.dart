import 'dart:async';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../services/auth_service.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({
    super.key,
    required this.baseUrl,
    this.authService,
    this.initialEmail = '',
  });

  final String baseUrl;
  final AuthService? authService;
  final String initialEmail;

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final emailController = TextEditingController();
  final codeController = TextEditingController();
  final newPasswordController = TextEditingController();
  final confirmPasswordController = TextEditingController();

  final _client = http.Client();
  bool _submitting = false;
  String? _error;

  // Step 1: Enter email; Step 2: Enter code & new password
  int _step = 1;
  int _resendCountdown = 0;
  Timer? _countdownTimer;

  bool _obscureNewPassword = true;
  bool _obscureConfirmPassword = true;

  static const primary = Color(0xFF1B4D3E);
  static const background = Color(0xFFF6F7F4);
  static const textColor = Color(0xFF191C1B);
  static const outline = Color(0xFF707974);

  @override
  void initState() {
    super.initState();
    if (widget.initialEmail.isNotEmpty) {
      emailController.text = widget.initialEmail.trim();
    }
  }

  @override
  void dispose() {
    emailController.dispose();
    codeController.dispose();
    newPasswordController.dispose();
    confirmPasswordController.dispose();
    _countdownTimer?.cancel();
    _client.close();
    super.dispose();
  }

  void _startResendTimer() {
    _countdownTimer?.cancel();
    setState(() => _resendCountdown = 60);
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      if (_resendCountdown <= 1) {
        timer.cancel();
        setState(() => _resendCountdown = 0);
      } else {
        setState(() => _resendCountdown--);
      }
    });
  }

  InputDecoration inputDecoration({
    required String hint,
    required IconData icon,
    Widget? suffix,
  }) {
    return InputDecoration(
      counterText: '',
      hintText: hint,
      prefixIcon: Icon(icon, color: primary),
      suffixIcon: suffix,
      filled: true,
      fillColor: Colors.white,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: BorderSide(color: outline.withValues(alpha: .35)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: BorderSide(color: outline.withValues(alpha: .35)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: primary, width: 1.5),
      ),
    );
  }

  Future<void> _requestCode() async {
    final email = emailController.text.trim();
    if (!RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(email)) {
      setState(() => _error = 'Vui lòng nhập đúng định dạng email.');
      return;
    }

    setState(() {
      _submitting = true;
      _error = null;
    });

    try {
      final auth = widget.authService ?? await AuthService.load(_client);
      final msg = await auth.requestForgotPassword(
        baseUrl: widget.baseUrl,
        email: email,
      );
      if (mounted) {
        setState(() {
          _step = 2;
        });
        _startResendTimer();
      }
    } on AuthException catch (err) {
      if (mounted) setState(() => _error = err.message);
    } on Exception {
      if (mounted) {
        setState(() => _error = 'Không kết nối được máy chủ. Vui lòng thử lại.');
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  Future<void> _submitReset() async {
    final code = codeController.text.trim();
    final newPass = newPasswordController.text;
    final confirmPass = confirmPasswordController.text;

    if (code.length < 4) {
      setState(() => _error = 'Vui lòng nhập mã xác thực gồm 6 số.');
      return;
    }
    if (newPass.length < 8) {
      setState(() => _error = 'Mật khẩu mới phải có ít nhất 8 ký tự.');
      return;
    }
    if (newPass != confirmPass) {
      setState(() => _error = 'Mật khẩu xác nhận không khớp.');
      return;
    }

    setState(() {
      _submitting = true;
      _error = null;
    });

    try {
      final auth = widget.authService ?? await AuthService.load(_client);
      final msg = await auth.verifyForgotPassword(
        baseUrl: widget.baseUrl,
        email: emailController.text.trim(),
        code: code,
        newPassword: newPass,
      );

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          backgroundColor: primary,
          content: Text(msg),
          duration: const Duration(seconds: 4),
        ),
      );
      Navigator.pop(context, true);
    } on AuthException catch (err) {
      if (mounted) setState(() => _error = err.message);
    } on Exception {
      if (mounted) {
        setState(() => _error = 'Không thể đặt lại mật khẩu. Vui lòng thử lại.');
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: background,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 520),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const SizedBox(height: 10),
                  // Persistent Brand Logo Header
                  Center(
                    child: Container(
                      width: 68,
                      height: 68,
                      decoration: BoxDecoration(
                        color: primary,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: const Center(
                        child: Text(
                          '汉',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 34,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 18),
                  const Text(
                    'HanziGo · Hán Ngữ Xanh',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 30,
                      fontWeight: FontWeight.w800,
                      color: primary,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    _step == 1
                        ? 'Khôi phục mật khẩu tài khoản của bạn'
                        : 'Nhập mã xác thực đã gửi về email',
                    textAlign: TextAlign.center,
                    style: const TextStyle(fontSize: 15, color: outline),
                  ),
                  const SizedBox(height: 28),

                  if (_step == 1) ...[
                    const Text(
                      'Email tài khoản',
                      style: TextStyle(
                        fontWeight: FontWeight.w700,
                        color: textColor,
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      enabled: !_submitting,
                      controller: emailController,
                      keyboardType: TextInputType.emailAddress,
                      maxLength: 120,
                      decoration: inputDecoration(
                        hint: 'Nhập email đã đăng ký',
                        icon: Icons.email_outlined,
                      ),
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'Hệ thống sẽ gửi một mã xác thực (OTP) 6 chữ số đến hộp thư email của bạn.',
                      style: TextStyle(fontSize: 13, color: outline, height: 1.4),
                    ),
                    const SizedBox(height: 24),
                    SizedBox(
                      height: 54,
                      child: ElevatedButton(
                        onPressed: _submitting ? null : _requestCode,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: primary,
                          foregroundColor: Colors.white,
                          elevation: 0,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                        ),
                        child: const Text(
                          'Gửi mã xác thực',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                    ),
                  ] else ...[
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: const Color(0xFFE9F3ED),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: primary.withValues(alpha: .3)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.mark_email_read_outlined, color: primary),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              'Mã đã gửi đến ${emailController.text.trim()}',
                              style: const TextStyle(
                                color: primary,
                                fontWeight: FontWeight.w600,
                                fontSize: 13,
                              ),
                            ),
                          ),
                          TextButton(
                            onPressed: _submitting ? null : () => setState(() => _step = 1),
                            child: const Text('Đổi email'),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                    const Text(
                      'Mã xác thực (OTP)',
                      style: TextStyle(
                        fontWeight: FontWeight.w700,
                        color: textColor,
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      enabled: !_submitting,
                      controller: codeController,
                      keyboardType: TextInputType.number,
                      maxLength: 8,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 22,
                        letterSpacing: 6,
                        fontWeight: FontWeight.w800,
                        color: primary,
                      ),
                      decoration: inputDecoration(
                        hint: '6 chữ số',
                        icon: Icons.lock_clock_outlined,
                      ),
                    ),
                    const SizedBox(height: 18),
                    const Text(
                      'Mật khẩu mới',
                      style: TextStyle(
                        fontWeight: FontWeight.w700,
                        color: textColor,
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      enabled: !_submitting,
                      controller: newPasswordController,
                      maxLength: 128,
                      obscureText: _obscureNewPassword,
                      decoration: inputDecoration(
                        hint: 'Nhập mật khẩu mới (ít nhất 8 ký tự)',
                        icon: Icons.lock_outline_rounded,
                        suffix: IconButton(
                          onPressed: () {
                            setState(() => _obscureNewPassword = !_obscureNewPassword);
                          },
                          icon: Icon(
                            _obscureNewPassword
                                ? Icons.visibility_off_outlined
                                : Icons.visibility_outlined,
                            color: outline,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 18),
                    const Text(
                      'Xác nhận mật khẩu mới',
                      style: TextStyle(
                        fontWeight: FontWeight.w700,
                        color: textColor,
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      enabled: !_submitting,
                      controller: confirmPasswordController,
                      maxLength: 128,
                      obscureText: _obscureConfirmPassword,
                      decoration: inputDecoration(
                        hint: 'Nhập lại mật khẩu mới',
                        icon: Icons.lock_reset_outlined,
                        suffix: IconButton(
                          onPressed: () {
                            setState(() =>
                                _obscureConfirmPassword = !_obscureConfirmPassword);
                          },
                          icon: Icon(
                            _obscureConfirmPassword
                                ? Icons.visibility_off_outlined
                                : Icons.visibility_outlined,
                            color: outline,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 10),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Chưa nhận được mã?',
                          style: TextStyle(fontSize: 13, color: outline),
                        ),
                        TextButton(
                          onPressed: _resendCountdown > 0 || _submitting
                              ? null
                              : _requestCode,
                          child: Text(
                            _resendCountdown > 0
                                ? 'Gửi lại sau (${_resendCountdown}s)'
                                : 'Gửi lại mã OTP',
                            style: TextStyle(
                              color: _resendCountdown > 0 ? outline : primary,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),
                    SizedBox(
                      height: 54,
                      child: ElevatedButton(
                        onPressed: _submitting ? null : _submitReset,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: primary,
                          foregroundColor: Colors.white,
                          elevation: 0,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                        ),
                        child: const Text(
                          'Đặt lại mật khẩu',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                    ),
                  ],

                  const SizedBox(height: 16),
                  if (_error != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Text(
                        _error!,
                        style: const TextStyle(color: Colors.red, fontWeight: FontWeight.w600),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  if (_submitting)
                    const Padding(
                      padding: EdgeInsets.only(bottom: 12),
                      child: LinearProgressIndicator(),
                    ),

                  TextButton(
                    onPressed: _submitting ? null : () => Navigator.pop(context),
                    child: const Text(
                      '← Quay lại Đăng nhập',
                      style: TextStyle(color: textColor, fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
