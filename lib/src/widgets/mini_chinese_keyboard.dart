import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Helper function to safely insert text at cursor position in TextEditingController
void insertAtCursor(TextEditingController controller, String text) {
  final current = controller.value;
  final selection = current.selection;
  final start = selection.start >= 0 ? selection.start : current.text.length;
  final end = selection.end >= 0 ? selection.end : current.text.length;
  final newText = current.text.replaceRange(start, end, text);
  controller.value = TextEditingValue(
    text: newText,
    selection: TextSelection.collapsed(offset: start + text.length),
  );
}

/// Helper function to delete character at cursor position in TextEditingController
void backspaceAtCursor(TextEditingController controller) {
  final current = controller.value;
  final selection = current.selection;
  if (selection.start > 0 && selection.start == selection.end) {
    final textBefore = current.text.substring(0, selection.start);
    final textAfter = current.text.substring(selection.start);
    final charsBefore = textBefore.characters;
    final newBefore = charsBefore.skipLast(1).toString();
    controller.value = TextEditingValue(
      text: newBefore + textAfter,
      selection: TextSelection.collapsed(offset: newBefore.length),
    );
  } else if (selection.start >= 0 && selection.end > selection.start) {
    final newText = current.text.replaceRange(selection.start, selection.end, '');
    controller.value = TextEditingValue(
      text: newText,
      selection: TextSelection.collapsed(offset: selection.start),
    );
  }
}

/// Mini interactive Chinese virtual keyboard for web & mobile
class MiniChineseKeyboard extends StatefulWidget {
  const MiniChineseKeyboard({
    super.key,
    required this.controller,
    this.targetLabel = 'Văn bản',
    this.onClose,
  });

  final TextEditingController controller;
  final String targetLabel;
  final VoidCallback? onClose;

  @override
  State<MiniChineseKeyboard> createState() => _MiniChineseKeyboardState();
}

class _MiniChineseKeyboardState extends State<MiniChineseKeyboard> {
  int _selectedCategoryIndex = 0;

  static const List<Map<String, dynamic>> _tabs = [
    {
      'title': 'Pinyin có dấu',
      'icon': Icons.spellcheck,
      'groups': [
        {'name': 'a', 'keys': ['ā', 'á', 'ǎ', 'à', 'a']},
        {'name': 'o', 'keys': ['ō', 'ó', 'ǒ', 'ò', 'o']},
        {'name': 'e', 'keys': ['ē', 'é', 'ě', 'è', 'e']},
        {'name': 'i', 'keys': ['ī', 'í', 'ǐ', 'ì', 'i']},
        {'name': 'u', 'keys': ['ū', 'ú', 'ǔ', 'ù', 'u']},
        {'name': 'ü', 'keys': ['ǖ', 'ǘ', 'ǚ', 'ǜ', 'ü']},
      ],
    },
    {
      'title': 'Đại từ & Nhân xưng',
      'icon': Icons.people_alt_outlined,
      'keys': [
        '我', '你', '您', '他', '她', '它', '我们', '你们', '他们', '她们',
        '谁', '大家', '自己', '朋友', '老师', '同学', '爸爸', '妈妈', '人'
      ],
    },
    {
      'title': 'Động từ thông dụng',
      'icon': Icons.directions_run_outlined,
      'keys': [
        '是', '有', '在', '去', '来', '看', '听', '说', '读', '写',
        '做', '想', '要', '会', '能', '吃', '喝', '买', '叫', '走',
        '认识', '学习', '喜欢', '知道', '觉得', '工作', '睡觉', '给'
      ],
    },
    {
      'title': 'Phó từ & Trợ từ',
      'icon': Icons.auto_awesome,
      'keys': [
        '的', '了', '很', '吗', '呢', '吧', '不', '没', '也', '都',
        '还', '就', '太', '真', '最', '再', '一起', '已经', '非常', '得'
      ],
    },
    {
      'title': 'Hỏi & Chỉ định',
      'icon': Icons.help_outline,
      'keys': [
        '这', '那', '哪', '什么', '怎么', '为什么', '多少', '几',
        '哪里', '什么时候', '怎么样', '哪个', '这个', '那个'
      ],
    },
    {
      'title': 'Dấu câu tiếng Trung',
      'icon': Icons.text_fields,
      'keys': [
        '，', '。', '、', '？', '！', '“', '”', '《', '》', '：',
        '；', '……', '—', '（', '）', '【', '】', '·', '~'
      ],
    },
  ];

