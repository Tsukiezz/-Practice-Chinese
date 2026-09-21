import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/reading_exam.dart';

abstract interface class ReadingExamRepository {
  Future<List<ReadingExam>> fetchReadingExams(int hsk);

  Future<ReadingResult> submitReadingExam(
    ReadingExam exam,
    Map<String, dynamic> answers,
  );
}

class ReadingApiException implements Exception {
  const ReadingApiException(this.statusCode, this.message);

  final int? statusCode;
  final String message;

  @override
  String toString() => message;
}

class ReadingExamService implements ReadingExamRepository {
  ReadingExamService({
    required this.baseUrl,
    required this.tokenProvider,
    http.Client? client,
    this.comprehensive = false,
  }) : _client = client ?? http.Client();

  final String baseUrl;
  final Future<String?> Function() tokenProvider;
  final http.Client _client;
  final bool comprehensive;

  @override
  Future<List<ReadingExam>> fetchReadingExams(int hsk) async {
    final response = await _request(
      'GET',
      Uri.parse('$baseUrl/exams?hsk=$hsk'),
    );
    try {
      final rows = jsonDecode(response.body) as List<dynamic>;
      return rows
          .map((row) => ReadingExam.fromJson(row as Map<String, dynamic>))
          .where((exam) {
        if (exam.questions.isEmpty) return false;
        final sections =
            exam.questions.map((question) => question.section).toSet();
        return comprehensive
            ? sections.length > 1
            : sections.length == 1 && sections.single == 'reading';
      }).toList(growable: false);
    } on Object {
      throw const ReadingApiException(
        null,
        'Dữ liệu đề từ máy chủ không đúng định dạng.',
      );
    }
  }

  @override
  Future<ReadingResult> submitReadingExam(
    ReadingExam exam,
    Map<String, dynamic> answers,
  ) async {
    final response = await _request(
      'POST',
      Uri.parse('$baseUrl/exams/${exam.id}/submit'),
      body: jsonEncode({'version': exam.version, 'answers': answers}),
    );
    try {
      final result = jsonDecode(response.body) as Map<String, dynamic>;
      final snapshot =
          jsonDecode(result['content'] as String) as Map<String, dynamic>;
      final submittedAnswers = snapshot['answers'] as Map<String, dynamic>;
      final questions = snapshot['questions'] as List<dynamic>;
      final questionScores =
          snapshot['question_scores'] as Map<String, dynamic>? ?? const {};
      final aiReviewItems = <String, String>{
        for (final item
            in snapshot['ai_review_items'] as List<dynamic>? ?? const [])
          if (item is Map<String, dynamic> &&
              item['id'] is String &&
              item['explanation'] is String)
            item['id'] as String: item['explanation'] as String,
      };
      return ReadingResult(
        id: result['id'] as int,
        score: (result['score'] as num).toDouble(),
        feedback: result['feedback'] as String? ?? '',
        reviewItems: questions.map((item) {
          final question = item as Map<String, dynamic>;
          final id = question['id'] as String;
          final scoreData = questionScores[id] as Map<String, dynamic>?;
          return ReadingReviewItem(
            id: id,
            prompt: question['prompt'] as String,
            answer: question['answer'] as String,
            submittedAnswer: _displayAnswer(submittedAnswers[id]),
            explanation: _questionFeedback(
              scoreData,
              aiReviewItems[id] ?? question['explanation'] as String? ?? '',
            ),
            transcript: question['transcript'] as String? ?? '',
            questionType: question['question_type'] as String?,
            score: (scoreData?['score'] as num?)?.toDouble(),
          );
        }).toList(growable: false),
      );
    } on Object {
      throw const ReadingApiException(
        null,
        'Kết quả chấm từ máy chủ không đúng định dạng.',
      );
    }
  }

  String _displayAnswer(dynamic answer) {
    if (answer is String) return answer;
    if (answer is Map<String, dynamic>) {
      if (answer['kind'] == 'essay') return answer['text'] as String? ?? '';
      if (answer['kind'] == 'hanzi_canvas') {
        final strokes = answer['strokes'] as List<dynamic>? ?? const [];
        return 'Đã viết ${strokes.length} nét';
      }
    }
    return '';
  }

  String _questionFeedback(
    Map<String, dynamic>? scoreData,
    String fallback,
  ) {
    if (scoreData == null) return fallback;
    final lines = <String>[
      if ((scoreData['feedback'] as String? ?? '').isNotEmpty)
        scoreData['feedback'] as String,
    ];
    final details = scoreData['details'];
    if (details is Map<String, dynamic>) {
      const labels = {
        'grammar': 'Ngữ pháp',
        'vocabulary': 'Từ vựng',
        'coherence': 'Mạch lạc',
        'task_fulfillment': 'Đáp ứng đề bài và độ dài',
      };
      for (final entry in labels.entries) {
        final criterion = details[entry.key];
        if (criterion is Map<String, dynamic>) {
          lines.add(
            '${entry.value}: ${criterion['score']} điểm — '
            '${criterion['feedback']}',
          );
        }
      }
      for (final entry in const {
        'strengths': 'Điểm mạnh',
        'weaknesses': 'Điểm cần cải thiện',
      }.entries) {
        final values = details[entry.key];
        if (values is List && values.isNotEmpty) {
          lines.add('${entry.value}: ${values.join('; ')}');
        }
      }
    }
    return lines.isEmpty ? fallback : lines.join('\n');
  }

  Future<http.Response> _request(
    String method,
    Uri uri, {
    String? body,
  }) async {
    final token = (await tokenProvider())?.trim() ?? '';
    if (token.isEmpty) {
      throw const ReadingApiException(
        401,
        'Bạn cần đăng nhập bằng tài khoản học viên để làm bài.',
      );
    }

    try {
      final headers = {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      };
      final response = method == 'POST'
          ? await _client
              .post(uri, headers: headers, body: body)
              .timeout(const Duration(seconds: 75))
          : await _client
              .get(uri, headers: headers)
              .timeout(const Duration(seconds: 15));
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return response;
      }
      throw ReadingApiException(
        response.statusCode,
        _errorMessage(response),
      );
    } on ReadingApiException {
      rethrow;
    } on TimeoutException {
      throw const ReadingApiException(
        null,
        'AI đang phản hồi chậm. Hãy kiểm tra lịch sử bài làm trước khi nộp lại.',
      );
    } on Exception {
      throw const ReadingApiException(
        null,
        'Không thể kết nối máy chủ. Hãy kiểm tra mạng và thử lại.',
      );
    }
  }

  String _errorMessage(http.Response response) {
    try {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final detail = data['detail'];
      if (detail is String && detail.isNotEmpty) return detail;
      if (detail is List && detail.isNotEmpty) {
        final first = detail.first;
        if (first is Map<String, dynamic> && first['msg'] is String) {
          return first['msg'] as String;
        }
      }
    } on Object {
      // Fall through to the safe generic message below.
    }
    return 'Máy chủ không xử lý được yêu cầu (${response.statusCode}).';
  }
}
