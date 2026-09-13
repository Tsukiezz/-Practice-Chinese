import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../services/auth_service.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key, required this.baseUrl, this.authService});
  final String baseUrl;
  final AuthService? authService;

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final nameController = TextEditingController();
  final emailController = TextEditingController();
  final passwordController = TextEditingController();
  final confirmPasswordController = TextEditingController();

  final _client = http.Client();
  bool _submitting = false;
  String? _error;
  bool obscurePassword = true;
  bool obscureConfirmPassword = true;
  bool acceptTerms = false;

  static const primary = Color(0xFF1B4D3E);
  static const secondary = Color(0xFFE2C391);
  static const accent = Color(0xFFD97706);
  static const background = Color(0xFFF6F7F4);
  static const textColor = Color(0xFF191C1B);
  static const outline = Color(0xFF707974);

  @override
  void dispose() {
    nameController.dispose();
    emailController.dispose();
    passwordController.dispose();
    confirmPasswordController.dispose();
    _client.close();
    super.dispose();
  }

  InputDecoration inputDecoration({
    required String hint,
    required IconData icon,
    Widget? suffix,
  }) {
    return InputDecoration(
      counterText: '',
      hintText: hint,
      labelText: switch (hint) {
        'Nhập email' => 'Email',
        'Nhập mật khẩu' || 'Tạo mật khẩu' => 'Mật khẩu',
        'Nhập họ và tên' => 'Họ và tên',
        'Nhập lại mật khẩu' => 'Xác nhận mật khẩu',
        _ => hint,
      },
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

  Future<void> _submit() async {
    if (_submitting || !acceptTerms) return;
    final email = emailController.text.trim();
    String? error;
    if (nameController.text.trim().length < 2) {
      error = 'Họ tên cần ít nhất 2 ký tự.';
    } else if (!RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(email)) {
      error = 'Email không hợp lệ.';
    } else if (passwordController.text.length < 8) {
      error = 'Mật khẩu cần ít nhất 8 ký tự.';
    } else if (passwordController.text != confirmPasswordController.text) {
      error = 'Mật khẩu xác nhận không khớp.';
    }
    if (error != null) {
      setState(() => _error = error);
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      final auth = widget.authService ?? await AuthService.load(_client);
      await auth.register(
          baseUrl: widget.baseUrl,
          name: nameController.text.trim(),
          email: email,
          password: passwordController.text);
      if (mounted) Navigator.pop(context, true);
    } on AuthException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } on Exception {
      if (mounted) {
        setState(
            () => _error = 'Không kết nối được máy chủ. Vui lòng thử lại.');
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
                  Container(
                    width: 68,
                    height: 68,
                    decoration: BoxDecoration(
                      color: primary,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Icon(
                      Icons.menu_book_rounded,
                      color: Colors.white,
                      size: 34,
                    ),
                  ),
                  const SizedBox(height: 18),
                  const Text(
                    'HanziGo · Hán Ngữ Xanh',
                    style: TextStyle(
                      fontSize: 30,
                      fontWeight: FontWeight.w800,
                      color: primary,
                    ),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Tạo tài khoản và bắt đầu học tiếng Trung',
                    style: TextStyle(fontSize: 15, color: outline),
                  ),
                  const SizedBox(height: 28),
                  Container(
                    padding: const EdgeInsets.all(4),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: TextButton(
                            onPressed: _submitting
                                ? null
                                : () => Navigator.pop(context),
                            child: const Text(
                              'Đăng nhập',
                              style: TextStyle(
                                color: textColor,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ),
                        Expanded(
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            decoration: BoxDecoration(
                              color: primary,
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: const Center(
                              child: Text(
                                'Đăng ký mới',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 28),
                  const Text(
                    'Họ và tên',
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      color: textColor,
                    ),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    enabled: !_submitting,
                    controller: nameController,
                    maxLength: 60,
                    textCapitalization: TextCapitalization.words,
                    decoration: inputDecoration(
                      hint: 'Nhập họ và tên',
                      icon: Icons.person_outline_rounded,
                    ),
                  ),
                  const SizedBox(height: 18),
                  const Text(
                    'Email',
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      color: textColor,
                    ),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    enabled: !_submitting,
                    controller: emailController,
                    autofillHints: const [AutofillHints.email],
                    maxLength: 120,
                    keyboardType: TextInputType.emailAddress,
                    decoration: inputDecoration(
                      hint: 'Nhập email',
                      icon: Icons.alternate_email_rounded,
                    ),
                  ),
                  const SizedBox(height: 18),
                  const Text(
                    'Mật khẩu',
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      color: textColor,
                    ),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    enabled: !_submitting,
                    controller: passwordController,
                    autofillHints: const [AutofillHints.password],
                    maxLength: 128,
                    obscureText: obscurePassword,
                    decoration: inputDecoration(
                      hint: 'Tạo mật khẩu',
                      icon: Icons.lock_outline_rounded,
                      suffix: IconButton(
                        onPressed: () {
                          setState(() => obscurePassword = !obscurePassword);
                        },
                        icon: Icon(
                          obscurePassword
                              ? Icons.visibility_off_outlined
                              : Icons.visibility_outlined,
                          color: outline,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 18),
                  const Text(
                    'Xác nhận mật khẩu',
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
                    obscureText: obscureConfirmPassword,
                    decoration: inputDecoration(
                      hint: 'Nhập lại mật khẩu',
                      icon: Icons.lock_reset_outlined,
                      suffix: IconButton(
                        onPressed: () {
                          setState(
                            () => obscureConfirmPassword =
                                !obscureConfirmPassword,
                          );
                        },
                        icon: Icon(
                          obscureConfirmPassword
                              ? Icons.visibility_off_outlined
                              : Icons.visibility_outlined,
                          color: outline,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),
                  CheckboxListTile(
                    value: acceptTerms,
                    activeColor: primary,
                    contentPadding: EdgeInsets.zero,
                    controlAffinity: ListTileControlAffinity.leading,
                    title: const Text(
                      'Tôi đồng ý tạo tài khoản và lưu tiến trình học.',
                      style: TextStyle(
                        fontSize: 13,
                        height: 1.4,
                        color: textColor,
                      ),
                    ),
                    onChanged: _submitting
                        ? null
                        : (value) {
                            setState(() => acceptTerms = value ?? false);
                          },
                  ),
                  const SizedBox(height: 12),
                  if (_error != null)
                    Padding(
                        padding: const EdgeInsets.only(bottom: 12),
                        child: Semantics(
                            liveRegion: true,
                            child: Text(_error!,
                                style: const TextStyle(color: Colors.red)))),
                  if (_submitting)
                    const Padding(
                        padding: EdgeInsets.only(bottom: 12),
                        child: LinearProgressIndicator()),
                  SizedBox(
                    height: 54,
                    child: ElevatedButton(
                      onPressed: acceptTerms && !_submitting ? _submit : null,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: primary,
                        disabledBackgroundColor: outline.withValues(alpha: .25),
                        foregroundColor: Colors.white,
                        elevation: 0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                      ),
                      child: const Text(
                        'Tạo tài khoản',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),
                  Container(
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      color: secondary.withValues(alpha: .35),
                      borderRadius: BorderRadius.circular(18),
                    ),
                    child: const Row(
                      children: [
                        Icon(
                          Icons.local_fire_department_rounded,
                          color: accent,
                          size: 30,
                        ),
                        SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Học tiếng Trung mỗi ngày',
                                style: TextStyle(
                                  fontWeight: FontWeight.w800,
                                  color: textColor,
                                ),
                              ),
                              SizedBox(height: 4),
                              Text(
                                'Khởi động thói quen học tiếng Trung mỗi ngày.',
                                style: TextStyle(
                                  fontSize: 13,
                                  color: outline,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
                  Wrap(
                    alignment: WrapAlignment.center,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: [
                      const Text(
                        'Đã có tài khoản? ',
                        style: TextStyle(color: outline),
                      ),
                      TextButton(
                        onPressed:
                            _submitting ? null : () => Navigator.pop(context),
                        child: const Text(
                          'Đăng nhập',
                          style: TextStyle(
                            color: primary,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                    ],
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
