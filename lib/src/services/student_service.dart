import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

class StudentResult {
  const StudentResult({
    required this.id,
    required this.examId,
    required this.kind,
    required this.content,
    required this.score,
    required this.originalScore,
    required this.feedback,
    required this.gradedBy,
    required this.version,
    required this.createdAt,
    required this.overrides,
    this.latestScore,
    this.latestFeedback,
  });

  final int id;
  final int? examId;
  final String kind;
  final String content;
  final double score;
  final double originalScore;
  final String feedback;
  final String gradedBy;
  final int version;
  final int createdAt;
  final List<ScoreOverride> overrides;
  final double? latestScore;
  final String? latestFeedback;

  double get reviewScore => latestScore ?? score;
  String get reviewFeedback => latestFeedback ?? feedback;

  factory StudentResult.fromJson(Map<String, dynamic> json) {
    final overrides =
        (json['overrides'] as List<dynamic>? ?? const <dynamic>[]);
    final latest = json['latest_result'] as Map<String, dynamic>?;
    return StudentResult(
      id: json['id'] as int,
      examId: json['exam_id'] as int?,
      kind: json['kind'] as String,
      content: json['content'] as String,
      score: (json['score'] as num).toDouble(),
      originalScore: (json['original_score'] as num).toDouble(),
      feedback: json['feedback'] as String? ?? '',
      gradedBy: json['graded_by'] as String,
      version: json['version'] as int,
      createdAt: json['created_at'] as int,
      overrides: overrides
          .map((item) => ScoreOverride.fromJson(item as Map<String, dynamic>))
          .toList(growable: false),
      latestScore: (latest?['score'] as num?)?.toDouble(),
      latestFeedback: latest?['feedback'] as String?,
    );
  }
}

class ScoreOverride {
  const ScoreOverride({
    required this.oldScore,
    required this.newScore,
    required this.reason,
    required this.createdAt,
  });

  final double oldScore;
  final double newScore;
  final String reason;
  final int createdAt;

  factory ScoreOverride.fromJson(Map<String, dynamic> json) {
    return ScoreOverride(
      oldScore: (json['old_score'] as num).toDouble(),
      newScore: (json['new_score'] as num).toDouble(),
      reason: json['reason'] as String,
      createdAt: json['created_at'] as int,
    );
  }
}

class StudentDashboard {
  const StudentDashboard({
    required this.results,
    required this.averageScore,
    required this.needsReview,
    required this.vocabularyCount,
    required this.streak,
    required this.progressPercent,
    required this.skillScores,
  });

  final int results;
  final double averageScore;
  final int needsReview;
  final int vocabularyCount;
  final int streak;
  final double progressPercent;
  final Map<String, double> skillScores;

  factory StudentDashboard.fromJson(Map<String, dynamic> json) {
    return StudentDashboard(
      results: json['results'] as int,
      averageScore: (json['average_score'] as num).toDouble(),
      needsReview: json['needs_review'] as int,
      vocabularyCount: json['vocabulary_count'] as int,
      streak: json['streak'] as int,
      progressPercent: (json['progress_percent'] as num).toDouble(),
      skillScores: (json['skill_scores'] as Map<String, dynamic>).map(
        (key, value) => MapEntry(key, (value as num).toDouble()),
      ),
    );
  }
}

class VocabularyEntry {
  const VocabularyEntry({
    required this.id,
    required this.hanzi,
    required this.pinyin,
    required this.meaning,
    required this.hsk,
    required this.example,
    required this.audioUrl,
    this.topics = const [],
    this.senses = const [],
    this.lookupCount = 0,
    this.lastLookedAt = 0,
  });

  final int id, hsk, lookupCount, lastLookedAt;
  final String hanzi, pinyin, meaning, example, audioUrl;
  final List<String> topics;
  final List<Map<String, dynamic>> senses;

  factory VocabularyEntry.fromJson(Map<String, dynamic> json) {
    return VocabularyEntry(
      id: (json['word_id'] ?? json['id']) as int,
      hanzi: json['hanzi'] as String,
      pinyin: json['pinyin'] as String,
      meaning: json['meaning'] as String,
      hsk: json['hsk'] as int,
      example: json['example'] as String? ?? '',
      audioUrl: json['audio_url'] as String? ?? '',
      topics: (json['topics'] as List? ?? []).cast<String>(),
      senses: (json['senses'] as List? ?? [])
          .map((s) => Map<String, dynamic>.from(s as Map))
          .toList(),
      lookupCount: json['lookup_count'] as int? ?? 0,
      lastLookedAt: json['last_looked_at'] as int? ?? 0,
    );
  }
}

