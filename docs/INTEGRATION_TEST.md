# Tích hợp Nguyên + Kiệt vào test — 09/09/2026

## Cập nhật 12/09/2026: ghép giao diện Tuyến và xác thực

Nguồn `origin/tuyen` tại `58fb360` (hai màn hình đăng nhập/đăng ký), ghép vào `test` đang ở `b01de59`. Giải quyết xung đột add/add của login bằng thiết kế Tuyến và cơ chế xác thực/phân quyền hiện có của nhánh test. Giữ nguyên các luồng học, chấm bài, Admin và phúc khảo đã tích hợp.

- `LoginScreen`: nhận baseUrl/AuthService/callback của AppShell, gọi API thật, giữ hiện/ẩn mật khẩu, trạng thái chờ và thông báo lỗi. Ghi nhớ đăng nhập có tác dụng thực; khi bỏ chọn, session chỉ nằm trong bộ nhớ.
- `RegisterScreen`: điều hướng qua lại với login, kiểm tra họ tên/email/mật khẩu/xác nhận, khóa nút trong lúc gửi, gọi API rồi trở về AppShell với phiên học viên mới.
- `AuthService.register`: `POST /api/auth/register` với `{name,email,password}`, nhận 201 `{token,user,expires_in}`; lưu đúng phiên do server cấp. Xử lý lỗi trùng email, 422 và phản hồi không phải JSON; timeout request xác thực 20 giây.
- Backend: dùng chung bảng users và sessions, chỉ tạo role student, mật khẩu PBKDF2, email chuẩn hóa và unique; tên được trim nhưng mật khẩu giữ nguyên khoảng trắng. Khóa/hạ quyền vẫn thu hồi phiên theo luồng Admin.
- Không nhận role, score hay trường quản trị từ form đăng ký. Admin được cấp riêng qua công cụ server.
- Chỉ hiển thị đăng nhập/đăng ký bằng email. Các nút số điện thoại, OAuth, quên mật khẩu trong bản thiết kế chưa có dịch vụ tương ứng; đã ẩn khỏi bản tích hợp để không có nút bấm rỗng. Checkbox đăng ký mô tả việc tạo tài khoản/lưu tiến trình, không dẫn tới điều khoản chưa được cung cấp.
- Chỉ commit/push **test**, không cập nhật main.

Kiểm thử bổ sung trong `test/auth_screens_test.dart`, `test/auth_service_test.dart`, `backend/test_admin.py` và `backend/smoke_unified.py`: xác nhận mật khẩu, lỗi đăng nhập, đăng ký lưu phiên, tùy chọn ghi nhớ, mật khẩu có khoảng trắng, đăng ký bằng web mobile 390px/320px và lỗi email trùng. Smoke hiện có tiếp tục kiểm tra chuyển Admin/học viên, logout/reload, audio bài Nghe, nộp bài và chặn học viên truy cập Admin. Các kiểm thử dùng DB tạm và không gọi AI thật.

Chạy theo README: build Flutter web, đặt `WEB_APP_DIR`, chạy FastAPI rồi mở `/`. Khi cập nhật giao diện phải build lại web; khởi động riêng backend không tự biên dịch Dart.

Kết quả local 12/09: **32/32 API**, **26/26 Flutter**, `flutter analyze`, build web, smoke Admin và smoke website chung trên Edge đều PASS. Đăng ký mới ở 390px vào đúng phiên student; đăng ký trùng email ở 320px hiển thị lỗi từ backend. Đã kiểm tra ảnh giao diện và không có lỗi JavaScript. Chưa build/chạy bản cài Android/iOS; kết quả mobile ở đây là trình duyệt cảm ứng và widget test.

## Cập nhật 10/09/2026: website chung và bài Nghe

`kiet` vẫn tại `bb9d307`, đã là tổ tiên của nhánh test; phần bài Nghe thiếu do đề seed ở trạng thái nháp, không phải thiếu commit. Bổ sung 3 bài Nghe HSK 1 mẫu có audio MP3 tổng hợp từ đúng transcript; seed riêng cho phép phát hành bài mới, giữ nguyên chỉnh sửa của Admin và dữ liệu học viên.

FastAPI phục vụ Flutter build ở `/` khi đặt `WEB_APP_DIR`, cùng với `/api`, `/admin` và `/media`. Flutter dùng cùng phiên đăng nhập để đọc vai trò từ server. Admin chuyển tới `/admin`, học viên ở ứng dụng học tập; đăng xuất quay về cùng trang đăng nhập. Tài khoản học viên không được phép lấy dữ liệu Admin dù sửa token trong trình duyệt.

Kiểm thử mới: `test/auth_service_test.dart`, hai bài kiểm thử API về dữ liệu/audio, và `backend/smoke_unified.py` chạy website build thật với database tạm. Bộ chấm được thay thế chỉ trong tiến trình kiểm thử; vận hành thật vẫn cần cấu hình Gemini để chấm bài. Giọng đọc là giọng tổng hợp, không phải bản ghi người thật hay đề HSK chính thức.

Hướng dẫn chạy website chung ở README. Workflow `unified-web` bổ sung analyze, Flutter tests, build web và kiểm thử chung trên Chromium.

Kết quả local 10/09: **31/31 API**, **21/21 Flutter**, `flutter analyze`, build web, smoke Admin và smoke website chung đều PASS. Smoke website đã kiểm tra phát MP3 thành công, nộp bài với grader chỉ dành cho test, đăng nhập/đăng xuất Admin và học viên, khôi phục phiên sau reload và chặn token học viên truy cập Admin.

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
