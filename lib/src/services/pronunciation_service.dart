import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/foundation.dart';

import 'pronunciation_service_stub.dart'
    if (dart.library.js_interop) 'pronunciation_service_web.dart';

class PronunciationService {
  static final AudioPlayer _player = AudioPlayer();

  static Future<void> playWord(
    String text, {
    String? audioUrl,
    String? baseUrl,
  }) async {
    final clean = text.trim();
    if (clean.isEmpty) return;

    // 1. If audioUrl is non-empty, try playing that direct audio
    if (audioUrl != null && audioUrl.trim().isNotEmpty) {
      try {
        final url = baseUrl != null
            ? Uri.parse(baseUrl).resolve(audioUrl).toString()
            : audioUrl;
        await _player.stop();
        await _player.play(UrlSource(url)).timeout(const Duration(seconds: 10));
        return;
      } catch (_) {}
    }

    // 2. On web, use native Web Speech Synthesis (0ms latency, native zh-CN)
    if (kIsWeb) {
      try {
        playChineseSpeech(clean);
        return;
      } catch (_) {}
    }

    // 3. Fallback: call backend TTS
    if (baseUrl != null) {
      try {
        final ttsUrl = Uri.parse(baseUrl)
            .resolve('/api/tts?text=${Uri.encodeComponent(clean)}')
            .toString();
        await _player.stop();
        await _player.play(UrlSource(ttsUrl)).timeout(const Duration(seconds: 10));
      } catch (_) {}
    }
  }
}
