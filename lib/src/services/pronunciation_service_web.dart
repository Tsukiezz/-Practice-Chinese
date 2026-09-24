import 'package:web/web.dart' as web;

void playChineseSpeech(String text) {
  try {
    final synth = web.window.speechSynthesis;
    synth.cancel();
    final utterance = web.SpeechSynthesisUtterance(text);
    utterance.lang = 'zh-CN';
    utterance.rate = 0.85; // slightly slower for language learners
    synth.speak(utterance);
  } catch (_) {}
}
