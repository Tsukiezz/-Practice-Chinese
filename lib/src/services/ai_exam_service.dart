import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

class AIExamQuestion {
  const AIExamQuestion({
    required this.id,
    required this.prompt,
    required this.options,
    required this.answer,
    required this.explanation,
    required this.correction,
    this.pinyin = '',
  });

  final String id;
  final String prompt;
  final String pinyin;
  final List<String> options;
  final String answer;
  final String explanation;
  final String correction;

  factory AIExamQuestion.fromJson(Map<String, dynamic> json) {
    return AIExamQuestion(
      id: json['id'] as String? ?? '',
      prompt: json['prompt'] as String? ?? '',
      pinyin: json['pinyin'] as String? ?? '',
      options: (json['options'] as List<dynamic>? ?? const [])
          .map((o) => o.toString())
          .toList(growable: false),
      answer: json['answer'] as String? ?? '',
      explanation: json['explanation'] as String? ?? '',
      correction: json['correction'] as String? ?? '',
    );
  }
}

class AIExam {
  const AIExam({
    required this.id,
    required this.title,
    required this.contentType,
    required this.questionCount,
    required this.durationMinutes,
    required this.durationSeconds,
    required this.status,
    required this.createdAt,
    this.hskLevel,
    this.topic,
    this.questions = const [],
    this.score,
    this.userAnswers = const {},
    this.aiFeedback,
    this.submittedAt,
    this.isStandardPreset = false,
  });

  final int id;
  final String title;
  final String contentType;
  final int? hskLevel;
  final String? topic;
  final int questionCount;
  final int durationMinutes;
  final int durationSeconds;
  final String status;
  final int createdAt;
  final int? submittedAt;
  final List<AIExamQuestion> questions;
  final double? score;
  final Map<String, String> userAnswers;
  final AIExamFeedback? aiFeedback;
  final bool isStandardPreset;

  factory AIExam.fromJson(Map<String, dynamic> json) {
    final rawQuestions = json['questions'] as List<dynamic>? ?? const [];
    final questions = rawQuestions
        .map((q) => AIExamQuestion.fromJson(q as Map<String, dynamic>))
        .toList(growable: false);

    final rawAnswers = json['user_answers'] as Map<String, dynamic>? ?? const {};
    final userAnswers = rawAnswers.map((k, v) => MapEntry(k, v.toString()));

    AIExamFeedback? feedback;
    if (json['ai_feedback'] != null && json['ai_feedback'] is Map<String, dynamic>) {
      feedback = AIExamFeedback.fromJson(json['ai_feedback'] as Map<String, dynamic>);
    }

    return AIExam(
      id: json['id'] as int,
      title: json['title'] as String? ?? 'Đề thi tiếng Trung',
      contentType: json['content_type'] as String? ?? 'random',
      hskLevel: json['hsk_level'] as int?,
      topic: json['topic'] as String?,
      questionCount: json['question_count'] as int? ?? questions.length,
      durationMinutes: json['duration_minutes'] as int? ?? 5,
      durationSeconds: json['duration_seconds'] as int? ?? ((json['duration_minutes'] as int? ?? 5) * 60),
      status: json['status'] as String? ?? 'pending',
      createdAt: json['created_at'] as int? ?? 0,
      submittedAt: json['submitted_at'] as int?,
      questions: questions,
      score: (json['score'] as num?)?.toDouble(),
      userAnswers: userAnswers,
      aiFeedback: feedback,
      isStandardPreset: json['is_standard_preset'] as bool? ?? false,
    );
  }
}

class AIExamFeedbackItem {
  const AIExamFeedbackItem({
    required this.id,
    required this.prompt,
    required this.pinyin,
    required this.options,
    required this.userAnswer,
    required this.correctAnswer,
    required this.isCorrect,
    required this.explanation,
    required this.correction,
  });

  final String id;
  final String prompt;
  final String pinyin;
  final List<String> options;
  final String userAnswer;
  final String correctAnswer;
  final bool isCorrect;
  final String explanation;
  final String correction;

  factory AIExamFeedbackItem.fromJson(Map<String, dynamic> json) {
    return AIExamFeedbackItem(
      id: json['id'] as String? ?? '',
      prompt: json['prompt'] as String? ?? '',
      pinyin: json['pinyin'] as String? ?? '',
      options: (json['options'] as List<dynamic>? ?? const [])
          .map((o) => o.toString())
          .toList(growable: false),
      userAnswer: json['user_answer'] as String? ?? '',
      correctAnswer: json['correct_answer'] as String? ?? '',
      isCorrect: json['is_correct'] as bool? ?? false,
      explanation: json['explanation'] as String? ?? '',
      correction: json['correction'] as String? ?? '',
    );
  }
}

class AIExamFeedback {
  const AIExamFeedback({
    required this.score,
    required this.correctCount,
    required this.totalQuestions,
    required this.summary,
    required this.details,
  });

  final double score;
  final int correctCount;
  final int totalQuestions;
  final String summary;
  final List<AIExamFeedbackItem> details;