class VocabularyPage {
  const VocabularyPage({
    required this.items,
    required this.total,
    this.offset = 0,
    this.limit = 40,
    this.topics = const [],
  });
  final List<VocabularyEntry> items;
  final int total, offset, limit;
  final List<Map<String, dynamic>> topics;
}

class HandwritingCandidate {
  const HandwritingCandidate({
    required this.hanzi,
    required this.confidence,
    required this.words,
  });

  final String hanzi;
  final double confidence;
  final List<VocabularyEntry> words;

  factory HandwritingCandidate.fromJson(Map<String, dynamic> json) =>
      HandwritingCandidate(
        hanzi: json['hanzi'] as String,
        confidence: (json['confidence'] as num).toDouble(),
        words: (json['words'] as List<dynamic>? ?? const [])
            .map(
              (word) => VocabularyEntry.fromJson(word as Map<String, dynamic>),
            )
            .toList(growable: false),
      );
}

class HandwritingRecognitionResult {
  const HandwritingRecognitionResult({
    required this.score,
    required this.feedback,
    required this.recognizedHanzi,
    required this.candidates,
  });

  final double score;
  final String feedback;
  final String recognizedHanzi;
  final List<HandwritingCandidate> candidates;

  factory HandwritingRecognitionResult.fromJson(Map<String, dynamic> json) {
    final details = json['details'] as Map<String, dynamic>;
    return HandwritingRecognitionResult(
      score: (json['score'] as num).toDouble(),
      feedback: json['feedback'] as String,
      recognizedHanzi: details['recognized_hanzi'] as String,
      candidates: (details['candidates'] as List<dynamic>)
          .map(
            (candidate) => HandwritingCandidate.fromJson(
              candidate as Map<String, dynamic>,
            ),
          )
          .toList(growable: false),
    );
  }
}

class HandwritingGradeResult {
  const HandwritingGradeResult({
    required this.score,
    required this.feedback,
    required this.wrongStrokes,
    this.countScore = 0,
    this.orderPositionScore = 0,
    this.directionScore = 0,
  });

  final double score;
  final String feedback;
  final List<int> wrongStrokes;
  final double countScore;
  final double orderPositionScore;
  final double directionScore;

  factory HandwritingGradeResult.fromJson(Map<String, dynamic> json) {
    final details = json['details'] as Map<String, dynamic>;
    return HandwritingGradeResult(
      score: (json['score'] as num).toDouble(),
      feedback: json['feedback'] as String,
      wrongStrokes: (details['wrong_strokes'] as List<dynamic>)
          .map((index) => index as int)
          .toList(growable: false),
      countScore: (details['count_score'] as num?)?.toDouble() ?? 0,
      orderPositionScore:
          (details['order_position_score'] as num?)?.toDouble() ?? 0,
      directionScore: (details['direction_score'] as num?)?.toDouble() ?? 0,
    );
  }
}

class HandwritingRetryItem {
  const HandwritingRetryItem({
    required this.hanzi,
    required this.latestScore,
    required this.attempts,
    required this.lastPracticedAt,
  });

  final String hanzi;
  final double latestScore;
  final int attempts;
  final int lastPracticedAt;

  factory HandwritingRetryItem.fromJson(Map<String, dynamic> json) =>
      HandwritingRetryItem(
        hanzi: json['hanzi'] as String,
        latestScore: (json['latest_score'] as num).toDouble(),
        attempts: json['attempts'] as int,
        lastPracticedAt: json['last_practiced_at'] as int,
      );
}

class GrammarCorrectionError {
  const GrammarCorrectionError({
    required this.position,
    required this.original,
    required this.suggestion,
    required this.reason,
  });

  final String position;
  final String original;
  final String suggestion;
  final String reason;

  factory GrammarCorrectionError.fromJson(Map<String, dynamic> json) =>
      GrammarCorrectionError(
        position: json['position'] as String,
        original: json['original'] as String,
        suggestion: json['suggestion'] as String,
        reason: json['reason'] as String,
      );
}

class GrammarAnalysisResult {
  const GrammarAnalysisResult({
    required this.score,
    required this.feedback,
    required this.errors,
    required this.correctedSentence,
  });

  final double score;
  final String feedback;
  final List<GrammarCorrectionError> errors;
  final String correctedSentence;

