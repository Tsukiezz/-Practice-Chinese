import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:hanzi_go/src/services/student_service.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  test('đọc danh sách chữ luyện lại theo contract backend', () async {
    final client = MockClient((request) async {
      expect(request.method, 'GET');
      expect(request.url.path, '/api/me/handwriting-retry-items');
      expect(request.headers['authorization'], 'Bearer token');
      return http.Response.bytes(
        utf8.encode(jsonEncode([
          {
            'hanzi': '一',
            'latest_score': 45,
            'attempts': 3,
            'last_practiced_at': 123,
          },
        ])),
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });
    final service = StudentService(
      baseUrl: 'http://test/api',
      tokenProvider: () async => 'token',
      client: client,
    );

    final item = (await service.fetchHandwritingRetryItems()).single;

    expect(item.hanzi, '一');
    expect(item.latestScore, 45);
    expect(item.attempts, 3);
    expect(item.lastPracticedAt, 123);
  });
}
