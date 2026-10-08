import 'dart:async';
import 'dart:convert';
import 'dart:js_interop';
import 'package:web/web.dart' as web;

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

Future<GoogleAuthResult> triggerGoogleWebSignIn(String clientId) {
  final completer = Completer<GoogleAuthResult>();

  web.EventListener? listener;
  Timer? timeoutTimer;

  void cleanup() {
    timeoutTimer?.cancel();
    if (listener != null) {
      web.window.removeEventListener('hanzigo-google-signin-response', listener);
    }
  }

  listener = ((web.Event event) {
    try {
      final customEvent = event as web.CustomEvent;
      final detailJs = customEvent.detail;
      if (detailJs != null) {
        final detailStr = (detailJs as JSString).toDart;
        final map = jsonDecode(detailStr) as Map<String, dynamic>;
        cleanup();
        if (map['success'] == true) {
          final data = map['data'] as Map<String, dynamic>? ?? {};
          completer.complete(GoogleAuthResult(
            success: true,
            email: data['email']?.toString() ?? '',
            name: data['name']?.toString() ?? '',
            avatar: data['avatar']?.toString() ?? '',
            accessToken: data['accessToken']?.toString() ?? '',
            googleId: data['googleId']?.toString() ?? '',
          ));
        } else {
          completer.complete(GoogleAuthResult(
            success: false,
            error: map['error']?.toString() ?? 'Đăng nhập Google bị hủy hoặc thất bại.',
          ));
        }
      }
    } catch (e) {
      cleanup();
      completer.complete(GoogleAuthResult(
        success: false,
        error: 'Lỗi khi đọc phản hồi từ Google: $e',
      ));
    }
  }).toJS;

  web.window.addEventListener('hanzigo-google-signin-response', listener);

  // Gửi sự kiện yêu cầu mở popup Google
  final payload = jsonEncode({'clientId': clientId});
  web.window.dispatchEvent(web.CustomEvent(
    'hanzigo-google-signin-request',
    web.CustomEventInit(detail: payload.toJS),
  ));

  // Hết thời gian chờ nếu người dùng giữ cửa sổ quá lâu mà không thao tác
  timeoutTimer = Timer(const Duration(minutes: 3), () {
    cleanup();
    if (!completer.isCompleted) {
      completer.complete(const GoogleAuthResult(
        success: false,
        error: 'Đã hết thời gian chờ xác thực từ Google.',
      ));
    }
  });

  return completer.future;
}