  factory GrammarAnalysisResult.fromJson(Map<String, dynamic> json) {
    final details = json['details'] as Map<String, dynamic>;
    return GrammarAnalysisResult(
      score: (json['score'] as num).toDouble(),
      feedback: json['feedback'] as String,
      errors: (details['errors'] as List<dynamic>)
          .map(
            (error) =>
                GrammarCorrectionError.fromJson(error as Map<String, dynamic>),
          )
          .toList(growable: false),
      correctedSentence: details['corrected_sentence'] as String,
    );
  }
}

class CapabilityReport {
  const CapabilityReport({
    required this.skillScores,
    required this.feedback,
    required this.strengths,
    required this.improvements,
  });
  final Map<String, double> skillScores;
  final String feedback;
  final List<String> strengths, improvements;

  factory CapabilityReport.fromJson(Map<String, dynamic> json) =>
      CapabilityReport(
        skillScores: (json['skill_scores'] as Map<String, dynamic>).map(
          (key, value) => MapEntry(key, (value as num).toDouble()),
        ),
        feedback: json['feedback'] as String,
        strengths: (json['strengths'] as List<dynamic>).cast<String>(),
        improvements: (json['improvements'] as List<dynamic>).cast<String>(),
      );
}

class StudentApiException implements Exception {
  const StudentApiException(this.statusCode, this.message);

  final int? statusCode;
  final String message;

  @override
  String toString() => message;
}

class StudentService {
  StudentService({
    required this.baseUrl,
    required this.tokenProvider,
    http.Client? client,
  }) : _client = client ?? http.Client();

  final String baseUrl;
  final Future<String?> Function() tokenProvider;
  final http.Client _client;

