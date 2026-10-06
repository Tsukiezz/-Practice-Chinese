import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hanzi_go/src/widgets/streak_card.dart';

void main() {
  testWidgets('Personal streak distinguishes learning and protection on mobile', (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    var refreshed = false;
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: SingleChildScrollView(child: StreakCard(
      onRefresh: () => refreshed = true,
      details: {
        'current': 3, 'longest': 7, 'total_learning_days': 12,
        'today': '2026-10-06', 'next_milestone': 7, 'learned_today': true,
        'is_premium': true, 'freezes_remaining': 2, 'freeze_month': '2026-10',
        'calendar': List.generate(28, (i) => {
          'date': DateTime(2026, 9, 9).add(Duration(days: i)).toIso8601String().substring(0, 10),
          'status': i == 26 ? 'protected' : i == 27 ? 'learned' : 'empty',
        }),
      },
    )))));
    expect(find.text('3 ngày liên tiếp'), findsOneWidget);
    expect(find.text('Kỷ lục: 7 ngày'), findsOneWidget);
    expect(find.byTooltip('2026-10-05: Bảo lưu'), findsOneWidget);
    expect(find.byTooltip('2026-10-06: Đã học · hôm nay'), findsOneWidget);
    expect(find.textContaining('2/3 lượt còn lại'), findsOneWidget);
    await tester.tap(find.byTooltip('Cập nhật chuỗi ngày học'));
    expect(refreshed, isTrue);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Free empty streak does not claim learning', (tester) async {
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: StreakCard(
      details: const {'current': 0, 'is_premium': false}, onRefresh: () {},
    ))));
    expect(find.text('0 ngày liên tiếp'), findsOneWidget);
    expect(find.text('Học hôm nay để tiếp nối chuỗi của bạn.'), findsOneWidget);
    expect(find.textContaining('Tài khoản miễn phí'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
