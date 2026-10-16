import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../services/auth_service.dart';
import '../services/facebook_auth.dart';
import 'google_sign_in_sheet.dart';

class SocialSignIn extends StatelessWidget {
  const SocialSignIn({super.key, required this.baseUrl, this.authService,
    required this.onSuccess, this.googleLabel = 'Đăng nhập với Google'});
  final String baseUrl, googleLabel;
  final AuthService? authService;
  final VoidCallback onSuccess;
  @override
  Widget build(BuildContext context) => Column(children: [
    const Text('Tiếp tục với', style: TextStyle(color: Color(0xFF707974))),
    const SizedBox(height: 8),
    Row(children: [
      Expanded(child: Tooltip(message: googleLabel, child: GoogleSignInButton(
        baseUrl: baseUrl, authService: authService, onSuccess: onSuccess, label: 'Google'))),
      const SizedBox(width: 10),
      Expanded(child: FacebookSignInButton(
        baseUrl: baseUrl, authService: authService, onSuccess: onSuccess)),
    ]),
  ]);
}

class FacebookSignInButton extends StatefulWidget {
  const FacebookSignInButton({super.key, required this.baseUrl, this.authService, required this.onSuccess});
  final String baseUrl;
  final AuthService? authService;
  final VoidCallback onSuccess;
  @override
  State<FacebookSignInButton> createState() => _FacebookSignInButtonState();
}

class _FacebookSignInButtonState extends State<FacebookSignInButton> {
  bool _ready = false, _busy = false, _loading = true;
  final _client = http.Client();
  @override
  void initState() { super.initState(); _prepare(); }
  Future<void> _prepare() async {
    bool ready = false;
    try { ready = await prepareFacebook(widget.baseUrl); } catch (_) {}
    if (mounted) setState(() { _ready = ready; _loading = false; });
  }
  @override
  void dispose() { _client.close(); super.dispose(); }
  Future<void> _login() async {
    if (!_ready) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text(
        'Đăng nhập Facebook chưa được cấu hình. Bạn có thể dùng Google hoặc email.')));
      _prepare();
      return;
    }
    setState(() => _busy = true);
    try {
      final token = await signInFacebook();
      final auth = widget.authService ?? await AuthService.load(_client);
      await auth.loginWithFacebook(baseUrl: widget.baseUrl, accessToken: token);
      if (mounted) widget.onSuccess();
    } on AuthException catch (error) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error.message)));
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Không hoàn tất đăng nhập Facebook. Vui lòng thử lại.')));
    } finally { if (mounted) setState(() => _busy = false); }
  }
  @override
  Widget build(BuildContext context) => Tooltip(
    message: _ready ? 'Đăng nhập với Facebook' : 'Facebook · Chưa cấu hình',
    child: SizedBox(height: 52, child: OutlinedButton(
      onPressed: _busy || _loading ? null : _login,
      style: OutlinedButton.styleFrom(backgroundColor: Colors.white, foregroundColor: const Color(0xFF1877F2),
        padding: const EdgeInsets.symmetric(horizontal: 8),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14))),
      child: _busy || _loading ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
        : const Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          Icon(Icons.facebook, size: 24), SizedBox(width: 8),
          Flexible(child: Text('Facebook', maxLines: 1, overflow: TextOverflow.ellipsis)),
        ]),
    )),
  );
}
