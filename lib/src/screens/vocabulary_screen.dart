import 'package:flutter/material.dart';
import 'dart:async';
import 'package:audioplayers/audioplayers.dart';

import '../services/student_service.dart';
import '../theme/app_theme.dart';
import '../widgets/common.dart';
import 'handwriting_screen.dart';
import 'translation_screen.dart';

class VocabularyScreen extends StatefulWidget {
  const VocabularyScreen(
      {super.key, required this.service, this.notebook = false});
  final bool notebook;

  final StudentService service;

  @override
  State<VocabularyScreen> createState() => _VocabularyScreenState();
}

class _VocabularyScreenState extends State<VocabularyScreen> {
  final _searchController = TextEditingController();
  bool _historyMode = false;
  late Future<List<VocabularyEntry>> _future;
  final _audio = AudioPlayer();
  Timer? _debounce;
  final Set<int> _saved = {};
  final Set<int> _saving = {};
  int? _playing;

  @override
  void initState() {
    super.initState();
    _load();
    _loadSaved();
  }

  Future<void> _loadSaved() async {
    try {
      final words = await widget.service.fetchSavedVocabulary();
      if (mounted) {
        setState(() {
          _saved.clear();
          _saved.addAll(words.map((w) => w.id));
        });
      }
    } on StudentApiException {
      // The notebook itself exposes loading errors and retry; dictionary remains usable.
    }
  }

