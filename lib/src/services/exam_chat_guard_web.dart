import 'dart:js_interop';
@JS('hanziGoExamGuard.start')
external JSPromise<JSBoolean> _start(JSString lease);
@JS('hanziGoExamGuard.end')
external void _end(JSString lease);
Future<bool> startExamChatGuard(String lease) async => (await _start(lease.toJS).toDart).toDart;
void endExamChatGuard(String lease) => _end(lease.toJS);
