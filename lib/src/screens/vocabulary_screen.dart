import 'package:flutter/material.dart';

import '../services/student_service.dart';
import '../theme/app_theme.dart';
import '../widgets/common.dart';

class VocabularyScreen extends StatefulWidget {
  const VocabularyScreen({super.key, required this.service});

  final StudentService service;

  @override
  State<VocabularyScreen> createState() => _VocabularyScreenState();
}

class _VocabularyScreenState extends State<VocabularyScreen> {
  final _searchController = TextEditingController();
  bool _historyMode = false;
  late Future<List<VocabularyEntry>> _future;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _load() {
    _future = _historyMode
        ? widget.service.fetchDictionaryHistory()
        : widget.service.fetchVocabulary(search: _searchController.text);
  }

  void _reload() => setState(_load);

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        children: [
          const ScreenHeader(
            eyebrow: 'Tra cứu và ghi nhớ',
            title: 'Từ điển',
            trailing: Icon(Icons.translate_rounded, color: AppTheme.jade),
          ),
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
          if (!_historyMode)
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 14, 20, 8),
              child: TextField(
                key: const Key('dictionary-search'),
                controller: _searchController,
                textInputAction: TextInputAction.search,
                onSubmitted: (_) => _reload(),
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
                    title: _historyMode
                        ? 'Chưa có lịch sử tra từ'
                        : 'Không tìm thấy từ phù hợp',
                    message: _historyMode
                        ? 'Hãy mở một từ trong mục Tra từ để lưu vào lịch sử.'
                        : 'Thử tìm bằng Hán tự, pinyin hoặc nghĩa khác.',
                  );
                }
                return Column(
                  children: [
                    if (_historyMode)
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
  const _WordCard({required this.word, required this.onTap});
  final VocabularyEntry word;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Card(
        child: ListTile(
          onTap: onTap,
          leading:
              HanziAvatar(word.hanzi, size: 54, color: const Color(0xFFFFEDE4)),
          title: Text(word.pinyin,
              style: const TextStyle(fontWeight: FontWeight.w800)),
          subtitle: Text(word.meaning),
          trailing: word.lookupCount > 0
              ? Text('${word.lookupCount} lần',
                  style: const TextStyle(color: AppTheme.jade))
              : const Icon(Icons.chevron_right),
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
