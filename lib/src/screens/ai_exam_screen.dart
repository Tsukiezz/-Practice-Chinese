import 'dart:async';
import 'package:flutter/material.dart';

import '../services/ai_exam_service.dart';
import '../theme/app_theme.dart';
import '../widgets/common.dart';

class AiExamScreen extends StatefulWidget {
  const AiExamScreen({
    super.key,
    required this.service,
  });

  final AIExamService service;

  @override
  State<AiExamScreen> createState() => _AiExamScreenState();
}

class _AiExamScreenState extends State<AiExamScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  // Creation form state
  int _questionCount = 5;
  String _contentType = 'random'; // 'random' or 'vocabulary'
  int? _selectedHsk;
  String? _selectedTopic;
  List<Map<String, String>> _topics = [];
  bool _generating = false;

  // History state
  bool _loadingHistory = false;
  List<AIExam> _pendingExams = [];
  List<AIExam> _completedExams = [];

  // Active exam taking state
  AIExam? _activeExam;
  int _currentQuestionIndex = 0;
  final Map<String, String> _userAnswers = {};
  Timer? _countdownTimer;
  int _remainingSeconds = 0;
  bool _submitting = false;

  // Results state
  AIExamFeedback? _currentFeedback;
  AIExam? _reviewedExam;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _tabController.addListener(() {
      if (_tabController.index == 1 && !_tabController.indexIsChanging) {
        _loadHistory();
      }
    });
    _loadTopics();
    _loadHistory();
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadTopics() async {
    try {
      final topics = await widget.service.loadTopics();
      if (mounted) setState(() => _topics = topics);
    } catch (_) {}
  }

  Future<void> _loadHistory() async {
    setState(() => _loadingHistory = true);
    try {
      final data = await widget.service.listExams();
      if (mounted) {
        setState(() {
          _pendingExams = data['pending'] ?? [];
          _completedExams = data['completed'] ?? [];
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Lỗi tải đề thi: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _loadingHistory = false);
    }
  }

  Future<void> _generateExam() async {
    setState(() => _generating = true);
    try {
      final exam = await widget.service.generateExam(
        questionCount: _questionCount,
        contentType: _contentType,
        hskLevel: _contentType == 'vocabulary' ? _selectedHsk : null,
        topic: _contentType == 'vocabulary' ? _selectedTopic : null,
      );

      if (!mounted) return;

      // Show dialog: "Làm ngay" or "Làm sau"
      showDialog<void>(
        context: context,
        barrierDismissible: false,
        builder: (ctx) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          title: const Row(
            children: [
              Icon(Icons.auto_awesome, color: AppTheme.jade),
              SizedBox(width: 8),
              Text('Đã tạo đề thi thành công!', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                exam.title,
                style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
              ),
              const SizedBox(height: 8),
              Text(
                '• Số câu hỏi: ${exam.questionCount} câu\n'
                '• Thời gian làm bài: ${exam.durationMinutes} phút (1 phút / câu)',
                style: const TextStyle(color: Color(0xFF5C6F64), height: 1.5),
              ),
              const SizedBox(height: 12),
              const Text('Bạn muốn bắt đầu làm bài ngay bây giờ hay để làm sau?'),
            ],
          ),
          actions: [
            OutlinedButton(
              onPressed: () {
                Navigator.of(ctx).pop();
                _loadHistory();
                _tabController.animateTo(1);
              },
              child: const Text('⏱️ Làm sau'),
            ),
            FilledButton(
              style: FilledButton.styleFrom(backgroundColor: AppTheme.jade),
              onPressed: () {
                Navigator.of(ctx).pop();
                _startExam(exam);
              },
              child: const Text('🚀 Làm ngay'),
            ),
          ],
        ),
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Lỗi tạo đề thi: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _generating = false);
    }
  }

  void _startExam(AIExam exam) {
    setState(() {
      _activeExam = exam;
      _currentQuestionIndex = 0;
      _userAnswers.clear();
      _currentFeedback = null;
      _reviewedExam = null;
      _remainingSeconds = exam.durationSeconds > 0 ? exam.durationSeconds : (exam.durationMinutes * 60);
    });

    _countdownTimer?.cancel();
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      setState(() {
        if (_remainingSeconds > 0) {
          _remainingSeconds--;
        } else {
          timer.cancel();
          _onTimeExpired();
        }
      });
    });
  }

  void _onTimeExpired() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Đã hết thời gian làm bài! Hệ thống đang tự động nộp bài...'),
        backgroundColor: Colors.red,
      ),
    );
    _submitExam(auto: true);
  }

  Future<void> _confirmSubmit() async {
    final total = _activeExam?.questions.length ?? 0;
    final answered = _userAnswers.length;
    final unanswered = total - answered;

    final shouldSubmit = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
        title: const Text('Xác nhận nộp bài'),
        content: Text(
          unanswered > 0
              ? 'Bạn còn $unanswered câu chưa làm. Bạn có chắc chắn muốn nộp bài ngay?'
              : 'Bạn đã hoàn thành tất cả câu hỏi. Bạn muốn nộp bài để AI chấm điểm ngay?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Làm tiếp'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: AppTheme.jade),
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('Nộp bài ngay'),
          ),
        ],
      ),
    );

    if (shouldSubmit == true) {
      _submitExam();
    }
  }

  Future<void> _submitExam({bool auto = false}) async {
    if (_activeExam == null || _submitting) return;

    _countdownTimer?.cancel();
    setState(() => _submitting = true);

    try {
      final feedback = await widget.service.submitExam(_activeExam!.id, _userAnswers);
      if (mounted) {
        setState(() {
          _reviewedExam = _activeExam;
          _currentFeedback = feedback;
          _activeExam = null;
        });
        _loadHistory();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Lỗi nộp bài: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  Future<void> _deleteExam(int examId) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Xóa đề thi'),
        content: const Text('Bạn có chắc chắn muốn xóa đề thi này?'),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: const Text('Hủy')),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('Xóa'),
          ),
        ],
      ),
    );

    if (confirm == true) {
      try {
        await widget.service.deleteExam(examId);
        _loadHistory();
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Không thể xóa đề: $e')),
          );
        }
      }
    }
  }

  Future<void> _openExamResult(int examId) async {
    try {
      final exam = await widget.service.getExam(examId);
      if (exam.aiFeedback != null && mounted) {
        setState(() {
          _reviewedExam = exam;
          _currentFeedback = exam.aiFeedback;
          _activeExam = null;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Lỗi tải kết quả: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_currentFeedback != null && _reviewedExam != null) {
      return _buildResultView();
    }
    if (_activeExam != null) {
      return _buildExamTakingView();
    }

    return SafeArea(
      child: Column(
        children: [
          const ScreenHeader(
            eyebrow: 'Khảo thí AI · Đề thi tiếng Trung',
            title: 'Kiểm tra',
            trailing: Icon(Icons.assignment_turned_in_rounded, color: AppTheme.jade),
          ),
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 20),
            decoration: BoxDecoration(
              color: const Color(0xFFE5EDE8),
              borderRadius: BorderRadius.circular(14),
            ),
            child: TabBar(
              controller: _tabController,
              indicatorSize: TabBarIndicatorSize.tab,
              dividerColor: Colors.transparent,
              indicator: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                boxShadow: const [
                  BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 2)),
                ],
              ),
              labelColor: AppTheme.jade,
              unselectedLabelColor: const Color(0xFF60736A),
              labelStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
              tabs: const [
                Tab(text: '✨ Tạo đề thi mới'),
                Tab(text: '📚 Đề thi của tôi'),
              ],
            ),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildCreateExamTab(),
                _buildMyExamsTab(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCreateExamTab() {
    return ListView(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      children: [
        Card(
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
            side: const BorderSide(color: Color(0xFFDDE5E0)),
          ),
          color: Colors.white,
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Yêu cầu AI tạo đề thi',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: AppTheme.ink),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Chọn số lượng câu hỏi và nội dung học tập. Mỗi câu làm bài trong 1 phút.',
                  style: TextStyle(color: Color(0xFF60736A), fontSize: 13, height: 1.4),
                ),
                const SizedBox(height: 20),

                // Question Count Selector
                const Text('1. Số lượng câu hỏi:', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
                const SizedBox(height: 10),
                Wrap(
                  spacing: 8,
                  children: [5, 10, 15, 20, 25].map((count) {
                    final selected = _questionCount == count;
                    return ChoiceChip(
                      label: Text('$count câu'),
                      selected: selected,
                      onSelected: (_) => setState(() => _questionCount = count),
                      selectedColor: const Color(0xFFE8F0EC),
                      side: BorderSide(color: selected ? AppTheme.jade : const Color(0xFFDDE5E0)),
                      labelStyle: TextStyle(
                        color: selected ? AppTheme.jade : Colors.black87,
                        fontWeight: selected ? FontWeight.bold : FontWeight.normal,
                      ),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFDF6E2),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.timer_outlined, size: 18, color: Color(0xFF8C6200)),
                      const SizedBox(width: 6),
                      Text(
                        'Thời gian làm bài: $_questionCount phút (1 phút / câu)',
                        style: const TextStyle(color: Color(0xFF8C6200), fontWeight: FontWeight.w700, fontSize: 13),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                // Content Type Selector
                const Text('2. Nội dung đề thi:', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
                const SizedBox(height: 10),
                SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(value: 'random', label: Text('Ngẫu nhiên (Tổng hợp)')),
                    ButtonSegment(value: 'vocabulary', label: Text('Theo từ vựng')),
                  ],
                  selected: {_contentType},
                  onSelectionChanged: (val) => setState(() => _contentType = val.first),
                ),

                // Filters when 'vocabulary' is selected
                if (_contentType == 'vocabulary') ...[
                  const SizedBox(height: 20),
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF9FBF9),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: const Color(0xFFDDE5E0)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Cấp độ HSK:', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                        const SizedBox(height: 8),
                        Wrap(
                          spacing: 6,
                          children: [
                            ChoiceChip(
                              label: const Text('Tất cả'),
                              selected: _selectedHsk == null,
                              onSelected: (_) => setState(() => _selectedHsk = null),
                            ),
                            ...List.generate(6, (i) {
                              final hsk = i + 1;
                              final selected = _selectedHsk == hsk;
                              return ChoiceChip(
                                label: Text('HSK $hsk'),
                                selected: selected,
                                onSelected: (_) => setState(() => _selectedHsk = hsk),
                              );
                            }),
                          ],
                        ),
                        if (_topics.isNotEmpty) ...[
                          const SizedBox(height: 14),
                          const Text('Chủ đề từ vựng:', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                          const SizedBox(height: 6),
                          DropdownButtonFormField<String>(
                            value: _selectedTopic,
                            isExpanded: true,
                            decoration: InputDecoration(
                              contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                              border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                            ),
                            hint: const Text('Tất cả chủ đề'),
                            items: [
                              const DropdownMenuItem(value: null, child: Text('Tất cả chủ đề')),
                              ..._topics.map((t) => DropdownMenuItem(
                                    value: t['id'],
                                    child: Text(t['label'] ?? ''),
                                  )),
                            ],
                            onChanged: (val) => setState(() => _selectedTopic = val),
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
                const SizedBox(height: 28),

                // Submit Button
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: FilledButton.icon(
                    style: FilledButton.styleFrom(
                      backgroundColor: AppTheme.jade,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    ),
                    onPressed: _generating ? null : _generateExam,
                    icon: _generating
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : const Icon(Icons.auto_awesome_rounded),
                    label: Text(
                      _generating ? 'Đang tạo đề thi…' : 'Yêu cầu AI tạo đề thi',
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildMyExamsTab() {
    if (_loadingHistory) {
      return const Center(child: CircularProgressIndicator());
    }

    return RefreshIndicator(
      onRefresh: _loadHistory,
      child: ListView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        children: [
          // Pending Exams (Do Later)
          Row(
            children: [
              const Icon(Icons.timer_outlined, size: 18, color: AppTheme.jade),
              const SizedBox(width: 6),
              Text(
                'Đề thi chờ làm (${_pendingExams.length})',
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppTheme.ink),
              ),
            ],
          ),
          const SizedBox(height: 8),
          if (_pendingExams.isEmpty)
            const Card(
              elevation: 0,
              color: Colors.white,
              child: Padding(
                padding: EdgeInsets.all(20),
                child: Text('Không có đề thi nào đang chờ làm.', style: TextStyle(color: Colors.grey)),
              ),
            )
          else
            ..._pendingExams.map((exam) => Card(
                  elevation: 0,
                  margin: const EdgeInsets.only(bottom: 10),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                    side: const BorderSide(color: Color(0xFFDDE5E0)),
                  ),
                  color: Colors.white,
                  child: ListTile(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    title: Text(exam.title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
                    subtitle: Text(
                      '⏱️ ${exam.durationMinutes} phút · ${exam.questionCount} câu',
                      style: const TextStyle(color: Color(0xFF5C6F64), fontSize: 13),
                    ),
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        FilledButton(
                          style: FilledButton.styleFrom(
                            backgroundColor: AppTheme.jade,
                            padding: const EdgeInsets.symmetric(horizontal: 14),
                          ),
                          onPressed: () => _startExam(exam),
                          child: const Text('Làm ngay'),
                        ),
                        IconButton(
                          icon: const Icon(Icons.delete_outline, color: Colors.grey, size: 20),
                          onPressed: () => _deleteExam(exam.id),
                        ),
                      ],
                    ),
                  ),
                )),
          const SizedBox(height: 24),

          // Completed Exams
          Row(
            children: [
              const Icon(Icons.check_circle_outline_rounded, size: 18, color: Colors.green),
              const SizedBox(width: 6),
              Text(
                'Đề thi đã hoàn thành (${_completedExams.length})',
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppTheme.ink),
              ),
            ],
          ),
          const SizedBox(height: 8),
          if (_completedExams.isEmpty)
            const Card(
              elevation: 0,
              color: Colors.white,
              child: Padding(
                padding: EdgeInsets.all(20),
                child: Text('Chưa có đề thi nào đã hoàn thành.', style: TextStyle(color: Colors.grey)),
              ),
            )
          else
            ..._completedExams.map((exam) {
              final score = exam.score ?? 0.0;
              final scoreColor = score >= 80 ? Colors.green : (score >= 50 ? Colors.orange : Colors.red);
              return Card(
                elevation: 0,
                margin: const EdgeInsets.only(bottom: 10),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                  side: const BorderSide(color: Color(0xFFDDE5E0)),
                ),
                color: Colors.white,
                child: ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  title: Text(exam.title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
                  subtitle: Text(
                    '${exam.questionCount} câu',
                    style: const TextStyle(color: Color(0xFF5C6F64), fontSize: 13),
                  ),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: scoreColor.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          '$score điểm',
                          style: TextStyle(color: scoreColor, fontWeight: FontWeight.bold, fontSize: 14),
                        ),
                      ),
                      const SizedBox(width: 8),
                      OutlinedButton(
                        onPressed: () => _openExamResult(exam.id),
                        child: const Text('Xem lại & Sửa'),
                      ),
                    ],
                  ),
                ),
              );
            }),
        ],
      ),
    );
  }

  Widget _buildExamTakingView() {
    final exam = _activeExam!;
    final total = exam.questions.length;
    final q = exam.questions[_currentQuestionIndex];

    final minutes = _remainingSeconds ~/ 60;
    final seconds = _remainingSeconds % 60;
    final timeStr = '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';

    final timerColor = _remainingSeconds <= 60
        ? Colors.red
        : (_remainingSeconds <= 120 ? Colors.orange : AppTheme.jade);

    return Scaffold(
      appBar: AppBar(
        title: Text(exam.title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () async {
            final exit = await showDialog<bool>(
              context: context,
              builder: (ctx) => AlertDialog(
                title: const Text('Tạm dừng bài thi?'),
                content: const Text('Bạn có thể lưu đề thi này và tiếp tục làm sau trong mục "Đề thi của tôi".'),
                actions: [
                  TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: const Text('Ở lại')),
                  FilledButton(
                    onPressed: () => Navigator.of(ctx).pop(true),
                    child: const Text('Lưu & Để làm sau'),
                  ),
                ],
              ),
            );
            if (exit == true) {
              _countdownTimer?.cancel();
              setState(() => _activeExam = null);
              _loadHistory();
            }
          },
        ),
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 12),
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: timerColor.withOpacity(0.12),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              children: [
                Icon(Icons.timer_outlined, size: 18, color: timerColor),
                const SizedBox(width: 4),
                Text(
                  timeStr,
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: timerColor),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: FilledButton(
              style: FilledButton.styleFrom(backgroundColor: AppTheme.jade),
              onPressed: _submitting ? null : _confirmSubmit,
              child: _submitting
                  ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Text('Nộp bài'),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            LinearProgressIndicator(
              value: (_currentQuestionIndex + 1) / total,
              backgroundColor: const Color(0xFFE5EDE8),
              valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.jade),
            ),
            // Question selector jump bar
            SizedBox(
              height: 48,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                itemCount: total,
                separatorBuilder: (_, __) => const SizedBox(width: 6),
                itemBuilder: (context, i) {
                  final isCurrent = i == _currentQuestionIndex;
                  final isAnswered = _userAnswers.containsKey(exam.questions[i].id);
                  return ChoiceChip(
                    label: Text('${i + 1}'),
                    selected: isCurrent,
                    onSelected: (_) => setState(() => _currentQuestionIndex = i),
                    selectedColor: AppTheme.jade,
                    labelStyle: TextStyle(
                      color: isCurrent ? Colors.white : (isAnswered ? AppTheme.jade : Colors.black87),
                      fontWeight: (isCurrent || isAnswered) ? FontWeight.bold : FontWeight.normal,
                    ),
                    backgroundColor: isAnswered ? const Color(0xFFE5EDE8) : Colors.white,
                  );
                },
              ),
            ),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  Card(
                    elevation: 0,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(18),
                      side: const BorderSide(color: Color(0xFFDDE5E0)),
                    ),
                    color: Colors.white,
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'CÂU HỎI ${_currentQuestionIndex + 1} / $total',
                            style: const TextStyle(
                              color: AppTheme.jade,
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                              letterSpacing: 1,
                            ),
                          ),
                          const SizedBox(height: 12),
                          Text(
                            q.prompt,
                            style: const TextStyle(
                              fontSize: 19,
                              fontWeight: FontWeight.w700,
                              color: AppTheme.ink,
                              height: 1.4,
                            ),
                          ),
                          if (q.pinyin.isNotEmpty) ...[
                            const SizedBox(height: 6),
                            Text(
                              q.pinyin,
                              style: const TextStyle(fontSize: 14, color: Color(0xFF5C6F64), fontStyle: FontStyle.italic),
                            ),
                          ],
                          const SizedBox(height: 24),
                          ...q.options.map((opt) {
                            final selected = _userAnswers[q.id] == opt;
                            return Padding(
                              padding: const EdgeInsets.only(bottom: 10),
                              child: InkWell(
                                borderRadius: BorderRadius.circular(12),
                                onTap: () => setState(() => _userAnswers[q.id] = opt),
                                child: Container(
                                  padding: const EdgeInsets.all(16),
                                  decoration: BoxDecoration(
                                    color: selected ? const Color(0xFFE8F0EC) : Colors.white,
                                    borderRadius: BorderRadius.circular(12),
                                    border: Border.all(
                                      color: selected ? AppTheme.jade : const Color(0xFFDDE5E0),
                                      width: selected ? 2 : 1,
                                    ),
                                  ),
                                  child: Row(
                                    children: [
                                      Icon(
                                        selected ? Icons.radio_button_checked : Icons.radio_button_off,
                                        color: selected ? AppTheme.jade : Colors.grey,
                                      ),
                                      const SizedBox(width: 12),
                                      Expanded(
                                        child: Text(
                                          opt,
                                          style: TextStyle(
                                            fontSize: 15,
                                            fontWeight: selected ? FontWeight.bold : FontWeight.w500,
                                            color: selected ? AppTheme.jade : AppTheme.ink,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            );
                          }),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      OutlinedButton(
                        onPressed: _currentQuestionIndex > 0
                            ? () => setState(() => _currentQuestionIndex--)
                            : null,
                        child: const Text('← Câu trước'),
                      ),
                      FilledButton(
                        style: FilledButton.styleFrom(backgroundColor: AppTheme.jade),
                        onPressed: () {
                          if (_currentQuestionIndex < total - 1) {
                            setState(() => _currentQuestionIndex++);
                          } else {
                            _confirmSubmit();
                          }
                        },
                        child: Text(_currentQuestionIndex < total - 1 ? 'Câu tiếp theo →' : 'Kiểm tra & Nộp bài'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildResultView() {
    final feedback = _currentFeedback!;
    final exam = _reviewedExam!;
    final score = feedback.score;
    final scoreColor = score >= 80 ? Colors.green : (score >= 50 ? Colors.orange : Colors.red);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Kết quả & Sửa bài', style: TextStyle(fontWeight: FontWeight.bold)),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => setState(() {
            _currentFeedback = null;
            _reviewedExam = null;
          }),
        ),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            // Score Banner
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF163F35), Color(0xFF2D6A4F)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(24),
              ),
              child: Column(
                children: [
                  const Text(
                    'ĐIỂM KẾT QUẢ BÀI THI AI',
                    style: TextStyle(color: Color(0xFFEAD8B3), fontSize: 13, letterSpacing: 1.2, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    '${score.toStringAsFixed(1)} / 100',
                    style: const TextStyle(color: Colors.white, fontSize: 44, fontWeight: FontWeight.w900),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    feedback.summary,
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Color(0xFFE0ECE5), fontSize: 15),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Chi tiết từng câu & Sửa bài', style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
                FilledButton.tonal(
                  onPressed: () => setState(() {
                    _currentFeedback = null;
                    _reviewedExam = null;
                    _tabController.animateTo(0);
                  }),
                  child: const Text('Làm đề mới'),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Detailed question reviews with corrections
            ...feedback.details.asMap().entries.map((entry) {
              final idx = entry.key;
              final item = entry.value;
              return Card(
                elevation: 0,
                margin: const EdgeInsets.only(bottom: 14),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                  side: BorderSide(
                    color: item.isCorrect ? Colors.green.shade300 : Colors.red.shade300,
                    width: 1.5,
                  ),
                ),
                color: Colors.white,
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: item.isCorrect ? const Color(0xFFE8F5E9) : const Color(0xFFFFEBEE),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              item.isCorrect ? '✅ Làm đúng' : '❌ Làm sai',
                              style: TextStyle(
                                color: item.isCorrect ? Colors.green.shade800 : Colors.red.shade800,
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                              ),
                            ),
                          ),
                          Text('Câu ${idx + 1}', style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Text(item.prompt, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, height: 1.3)),
                      if (item.pinyin.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(item.pinyin, style: const TextStyle(fontSize: 13, color: Color(0xFF5C6F64), fontStyle: FontStyle.italic)),
                      ],
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: const Color(0xFFF8FAF9),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text.rich(
                              TextSpan(
                                text: 'Đáp án của bạn: ',
                                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                                children: [
                                  TextSpan(
                                    text: item.userAnswer,
                                    style: TextStyle(
                                      color: item.isCorrect ? Colors.green.shade700 : Colors.red.shade700,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text.rich(
                              TextSpan(
                                text: 'Đáp án đúng: ',
                                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                                children: [
                                  TextSpan(
                                    text: item.correctAnswer,
                                    style: TextStyle(color: Colors.green.shade800, fontWeight: FontWeight.bold),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 12),

                      // Sửa thành cho đúng & Giải thích chi tiết
                      Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFF9E6),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: const Color(0xFFFFE494)),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Row(
                              children: [
                                Icon(Icons.lightbulb_outline, size: 18, color: Color(0xFF8C6200)),
                                SizedBox(width: 6),
                                Text(
                                  'SỬA THÀNH CHO ĐÚNG & GIẢI THÍCH:',
                                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Color(0xFF8C6200)),
                                ),
                              ],
                            ),
                            const SizedBox(height: 6),
                            Text(
                              item.explanation,
                              style: const TextStyle(fontSize: 13, height: 1.4, color: Color(0xFF4A3B18)),
                            ),
                            if (item.correction.isNotEmpty) ...[
                              const SizedBox(height: 6),
                              Text(
                                item.correction,
                                style: const TextStyle(fontSize: 13, height: 1.4, color: Color(0xFF4A3B18)),
                              ),
                            ],
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}
