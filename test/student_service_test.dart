import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:hanzi_go/src/services/student_service.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

http.Response _json(Object value, [int status = 200]) => http.Response.bytes(
      utf8.encode(jsonEncode(value)),
      status,
      headers: {'content-type': 'application/json; charset=utf-8'},
    );

Map<String, Object?> _result({
  int id = 1,
  String kind = 'writing',
  double score = 60,
  String feedback = 'Cần luyện lại.',
}) =>
    {
      'id': id,
      'exam_id': null,
      'kind': kind,
      'content': jsonEncode({'content': '我学习中文。', 'target': '一'}),
      'score': score,
      'original_score': score,
      'feedback': feedback,
      'graded_by': 'ai',
      'version': 1,
      'created_at': 1,
      'overrides': <Object>[],
    };

void main() {
  test('đọc Dashboard và báo cáo năng lực Gemini bằng dữ liệu máy chủ',
      () async {
    final client = MockClient((request) async {
      expect(request.headers['authorization'], 'Bearer student-token');
      if (request.url.path.endsWith('/me/dashboard')) {
        return _json({
          'results': 4,
          'average_score': 81.5,
          'needs_review': 1,
          'vocabulary_count': 9,
          'streak': 3,
          'progress_percent': 81.5,
          'skill_scores': {
            'listening': 90,
            'reading': 80,
            'writing': 76,
            'handwriting': 80,
          },
        });
      }
      return _json({
        'skill_scores': {
          'listening': 90,
          'reading': 80,
          'writing': 76,
          'handwriting': 80,
        },
        'feedback': 'Nghe là điểm mạnh.',
        'strengths': ['Nghe tốt'],
        'improvements': ['Luyện viết'],
      });
    });
    final service = StudentService(
      baseUrl: 'http://test/api',
      tokenProvider: () async => 'student-token',
      client: client,
    );

    final dashboard = await service.fetchMyDashboard();
    final report = await service.fetchCapabilityReport();

    expect(dashboard.streak, 3);
    expect(dashboard.skillScores['listening'], 90);
    expect(report.feedback, 'Nghe là điểm mạnh.');
    expect(report.improvements, ['Luyện viết']);
  });

  test('tra từ ghi đúng lịch sử riêng của học viên', () async {
    var posted = false;
    final word = {
      'id': 7,
      'hanzi': '你好',
      'pinyin': 'nǐ hǎo',
      'meaning': 'xin chào',
      'hsk': 1,
      'example': '你好！',
      'audio_url': '',
    };
    final client = MockClient((request) async {
      if (request.method == 'POST') {
        posted = true;
        expect(request.url.path, '/api/me/dictionary-history/7');
        expect(jsonDecode(request.body), {'query': 'ni hao'});
        return _json({...word, 'word_id': 7, 'lookup_count': 1});
      }
      expect(request.url.queryParameters['search'], 'ni hao');
      return _json([word]);
    });
    final service = StudentService(
      baseUrl: 'http://test/api',
      tokenProvider: () async => 'student-token',
      client: client,
    );

    final words = await service.fetchVocabulary(search: 'ni hao');
    final history =
        await service.recordDictionaryLookup(words.single, 'ni hao');

    expect(posted, isTrue);
    expect(history.lookupCount, 1);
  });

  test('danh sách ôn tập dùng điểm và góp ý của lần nộp gần nhất', () async {
    final client = MockClient((request) async {
      return _json([
        {
          ..._result(),
          'latest_result': _result(
            id: 2,
            score: 72,
            feedback: 'Lần hai đã tốt hơn.',
          ),
        }
      ]);
    });
    final service = StudentService(
      baseUrl: 'http://test/api',
      tokenProvider: () async => 'student-token',
      client: client,
    );

    final result = (await service.fetchReviewItems('writing')).single;

    expect(result.score, 60);
    expect(result.reviewScore, 72);
    expect(result.reviewFeedback, 'Lần hai đã tốt hơn.');
  });

  test('gửi Canvas dưới dạng các nét tọa độ cho backend', () async {
    final client = MockClient((request) async {
      expect(request.url.path, '/api/handwriting/submit');
      final body = jsonDecode(request.body) as Map<String, dynamic>;
      expect(body['target'], '一');
      expect((body['strokes'] as List).single, hasLength(2));
      return _json(_result(kind: 'handwriting', score: 88), 201);
    });
    final service = StudentService(
      baseUrl: 'http://test/api',
      tokenProvider: () async => 'student-token',
      client: client,
    );

    final result = await service.submitHandwriting('一', [
      [
        {'x': 10, 'y': 20},
        {'x': 900, 'y': 20},
      ]
    ]);

    expect(result.score, 88);
  });
}