  Future<void> _toggleSave(VocabularyEntry word) async {
    if (_saving.contains(word.id)) return;
    final saved = widget.notebook || _saved.contains(word.id);
    setState(() => _saving.add(word.id));
    try {
      await widget.service.setWordSaved(word.id, !saved);
      if (!mounted) return;
      setState(() {
        saved ? _saved.remove(word.id) : _saved.add(word.id);
        if (widget.notebook) _load();
      });
    } on StudentApiException catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(error.message)));
      }
    } finally {
      if (mounted) setState(() => _saving.remove(word.id));
    }
  }

  Future<void> _playAudio(VocabularyEntry word) async {
    if (word.audioUrl.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Chưa có audio phát âm cho từ này.')));
      return;
    }
    setState(() => _playing = word.id);
    try {
      final url =
          Uri.parse(widget.service.baseUrl).resolve(word.audioUrl).toString();
      await _audio.stop();
      await _audio.play(UrlSource(url)).timeout(const Duration(seconds: 15));
    } on Exception {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Không phát được audio. Vui lòng thử lại.')));
      }
    } finally {
      if (mounted) setState(() => _playing = null);
    }
  }

  @override
  void dispose() {
    _searchController.dispose();
    _debounce?.cancel();
    _audio.dispose();
    super.dispose();
  }

  void _load() {
    _future = widget.notebook
        ? widget.service.fetchSavedVocabulary()
        : _historyMode
            ? widget.service.fetchDictionaryHistory()
            : widget.service.fetchVocabulary(search: _searchController.text);
  }

  void _reload() => setState(_load);

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        children: [
          ScreenHeader(
            eyebrow: 'Tra cứu và ghi nhớ',
            title: widget.notebook ? 'Sổ tay' : 'Từ điển',
            trailing: Row(mainAxisSize: MainAxisSize.min, children: [
              if (!widget.notebook)
                IconButton(
                    tooltip: 'Sổ tay từ vựng',
                    icon: const Icon(Icons.bookmark_rounded),
                    onPressed: () async {
                      await Navigator.of(context).push(MaterialPageRoute(
                          builder: (_) => Scaffold(
                              appBar:
                                  AppBar(title: const Text('Sổ tay từ vựng')),
                              body: VocabularyScreen(
                                  service: widget.service, notebook: true))));
                      if (mounted) _loadSaved();
                    }),
              IconButton(
                  tooltip: 'Ngữ pháp & ngữ cảnh',
                  icon: const Icon(Icons.translate_rounded),
                  onPressed: () => Navigator.of(context).push(MaterialPageRoute(
                      builder: (_) =>
                          TranslationScreen(service: widget.service)))),
            ]),
          ),
          if (!widget.notebook)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: SegmentedButton<bool>(
                segments: const [
                  ButtonSegment(
                      value: false,
                      label: Text('Tra từ'),
                      icon: Icon(Icons.search)),
                  ButtonSegment(
                      value: true,
                      label: Text('Lịch sử'),
                      icon: Icon(Icons.history)),
                ],
                selected: {_historyMode},
                onSelectionChanged: (value) {
                  setState(() {
                    _historyMode = value.first;
                    _load();
                  });
                },
              ),
            ),
          if (!_historyMode && !widget.notebook)
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 14, 20, 8),
              child: TextField(
                key: const Key('dictionary-search'),
                controller: _searchController,
                textInputAction: TextInputAction.search,
                onSubmitted: (_) => _reload(),
                onChanged: (_) {
                  _debounce?.cancel();
                  _debounce = Timer(const Duration(milliseconds: 300), () {
                    if (mounted) _reload();
                  });
                },
                decoration: InputDecoration(
                  hintText: 'Hán tự, pinyin hoặc nghĩa tiếng Việt',
                  prefixIcon: const Icon(Icons.search),
                  suffixIcon: IconButton(
                      onPressed: _reload,
                      icon: const Icon(Icons.arrow_forward)),
                ),
              ),
            ),
          Expanded(
            child: FutureBuilder<List<VocabularyEntry>>(
              future: _future,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.hasError) {
                  return _StateMessage(
                    icon: Icons.cloud_off,
                    title: 'Không tải được từ vựng',
                    message: snapshot.error.toString(),
                    onRetry: _reload,
                  );
                }
                final words = snapshot.data ?? const [];
                if (words.isEmpty) {
                  return _StateMessage(
                    icon: _historyMode
                        ? Icons.history_toggle_off
                        : Icons.search_off,
                    title: widget.notebook
                        ? 'Sổ tay chưa có từ vựng'
                        : _historyMode
                            ? 'Chưa có lịch sử tra từ'
                            : 'Không tìm thấy từ phù hợp',
                    message: widget.notebook
                        ? 'Bấm biểu tượng lưu bên cạnh từ để thêm vào sổ tay.'
                        : _historyMode
                            ? 'Hãy mở một từ trong mục Tra từ để lưu vào lịch sử.'
                            : 'Thử tìm bằng Hán tự, pinyin hoặc nghĩa khác.',
                  );
                }
                return Column(
                  children: [
                    if (!_historyMode && !widget.notebook)
                      Padding(
                        padding: const EdgeInsets.fromLTRB(20, 4, 20, 4),
                        child: Row(
                          children: [
                            Text(
                              '${words.length} từ vựng',
                              key: const Key('vocabulary-count'),
                              style: const TextStyle(
                                color: AppTheme.jade,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                            const Spacer(),
                            IconButton(
                              tooltip: 'Tải lại từ vựng',
                              onPressed: _reload,
                              icon: const Icon(Icons.refresh),
                            ),
                            OutlinedButton.icon(
                              key: const Key('open-handwriting'),
                              onPressed: () => Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (_) => HandwritingScreen(
                                    service: widget.service,
                                  ),
                                ),
                              ),
                              icon: const Icon(Icons.draw_outlined),
                              label: const Text('Viết tay'),
                            ),
                          ],
                        ),
                      ),
                    if (_historyMode || widget.notebook)
                      Padding(
                        padding: const EdgeInsets.fromLTRB(20, 12, 20, 4),
                        child: SizedBox(
                          width: double.infinity,
                          child: FilledButton.icon(
                            onPressed: () => Navigator.of(context).push(
                              MaterialPageRoute(
                                  builder: (_) =>
                                      FlashcardScreen(words: words)),
                            ),
                            icon: const Icon(Icons.style_rounded),
                            label: Text('Ôn Flashcard (${words.length} từ)'),
                          ),
                        ),
                      ),
                    Expanded(
                      child: RefreshIndicator(
                        onRefresh: () async => _reload(),
                        child: ListView.separated(
                          padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
                          itemCount: words.length,
                          separatorBuilder: (_, __) =>
                              const SizedBox(height: 10),
                          itemBuilder: (_, index) => _WordCard(
                            word: words[index],
                            onTap: () => _openWord(words[index]),
                            saved: widget.notebook ||
                                _saved.contains(words[index].id),
                            onSave: _saving.contains(words[index].id)
                                ? null
                                : () => _toggleSave(words[index]),
                            onPlay: _playing == words[index].id
                                ? null
                                : () => _playAudio(words[index]),
                          ),
                        ),
                      ),
                    ),
                  ],
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _openWord(VocabularyEntry word) async {
    try {
      await widget.service
          .recordDictionaryLookup(word, _searchController.text.trim());
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (_) => AlertDialog(
          title: Text('${word.hanzi}  ${word.pinyin}'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(word.meaning,
                  style: const TextStyle(
                      fontSize: 18, fontWeight: FontWeight.w800)),
              const SizedBox(height: 12),
              Text(word.example.isEmpty ? 'Chưa có câu ví dụ.' : word.example),
              const SizedBox(height: 8),
              Text('HSK ${word.hsk}',
                  style: const TextStyle(color: AppTheme.red)),
            ],
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Đóng'))
          ],
        ),
      );
      if (_historyMode) _reload();
    } on StudentApiException catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(error.message)));
      }
    }
  }
}