  @override
  Widget build(BuildContext context) {
    final currentTab = _tabs[_selectedCategoryIndex];

    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFFAFBF9),
        borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            blurRadius: 16,
            offset: const Offset(0, -4),
          ),
        ],
        border: Border.all(color: const Color(0xFFDCE5E0)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Header Bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            decoration: const BoxDecoration(
              color: Color(0xFFEDF3F0),
              borderRadius: BorderRadius.vertical(top: Radius.circular(19)),
            ),
            child: Row(
              children: [
                const Icon(Icons.keyboard_alt_outlined, size: 20, color: AppTheme.jade),
                const SizedBox(width: 8),
                Expanded(
                  child: RichText(
                    text: TextSpan(
                      style: const TextStyle(fontSize: 13, color: Color(0xFF26322C)),
                      children: [
                        const TextSpan(
                          text: 'Bàn phím tiếng Trung mini · ',
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                        TextSpan(
                          text: widget.targetLabel,
                          style: const TextStyle(color: AppTheme.jade, fontWeight: FontWeight.w600),
                        ),
                      ],
                    ),
                  ),
                ),
                // Space Button
                IconButton(
                  tooltip: 'Khoảng trắng',
                  icon: const Icon(Icons.space_bar, size: 20, color: Color(0xFF384A41)),
                  onPressed: () => insertAtCursor(widget.controller, ' '),
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
                ),
                // Backspace Button
                IconButton(
                  tooltip: 'Xóa ký tự (Backspace)',
                  icon: const Icon(Icons.backspace_outlined, size: 18, color: AppTheme.red),
                  onPressed: () => backspaceAtCursor(widget.controller),
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
                ),
                // Close Button
                if (widget.onClose != null)
                  IconButton(
                    tooltip: 'Đóng bàn phím',
                    icon: const Icon(Icons.keyboard_hide_outlined, size: 20, color: Color(0xFF6B7E74)),
                    onPressed: widget.onClose,
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
                  ),
              ],
            ),
          ),

          // Categories Tabs Bar
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            child: Row(
              children: List.generate(_tabs.length, (index) {
                final tab = _tabs[index];
                final isSelected = _selectedCategoryIndex == index;
                return Padding(
                  padding: const EdgeInsets.only(right: 6),
                  child: ChoiceChip(
                    avatar: Icon(
                      tab['icon'] as IconData,
                      size: 14,
                      color: isSelected ? Colors.white : AppTheme.jade,
                    ),
                    label: Text(
                      tab['title'] as String,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                        color: isSelected ? Colors.white : const Color(0xFF26322C),
                      ),
                    ),
                    selected: isSelected,
                    selectedColor: AppTheme.jade,
                    backgroundColor: Colors.white,
                    side: BorderSide(
                      color: isSelected ? AppTheme.jade : const Color(0xFFD4DFD8),
                    ),
                    onSelected: (_) => setState(() => _selectedCategoryIndex = index),
                  ),
                );
              }),
            ),
          ),

          // Keys Grid / Layout
          Container(
            height: 145,
            padding: const EdgeInsets.fromLTRB(10, 4, 10, 10),
            child: currentTab.containsKey('groups')
                ? _buildPinyinGroups(currentTab['groups'] as List<Map<String, dynamic>>)
                : _buildKeysGrid(currentTab['keys'] as List<String>),
          ),
        ],
      ),
    );
  }

  Widget _buildPinyinGroups(List<Map<String, dynamic>> groups) {
    return ListView.separated(
      scrollDirection: Axis.horizontal,
      itemCount: groups.length,
      separatorBuilder: (_, __) => const SizedBox(width: 8),
      itemBuilder: (context, idx) {
        final grp = groups[idx];
        final name = grp['name'] as String;
        final keys = (grp['keys'] as List).cast<String>();

        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 6),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFFE2EBE5)),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                name.toUpperCase(),
                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.jade),
              ),
              const SizedBox(height: 4),
              Expanded(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: keys.map((k) => _buildKeyButton(k, width: 38, height: 26)).toList(),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildKeysGrid(List<String> keys) {
    return SingleChildScrollView(
      child: Wrap(
        spacing: 6,
        runSpacing: 6,
        children: keys.map((k) => _buildKeyButton(k, height: 36)).toList(),
      ),
    );
  }

  Widget _buildKeyButton(String text, {double? width, double height = 34}) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(8),
      elevation: 0.5,
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: () => insertAtCursor(widget.controller, text),
        child: Container(
          width: width,
          height: height,
          padding: EdgeInsets.symmetric(horizontal: width == null ? 10 : 0),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: const Color(0xFFD6E2DC)),
          ),
          child: Text(
            text,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w600,
              color: Color(0xFF1E2B25),
            ),
          ),
        ),
      ),
    );
  }
}
