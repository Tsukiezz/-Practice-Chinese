import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../theme/app_theme.dart';

/// Cosmetics follow the authenticated server snapshot; content access is enforced by API.
class BenefitsService extends ChangeNotifier {
  static final instance = BenefitsService();
  Map<String, dynamic> _state = {};
  String? _baseUrl, _token;
  http.Client? _client;
  Timer? _expiry;
  int _generation = 0;
  bool get isPremium => (_state['premium_until'] as int? ?? 0) > DateTime.now().millisecondsSinceEpoch ~/ 1000;
  String get brush => isPremium ? _state['brush'] as String? ?? 'default' : 'default';
  int get freezes => isPremium ? _state['streak_freezes'] as int? ?? 0 : 0;

  void clear() {
    _generation++;
    _expiry?.cancel();
    _state = {};
    _token = null;
    ThemeManager.palette.value = InterfacePalette.dark;
    notifyListeners();
  }

  Future<void> connect(String baseUrl, String token, http.Client client) async {
    clear();
    _baseUrl = baseUrl;
    _token = token;
    _client = client;
    await refresh();
  }

  Future<void> refresh() async {
    if (_token == null || _baseUrl == null || _client == null) return;
    final generation = _generation;
    try {
      final response = await _client!.get(Uri.parse('$_baseUrl/me/benefits'),
        headers: {'Authorization': 'Bearer $_token'}).timeout(const Duration(seconds: 10));
      if (generation != _generation) return;
      if (response.statusCode == 200) _apply(jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>);
    } catch (_) {
      // A failed entitlement refresh cannot grant a paid feature.
    }
  }

  void _apply(Map<String, dynamic> state) {
    _state = state;
    ThemeManager.palette.value = InterfacePalette.values.firstWhere(
      (p) => p.name == (isPremium ? state['palette'] : 'dark'), orElse: () => InterfacePalette.dark);
    _expiry?.cancel();
    if (isPremium) {
      final remaining = (state['premium_until'] as int) - DateTime.now().millisecondsSinceEpoch ~/ 1000 + 1;
      // Browser timers cannot safely span a yearly subscription in one timeout.
      _expiry = Timer(Duration(seconds: remaining > 86400 ? 86400 : remaining),
        () => _apply(Map<String, dynamic>.from(_state)));
    }
    notifyListeners();
  }

  Future<void> select({String? brush, InterfacePalette? palette}) async {
    if (_token == null || _client == null) throw Exception('Vui lòng đăng nhập.');
    final generation = _generation;
    final response = await _client!.put(Uri.parse('$_baseUrl/me/benefits/preferences'),
      headers: {'Authorization': 'Bearer $_token', 'Content-Type': 'application/json'},
      body: jsonEncode({'brush': brush ?? this.brush, 'palette': palette?.name ?? ThemeManager.palette.value.name}),
    ).timeout(const Duration(seconds: 15));
    if (generation != _generation) return;
    final data = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    if (response.statusCode != 200) throw Exception(data['detail'] ?? 'Không lưu được tùy chọn.');
    _apply(data);
  }
}
