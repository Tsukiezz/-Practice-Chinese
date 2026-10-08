class GoogleAuthResult {
  final bool success;
  final String email;
  final String name;
  final String avatar;
  final String accessToken;
  final String googleId;
  final String? error;

  const GoogleAuthResult({
    required this.success,
    this.email = '',
    this.name = '',
    this.avatar = '',
    this.accessToken = '',
    this.googleId = '',
    this.error,
  });
}

Future<GoogleAuthResult> triggerGoogleWebSignIn(String clientId) async {
  return const GoogleAuthResult(
    success: false,
    error: 'Đăng nhập Google trực tiếp qua trình duyệt chỉ khả dụng trên nền tảng Web.',
  );
}