  Future<Map<String, dynamic>> fetchLessons() async {
    final response = await _request(
      'GET',
      Uri.parse('$baseUrl/lessons'),
      requiresAuth: false,
    );
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> fetchLesson(String id) async {
    final response = await _request(
      'GET',
      Uri.parse('$baseUrl/lessons/${Uri.encodeComponent(id)}'),
      requiresAuth: false,
    );
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<List<Map<String, dynamic>>> fetchLessonProgress() async {
    final response = await _request('GET', Uri.parse('$baseUrl/me/lessons'));
    return (jsonDecode(response.body) as List).cast<Map<String, dynamic>>();
  }

  Future<void> saveLessonStage(String id, int stage) async {
    await _request(
      'PUT',
      Uri.parse('$baseUrl/me/lessons/${Uri.encodeComponent(id)}/progress'),
      body: jsonEncode({'stage': stage}),
    );
  }

  Future<Map<String, dynamic>> submitLesson(
    String id,
    Map<String, int> answers,
  ) async {
    final response = await _request(
      'POST',
      Uri.parse('$baseUrl/me/lessons/${Uri.encodeComponent(id)}/submit'),
      body: jsonEncode({'answers': answers}),
    );
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<List<StudentResult>> fetchMyResults() async {
    final response = await _request('GET', Uri.parse('$baseUrl/me/results'));
    try {
      final rows = jsonDecode(response.body) as List<dynamic>;
      return rows
          .map((row) => StudentResult.fromJson(row as Map<String, dynamic>))
          .toList(growable: false);
    } on Object {
      throw const StudentApiException(
        null,
        'Dữ liệu kết quả từ máy chủ không đúng định dạng.',
      );
    }
  }

  Future<StudentDashboard> fetchMyDashboard() async {
    final response = await _request('GET', Uri.parse('$baseUrl/me/dashboard'));
    try {
      return StudentDashboard.fromJson(
        jsonDecode(response.body) as Map<String, dynamic>,
      );
    } on Object {
      throw const StudentApiException(
        null,
        'Dữ liệu thống kê từ máy chủ không đúng định dạng.',
      );
    }
  }

  Future<CapabilityReport> fetchCapabilityReport() async {
    final response = await _request('GET', Uri.parse('$baseUrl/me/capability'));
    try {
      return CapabilityReport.fromJson(
        jsonDecode(response.body) as Map<String, dynamic>,
      );
    } on Object {
      throw const StudentApiException(
        null,
        'Báo cáo năng lực không đúng định dạng.',
      );
    }
  }

  Future<VocabularyPage> fetchVocabularyPage({
    String search = '',
    int? hsk,
    String? topic,
    int offset = 0,
  }) async {
    final uri = Uri.parse('$baseUrl/vocabulary/page').replace(
      queryParameters: {
        'search': search.trim(),
        'offset': '$offset',
        'limit': '40',
        if (hsk != null) 'hsk': '$hsk',
        if (topic != null) 'topic': topic,
      },
    );
    final response = await _request('GET', uri, requiresAuth: false);
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return VocabularyPage(
      items: (data['items'] as List)
          .map((v) => VocabularyEntry.fromJson(v as Map<String, dynamic>))
          .toList(),
      total: data['total'] as int,
      offset: data['offset'] as int,
      limit: data['limit'] as int,
      topics: (data['topics'] as List)
          .map((t) => Map<String, dynamic>.from(t as Map))
          .toList(),
    );
  }

  Future<List<VocabularyEntry>> fetchVocabulary({String search = ''}) async {
    final uri = Uri.parse('$baseUrl/vocabulary').replace(
      queryParameters: search.trim().isEmpty ? null : {'search': search.trim()},
    );
    final response = await _request('GET', uri, requiresAuth: false);
    return _decodeVocabularyList(response.body);
  }

  Future<List<VocabularyEntry>> fetchDictionaryHistory() async {
    final response = await _request(
      'GET',
      Uri.parse('$baseUrl/me/dictionary-history'),
    );
    return _decodeVocabularyList(response.body);
  }

  Future<List<VocabularyEntry>> fetchSavedVocabulary() async {
    final response = await _request(
      'GET',
      Uri.parse('$baseUrl/me/saved-words'),
    );
    return _decodeVocabularyList(response.body);
  }

  Future<void> setWordSaved(int wordId, bool saved) async {
    await _request(
      saved ? 'PUT' : 'DELETE',
      Uri.parse('$baseUrl/me/saved-words/$wordId'),
    );
  }

  Future<VocabularyEntry> recordDictionaryLookup(
    VocabularyEntry word,
    String query,
  ) async {
    final response = await _request(
      'POST',
      Uri.parse('$baseUrl/me/dictionary-history/${word.id}'),
      body: jsonEncode({'query': query}),
    );
    return VocabularyEntry.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  Future<List<StudentResult>> fetchReviewItems(String kind) async {
    final response = await _request(
      'GET',
      Uri.parse('$baseUrl/me/review-items?kind=$kind&below=80'),
    );
    final rows = jsonDecode(response.body) as List<dynamic>;
    return rows
        .map((row) => StudentResult.fromJson(row as Map<String, dynamic>))
        .toList(growable: false);
  }

  Future<List<HandwritingRetryItem>> fetchHandwritingRetryItems() async {
    final response = await _request(
      'GET',
      Uri.parse('$baseUrl/me/handwriting-retry-items'),
    );
    try {
      return (jsonDecode(response.body) as List<dynamic>)
          .map(
            (row) => HandwritingRetryItem.fromJson(row as Map<String, dynamic>),
          )
          .toList(growable: false);
    } on Object {
      throw const StudentApiException(
        null,
        'Danh sách chữ cần luyện lại không đúng định dạng.',
      );
    }
  }

  Future<StudentResult> resubmitWriting(
    int sourceResultId,
    String content,
  ) async {
    final response = await _request(
      'POST',
      Uri.parse('$baseUrl/me/review/writing/$sourceResultId'),
      body: jsonEncode({'content': content}),
    );
    return StudentResult.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  Future<StudentResult> submitWriting(String content) async {
    final response = await _request(
      'POST',
      Uri.parse('$baseUrl/writing/submit'),
      body: jsonEncode({'content': content}),
    );
    return StudentResult.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  Future<String> translateText(
    String text,
    String source,
    String target,
  ) async {
    final response = await _request(
      'POST',
      Uri.parse('$baseUrl/translation/text'),
      requiresAuth: false,
      body: jsonEncode({'text': text, 'source': source, 'target': target}),
      timeout: const Duration(seconds: 75),
    );
    return (jsonDecode(response.body) as Map<String, dynamic>)['translation']
        as String;
  }

  Future<Map<String, dynamic>> fetchStudyGoals() async {
    final response = await _request('GET', Uri.parse('$baseUrl/me/goals'));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<String> fetchAvatar() async {
    final response = await _request('GET', Uri.parse('$baseUrl/account'));
    return (jsonDecode(response.body) as Map<String, dynamic>)['avatar']
            as String? ??
        '';
  }

  Future<Map<String, dynamic>> generatePersonalizedPractice() async {
    final response = await _request(
      'POST',
      Uri.parse('$baseUrl/me/personalized-practice'),
      timeout: const Duration(seconds: 75),
    );
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> submitPersonalizedPractice(
    int plan,
    int index,
    String text,
  ) async {
    final response = await _request(
      'POST',
      Uri.parse('$baseUrl/me/personalized-practice/$plan/$index'),
      body: jsonEncode({'text': text}),
      timeout: const Duration(seconds: 75),
    );
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<GrammarAnalysisResult> analyzeGrammar(
    String sentence, {
    String context = '',
    bool guest = false,
  }) async {
    final response = await _request(
      'POST',
      Uri.parse(
        guest ? '$baseUrl/guest/grammar' : '$baseUrl/translation/analyze',
      ),
      requiresAuth: !guest,
      body: jsonEncode({'sentence': sentence, 'context': context}),
      timeout: const Duration(seconds: 75),
    );
    try {
      return GrammarAnalysisResult.fromJson(
        jsonDecode(response.body) as Map<String, dynamic>,
      );
    } on Object {
      throw const StudentApiException(
        null,
        'Kết quả sửa câu từ máy chủ không đúng định dạng.',
      );
    }
  }

  Future<HandwritingGradeResult> submitHandwriting(
    String target,
    List<List<Map<String, double>>> strokes, {
    int? sourceResultId,
  }) async {
    final path = sourceResultId == null
        ? '/handwriting/submit'
        : '/me/review/handwriting/$sourceResultId';
    final response = await _request(
      'POST',
      Uri.parse('$baseUrl$path'),
      body: jsonEncode({'target': target, 'strokes': strokes}),
    );
    try {
      return HandwritingGradeResult.fromJson(
        jsonDecode(response.body) as Map<String, dynamic>,
      );
    } on Object {
      throw const StudentApiException(
        null,
        'Kết quả chấm nét từ máy chủ không đúng định dạng.',
      );
    }
  }

  Future<HandwritingRecognitionResult> recognizeHandwriting(
    List<List<Map<String, double>>> strokes, {
    bool guest = false,
  }) async {
    final response = await _request(
      'POST',
      Uri.parse(
        guest ? '$baseUrl/guest/handwriting' : '$baseUrl/handwriting/recognize',
      ),
      requiresAuth: !guest,
      body: jsonEncode({'strokes': strokes}),
      timeout: const Duration(seconds: 75),
    );
    try {
      return HandwritingRecognitionResult.fromJson(
        jsonDecode(response.body) as Map<String, dynamic>,
      );
    } on Object {
      throw const StudentApiException(
        null,
        'Kết quả nhận dạng chữ viết tay không đúng định dạng.',
      );
    }
  }

  List<VocabularyEntry> _decodeVocabularyList(String body) {
    try {
      return (jsonDecode(body) as List<dynamic>)
          .map((row) => VocabularyEntry.fromJson(row as Map<String, dynamic>))
          .toList(growable: false);
    } on Object {
      throw const StudentApiException(
        null,
        'Dữ liệu từ vựng không đúng định dạng.',
      );
    }
  }

  Future<http.Response> _request(
    String method,
    Uri uri, {
    String? body,
    bool requiresAuth = true,
    Duration? timeout,
  }) async {
    final token = (await tokenProvider())?.trim() ?? '';
    if (requiresAuth && token.isEmpty) {
      throw const StudentApiException(
        401,
        'Bạn cần đăng nhập bằng tài khoản học viên.',
      );
    }

    try {
      final headers = {
        if (token.isNotEmpty) 'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      };
      final response = await (switch (method) {
        'POST' => _client.post(uri, headers: headers, body: body),
        'PUT' => _client.put(uri, headers: headers, body: body),
        'DELETE' => _client.delete(uri, headers: headers),
        _ => _client.get(uri, headers: headers),
      })
          .timeout(timeout ?? Duration(seconds: method == 'POST' || uri.path.endsWith('/capability') ? 75 : 15));
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return response;
      }
      throw StudentApiException(response.statusCode, _errorMessage(response));
    } on StudentApiException {
      rethrow;
    } on TimeoutException {
      throw const StudentApiException(
        null,
        'AI đang phản hồi chậm. Hãy kiểm tra lịch sử bài làm trước khi nộp lại.',
      );
    } on Exception {
      throw const StudentApiException(
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
      // fall through
    }
    return 'Máy chủ không xử lý được yêu cầu (${response.statusCode}).';
  }
}
