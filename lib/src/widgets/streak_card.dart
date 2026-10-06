import 'package:flutter/material.dart';

class StreakCard extends StatelessWidget {
  const StreakCard({super.key, required this.details, required this.onRefresh});
  final Map<String, dynamic> details;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final current = details['current'] as int? ?? 0;
    final milestone = details['next_milestone'] as int? ?? 3;
    final learned = details['learned_today'] == true;
    final calendar = details['calendar'] as List? ?? [];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Icon(Icons.local_fire_department, color: colors.primary),
            const SizedBox(width: 8),
            const Expanded(child: Text('Chuỗi ngày học', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800))),
            IconButton(onPressed: onRefresh, tooltip: 'Cập nhật chuỗi ngày học', icon: const Icon(Icons.refresh)),
          ]),
          Text('$current ngày liên tiếp', style: const TextStyle(fontSize: 26, fontWeight: FontWeight.bold)),
          Text(learned ? 'Hôm nay bạn đã học. Giữ nhịp vào ngày mai nhé!' : 'Học hôm nay để tiếp nối chuỗi của bạn.'),
          const SizedBox(height: 12),
          Wrap(spacing: 16, runSpacing: 8, children: [
            Text('Kỷ lục: ${details['longest'] ?? 0} ngày'),
            Text('Đã học: ${details['total_learning_days'] ?? 0} ngày'),
          ]),
          const SizedBox(height: 12),
          LinearProgressIndicator(value: (current / milestone).clamp(0.0, 1.0), minHeight: 6),
          const SizedBox(height: 6),
          Text('Mốc tiếp theo: $milestone ngày · còn ${milestone - current} ngày'),
          const SizedBox(height: 16),
          const Text('28 ngày gần đây · giờ Việt Nam (UTC+7)', style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          GridView.builder(
            shrinkWrap: true, physics: const NeverScrollableScrollPhysics(),
            itemCount: calendar.length,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 7, mainAxisExtent: 48, mainAxisSpacing: 6, crossAxisSpacing: 6),
            itemBuilder: (context, index) {
              final day = calendar[index] as Map;
              final date = day['date'] as String;
              final active = day['status'] == 'learned';
              final frozen = day['status'] == 'protected';
              final label = active ? 'Đã học' : frozen ? 'Bảo lưu' : 'Chưa học';
              final isToday = date == details['today'];
              return Tooltip(
                message: '$date: $label${isToday ? ' · hôm nay' : ''}',
                child: Semantics(label: '$date: $label${isToday ? ', hôm nay' : ''}', excludeSemantics: true,
                  child: Container(
                    decoration: BoxDecoration(
                      color: active ? colors.primaryContainer : frozen ? colors.secondaryContainer : colors.surfaceContainerHighest,
                      borderRadius: BorderRadius.circular(8),
                      border: isToday ? Border.all(color: colors.primary, width: 2) : null,
                    ),
                    child: Center(child: FittedBox(child: Column(mainAxisSize: MainAxisSize.min, children: [
                      Text(date.substring(8), style: TextStyle(color: active ? colors.onPrimaryContainer : frozen ? colors.onSecondaryContainer : colors.onSurface)),
                      Icon(active ? Icons.check : frozen ? Icons.ac_unit : Icons.remove, size: 14,
                        color: active ? colors.onPrimaryContainer : frozen ? colors.onSecondaryContainer : colors.onSurface),
                    ]))),
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: 8),
          const Text('✓ Đã học   ❄ Bảo lưu   − Chưa học'),
          const SizedBox(height: 12),
          Text(details['is_premium'] == true
              ? "Bảo lưu Premium: ${details['freezes_remaining']}/3 lượt còn lại · tháng ${details['freeze_month']}"
              : 'Premium có 3 lượt bảo lưu mỗi tháng. Tài khoản miễn phí vẫn theo dõi đầy đủ chuỗi học.'),
          const SizedBox(height: 8),
          const Text('Hoàn thành bài luyện, học bài, đọc hoặc tra từ để ghi nhận ngày học. Mở trang cá nhân không được tính là học. Ngày bảo lưu giữ chuỗi nhưng không cộng vào tổng ngày đã học.'),
        ]),
      ),
    );
  }
}
