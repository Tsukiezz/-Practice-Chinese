import 'package:flutter/material.dart';

import '../services/student_service.dart';
import '../theme/app_theme.dart';
import 'lesson_study_screen.dart';

class LessonsScreen extends StatefulWidget {
  const LessonsScreen({super.key, required this.service, this.onBack});
  final StudentService service;
  final VoidCallback? onBack;

  @override
  State<LessonsScreen> createState() => _LessonsScreenState();
}

class _LessonsScreenState extends State<LessonsScreen> {
  final _search = TextEditingController();
  Map<String, dynamic>? _course;
  Map<String, Map<String, dynamic>> _progress = {};
  String? _error;
  int _level = 0;
  String _status = 'Tất cả';
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await Future.wait<Object>([
        widget.service.fetchLessons(),
        widget.service.fetchLessonProgress(),
      ]);
      if (!mounted) return;
      setState(() {
        _course = data[0] as Map<String, dynamic>;
        _progress = {
          for (final p in data[1] as List<Map<String, dynamic>>)
            p['lesson_id'] as String: p,
        };
        _loading = false;
      });
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _loading = false;
        });
      }
    }
  }

  int _stage(Map<String, dynamic> lesson) =>
      _progress[lesson['id']]?['stage'] as int? ?? 0;

  Future<void> _open(Map<String, dynamic> lesson) async {
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => LessonStudyScreen(
          service: widget.service,
          lessonId: lesson['id'] as String,
          initialStage: _stage(lesson),
        ),
      ),
    );
    if (mounted) await _load();
  }

  String _normalize(String value) {
    const groups = [
      'àáạảãâầấậẩẫăằắặẳẵ',
      'èéẹẻẽêềếệểễ',
      'ìíịỉĩ',
      'òóọỏõôồốộổỗơờớợởỡ',
      'ùúụủũưừứựửữ',
      'ỳýỵỷỹ',
      'đ',
    ];
    var text = value.toLowerCase();
    for (var i = 0; i < groups.length; i++) {
      for (final char in groups[i].split('')) {
        text = text.replaceAll(char, 'aeiouyd'[i]);
      }
    }
    return text;
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.cloud_off_outlined, size: 40),
              const SizedBox(height: 12),
              Text(
                'Chưa tải được lộ trình.\n$_error',
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              FilledButton(onPressed: _load, child: const Text('Thử lại')),
            ],
          ),
        ),
      );
    }
    final all = (_course!['items'] as List).cast<Map<String, dynamic>>();
    final inLevel =
        all.where((l) => _level == 0 || l['hsk'] == _level).toList();
    final completed = inLevel.where((l) => _stage(l) == 4).length;
    final query = _normalize(_search.text.trim());
    final visible = inLevel.where((l) {
      final stage = _stage(l);
      return _normalize('${l['title']} ${l['objective']} HSK ${l['hsk']}')
              .contains(query) &&
          (_status == 'Tất cả' ||
              (_status == 'Đang học' && stage > 0 && stage < 4) ||
              (_status == 'Hoàn thành' && stage == 4) ||
              (_status == 'Chưa học' && stage == 0));
    }).toList();
    final pending = inLevel.where((l) => _stage(l) < 4).toList();
    final active = pending.where((l) => _stage(l) > 0).toList();
    final next = active.isNotEmpty
        ? active.first
        : (pending.isEmpty ? null : pending.first);
    final info = _level == 0
        ? null
        : (_course!['levels'] as List).cast<Map<String, dynamic>>().firstWhere(
              (l) => l['hsk'] == _level,
            );
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final primary = Theme.of(context).colorScheme.primary;
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 1120),
            child: LayoutBuilder(
              builder: (context, constraints) {
                final columns = constraints.maxWidth >= 760 ? 2 : 1;
                return RefreshIndicator(
                  onRefresh: _load,
                  child: CustomScrollView(
                    key: const PageStorageKey('lesson-roadmap'),
                    physics: const AlwaysScrollableScrollPhysics(),
                    slivers: [
                      SliverPadding(
                        padding: const EdgeInsets.fromLTRB(20, 24, 20, 8),
                        sliver: SliverToBoxAdapter(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              if (widget.onBack != null || Navigator.of(context).canPop()) ...[
                                Padding(
                                  padding: const EdgeInsets.only(bottom: 14),
                                  child: InkWell(
                                    onTap: widget.onBack ?? () => Navigator.of(context).maybePop(),
                                    borderRadius: BorderRadius.circular(12),
                                    child: Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
                                      decoration: BoxDecoration(
                                        color: isDark ? const Color(0xFF1A2924) : Colors.white,
                                        borderRadius: BorderRadius.circular(12),
                                        border: Border.all(
                                          color: isDark ? const Color(0xFF283B34) : const Color(0xFFD4E2DA),
                                        ),
                                        boxShadow: [
                                          BoxShadow(
                                            color: isDark
                                                ? Colors.black.withOpacity(0.2)
                                                : const Color(0xFF1B4D3E).withOpacity(0.06),
                                            blurRadius: 6,
                                            offset: const Offset(0, 2),
                                          ),
                                        ],
                                      ),
                                      child: Row(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          Icon(
                                            Icons.arrow_back_rounded,
                                            color: primary,
                                            size: 18,
                                          ),
                                          const SizedBox(width: 4),
                                          Text(
                                            'Quay lại',
                                            style: TextStyle(
                                              color: primary,
                                              fontSize: 13,
                                              fontWeight: FontWeight.w700,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                              Text(
                                'HỌC MỖI NGÀY · HSK 1–6',
                                style: TextStyle(
                                  color: primary,
                                  fontSize: 12,
                                  fontWeight: FontWeight.w700,
                                  letterSpacing: 1,
                                ),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                'Từng bài nhỏ, tiến bộ lớn',
                                style: TextStyle(
                                  fontSize: 27,
                                  fontWeight: FontWeight.w800,
                                  color: isDark ? const Color(0xFFE2ECE7) : AppTheme.ink,
                                ),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                '${all.length} bài học • Từ vựng, mẫu câu, đọc hiểu và luyện tập',
                                style: TextStyle(
                                  color: isDark ? const Color(0xFF9CB2A8) : Colors.grey.shade700,
                                  height: 1.5,
                                ),
                              ),
                            const SizedBox(height: 20),
                            SingleChildScrollView(
                              scrollDirection: Axis.horizontal,
                              child: Row(
                                children: List.generate(
                                  7,
                                  (i) => Padding(
                                    padding: const EdgeInsets.only(right: 8),
                                    child: ChoiceChip(
                                      key: ValueKey('hsk-filter-$i'),
                                      label: Text(i == 0 ? 'Tất cả' : 'HSK $i'),
                                      selected: _level == i,
                                      onSelected: (_) =>
                                          setState(() => _level = i),
                                    ),
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(height: 14),
                            Container(
                              width: double.infinity,
                              padding: const EdgeInsets.all(20),
                              decoration: BoxDecoration(
                                color: isDark ? const Color(0xFF1E322A) : const Color(0xFFE6F0EB),
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(
                                  color: isDark ? const Color(0xFF2C4A3E) : const Color(0xFFD4E5DB),
                                ),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    info == null
                                        ? 'Lộ trình của bạn'
                                        : 'HSK $_level · ${info['title']}',
                                    style: TextStyle(
                                      fontSize: 19,
                                      fontWeight: FontWeight.w800,
                                      color: isDark ? const Color(0xFFF0FDF4) : primary,
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    info?['description'] as String? ??
                                        'Bắt đầu từ HSK 1 hoặc chọn cấp phù hợp. Bạn có thể học lại và chuyển cấp bất cứ lúc nào.',
                                    style: TextStyle(
                                      height: 1.5,
                                      color: isDark ? const Color(0xFFCBD5E1) : const Color(0xFF4A5568),
                                    ),
                                  ),
                                  if (info != null) ...[
                                    const SizedBox(height: 8),
                                    Text(
                                      'Trước khi học: ${info['prerequisite']}',
                                      style: TextStyle(
                                        fontSize: 12,
                                        color: isDark ? const Color(0xFFA3BFB3) : Colors.grey.shade800,
                                        height: 1.5,
                                      ),
                                    ),
                                  ],
                                  const SizedBox(height: 16),
                                  LinearProgressIndicator(
                                    value: inLevel.isEmpty
                                        ? 0
                                        : completed / inLevel.length,
                                    minHeight: 7,
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    '$completed/${inLevel.length} bài hoàn thành • Đạt từ 75% câu đúng để hoàn thành',
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: isDark ? const Color(0xFFA3BFB3) : Colors.grey.shade700,
                                    ),
                                  ),
                                  if (next != null) ...[
                                    const SizedBox(height: 14),
                                    FilledButton.icon(
                                      onPressed: () => _open(next),
                                      icon: Icon(
                                        _stage(next) > 0
                                            ? Icons.play_arrow_rounded
                                            : Icons.auto_stories_outlined,
                                      ),
                                      label: Text(
                                        '${_stage(next) > 0 ? 'Tiếp tục' : 'Bắt đầu'}: ${next['title']}',
                                      ),
                                    ),
                                  ],
                                  if (next == null) ...[
                                    const SizedBox(height: 12),
                                    Text(
                                      'Bạn đã hoàn thành phần này. Hãy ôn lại hoặc chọn cấp tiếp theo.',
                                      style: TextStyle(
                                        color: isDark ? const Color(0xFFCBD5E1) : const Color(0xFF4A5568),
                                      ),
                                    ),
                                  ],
                                ],
                              ),
                            ),
                            const SizedBox(height: 20),
                            TextField(
                              controller: _search,
                              onChanged: (_) => setState(() {}),
                              style: TextStyle(
                                color: isDark ? const Color(0xFFF0FDF4) : AppTheme.ink,
                              ),
                              decoration: InputDecoration(
                                hintText: 'Tìm chủ đề, mẫu câu…',
                                hintStyle: TextStyle(
                                  color: isDark ? const Color(0xFF7A9388) : const Color(0xFF94A3B8),
                                ),
                                prefixIcon: Icon(
                                  Icons.search,
                                  color: isDark ? const Color(0xFF4DB697) : primary,
                                ),
                                suffixIcon: _search.text.isEmpty
                                    ? null
                                    : IconButton(
                                        tooltip: 'Xóa tìm kiếm',
                                        onPressed: () =>
                                            setState(_search.clear),
                                        icon: Icon(
                                          Icons.close,
                                          color: isDark ? const Color(0xFFA3BFB3) : Colors.grey,
                                        ),
                                      ),
                                filled: true,
                                fillColor: isDark ? const Color(0xFF1A2924) : Colors.white,
                                border: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(16),
                                  borderSide: BorderSide(
                                    color: isDark ? const Color(0xFF283B34) : const Color(0xFFDDE5E0),
                                  ),
                                ),
                                enabledBorder: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(16),
                                  borderSide: BorderSide(
                                    color: isDark ? const Color(0xFF283B34) : const Color(0xFFDDE5E0),
                                  ),
                                ),
                              ),
                            ),

                            const SizedBox(height: 12),
                            SingleChildScrollView(
                              scrollDirection: Axis.horizontal,
                              child: Row(
                                children: [
                                  'Tất cả',
                                  'Chưa học',
                                  'Đang học',
                                  'Hoàn thành',
                                ]
                                    .map(
                                      (s) => Padding(
                                        padding: const EdgeInsets.only(
                                          right: 8,
                                        ),
                                        child: ChoiceChip(
                                          label: Text(s),
                                          selected: _status == s,
                                          onSelected: (_) =>
                                              setState(() => _status = s),
                                        ),
                                      ),
                                    )
                                    .toList(),
                              ),
                            ),
                            const SizedBox(height: 12),
                            Text(
                              '${visible.length} bài học',
                              style: TextStyle(
                                fontWeight: FontWeight.w700,
                                color: isDark ? const Color(0xFFF0FDF4) : AppTheme.ink,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    if (visible.isEmpty)
                      SliverToBoxAdapter(
                        child: Padding(
                          padding: const EdgeInsets.all(32),
                          child: Column(
                            children: [
                              const Icon(Icons.search_off, size: 36),
                              const SizedBox(height: 12),
                              const Text('Chưa có bài phù hợp với bộ lọc.'),
                              TextButton(
                                onPressed: () => setState(() {
                                  _search.clear();
                                  _status = 'Tất cả';
                                  _level = 0;
                                }),
                                child: const Text('Xóa bộ lọc'),
                              ),
                            ],
                          ),
                        ),
                      ),
                    SliverPadding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      sliver: SliverList.builder(
                        itemCount: (visible.length / columns).ceil(),
                        itemBuilder: (context, row) => IntrinsicHeight(
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: List.generate(columns, (column) {
                              final index = row * columns + column;
                              return Expanded(
                                child: index >= visible.length
                                    ? const SizedBox()
                                    : _card(visible[index]),
                              );
                            }),
                          ),
                        ),
                      ),
                    ),
                    SliverToBoxAdapter(
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(20, 12, 20, 28),
                        child: Text(
                          _course!['description'] as String,
                          style: TextStyle(
                            color: Colors.grey.shade600,
                            fontSize: 12,
                            height: 1.5,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
        ),
      ),
    ),
  );
}

  Widget _card(Map<String, dynamic> lesson) {
    final stage = _stage(lesson);
    final done = stage == 4;
    final progress = _progress[lesson['id']];
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final primary = Theme.of(context).colorScheme.primary;

    return Card(
      margin: const EdgeInsets.fromLTRB(4, 5, 4, 9),
      child: InkWell(
        key: ValueKey('lesson-${lesson['id']}'),
        borderRadius: BorderRadius.circular(20),
        onTap: () => _open(lesson),
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 5,
                    ),
                    decoration: BoxDecoration(
                      color: isDark ? const Color(0xFF233A31) : const Color(0xFFE6F0EB),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      'HSK ${lesson['hsk']} · ${lesson['order']}/8',
                      style: TextStyle(
                        color: primary,
                        fontWeight: FontWeight.w700,
                        fontSize: 12,
                      ),
                    ),
                  ),
                  const Spacer(),
                  if (done)
                    Icon(
                      Icons.check_circle,
                      color: primary,
                      size: 22,
                    )
                  else
                    Icon(
                      Icons.chevron_right_rounded,
                      color: primary,
                    ),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                lesson['title'] as String,
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                  color: isDark ? const Color(0xFFF0FDF4) : AppTheme.ink,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                lesson['objective'] as String,
                style: TextStyle(
                  color: isDark ? const Color(0xFFA3BFB3) : const Color(0xFF5C6F66),
                  fontSize: 13,
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 16),
              Wrap(
                spacing: 12,
                runSpacing: 6,
                children: [
                  Text(
                    '${lesson['minutes']} phút',
                    style: TextStyle(
                      fontSize: 12,
                      color: isDark ? const Color(0xFF8FA69C) : Colors.grey.shade600,
                    ),
                  ),
                  if (lesson['review'] == true)
                    Text(
                      'Bài tổng kết',
                      style: TextStyle(
                        fontSize: 12,
                        color: isDark ? const Color(0xFF4DB697) : AppTheme.jade,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  Text(
                    done
                        ? 'Hoàn thành · ${progress?['best_score']}%'
                        : stage == 0
                            ? 'Chưa học'
                            : 'Đang học · Bước ${stage + 1}/4',
                    style: TextStyle(
                      fontSize: 12,
                      color: done
                          ? (isDark ? const Color(0xFF4DB697) : AppTheme.jade)
                          : (isDark ? const Color(0xFF8FA69C) : AppTheme.ink),
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 10),
              LinearProgressIndicator(
                value: stage / 4,
                minHeight: 4,
                borderRadius: BorderRadius.circular(4),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
