class ReadingQuestion {
  const ReadingQuestion({
    required this.id,
    required this.section,
    required this.prompt,
    required this.options,
    this.audioUrl = '',
    this.transcript = '',
    this.explanation = '',
  });

  final String id;
  final String section;
  final String prompt;
  final List<String> options;
  final String audioUrl;
  final String transcript;
  final String explanation;

  factory ReadingQuestion.fromJson(Map<String, dynamic> json) {
    return ReadingQuestion(
      id: json['id'] as String,
      section: json['section'] as String,
      prompt: json['prompt'] as String,
      options: (json['options'] as List<dynamic>? ?? const [])
          .map((option) => option as String)
          .toList(growable: false),
      audioUrl: (json['audio_url'] as String? ?? ''),
      transcript: (json['transcript'] as String? ?? ''),
      explanation: (json['explanation'] as String? ?? ''),
    );
  }
}

class ReadingExam {
  const ReadingExam({
    required this.id,
    required this.title,
    required this.hsk,
    required this.durationMinutes,
    required this.version,
    required this.questions,
  });

  final int id;
  final String title;
  final int hsk;
  final int durationMinutes;
  final int version;
  final List<ReadingQuestion> questions;

  factory ReadingExam.fromJson(Map<String, dynamic> json) {
    return ReadingExam(
      id: json['id'] as int,
      title: json['title'] as String,
      hsk: json['hsk'] as int,
      durationMinutes: json['duration_minutes'] as int,
      version: json['version'] as int,
      questions: (json['questions'] as List<dynamic>)
          .map((question) => ReadingQuestion.fromJson(
                question as Map<String, dynamic>,
              ))
          .toList(growable: false),
    );
  }
}

class ReadingReviewItem {
  const ReadingReviewItem({
    required this.id,
    required this.prompt,
    required this.answer,
    required this.submittedAnswer,
    required this.explanation,
    this.transcript = '',
  });

  final String id;
  final String prompt;
  final String answer;
  final String submittedAnswer;
  final String explanation;
  final String transcript;

  bool get isCorrect => answer.trim() == submittedAnswer.trim();
}

class ReadingResult {
  const ReadingResult({
    required this.id,
    required this.score,
    required this.feedback,
    required this.reviewItems,
  });

  final int id;
  final double score;
  final String feedback;
  final List<ReadingReviewItem> reviewItems;
}
