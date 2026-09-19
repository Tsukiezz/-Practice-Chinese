import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../services/student_service.dart';
import 'vocabulary_screen.dart';

class GuestDictionaryScreen extends StatefulWidget {
  const GuestDictionaryScreen({super.key, required this.baseUrl});
  final String baseUrl;

  @override
  State<GuestDictionaryScreen> createState() => _GuestDictionaryScreenState();
}

class _GuestDictionaryScreenState extends State<GuestDictionaryScreen> {
  final _client = http.Client();
  late final _service = StudentService(
    baseUrl: widget.baseUrl,
    tokenProvider: () async => null,
    client: _client,
  );

  @override
  void dispose() {
    _client.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Khám phá cùng HanziGo')),
    body: Column(
      children: [
        const Padding(
          padding: EdgeInsets.fromLTRB(20, 8, 20, 16),
          child: Text(
            'Tra từ và nghe phát âm miễn phí. Đăng nhập để lưu từ vựng và tiến trình học.',
          ),
        ),
        Expanded(child: VocabularyScreen(service: _service, guest: true)),
      ],
    ),
  );
}