class _WordCard extends StatelessWidget {
  const _WordCard(
      {required this.word,
      required this.onTap,
      required this.saved,
      this.onSave,
      this.onPlay});
  final bool saved;
  final VoidCallback? onSave, onPlay;
  final VocabularyEntry word;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Card(
        child: Column(children: [
          ListTile(
            onTap: onTap,
            leading: HanziAvatar(word.hanzi,
                size: 54, color: const Color(0xFFFFEDE4)),
            title: Text(word.pinyin,
                style: const TextStyle(fontWeight: FontWeight.w800)),
            subtitle: Text(word.meaning),
            trailing: word.lookupCount > 0
                ? Text('${word.lookupCount} lần',
                    style: const TextStyle(color: AppTheme.jade))
                : const Icon(Icons.chevron_right),
          ),
          Row(mainAxisAlignment: MainAxisAlignment.end, children: [
            IconButton(
                tooltip: 'Nghe phát âm',
                onPressed: onPlay,
                icon: const Icon(Icons.volume_up_rounded,
                    color: AppTheme.orange)),
            IconButton(
                tooltip: saved ? 'Bỏ lưu' : 'Lưu vào sổ tay',
                onPressed: onSave,
                icon: Icon(
                    saved
                        ? Icons.bookmark_rounded
                        : Icons.bookmark_outline_rounded,
                    color: AppTheme.jade)),
          ])
        ]),
      );
}

class FlashcardScreen extends StatefulWidget {
  const FlashcardScreen({super.key, required this.words});
  final List<VocabularyEntry> words;

  @override
  State<FlashcardScreen> createState() => _FlashcardScreenState();
}

class _FlashcardScreenState extends State<FlashcardScreen> {
  int _index = 0;
  bool _revealed = false;

  @override
  Widget build(BuildContext context) {
    final word = widget.words[_index];
    return Scaffold(
      appBar:
          AppBar(title: Text('Flashcard ${_index + 1}/${widget.words.length}')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            Expanded(
              child: InkWell(
                key: const Key('flashcard'),
                onTap: () => setState(() => _revealed = !_revealed),
                borderRadius: BorderRadius.circular(28),
                child: Card(
                  child: Center(
                    child: Padding(
                      padding: const EdgeInsets.all(30),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(word.hanzi,
                              style: const TextStyle(
                                  fontSize: 72, fontWeight: FontWeight.w700)),
                          if (_revealed) ...[
                            const SizedBox(height: 20),
                            Text(word.pinyin,
                                style: const TextStyle(
                                    color: AppTheme.red, fontSize: 22)),
                            Text(word.meaning,
                                style: const TextStyle(
                                    fontSize: 20, fontWeight: FontWeight.w800)),
                            if (word.example.isNotEmpty) ...[
                              const SizedBox(height: 12),
                              Text(word.example, textAlign: TextAlign.center),
                            ],
                          ] else
                            const Padding(
                              padding: EdgeInsets.only(top: 18),
                              child: Text('Chạm để xem đáp án'),
                            ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: _index == 0
                        ? null
                        : () => setState(() {
                              _index--;
                              _revealed = false;
                            }),
                    child: const Text('Trước'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton(
                    onPressed: _index == widget.words.length - 1
                        ? null
                        : () => setState(() {
                              _index++;
                              _revealed = false;
                            }),
                    child: const Text('Tiếp'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _StateMessage extends StatelessWidget {
  const _StateMessage(
      {required this.icon,
      required this.title,
      required this.message,
      this.onRetry});
  final IconData icon;
  final String title, message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 52, color: AppTheme.jade),
              const SizedBox(height: 12),
              Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
              const SizedBox(height: 6),
              Text(message, textAlign: TextAlign.center),
              if (onRetry != null) ...[
                const SizedBox(height: 14),
                FilledButton(onPressed: onRetry, child: const Text('Thử lại')),
              ],
            ],
          ),
        ),
      );
}
