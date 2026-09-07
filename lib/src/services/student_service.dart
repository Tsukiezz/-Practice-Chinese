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

  factory StudentResult.fromJson(Map<String, dynamic> json) {
    final overrides = (json['overrides'] as List<dynamic>? ?? const <dynamic>[]);
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
  });

  final int results;
  final double averageScore;
  final int needsReview;

  factory StudentDashboard.fromJson(Map<String, dynamic> json) {
    return StudentDashboard(
      results: json['results'] as int,
      averageScore: (json['average_score'] as num).toDouble(),
      needsReview: json['needs_review'] as int,
    );
  }
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
      return StudentDashboard.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
    } on Object {
      throw const StudentApiException(
        null,
        'Dữ liệu thống kê từ máy chủ không đúng định dạng.',
      );
    }
  }

  Future<http.Response> _request(String method, Uri uri, {String? body}) async {
    final token = (await tokenProvider())?.trim() ?? '';
    if (token.isEmpty) {
      throw const StudentApiException(
        401,
        'Bạn cần đăng nhập bằng tài khoản học viên.',
      );
    }

    try {
      final headers = {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      };
      final response = method == 'POST'
          ? await _client.post(uri, headers: headers, body: body).timeout(const Duration(seconds: 15))
          : await _client.get(uri, headers: headers).timeout(const Duration(seconds: 15));
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return response;
      }
      throw StudentApiException(response.statusCode, _errorMessage(response));
    } on StudentApiException {
      rethrow;
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
