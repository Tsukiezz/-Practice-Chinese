import 'package:flutter_test/flutter_test.dart';
import 'package:hanzi_go/src/app.dart';

void main() {
  testWidgets('hiển thị trang chủ học tiếng Trung', (tester) async {
    await tester.pumpWidget(const HanziGoApp());
    expect(find.text('Mỗi ngày một chút,\ntiến bộ thật nhiều.'), findsOneWidget);
    expect(find.text('Từ vựng hôm nay'), findsOneWidget);
  });
}
