import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hanzi_go/src/screens/review_screen.dart';
import 'package:hanzi_go/src/services/student_service.dart';
import 'package:hanzi_go/src/widgets/hanzi_drawing_canvas.dart';

class ReviewService extends StudentService {
  ReviewService() : super(baseUrl: 'http://test/api', tokenProvider: () async => 'test');
  String? kind;
  @override
  Future<List<StudentResult>> fetchReviewItems(String kind) async { this.kind = kind; return []; }
}
void main() {
  testWidgets('review offers only reading listening and exams', (tester) async {
    final service = ReviewService();
    await tester.pumpWidget(MaterialApp(home: ReviewScreen(service: service, initialKind: 'vocabulary')));
    await tester.pumpAndSettle();
    expect(service.kind, 'reading');
    expect(find.text('Từ vựng'), findsNothing);
    expect(find.text('Viết tay'), findsNothing);
    expect(find.text('Đoạn văn'), findsNothing);
    for (final entry in {'Nghe hiểu': 'listening', 'Kiểm tra': 'exam', 'Đọc phát âm': 'reading'}.entries) {
      await tester.tap(find.text(entry.key));
      await tester.pumpAndSettle();
      expect(service.kind, entry.value);
    }
  });
  test('dense canvas payload keeps endpoints within the API bounds', () {
    final controller = HanziCanvasController();
    addTearDown(controller.dispose);
    controller.start(const Offset(-1, 50), const Size(100, 100));
    for (var i = 0; i < 2000; i++) {
      controller.update(Offset(i / 20, 50), const Size(100, 100));
    }
    controller.end();
    expect(controller.payload.single.length, 512);
    expect(controller.payload.single.first['x'], 0);
    expect(controller.payload.single.last['x'], closeTo(1023.488, .01));
  });
}
