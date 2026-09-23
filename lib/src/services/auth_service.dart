import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;

class AuthUser {
  const AuthUser({
    required this.id,
    required this.name,
    required this.email,
    required this.role,
    required this.expiresAt,
  });

  final int id;
  final String name;
  final String email;
  final String role;
  final int expiresAt;

  bool get isAdmin => role == 'admin';

  factory AuthUser.fromJson(Map<String, dynamic> json) {
    return AuthUser(
      id: json['id'] as int,
      name: json['name'] as String,
      email: json['email'] as String,
      role: json['role'] as String,
      expiresAt: json['expires_at'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() => <String, dynamic>{
        'id': id,
        'name': name,
        'email': email,
        'role': role,
        'expires_at': expiresAt,
      };
}

class AuthService {
  AuthService(this._prefs, this.httpClient);

  final SharedPreferences _prefs;
  final http.Client httpClient;

  static const _tokenKey = 'auth_token';
  static const _userKey = 'auth_user';
  static const _apiBaseUrlKey = 'api_base_url';
  static const _lastActiveKey = 'auth_last_active_at';
  static const int defaultInactivityTimeoutSeconds = 86400; // 24 giờ
  bool _persistSession = true;
  String? _memoryToken;
  AuthUser? _memoryUser;
  String? _memoryBaseUrl;

  String? get token => _memoryToken ?? _prefs.getString(_tokenKey);

  AuthUser? get currentUser {
    if (_memoryUser != null) return _memoryUser;
    final raw = _prefs.getString(_userKey);
    if (raw == null || raw.isEmpty) return null;
    return AuthUser.fromJson(jsonDecode(raw) as Map<String, dynamic>);
  }

  bool get isSessionExpiredDueToInactivity {
    final lastActive = _prefs.getInt(_lastActiveKey);
    if (lastActive == null) return false;
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    return (now - lastActive) > defaultInactivityTimeoutSeconds;
  }

  bool get isAuthenticated {
    final user = currentUser;
    if (user == null) return false;
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    if (user.expiresAt <= now) return false;
    if (isSessionExpiredDueToInactivity) return false;
    return true;
  }

  Future<void> recordActivity() async {
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    if (_persistSession) {
      await _prefs.setInt(_lastActiveKey, now);
    }
  }

  Future<void> saveSession(String token, AuthUser user) async {
    _memoryToken = token;
    _memoryUser = user;
    if (_persistSession) {
      await _prefs.setString(_tokenKey, token);
      await _prefs.setString(_userKey, jsonEncode(user.toJson()));
      await recordActivity();
    }
  }

  Future<void> clearSession() async {
    _memoryToken = null;
    _memoryUser = null;
    await _prefs.remove(_tokenKey);
    await _prefs.remove(_userKey);
    await _prefs.remove(_lastActiveKey);
  }

  Future<AuthUser> login({
    required String baseUrl,
    required String email,
    required String password,
    bool remember = true,
  }) async {
    return _authenticate(baseUrl, 'login',
        {'email': email.trim(), 'password': password}, remember);
  }

  Future<AuthUser> register(
      {required String baseUrl,
      required String name,
      required String email,
      required String password}) {
    return _authenticate(
        baseUrl,
        'register',
        {'name': name.trim(), 'email': email.trim(), 'password': password},
        true);
  }

  Future<String> requestRegister({
    required String baseUrl,
    required String name,
    required String email,
    required String password,
  }) async {
    final response = await httpClient
        .post(
          Uri.parse('$baseUrl/auth/register-request'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'name': name.trim(),
            'email': email.trim(),
            'password': password,
          }),
        )
        .timeout(const Duration(seconds: 25));

    final data = _parseJson(response);
    if (response.statusCode != 200) {
      final detail = data['detail'];
      throw AuthException(detail is String
          ? detail
          : 'Không thể gửi mã xác thực. Vui lòng thử lại.');
    }
    return data['message'] as String? ?? 'Mã xác thực đã được gửi tới email.';
  }

  Future<AuthUser> verifyRegister({
    required String baseUrl,
    required String email,
    required String code,
    bool remember = true,
  }) async {
    return _authenticate(
      baseUrl,
      'register-verify',
      {'email': email.trim(), 'code': code.trim()},
      remember,
    );
  }

  Future<String> requestForgotPassword({
    required String baseUrl,
    required String email,
  }) async {
    final response = await httpClient
        .post(
          Uri.parse('$baseUrl/auth/forgot-password-request'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'email': email.trim()}),
        )
        .timeout(const Duration(seconds: 25));

    final data = _parseJson(response);
    if (response.statusCode != 200) {
      final detail = data['detail'];
      throw AuthException(detail is String
          ? detail
          : 'Không thể gửi mã xác thực đặt lại mật khẩu.');
    }
    return data['message'] as String? ?? 'Mã xác thực đã được gửi tới email.';
  }

  Future<String> verifyForgotPassword({
    required String baseUrl,
    required String email,
    required String code,
    required String newPassword,
  }) async {
    final response = await httpClient
        .post(
          Uri.parse('$baseUrl/auth/forgot-password-verify'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'email': email.trim(),
            'code': code.trim(),
            'new_password': newPassword,
          }),
        )
        .timeout(const Duration(seconds: 25));

    final data = _parseJson(response);
    if (response.statusCode != 200) {
      final detail = data['detail'];
      throw AuthException(detail is String
          ? detail
          : 'Không thể đặt lại mật khẩu. Vui lòng thử lại.');
    }
    return data['message'] as String? ?? 'Đặt lại mật khẩu thành công.';
  }

