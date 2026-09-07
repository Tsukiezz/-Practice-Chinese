import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';

import '../theme/app_theme.dart';
import '../widgets/common.dart';

class CustomExam {
  CustomExam({
    required this.id,
    required this.title,
    required this.section,
    required this.questions,
    required this.createdAt,
  });

  final String id;
  final String title;
  final String section;
  final List<CustomQuestion> questions;
  final int createdAt;

  Map<String, dynamic> toJson() => <String, dynamic>{
        'id': id,
        'title': title,
        'section': section,
        'questions': questions.map((q) => q.toJson()).toList(growable: false),
        'created_at': createdAt,
      };

  factory CustomExam.fromJson(Map<String, dynamic> json) {
    final questions = (json['questions'] as List<dynamic>? ?? const <dynamic>[]);
    return CustomExam(
      id: json['id'] as String,
      title: json['title'] as String,
      section: json['section'] as String,
      questions: questions
          .map((q) => CustomQuestion.fromJson(q as Map<String, dynamic>))
          .toList(growable: false),
      createdAt: json['created_at'] as int,
    );
  }
}

class CustomQuestion {
  const CustomQuestion({
    required this.id,
    required this.prompt,
    required this.options,
    required this.answer,
    this.audioUrl = '',
    this.transcript = '',
  });

  final String id;
  final String prompt;
  final List<String> options;
  final String answer;
  final String audioUrl;
  final String transcript;

  Map<String, dynamic> toJson() => <String, dynamic>{
        'id': id,
        'prompt': prompt,
        'options': options,
        'answer': answer,
        'audio_url': audioUrl,
        'transcript': transcript,
      };

  factory CustomQuestion.fromJson(Map<String, dynamic> json) {
    return CustomQuestion(
      id: json['id'] as String,
      prompt: json['prompt'] as String,
      options: (json['options'] as List<dynamic>? ?? const [])
          .map((o) => o as String)
          .toList(growable: false),
      answer: json['answer'] as String,
      audioUrl: json['audio_url'] as String? ?? '',
      transcript: json['transcript'] as String? ?? '',
    );
  }
}

class CustomExamResult {
  CustomExamResult({
    required this.examId,
    required this.score,
    required this.answers,
    required this.createdAt,
  });

  final String examId;
  final double score;
  final Map<String, String> answers;
  final int createdAt;

  Map<String, dynamic> toJson() => <String, dynamic>{
        'exam_id': examId,
        'score': score,
        'answers': answers,
        'created_at': createdAt,
      };

  factory CustomExamResult.fromJson(Map<String, dynamic> json) {
    final answers = (json['answers'] as Map<String, dynamic>? ?? const <String, dynamic>{});
    return CustomExamResult(
      examId: json['exam_id'] as String,
      score: (json['score'] as num).toDouble(),
      answers: answers.map((k, v) => MapEntry(k, v as String)),
      createdAt: json['created_at'] as int,
    );
  }
}

class CustomExamService {
  CustomExamService(this._prefs);

  final SharedPreferences _prefs;

  static CustomExamService? _instance;
  static CustomExamService? get instance => _instance;

  static Future<CustomExamService> create() async {
    final prefs = await SharedPreferences.getInstance();
    _instance = CustomExamService(prefs);
    return _instance!;
  }

  static const _examsKey = 'custom_exams';
  static const _resultsKey = 'custom_results';

  Future<void> saveExam(CustomExam exam) async {
    final exams = await loadExams();
    exams.add(exam);
    await _prefs.setString(
      _examsKey,
      jsonEncode(exams.map((e) => e.toJson()).toList(growable: false)),
    );
  }

  Future<List<CustomExam>> loadExams() async {
    final raw = _prefs.getString(_examsKey);
    if (raw == null || raw.isEmpty) return const <CustomExam>[];
    final list = jsonDecode(raw) as List<dynamic>;
    return list
        .map((item) => CustomExam.fromJson(item as Map<String, dynamic>))
        .toList(growable: false);
  }

  Future<void> saveResult(CustomExamResult result) async {
    final results = await loadResults();
    results.add(result);
    await _prefs.setString(
      _resultsKey,
      jsonEncode(results.map((r) => r.toJson()).toList(growable: false)),
    );
  }

  Future<List<CustomExamResult>> loadResults() async {
    final raw = _prefs.getString(_resultsKey);
    if (raw == null || raw.isEmpty) return const <CustomExamResult>[];
    final list = jsonDecode(raw) as List<dynamic>;
    return list
        .map((item) => CustomExamResult.fromJson(item as Map<String, dynamic>))
        .toList(growable: false);
  }
}
