import 'dart:js_interop';
@JS('hanziGoFacebook.prepare')
external JSPromise<JSBoolean> _prepare(JSString baseUrl);
@JS('hanziGoFacebook.signIn')
external JSPromise<JSString> _signIn();
Future<bool> prepareFacebook(String baseUrl) async =>
    (await _prepare(baseUrl.toJS).toDart.timeout(const Duration(seconds: 20))).toDart;
Future<String> signInFacebook() async =>
    (await _signIn().toDart.timeout(const Duration(minutes: 3))).toDart;
