import 'guest_dictionary_screen.dart';
import '../services/web_navigation.dart';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../services/auth_service.dart';
import 'register_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({
    super.key,
    required this.baseUrl,
    this.authService,
    required this.onLoginSuccess,
  });
  final String baseUrl;
  final AuthService? authService;
  final VoidCallback onLoginSuccess;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final emailController = TextEditingController();
  final passwordController = TextEditingController();

  final _client = http.Client();
  bool _submitting = false;
  String? _error;
  bool obscurePassword = true;
  bool rememberLogin = true;

  static const primary = Color(0xFF1B4D3E);
  static const secondary = Color(0xFFE2C391);
  static const accent = Color(0xFFD97706);
  static const background = Color(0xFFF6F7F4);
  static const textColor = Color(0xFF191C1B);
  static const outline = Color(0xFF707974);

  @override
  void dispose() {
    emailController.dispose();
    passwordController.dispose();
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

  Future<void> _openRegister() async {
    final success = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (_) => RegisterScreen(
          baseUrl: widget.baseUrl,
          authService: widget.authService,
        ),
      ),
    );
    if (success == true && mounted) widget.onLoginSuccess();
  }

  Future<void> _submit() async {
    if (_submitting) return;
    final email = emailController.text.trim();
    if (!RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(email) ||
        passwordController.text.isEmpty) {
      setState(() => _error = 'Nhập email hợp lệ và mật khẩu.');
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      final auth = widget.authService ?? await AuthService.load(_client);
      await auth.login(
        baseUrl: widget.baseUrl,
        email: email,
        password: passwordController.text,
        remember: rememberLogin,
      );
      if (mounted) widget.onLoginSuccess();
    } on AuthException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } on Exception {
      if (mounted) {
        setState(
          () => _error = 'Không kết nối được máy chủ. Vui lòng thử lại.',
        );
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
                    'Học tiếng Trung theo cách đơn giản và hiệu quả',
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
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            decoration: BoxDecoration(
                              color: primary,
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: const Center(
                              child: Text(
                                'Đăng nhập',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                          ),
                        ),
                        Expanded(
                          child: TextButton(
                            onPressed: _submitting ? null : _openRegister,
                            child: const Text(
                              'Đăng ký mới',
                              style: TextStyle(
                                color: textColor,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 28),
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
                      icon: Icons.person_outline_rounded,
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
                      hint: 'Nhập mật khẩu',
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
                  if (kIsWeb)
                    Align(
                      alignment: Alignment.centerRight,
                      child: TextButton(
                        onPressed: _submitting ? null : openRecovery,
                        child: const Text('Quên mật khẩu?'),
                      ),
                    ),
                  CheckboxListTile(
                    value: rememberLogin,
                    activeColor: primary,
                    contentPadding: EdgeInsets.zero,
                    controlAffinity: ListTileControlAffinity.leading,
                    title: const Text('Ghi nhớ đăng nhập'),
                    onChanged: _submitting
                        ? null
                        : (value) {
                            setState(() => rememberLogin = value ?? false);
                          },
                  ),
                  const SizedBox(height: 12),
                  if (_error != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Semantics(
                        liveRegion: true,
                        child: Text(
                          _error!,
                          style: const TextStyle(color: Colors.red),
                        ),
                      ),
                    ),
                  if (_submitting)
                    const Padding(
                      padding: EdgeInsets.only(bottom: 12),
                      child: LinearProgressIndicator(),
                    ),
                  SizedBox(
                    height: 54,
                    child: ElevatedButton(
                      onPressed: _submitting ? null : _submit,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: primary,
                        foregroundColor: Colors.white,
                        elevation: 0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                      ),
                      child: const Text(
                        'Đăng nhập',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    child: OutlinedButton.icon(
                      onPressed: _submitting
                          ? null
                          : () => Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (_) => GuestDictionaryScreen(
                                  baseUrl: widget.baseUrl,
                                ),
                              ),
                            ),
                      icon: const Icon(Icons.travel_explore_rounded),
                      label: const Text('Tiếp tục với tư cách khách'),
                    ),
                  ),
                  const SizedBox(height: 24),
                  Container(
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      color: secondary.withValues(alpha: .35),
                      borderRadius: BorderRadius.circular(18),
                    ),
                    child: Row(
                      children: [
                        const Icon(
                          Icons.local_fire_department_rounded,
                          color: accent,
                          size: 30,
                        ),
                        const SizedBox(width: 12),
                        const Expanded(
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
                                'Bắt đầu hành trình học tiếng Trung ngay hôm nay.',
                                style: TextStyle(fontSize: 13, color: outline),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'Đăng nhập bằng email đã đăng ký. Tài khoản quản trị được cấp riêng bởi quản trị viên.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 12, height: 1.5, color: outline),
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
