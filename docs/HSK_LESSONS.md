# Lộ trình bài học HSK 1–6

## Phạm vi nội dung

48 bài ngắn, 8 bài cho mỗi cấp HSK 1–6 truyền thống (HSK 2.0). Bài thứ 8 mỗi cấp là bài tổng kết. Đây là nội dung bổ trợ tự biên soạn cho HanziGo, **không phải giáo trình HSK chính thức, không bao phủ toàn bộ đề cương thi và chưa được giáo viên duyệt toàn bộ**.

Tham khảo định hướng năng lực của [tài liệu HSK sáu cấp](https://www.chinesetest.cn/userfiles/file/zhongying2010.pdf). Không sao chép bài đọc hoặc đề thi từ tài liệu này. Giữ cùng hệ HSK 2.0 với kho từ hiện có; không trộn nội dung với đề cương HSK 3.0.

| Cấp | Trọng tâm | Bài |
|---|---|---:|
| HSK 1 | Giới thiệu, hỏi đáp, gia đình, số lượng, giờ giấc, ăn uống, vị trí | 8 |
| HSK 2 | Hoàn thành, đang diễn ra, so sánh, nguyên nhân, khả năng, kế hoạch | 8 |
| HSK 3 | Trải nghiệm, 把, 被, điều kiện, nhượng bộ, xu hướng, trình tự | 8 |
| HSK 4 | Mục đích, tăng tiến, điều kiện cần/đủ, lựa chọn, đề xuất, giải pháp | 8 |
| HSK 5 | Quan điểm, nhân quả, đánh đổi, số liệu, ngoại lệ, tóm tắt, đề xuất | 8 |
| HSK 6 | Tiền đề, tương quan/nhân quả, sắc thái, hàm ý, liên kết, phản biện | 8 |

Mỗi bài có 5 mục từ trọng tâm, 1 phần hướng dẫn/mẫu câu kèm ví dụ Hán tự–pinyin–nghĩa Việt, 1 đoạn đọc với bản dịch ẩn/hiện, 1 nhiệm vụ tự nói/viết và 4 câu hỏi có lời giải. Tổng cộng 192 câu hỏi: 48 mẫu câu, 48 đọc hiểu, 96 từ vựng. Độ dài đoạn đọc và mức độ lập luận tăng dần.

Từ trọng tâm lấy từ kho đã đóng gói, bổ sung một số cụm từ theo ngữ cảnh. Mục ngoài cấp đang học được ghi rõ là mở rộng. Nghĩa từ kế thừa giới hạn rà soát của kho HSK hiện có. Phần bài học không bổ sung bản thu âm và không chấm bài tự viết; nhiệm vụ tự vận dụng được ghi rõ để học viên tự luyện.

## Trải nghiệm sử dụng

- Chọn Tất cả hoặc HSK 1–6; xem mô tả cấp và kiến thức nên có trước khi học.
- Tìm tiêu đề/mẫu câu, hỗ trợ tiếng Việt không dấu; lọc chưa học, đang học, hoàn thành.
- Gợi ý tiếp tục bài đang học, hoặc bắt đầu bài chưa hoàn thành trong cấp đang chọn.
- Bốn bước: Từ vựng → Mẫu câu → Đọc hiểu → Luyện tập. Có thể xem lại bất kỳ bước nào.
- Bấm Tiếp tục lưu mốc học trên máy chủ; lần sau mở lại sẽ tiếp tục ở bước đã lưu.
- Các lựa chọn câu hỏi chưa nộp chỉ tồn tại trong lần mở bài, không khôi phục sau khi thoát; màn hình ghi rõ điều này.
- Nộp đủ 4 câu, đạt ít nhất 3 câu đúng (75%) để hoàn thành. Hiển thị lời giải sau khi nộp.
- Lần làm lại không làm giảm điểm tốt nhất hoặc xóa trạng thái hoàn thành trước đó.
- Giao diện một cột trên điện thoại, hai cột từ 760 px; nội dung bài giới hạn chiều rộng 820 px trên desktop.

## Dữ liệu và API

- `backend/tools/build_lessons.py`: nội dung biên soạn và công cụ dựng dữ liệu; không gọi mạng/Gemini.
- `backend/data/lessons.json`: dữ liệu phiên bản 1, đóng gói trong Git; backend đọc trực tiếp, không cần chạy seed để có bài mới.
- `backend/lesson_catalog.py`: API danh mục, chi tiết, chấm điểm và tiến độ.
- `lesson_progress`: khóa `(user_id, lesson_id)`, bước học, điểm tốt nhất, số lần nộp, thời gian hoàn thành và cập nhật.
- Bảng được tạo bổ sung khi backend khởi động; không sửa/xóa tài khoản hoặc kết quả cũ.

```
GET  /api/lessons?hsk=1&search=chao
GET  /api/lessons/hsk1-01
GET  /api/me/lessons
PUT  /api/me/lessons/hsk1-01/progress  {"stage": 1}
POST /api/me/lessons/hsk1-01/submit    {"answers": {"q1": 1, "q2": 0, "q3": 0, "q4": 2}}
```

`answers` dùng chỉ số lựa chọn bắt đầu từ 0. Hai GET đầu công khai, các API `/me/` yêu cầu phiên đăng nhập. Danh mục không trả phần chi tiết; chi tiết không gửi đáp án/lời giải trước khi nộp. Máy chủ tự tính điểm, từ chối điểm hoặc trạng thái hoàn thành do client tự gửi. Nội dung bài dùng cache trong tiến trình: khi biên tập JSON cần khởi động lại backend.

Dựng lại sau khi biên tập:

```powershell
python backend/tools/build_lessons.py
```

Các ID ổn định `hsk1-01`…`hsk6-08` liên kết tiến độ. Khi thay đổi đáng kể mục tiêu hoặc đáp án, cân nhắc phiên bản bài/ID mới để không coi kết quả của nội dung cũ là kết quả của nội dung mới.

## Kiểm thử

- `backend/test_lessons.py`: đủ 48 bài, phân cấp, cấu trúc nội dung, lọc, giấu đáp án, xác thực, tách tài khoản, mốc hoàn thành, điểm tốt nhất và dữ liệu sai.
- `test/lessons_test.dart`: service, lọc cấp 6, tìm kiếm, trạng thái rỗng, lỗi tải/lưu, học tiếp, bản dịch, nộp câu hỏi và màn hình 320 px/desktop.
- `backend/smoke_unified.py`: đăng nhập trên bản web thật, học 4 bước, nộp bài, xem lời giải và tải lại để xác minh tiến độ còn lưu.
