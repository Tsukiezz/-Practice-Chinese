import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:hanzi_go/src/services/exam_draft_store.dart';

void main() {
  test(
    'drafts are isolated by user, exam version and cleared after submit',
    () async {
      SharedPreferences.setMockInitialValues({});
      await ExamDraftStore.save(1, 'reading', 2, 3, {'q': 'answer'});
      expect(await ExamDraftStore.read(1, 'reading', 2, 3), {'q': 'answer'});
      expect(await ExamDraftStore.read(2, 'reading', 2, 3), isEmpty);
      expect(await ExamDraftStore.read(1, 'reading', 2, 4), isEmpty);
      await ExamDraftStore.clear(1, 'reading', 2, 3);
      expect(await ExamDraftStore.read(1, 'reading', 2, 3), isEmpty);
    },
  );
}
