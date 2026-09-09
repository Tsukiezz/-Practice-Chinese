# Tích hợp Nguyên + Kiệt vào test — 09/09/2026

Nguồn: `origin/nguyen` tại `022265f`, `origin/kiet` tại `bb9d307`, trên lịch sử `origin/test` tại `3403b81`. Giữ thêm bản sửa kiểm tra output AI và biên bản nghiệm thu của Nguyên trong workspace.

## Kết quả tích hợp

- Giữ giao diện Admin responsive, version tài khoản, audit, cấu hình/test AI, sửa điểm, lịch sử và phúc khảo của Nguyên.
- Thêm Flutter học viên và API của Kiệt: đăng nhập, đề Nghe/Đọc/tổng hợp, lịch sử, Canvas, ôn tập và dashboard/báo cáo năng lực.
- Ghép migration appeals/users.version với dictionary_history, review_progress, review_attempts và capability_reports; không xóa dữ liệu cũ.
- Giữ adapter văn bản mặc định của Nguyên và các adapter đề thi/Canvas/báo cáo của Kiệt. Chuẩn hóa điểm số và phản hồi cho cả hai.
- Khi Admin sửa điểm hoặc duyệt phúc khảo cho lần ôn tập mới nhất, cập nhật completed_at trong cùng transaction. Điểm dưới 80 mở lại ôn tập, từ 80 hoàn thành lại; giữ điểm gốc và lịch sử.
- Kiểm thử phúc khảo và trình duyệt dùng grader giả lập trong tiến trình kiểm thử riêng. Backend chạy thật vẫn dùng Gemini; không thêm chế độ bỏ qua AI vào sản phẩm.
- Bật workflow API/trình duyệt cho push nhánh `test`.

## Kiểm chứng

- `python -m unittest -v test_admin`: 29 bài, gồm tích hợp sửa điểm/phúc khảo với ôn tập.
- `python smoke_browser.py`: Edge headless, desktop/mobile, Admin và phúc khảo.
- `flutter analyze`: không phát hiện vấn đề.
- `flutter test`: 20/20 đạt.

Flutter 3.47.2 chạy trên bản sao mã nguồn trong thư mục tạm không dấu, dùng junction SDK không dấu để tránh lỗi LSP/native-assets trên đường dẫn Windows có dấu/khoảng trắng. Backend dùng Python 3.13 và thư viện kiểm thử tạm, database tạm. Không đưa khóa, database, dependencies hay ảnh kiểm thử vào Git.

Chưa gọi Gemini thật bằng khóa của nhóm; kiểm thử AI giả lập phản hồi nhà cung cấp. Không có kết luận về chất lượng chấm thực tế hoặc Android/iOS release. Flutter kết nối API theo hướng dẫn README; Admin và phúc khảo web tại `/admin`, `/review`.
