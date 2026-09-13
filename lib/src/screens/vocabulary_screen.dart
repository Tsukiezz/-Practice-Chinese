import 'package:flutter/material.dart';

import '../data/learning_data.dart';
import '../data/pronunciation_service.dart';
import '../data/vocabulary_service.dart';
import '../theme/app_theme.dart';
import '../widgets/common.dart';
import 'notebook_screen.dart';
import 'translation_screen.dart';

class VocabularyScreen extends StatefulWidget {
  const VocabularyScreen({super.key});
  @override
  State<VocabularyScreen> createState() => _VocabularyScreenState();
}

class _VocabularyScreenState extends State<VocabularyScreen> {
  final _service = VocabularyService.instance;
  final _audio = PronunciationService.instance;

  String _query = '';
  List<ChineseWord> _results = words;
  bool _isFromServer = false;
  bool _searching = false;
  Set<String> _savedHanzi = {};
  String? _playingHanzi;
  String? _audioErrorHanzi;

  @override
  void initState() {
    super.initState();
    _loadSaved();
  }

  Future<void> _loadSaved() async {
    final saved = <String>{};
    for (final w in words) {
      if (await _service.isSaved(w.hanzi)) saved.add(w.hanzi);
    }
    if (mounted) setState(() => _savedHanzi = saved);
  }

  // UC-02 (#6) Tra cứu bằng phím: gõ tới đâu tìm tới đó, ưu tiên dữ liệu
  // server nhưng vẫn hoạt động mượt khi backend chưa sẵn sàng.
  Future<void> _runSearch(String value) async {
    setState(() {
      _query = value;
      _searching = true;
    });
    final result = await _service.search(value);
    if (!mounted || _query != value) return;
    setState(() {
      _results = result.words;
      _isFromServer = result.isFromServer;
      _searching = false;
    });
  }

  // UC-02 (#10) Nghe phát âm mẫu, có loading + báo lỗi khi thiếu audio.
  Future<void> _playAudio(String hanzi) async {
    setState(() {
      _playingHanzi = hanzi;
      _audioErrorHanzi = null;
    });
    final ok = await _audio.play(hanzi);
    if (!mounted) return;
    setState(() {
      _playingHanzi = null;
      _audioErrorHanzi = ok ? null : hanzi;
    });
    if (!ok) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Chưa có audio phát âm cho từ này.')),
      );
    }
  }

  // UC-02 (#11) Sổ tay từ vựng: lưu/bỏ lưu, cập nhật icon ngay lập tức.
  Future<void> _toggleSave(ChineseWord word) async {
    final nowSaved = await _service.toggleSaved(word);
    if (!mounted) return;
    setState(() {
      nowSaved ? _savedHanzi.add(word.hanzi) : _savedHanzi.remove(word.hanzi);
    });
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        children: [
          ScreenHeader(
            eyebrow: 'Bộ nhớ cá nhân',
            title: 'Từ vựng',
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                IconButton(
                  tooltip: 'Sổ tay từ vựng',
                  icon: const Icon(Icons.bookmark_rounded, color: AppTheme.jade),
                  onPressed: () => Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const NotebookScreen()),
                  ),
                ),
                IconButton(
                  tooltip: 'Dịch đoạn văn',
                  icon: const Icon(Icons.translate_rounded, color: AppTheme.jade),
                  onPressed: () => Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const TranslationScreen()),
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 0, 20, 6),
            child: TextField(
              onChanged: _runSearch,
              decoration: InputDecoration(
                hintText: 'Tìm Hán tự, pinyin hoặc nghĩa...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searching
                    ? const Padding(
                        padding: EdgeInsets.all(14),
                        child: SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                      )
                    : null,
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: BorderSide.none,
                ),
              ),
            ),
          ),
          if (_query.isNotEmpty && !_isFromServer)
            const Padding(
              padding: EdgeInsets.fromLTRB(20, 0, 20, 8),
              child: Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  'Đang dùng dữ liệu ngoại tuyến (chưa kết nối được máy chủ).',
                  style: TextStyle(color: Colors.grey, fontSize: 11),
                ),
              ),
            ),
          Expanded(
            child: _results.isEmpty
                ? const Center(
                    child: Text('Không tìm thấy từ phù hợp.', style: TextStyle(color: Colors.grey)),
                  )
                : ListView.separated(
                    padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
                    itemCount: _results.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 10),
                    itemBuilder: (context, index) {
                      final w = _results[index];
                      final isSaved = _savedHanzi.contains(w.hanzi);
                      final isPlaying = _playingHanzi == w.hanzi;
                      final hasAudioError = _audioErrorHanzi == w.hanzi;
                      return Card(
                        child: Padding(
                          padding: const EdgeInsets.all(15),
                          child: Row(
                            children: [
                              HanziAvatar(w.hanzi, size: 58, color: const Color(0xFFFFEDE4)),
                              const SizedBox(width: 14),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(w.pinyin, style: const TextStyle(color: AppTheme.red, fontWeight: FontWeight.w700)),
                                    Text(w.meaning, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800)),
                                    const SizedBox(height: 4),
                                    Text(w.example, style: const TextStyle(color: Colors.grey, fontSize: 11)),
                                    if (hasAudioError)
                                      const Padding(
                                        padding: EdgeInsets.only(top: 4),
                                        child: Text('Chưa có audio', style: TextStyle(color: AppTheme.red, fontSize: 10)),
                                      ),
                                  ],
                                ),
                              ),
                              IconButton(
                                tooltip: 'Nghe phát âm',
                                onPressed: isPlaying ? null : () => _playAudio(w.hanzi),
                                icon: isPlaying
                                    ? const SizedBox(
                                        width: 18,
                                        height: 18,
                                        child: CircularProgressIndicator(strokeWidth: 2),
                                      )
                                    : const Icon(Icons.volume_up_rounded, color: AppTheme.orange),
                              ),
                              IconButton(
                                tooltip: isSaved ? 'Bỏ lưu' : 'Lưu vào sổ tay',
                                onPressed: () => _toggleSave(w),
                                icon: Icon(
                                  isSaved ? Icons.bookmark_rounded : Icons.bookmark_outline_rounded,
                                  color: AppTheme.jade,
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