  Map<String, dynamic> _parseJson(http.Response response) {
    try {
      return jsonDecode(utf8.decode(response.bodyBytes))
          as Map<String, dynamic>;
    } on Exception {
      throw const AuthException(
          'Máy chủ chưa phản hồi hợp lệ. Vui lòng thử lại.');
    }
  }

  Future<AuthUser> _authenticate(String baseUrl, String action,
      Map<String, String> body, bool remember) async {
    final response = await httpClient
        .post(
          Uri.parse('$baseUrl/auth/$action'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 20));

    Map<String, dynamic> data;
    try {
      data =
          jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    } on FormatException {
      throw const AuthException(
          'Máy chủ chưa phản hồi hợp lệ. Vui lòng thử lại.');
    } on TypeError {
      throw const AuthException(
          'Máy chủ chưa phản hồi hợp lệ. Vui lòng thử lại.');
    }
    final expectedStatus =
        (action == 'register' || action == 'register-verify') ? 201 : 200;
    if (response.statusCode != expectedStatus) {
      final detail = data['detail'];
      throw AuthException(detail is String
          ? detail
          : response.statusCode == 422
              ? 'Thông tin chưa hợp lệ. Kiểm tra họ tên, email và mật khẩu.'
              : 'Không thực hiện được yêu cầu. Vui lòng thử lại.');
    }
    final token = data['token'] as String;
    final expiresIn = data['expires_in'] as int? ?? 86400;
    final userJson = Map<String, dynamic>.from(
      data['user'] as Map<String, dynamic>,
    )..['expires_at'] =
        DateTime.now().millisecondsSinceEpoch ~/ 1000 + expiresIn;
    final user = AuthUser.fromJson(userJson);
    await clearSession();
    _persistSession = remember;
    _memoryBaseUrl = baseUrl;
    if (remember) await _prefs.setString(_apiBaseUrlKey, baseUrl);
    await saveSession(token, user);
    return user;
  }

  Future<void> logout() async {
    final tokenValue = token;
    if (tokenValue != null) {
      try {
        final baseUrl = _memoryBaseUrl ??
            _prefs.getString(_apiBaseUrlKey) ??
            'http://localhost:8010/api';
        await httpClient.post(
          Uri.parse('$baseUrl/auth/logout'),
          headers: {
            'Authorization': 'Bearer $tokenValue',
            'Content-Type': 'application/json',
          },
        );
      } on Exception {
        // ignore logout network errors
      }
    }
    await clearSession();
  }

  Future<void> refreshUser(String baseUrl) async {
    final response = await httpClient.get(Uri.parse('$baseUrl/me'),
        headers: {'Authorization': 'Bearer $token'});
    if (response.statusCode != 200) {
      throw const AuthException('Phiên đăng nhập đã hết hạn.');
    }
    final data = Map<String, dynamic>.from(jsonDecode(response.body) as Map)
      ..['expires_at'] = currentUser?.expiresAt ?? 0;
    await saveSession(token!, AuthUser.fromJson(data));
  }

  static Future<AuthService> load(http.Client httpClient) async {
    final prefs = await SharedPreferences.getInstance();
    return AuthService(prefs, httpClient);
  }

  AuthService.test()
      : _prefs = _TestPrefs(),
        httpClient = http.Client();
}

class _TestPrefs implements SharedPreferences {
  _TestPrefs();

  final Map<String, Object> _values = <String, Object>{};

  @override
  String? getString(String key) => _values[key] as String?;

  @override
  Future<bool> setString(String key, String value) async {
    _values[key] = value;
    return true;
  }

  @override
  Future<bool> remove(String key) async {
    _values.remove(key);
    return true;
  }

  @override
  bool getBool(String key) => _values[key] as bool? ?? false;

  @override
  Future<bool> setBool(String key, bool value) async {
    _values[key] = value;
    return true;
  }

  @override
  int? getInt(String key) => _values[key] as int?;

  @override
  Future<bool> setInt(String key, int value) async {
    _values[key] = value;
    return true;
  }

  @override
  double? getDouble(String key) => null;

  @override
  Future<bool> setDouble(String key, double value) async => false;

  @override
  List<String>? getStringList(String key) => null;

  @override
  Future<bool> setStringList(String key, List<String> value) async => false;

  @override
  bool containsKey(String key) => _values.containsKey(key);

  @override
  Future<bool> clear() async {
    _values.clear();
    return true;
  }

  @override
  Future<bool> commit() async => true;

  @override
  Set<String> getKeys() => _values.keys.toSet();

  bool get onValueChanged => true;

  @override
  Future<bool> reload() async => true;

  @override
  Object? get(String key) => _values[key];
}

class AuthException implements Exception {
  const AuthException(this.message);
  final String message;

  @override
  String toString() => message;
}
