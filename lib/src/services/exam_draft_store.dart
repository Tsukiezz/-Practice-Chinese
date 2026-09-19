import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

class ExamDraftStore {
  static Future<void> _pending = Future<void>.value();
  static String _key(int owner, String kind, int exam, int version) =>
      'exam_draft:$owner:$kind:$exam:$version';

  static Future<void> _enqueue(Future<void> Function() action) {
    final next = _pending.then(
      (_) => action(),
      onError: (Object _) => action(),
    );
    _pending = next.catchError((Object _) {});
    return next;
  }

  static Future<void> save(
    int? owner,
    String kind,
    int exam,
    int version,
    Map<String, dynamic> answers,
  ) {
    if (owner == null) return Future<void>.value();
    final encoded = jsonEncode(answers);
    return _enqueue(() async {
      final prefs = await SharedPreferences.getInstance();
      if (!await prefs.setString(_key(owner, kind, exam, version), encoded)) {
        throw StateError('Could not save draft');
      }
    });
  }

  static Future<Map<String, dynamic>> read(
    int? owner,
    String kind,
    int exam,
    int version,
  ) async {
    if (owner == null) return {};
    await _pending;
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_key(owner, kind, exam, version));
    if (raw == null) return {};
    try {
      return Map<String, dynamic>.from(jsonDecode(raw) as Map);
    } on FormatException {
      return {};
    } on TypeError {
      return {};
    }
  }

  static Future<void> clear(int? owner, String kind, int exam, int version) {
    if (owner == null) return Future<void>.value();
    return _enqueue(() async {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_key(owner, kind, exam, version));
    });
  }
}
