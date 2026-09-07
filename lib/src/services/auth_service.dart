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

  String? get token => _prefs.getString(_tokenKey);

  AuthUser? get currentUser {
    final raw = _prefs.getString(_userKey);
    if (raw == null || raw.isEmpty) return null;
    return AuthUser.fromJson(jsonDecode(raw) as Map<String, dynamic>);
  }

  bool get isAuthenticated {
    final user = currentUser;
    if (user == null) return false;
    return user.expiresAt > DateTime.now().millisecondsSinceEpoch ~/ 1000;
  }

  Future<void> saveSession(String token, AuthUser user) async {
    await _prefs.setString(_tokenKey, token);
    await _prefs.setString(_userKey, jsonEncode(user.toJson()));
  }

  Future<void> clearSession() async {
    await _prefs.remove(_tokenKey);
    await _prefs.remove(_userKey);
  }

  Future<AuthUser> login({
    required String baseUrl,
    required String email,
    required String password,
  }) async {
    final response = await httpClient.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );

    if (response.statusCode != 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      throw AuthException(data['detail'] as String? ?? 'Đăng nhập thất bại');
    }

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final token = data['token'] as String;
    final user = AuthUser.fromJson(data['user'] as Map<String, dynamic>);
    await saveSession(token, user);
    return user;
  }

  Future<void> logout() async {
    final tokenValue = token;
    if (tokenValue != null) {
      try {
        final baseUrl = _prefs.getString('api_base_url') ?? 'http://localhost:8010/api';
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

  static Future<AuthService> load(http.Client httpClient) async {
    final prefs = await SharedPreferences.getInstance();
    return AuthService(prefs, httpClient);
  }

  AuthService.test() : _prefs = _TestPrefs(), httpClient = http.Client();
}

class _TestPrefs implements SharedPreferences {
  _TestPrefs();

  final Map<String, String> _values = <String, String>{};

  @override
  String? getString(String key) => _values[key];

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
  bool getBool(String key) => false;

  @override
  Future<bool> setBool(String key, bool value) async => false;

  @override
  int? getInt(String key) => null;

  @override
  Future<bool> setInt(String key, int value) async => false;

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
