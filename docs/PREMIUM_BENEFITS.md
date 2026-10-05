# HanziGo Premium — quyền lợi và học liệu nâng cao

## Phạm vi bản cập nhật

- Miễn phí: HSK 1–6, 3 đề AI/ngày (UTC+7), cọ mặc định, giao diện mặc định sáng/tối.
- Premium còn hạn: tạo đề AI không giới hạn số đề (1–50 câu/đề), bút lông / bút mực / thư pháp, toàn bộ bảng màu, khung và huy hiệu vàng.
- HSK 7, 8, 9: mỗi cấp 2 bài học, 2 bài nghe (2 câu/bài), 2 bài đọc (2 câu/bài), 1 kiểm tra Nghe + Đọc (8 câu, 20 phút). Có thêm 1 bài giao tiếp thương lượng lịch giao hàng.
- Nội dung mới do HanziGo biên soạn, chỉ là học liệu bổ trợ, không phải giáo trình đầy đủ hoặc đề thi chính thức. HSK 7–9 chính thức là kỳ thi chung; app dùng nhãn 7/8/9 cho mức luyện tăng dần. Tham khảo phạm vi: https://www.chinesetest.cn/HSK/7-9
- Đọc/Nghe: chọn chip HSK 7/8/9. Kiểm tra: nút `Kiểm tra HSK 7/8/9 · Premium`, hoặc chọn cấp nâng cao khi tạo đề AI. AI lỗi thì báo thử lại, không dùng bộ từ vựng HSK 1–6 làm đề thay thế.

## Bảo lưu chuỗi

Tối đa 3 ngày bỏ lỡ/tháng lịch Việt Nam (UTC+7), không cộng dồn. Tính khi tải thống kê; ngày hôm nay chưa kết thúc không bị xem là bỏ lỡ. Giữ lịch sử từng ngày trong `streak_protection` với khóa duy nhất `(user_id,day)`; transaction tránh tiêu lượt trùng. Chỉ bảo vệ khoảng bỏ lỡ trong thời gian được bật quyền, không khôi phục chuỗi cũ trước khi kích hoạt. Gói 30 ngày và 365 ngày đều dùng cùng chính sách theo tháng lịch.

`users.streak_freezes` và `added_freezes` cũ còn giữ để tương thích dữ liệu/API cũ, không còn là số dư dùng cho hạn mức hàng tháng. Số lượt hiển thị trong API người dùng/Premium là hạn mức tháng trừ các ngày đã bảo lưu. Bài học ghi ngày học trong `learner_activity_days` để không mất lịch sử khi cập nhật tiến độ cùng một bài.

## Quyền truy cập và dữ liệu

- `/api/me/benefits` và `PUT /api/me/benefits/preferences` dùng phiên đăng nhập, kiểm tra hạn gói từ DB. Lựa chọn màu/cọ lưu theo người dùng; hết hạn trả mặc định.
- `/api/lessons` chỉ công khai danh sách. Nội dung, tiến độ và nộp bài HSK 7–9/giao tiếp đều kiểm tra Premium phía máy chủ.
- `/api/exams?hsk=7..9` và `/api/exams/{id}/submit` kiểm tra Premium. ID âm thuộc catalog nâng cao bất biến, không trùng ID bảng `exams` cũ. Không phải nới CHECK HSK 1–6 hoặc rebuild bảng có dữ liệu khách hàng.
- Kết quả nâng cao lưu vào `results` với `exam_id=NULL` và snapshot đầy đủ để giữ lịch sử, điểm và giải thích. Không trả đáp án/giải thích trong đề chưa nộp.
- `ai_exam_daily_usage` giữ lượt độc lập với lịch sử đề: xóa đề không hoàn lượt; đề mẫu không tính quota. Kiểm tra lại hạn mức trong transaction lưu đề để chống nhiều yêu cầu đồng thời vượt 3.
- Schema mới chỉ thêm bảng, chạy idempotent trong startup local và Vercel. Không chạy seed hay sửa đơn thanh toán cũ.
- `product_knowledge.py` ghép thông tin giá/quyền lợi và mô tả tính năng thực tế vào prompt AI kể cả khi admin đã lưu prompt riêng. Fallback offline trả lời cùng nguồn; thanh toán lỗi chuyển người hỗ trợ, không tự xác nhận tiền.

## Kiểm tra

Backend: `python -m unittest test_premium_benefits test_premium test_sepay_gateway test_support_chat test_lessons test_usecase_features`

Flutter: `flutter test test/premium_benefits_test.dart test/theme_preferences_test.dart`, `flutter analyze`, `flutter build web --no-wasm-dry-run`.

Kiểm tra thủ công sau deploy: tài khoản thường bị chặn HSK 7–9; Premium mở được cả bốn mục, nghe được audio và lưu kết quả; đổi cọ/màu rồi đăng nhập lại; kiểm tra khung vàng và lượt bảo lưu. Không dùng biên lai hoặc `result=success` phía trình duyệt để cấp Premium.

### Kết quả kiểm thử ngày 05/10/2026

- 64 test backend nêu trên: đạt.
- 11 test Flutter thuộc `auth_screens_test.dart`, `premium_benefits_test.dart`, `theme_preferences_test.dart`: đạt.
- Phân tích Flutter: không có error/warning, còn 25 thông báo info có sẵn (deprecated/style).
- Browser smoke `smoke_premium_benefits.py`: đạt khóa màu miễn phí/Premium, lưu màu, phân quyền API HSK 7–9, render Flutter desktop 1200px/mobile 390px; không có lỗi JavaScript. Dùng database/tài khoản giả tách biệt production.
- Toàn bộ Flutter suite vẫn có 4 ca lỗi đã tái hiện trên mã gốc `2f778f1`: nút bản dịch trên mobile (`lessons_test`), hai ca viết tay (`student_features_widget_test`), và tìm nội dung trang chủ ngoài viewport (`widget_test`). Không tính chúng là kiểm thử đã đạt; không bỏ/disable các ca này.
- SDK Flutter cũ bị thiếu cache; kiểm tra dùng SDK 3.47.2 mới và bản sao mã trong thư mục tạm ASCII để tránh lỗi OneDrive/đường dẫn Unicode. Không thay SDK cũ hoặc xóa dữ liệu dự án.
