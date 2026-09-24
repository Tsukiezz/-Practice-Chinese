import 'package:flutter/material.dart';

import 'dart:async';

import 'package:audioplayers/audioplayers.dart';

import '../services/student_service.dart';
import '../theme/app_theme.dart';
import '../widgets/common.dart';
import 'handwriting_screen.dart';
import 'translation_screen.dart';

class VocabularyScreen extends StatefulWidget {
  const VocabularyScreen({
    super.key,
    required this.service,
    this.notebook = false,
    this.guest = false,
  });
  final bool notebook;
  final bool guest;

  final StudentService service;

  @override
  State<VocabularyScreen> createState() => _VocabularyScreenState();
}

class _VocabularyScreenState extends State<VocabularyScreen> {
  final _searchController = TextEditingController();
  final _searchFocusNode = FocusNode();
  bool _historyMode = false;
  late Future<VocabularyPage> _future;
  int? _hsk;
  String? _topic;
  int _offset = 0;
  List<Map<String, dynamic>> _topics = const [];
  final _listController = ScrollController();
  final _audio = AudioPlayer();
  Timer? _debounce;
  final Set<int> _saved = {};
  final Set<int> _saving = {};
  int? _playing;

  @override
  void initState() {
    super.initState();
    _load();
    if (!widget.guest) _loadSaved();
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
        const SnackBar(content: Text('Chưa có audio phát âm cho từ này.')),
      );
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
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Không phát được audio. Vui lòng thử lại.'),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _playing = null);
    }
  }

  @override
  void dispose() {
    _listController.dispose();
    _searchController.dispose();
    _searchFocusNode.dispose();
    _debounce?.cancel();
    _audio.dispose();
    super.dispose();
  }

  Future<void> _openHandwriting() async {
    final result = await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => HandwritingScreen(
          service: widget.service,
          guest: widget.guest,
        ),
      ),
    );
    if (result == 'focus_keyboard' && mounted) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) {
          _searchFocusNode.requestFocus();
        }
      });
    }
  }

  void _load({bool reset = true}) {
    if (reset) _offset = 0;
    if (_listController.hasClients) _listController.jumpTo(0);
    if (widget.notebook || _historyMode) {
      final request = widget.notebook
          ? widget.service.fetchSavedVocabulary()
          : widget.service.fetchDictionaryHistory();
      _future = request
          .then((words) => VocabularyPage(items: words, total: words.length));
    } else {
      _future = widget.service.fetchVocabularyPage(
          search: _searchController.text,
          hsk: _hsk,
          topic: _topic,
          offset: _offset);
    }
  }

  void _reload() => setState(() => _load());

  Future<void> _chooseFilters() async {
    var hsk = _hsk;
    var topic = _topic;
    final applied = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      showDragHandle: true,
      builder: (context) => StatefulBuilder(
          builder: (context, update) => SafeArea(
                top: false,
                child: SingleChildScrollView(
                    child: Padding(
                  padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
                  child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        const Text('Học từ theo nội dung',
                            style: TextStyle(
                                fontSize: 22, fontWeight: FontWeight.w800)),
                        const SizedBox(height: 8),
                        const Text('Bộ HSK 1–6 · HSK 2.0'),
                        const SizedBox(height: 20),
                        DropdownButtonFormField<int>(
                          key: ValueKey('hsk-filter-$hsk'),
                          initialValue: hsk ?? 0,
                          isExpanded: true,
                          decoration:
                              const InputDecoration(labelText: 'Cấp độ'),
                          items: [
                            const DropdownMenuItem(
                                value: 0, child: Text('Tất cả cấp độ')),
                            for (var i = 1; i <= 6; i++)
                              DropdownMenuItem(value: i, child: Text('HSK $i'))
                          ],
                          onChanged: (v) =>
                              update(() => hsk = v == 0 ? null : v),
                        ),
                        const SizedBox(height: 16),
                        DropdownButtonFormField<String>(
                          key: ValueKey('topic-filter-$topic'),
                          initialValue: topic ?? '',
                          isExpanded: true,
                          decoration:
                              const InputDecoration(labelText: 'Chủ đề'),
                          items: [
                            const DropdownMenuItem(
                                value: '', child: Text('Tất cả chủ đề')),
                            for (final t in _topics)
                              DropdownMenuItem(
                                  value: t['id'] as String,
                                  child: Text(t['label'] as String,
                                      overflow: TextOverflow.ellipsis))
                          ],
                          onChanged: (v) =>
                              update(() => topic = v == '' ? null : v),
                        ),
                        const SizedBox(height: 20),
                        FilledButton(
                            onPressed: () => Navigator.pop(context, true),
                            child: const Text('Áp dụng')),
                        TextButton(
                            onPressed: () => update(() {
                                  hsk = null;
                                  topic = null;
                                }),
                            child: const Text('Xóa bộ lọc')),
                      ]),
                )),
              )),
    );
    if (applied == true && mounted) {
      setState(() {
        _hsk = hsk;
        _topic = topic;
        _load();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (context, constraints) {
      final compact = constraints.maxWidth < 600;
      return SafeArea(
        child: Column(
          children: [
            ScreenHeader(
              eyebrow: 'Tra cứu và ghi nhớ',
              title: widget.notebook ? 'Sổ tay' : 'Từ điển',
              trailing: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (!widget.notebook && !widget.guest)
                    IconButton(
                      tooltip: 'Sổ tay từ vựng',
                      icon: const Icon(Icons.bookmark_rounded),
                      onPressed: () async {
                        await Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => Scaffold(
                              appBar:
                                  AppBar(title: const Text('Sổ tay từ vựng')),
                              body: VocabularyScreen(
                                service: widget.service,
                                notebook: true,
                              ),
                            ),
                          ),
                        );
                        if (mounted) _loadSaved();
                      },
                    ),
                  IconButton(
                    tooltip: 'Dịch & sửa câu',
                    icon: const Icon(Icons.translate_rounded),
                    onPressed: () => Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => TranslationScreen(
                          service: widget.service,
                          guest: widget.guest,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            if (!widget.notebook && !widget.guest)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: SegmentedButton<bool>(
                  segments: const [
                    ButtonSegment(
                      value: false,
                      label: Text('Tra từ'),
                      icon: Icon(Icons.search),
                    ),
                    ButtonSegment(
                      value: true,
                      label: Text('Lịch sử'),
                      icon: Icon(Icons.history),
                    ),
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
                  focusNode: _searchFocusNode,
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
                    suffixIcon: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (_searchController.text.isNotEmpty)
                          IconButton(
                            tooltip: 'Xóa tìm kiếm',
                            icon: const Icon(Icons.clear, size: 20),
                            onPressed: () {
                              _searchController.clear();
                              _reload();
                            },
                          ),
                        IconButton(
                          tooltip: 'Chuyển sang viết tay',
                          icon: const Icon(Icons.draw_outlined),
                          onPressed: _openHandwriting,
                        ),
                        IconButton(
                          tooltip: 'Tìm kiếm',
                          onPressed: _reload,
                          icon: const Icon(Icons.arrow_forward),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            if (!_historyMode && !widget.notebook)
              Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      key: const Key('vocabulary-filters'),
                      onPressed: _chooseFilters,
                      icon: const Icon(Icons.tune),
                      label: Text([
                        _hsk == null ? 'HSK 1–6' : 'HSK $_hsk',
                        _topic == null
                            ? 'Chọn chủ đề'
                            : _topics.firstWhere((t) => t['id'] == _topic,
                                    orElse: () => {'label': _topic})['label']
                                as String,
                      ].join(' · ')),
                    ),
                  )),
            Expanded(
              child: FutureBuilder<VocabularyPage>(
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
                  final page = snapshot.data!;
                  final words = page.items;
                  if (!_historyMode && !widget.notebook) _topics = page.topics;
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
                              : 'Thử từ khóa khác hoặc mở mục Dịch & sửa câu để dịch cả đoạn văn.',
                    );
                  }
                  return Column(
                    children: [
                      if (!_historyMode && !widget.notebook)
                        Padding(
                          padding: const EdgeInsets.fromLTRB(20, 4, 20, 4),
                          child: Row(
                            children: [
                              Expanded(
                                child: Text(
                                  '${page.total} từ vựng',
                                  key: const Key('vocabulary-count'),
                                  style: const TextStyle(
                                    color: AppTheme.jade,
                                    fontWeight: FontWeight.w800,
                                  ),
                                ),
                              ),
                              IconButton(
                                tooltip: 'Tải lại từ vựng',
                                onPressed: _reload,
                                icon: const Icon(Icons.refresh),
                              ),
                              OutlinedButton.icon(
                                key: const Key('open-handwriting'),
                                onPressed: _openHandwriting,
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
                                  builder: (_) => FlashcardScreen(words: words),
                                ),
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
                            controller: _listController,
                            padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
                            itemCount: words.length,
                            separatorBuilder: (_, __) =>
                                const SizedBox(height: 10),
                            itemBuilder: (_, index) => _WordCard(
                              word: words[index],
                              onTap: () => _openWord(words[index]),
                              saved: widget.notebook ||
                                  _saved.contains(words[index].id),
                              onSave: widget.guest ||
                                      _saving.contains(words[index].id)
                                  ? null
                                  : () => _toggleSave(words[index]),
                              onPlay: _playing == words[index].id
                                  ? null
                                  : () => _playAudio(words[index]),
                            ),
                          ),
                        ),
                      ),
                      if (!_historyMode &&
                          !widget.notebook &&
                          page.total > page.limit)
                        SafeArea(
                            top: false,
                            child: Padding(
                                padding:
                                    const EdgeInsets.symmetric(horizontal: 12),
                                child: Row(children: [
                                  IconButton(
                                      tooltip: 'Trang trước',
                                      onPressed: _offset == 0
                                          ? null
                                          : () => setState(() {
                                                _offset -= page.limit;
                                                _load(reset: false);
                                              }),
                                      icon: const Icon(Icons.chevron_left)),
                                  Expanded(
                                      child: Text(
                                          '${page.offset + 1}–${page.offset + words.length} / ${page.total}',
                                          textAlign: TextAlign.center)),
                                  IconButton(
                                      tooltip: 'Trang sau',
                                      onPressed: page.offset + words.length >=
                                              page.total
                                          ? null
                                          : () => setState(() {
                                                _offset += page.limit;
                                                _load(reset: false);
                                              }),
                                      icon: const Icon(Icons.chevron_right)),
                                ]))),
                    ],
                  );
                },
              ),
            ),
          ],
        ),
      );
    });
  }

  Future<void> _openWord(VocabularyEntry word) async {
    try {
      if (!widget.guest) {
        await widget.service.recordDictionaryLookup(
          word,
          _searchController.text.trim(),
        );
      }
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (_) => AlertDialog(
          title: Text('${word.hanzi}  ${word.pinyin}'),
          scrollable: true,
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                word.meaning,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                ),
              ),
              for (final sense in word.senses)
                Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text('${sense['pinyin']}: ${sense['meaning']}')),
              const SizedBox(height: 12),
              Text(word.example.isEmpty ? 'Chưa có câu ví dụ.' : word.example),
              const SizedBox(height: 8),
              Text(
                'HSK ${word.hsk}',
                style: const TextStyle(color: AppTheme.red),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Đóng'),
            ),
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
  const _WordCard({
    required this.word,
    required this.onTap,
    required this.saved,
    this.onSave,
    this.onPlay,
  });
  final bool saved;
  final VoidCallback? onSave, onPlay;
  final VocabularyEntry word;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Card(
        child: Column(
          children: [
            ListTile(
              onTap: onTap,
              leading: HanziAvatar(
                word.hanzi.characters.first,
                size: 54,
                color: const Color(0xFFFFEDE4),
              ),
              title: Text(
                word.hanzi,
                style: const TextStyle(fontWeight: FontWeight.w800),
              ),
              subtitle: Text('${word.pinyin}\n${word.meaning}'),
              trailing: word.lookupCount > 0
                  ? Text(
                      '${word.lookupCount} lần',
                      style: const TextStyle(color: AppTheme.jade),
                    )
                  : const Icon(Icons.chevron_right),
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                IconButton(
                  tooltip: word.audioUrl.isEmpty
                      ? 'Chưa có bản thu âm'
                      : 'Nghe phát âm',
                  onPressed: word.audioUrl.isEmpty ? null : onPlay,
                  icon: Icon(Icons.volume_up_rounded,
                      color: word.audioUrl.isEmpty
                          ? Colors.grey
                          : AppTheme.orange),
                ),
                IconButton(
                  tooltip: saved ? 'Bỏ lưu' : 'Lưu vào sổ tay',
                  onPressed: onSave,
                  icon: Icon(
                    saved
                        ? Icons.bookmark_rounded
                        : Icons.bookmark_outline_rounded,
                    color: AppTheme.jade,
                  ),
                ),
              ],
            ),
          ],
        ),
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
      appBar: AppBar(
        title: Text('Flashcard ${_index + 1}/${widget.words.length}'),
      ),
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
                          Text(
                            word.hanzi,
                            style: const TextStyle(
                              fontSize: 72,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          if (_revealed) ...[
                            const SizedBox(height: 20),
                            Text(
                              word.pinyin,
                              style: const TextStyle(
                                color: AppTheme.red,
                                fontSize: 22,
                              ),
                            ),
                            Text(
                              word.meaning,
                              style: const TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
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
  const _StateMessage({
    required this.icon,
    required this.title,
    required this.message,
    this.onRetry,
  });
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