  factory AIExamFeedback.fromJson(Map<String, dynamic> json) {
    final rawDetails = json['details'] as List<dynamic>? ?? const [];
    return AIExamFeedback(
      score: (json['score'] as num?)?.toDouble() ?? 0.0,
      correctCount: json['correct_count'] as int? ?? 0,
      totalQuestions: json['total_questions'] as int? ?? 0,
      summary: json['summary'] as String? ?? '',
      details: rawDetails
          .map((d) => AIExamFeedbackItem.fromJson(d as Map<String, dynamic>))
          .toList(growable: false),
    );
  }
}

class AIExamService {
  AIExamService({
    required this.baseUrl,
    required this.tokenProvider,
    http.Client? client,
  }) : _client = client ?? http.Client();

  final String baseUrl;
  final Future<String?> Function() tokenProvider;
  final http.Client _client;

  Future<Map<String, String>> _headers() async {
    final token = await tokenProvider();
    final headers = <String, String>{'Content-Type': 'application/json'};
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  Future<AIExam> generateExam({
    required int questionCount,
    required String contentType,
    int? hskLevel,
    String? topic,
  }) async {
    final headers = await _headers();
    final uri = Uri.parse('$baseUrl/me/ai-exams/generate');
    final response = await _client.post(
      uri,
      headers: headers,
      body: jsonEncode({
        'question_count': questionCount,
        'content_type': contentType,
        if (hskLevel != null) 'hsk_level': hskLevel,
        if (topic != null && topic.isNotEmpty) 'topic': topic,
      }),
    );

    if (response.statusCode != 201) {
      final error = jsonDecode(utf8.decode(response.bodyBytes));
      throw Exception(error['detail'] ?? 'Không thể tạo đề thi');
    }

    final data = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    return AIExam.fromJson(data);
  }

  Future<Map<String, List<AIExam>>> listExams({bool includeStandard = true}) async {
    final headers = await _headers();
    final uri = Uri.parse('$baseUrl/me/ai-exams?include_standard=$includeStandard');
    final response = await _client.get(uri, headers: headers);

    if (response.statusCode != 200) {
      throw Exception('Không thể tải danh sách đề thi');
    }

    final data = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    final pendingRaw = data['pending'] as List<dynamic>? ?? const [];
    final completedRaw = data['completed'] as List<dynamic>? ?? const [];
    final standardRaw = data['standard_hsk'] as List<dynamic>? ?? const [];

    return {
      'pending': pendingRaw.map((e) => AIExam.fromJson(e as Map<String, dynamic>)).toList(),
      'completed': completedRaw.map((e) => AIExam.fromJson(e as Map<String, dynamic>)).toList(),
      'standard_hsk': standardRaw.map((e) => AIExam.fromJson(e as Map<String, dynamic>)).toList(),
    };
  }

  Future<List<AIExam>> getStandardPresets() async {
    final headers = await _headers();
    final uri = Uri.parse('$baseUrl/me/ai-exams/standard-presets');
    final response = await _client.get(uri, headers: headers);

    if (response.statusCode != 200) {
      throw Exception('Không thể tải danh sách đề thi HSK chuẩn');
    }

    final data = jsonDecode(utf8.decode(response.bodyBytes)) as List<dynamic>;
    return data.map((e) => AIExam.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<AIExam> getExam(int examId) async {
    final headers = await _headers();
    final uri = Uri.parse('$baseUrl/me/ai-exams/$examId');
    final response = await _client.get(uri, headers: headers);

    if (response.statusCode != 200) {
      final error = jsonDecode(utf8.decode(response.bodyBytes));
      throw Exception(error['detail'] ?? 'Không thể tải đề thi');
    }

    final data = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    return AIExam.fromJson(data);
  }

  Future<AIExamFeedback> submitExam(int examId, Map<String, String> answers) async {
    final headers = await _headers();
    final uri = Uri.parse('$baseUrl/me/ai-exams/$examId/submit');
    final response = await _client.post(
      uri,
      headers: headers,
      body: jsonEncode({'answers': answers}),
    );

    if (response.statusCode != 200) {
      final error = jsonDecode(utf8.decode(response.bodyBytes));
      throw Exception(error['detail'] ?? 'Lỗi khi nộp bài');
    }

    final data = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    final feedbackData = data['feedback'] as Map<String, dynamic>;
    return AIExamFeedback.fromJson(feedbackData);
  }

  Future<void> deleteExam(int examId) async {
    final headers = await _headers();
    final uri = Uri.parse('$baseUrl/me/ai-exams/$examId');
    final response = await _client.delete(uri, headers: headers);

    if (response.statusCode != 204 && response.statusCode != 200) {
      throw Exception('Không thể xóa đề thi');
    }
  }

  Future<List<Map<String, String>>> loadTopics() async {
    final uri = Uri.parse('$baseUrl/ai-exams/topics');
    final response = await _client.get(uri);
    if (response.statusCode == 200) {
      final list = jsonDecode(utf8.decode(response.bodyBytes)) as List<dynamic>;
      return list
          .map((item) => {
                'id': item['id'] as String,
                'label': item['label'] as String,
              })
          .toList();
    }
    return const [];
  }
}
