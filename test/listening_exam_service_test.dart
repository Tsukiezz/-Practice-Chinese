import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:hanzi_go/src/models/reading_exam.dart';
import 'package:hanzi_go/src/services/listening_exam_service.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('đọc transcript và ưu tiên lời giải Gemini sau khi nộp', () async {
    final client = MockClient((request) async {
      return http.Response.bytes(
        utf8.encode(jsonEncode({
          'id': 5,
          'score': 75,
          'feedback': 'Cần chú ý từ khóa trong audio.',
          'content': jsonEncode({
            'answers': {'l1': 'hai'},
            'questions': [
              {
                'id': 'l1',
                'prompt': 'Nghe và chọn',
                'answer': 'một',
                'transcript': '一，yī, nghĩa là một.',
                'explanation': 'Lời giải của Admin.',
              }
            ],
            'ai_review_items': [
              {
                'id': 'l1',
                'explanation': 'Từ khóa 一 chỉ số một; hai là đáp án nhiễu.',
              }
            ],
          }),
        })),
        201,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });
    final service = ListeningExamService(
      baseUrl: 'http://test/api',
      tokenProvider: () async => 'student-token',
      client: client,
    );
    const exam = ReadingExam(
      id: 3,
      title: 'Đề nghe',
      hsk: 1,
      durationMinutes: 10,
      version: 1,
      questions: [
        ReadingQuestion(
          id: 'l1',
          section: 'listening',
          prompt: 'Nghe và chọn',
          options: ['một', 'hai'],
          audioUrl: 'https://example.test/audio.mp3',
        ),
      ],
    );

    final result = await service.submitListeningExam(exam, {'l1': 'hai'});

    expect(result.reviewItems.single.transcript, '一，yī, nghĩa là một.');
    expect(result.reviewItems.single.explanation, contains('đáp án nhiễu'));
  });
}
