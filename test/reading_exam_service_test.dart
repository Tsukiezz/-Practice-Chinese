import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:hanzi_go/src/services/reading_exam_service.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  test('tải đề published và chỉ giữ đề thuần kỹ năng Đọc', () async {
    final client = MockClient((request) async {
      expect(request.headers['authorization'], 'Bearer student-token');
      expect(request.url.toString(), 'http://test/api/exams?hsk=1');
      return http.Response.bytes(
        utf8.encode(jsonEncode([
          {
            'id': 1,
            'title': 'Đề đọc',
            'hsk': 1,
            'status': 'published',
            'duration_minutes': 10,
            'version': 1,
            'questions': [
              {
                'id': 'q1',
                'section': 'reading',
                'prompt': '一 nghĩa là gì?',
                'options': ['một', 'hai'],
              }
            ],
          },
          {
            'id': 2,
            'title': 'Đề nghe',
            'hsk': 1,
            'status': 'published',
            'duration_minutes': 10,
            'version': 1,
            'questions': [
              {
                'id': 'q1',
                'section': 'listening',
                'prompt': 'Nghe và chọn',
                'options': ['một', 'hai'],
              }
            ],
          }
        ])),
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });
    final service = ReadingExamService(
      baseUrl: 'http://test/api',
      tokenProvider: () async => 'student-token',
      client: client,
    );

    final exams = await service.fetchReadingExams(1);

    expect(exams, hasLength(1));
    expect(exams.single.title, 'Đề đọc');
    expect(exams.single.questions.single.section, 'reading');
  });

  test('nộp đáp án và đọc điểm cùng lời giải từ snapshot', () async {
    final client = MockClient((request) async {
      expect(request.method, 'POST');
      expect(jsonDecode(request.body), {
        'version': 3,
        'answers': {'q1': 'một'},
      });
      return http.Response.bytes(
        utf8.encode(jsonEncode({
          'id': 9,
          'score': 100,
          'feedback': 'Gemini nhận xét bài làm tốt.',
          'content': jsonEncode({
            'answers': {'q1': 'một'},
            'questions': [
              {
                'id': 'q1',
                'prompt': '一 nghĩa là gì?',
                'answer': 'một',
                'explanation': '一 nghĩa là một.',
              }
            ],
          }),
        })),
        201,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });
    final service = ReadingExamService(
      baseUrl: 'http://test/api',
      tokenProvider: () async => 'student-token',
      client: client,
    );
    final exam = (await ReadingExamService(
      baseUrl: 'http://test/api',
      tokenProvider: () async => 'student-token',
      client: MockClient((_) async => http.Response.bytes(
            utf8.encode(jsonEncode([
              {
                'id': 1,
                'title': 'Đề đọc',
                'hsk': 1,
                'duration_minutes': 10,
                'version': 3,
                'questions': [
                  {
                    'id': 'q1',
                    'section': 'reading',
                    'prompt': '一 nghĩa là gì?',
                    'options': ['một', 'hai'],
                  }
                ],
              }
            ])),
            200,
            headers: {'content-type': 'application/json; charset=utf-8'},
          )),
    ).fetchReadingExams(1))
        .single;

    final result = await service.submitReadingExam(exam, {'q1': 'một'});

    expect(result.score, 100);
    expect(result.feedback, 'Gemini nhận xét bài làm tốt.');
    expect(result.reviewItems.single.isCorrect, isTrue);
    expect(result.reviewItems.single.explanation, '一 nghĩa là một.');
  });

  test('không gọi API nếu chưa có token học viên', () async {
    final service = ReadingExamService(
      baseUrl: 'http://test/api',
      tokenProvider: () async => '',
      client: MockClient((_) async => fail('Không được gọi HTTP')),
    );

    expect(
      () => service.fetchReadingExams(1),
      throwsA(
        isA<ReadingApiException>()
            .having((error) => error.statusCode, 'statusCode', 401),
      ),
    );
  });

  test('chế độ tổng hợp chỉ lấy đề nhiều kỹ năng và giữ audio', () async {
    final client = MockClient((_) async => http.Response.bytes(
          utf8.encode(jsonEncode([
            {
              'id': 3,
              'title': 'Đề tổng hợp HSK 1',
              'hsk': 1,
              'duration_minutes': 30,
              'version': 1,
              'questions': [
                {
                  'id': 'l1',
                  'section': 'listening',
                  'prompt': 'Nghe và chọn',
                  'options': ['một', 'hai'],
                  'audio_url': 'https://example.test/listening.mp3',
                },
                {
                  'id': 'r1',
                  'section': 'reading',
                  'prompt': 'Chọn nghĩa đúng',
                  'options': ['một', 'hai'],
                },
                {
                  'id': 'w1',
                  'section': 'writing',
                  'prompt': 'Viết một câu',
                  'options': <String>[],
                },
              ],
            }
          ])),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        ));
    final service = ReadingExamService(
      baseUrl: 'http://test/api',
      tokenProvider: () async => 'student-token',
      client: client,
      comprehensive: true,
    );

    final exam = (await service.fetchReadingExams(1)).single;

    expect(exam.questions.map((question) => question.section),
        ['listening', 'reading', 'writing']);
    expect(exam.questions.first.audioUrl, 'https://example.test/listening.mp3');
  });
}
