import 'exam_chat_guard_stub.dart'
    if (dart.library.js_interop) 'exam_chat_guard_web.dart' as platform;

class ExamChatGuard {
  static int _sequence = 0;
  final String _lease = 'exam_${DateTime.now().microsecondsSinceEpoch}_${_sequence++}';
  bool _active = false;
  bool _disposed = false;
  Future<bool> start() async {
    if (_disposed) return false;
    try {
      final ready = await platform.startExamChatGuard(_lease);
      if (_disposed) { platform.endExamChatGuard(_lease); return false; }
      _active = ready;
      return ready;
    } catch (_) { return false; }
  }
  void end() {
    if (_active) platform.endExamChatGuard(_lease);
    _active = false;
  }
  void dispose() { _disposed = true; end(); }
}
