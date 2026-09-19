# Đối chiếu Usecase.xlsx

Nguồn: Usecase.xlsx do người dùng cung cấp. Đã đọc 4 sheet (UC tổng quan, UC phân rã, Đặc tả UC, Ma trận phân quyền) và xem 5 ảnh sơ đồ nhúng. Dữ liệu trích xuất nằm cùng thư mục trong usecase-workbook.json và usecase-assets/.

## Cách xử lý khác biệt trong tài liệu

- Sheet tổng quan và sơ đồ cho Khách đăng ký; một ô ma trận đánh ❌ ở đăng ký. Áp dụng luồng đăng ký của UC-01 và sơ đồ.
- Khách được OCR, dịch và dùng thử sửa câu; không lưu sổ tay, không chấm bài, không xem dữ liệu cá nhân. Phân tích ngữ cảnh chuyên sâu dành cho người đăng nhập.
- Ngưỡng hoàn thành ôn tập là >=80 theo đặc tả; không dùng >80 ở dòng mô tả không nhất quán.
- Dashboard hiển thị ba trục Nghe, Đọc, Viết. Điểm nét chữ riêng vẫn giữ trong dữ liệu để xem chi tiết.
- Email OTP: người dùng xác nhận chưa có dịch vụ gửi thư; chuẩn bị cấu hình SMTP và luồng xác nhận, không tuyên bố đã gửi OTP thật.

## Đối chiếu 35 chức năng

| STT | Chức năng | Đối chiếu/triển khai |
|---|---|---|
|1|Dùng thử|Tra từ, OCR, dịch, sửa câu có giới hạn 20 yêu cầu AI/giờ theo địa chỉ truy cập; không ghi vào lịch sử cá nhân.|
|2|Đăng ký|Email, họ tên, mật khẩu và xác nhận; kiểm tra email trùng, cấp phiên học viên.|
|3|Đăng nhập|Xác thực mật khẩu và điều hướng Admin/học viên theo quyền server.|
|4|Quên mật khẩu|Bổ sung mã email 6 số, 10 phút, tối đa 5 lần thử, dùng một lần; thiếu dịch vụ SMTP thật theo xác nhận người dùng.|
|5|Đăng xuất|Hủy token trên server và xóa phiên phía trình duyệt.|
|6|Tra từ bàn phím|Tìm chữ Hán/pinyin/nghĩa Việt qua kho từ.|
|7|Tra chữ Canvas|Bổ sung quyền OCR cho khách; giữ OCR có AI cho học viên.|
|8|Thứ tự nét|So khớp với nét chuẩn bằng thuật toán offline; không phải gọi mô hình AI.|
|9|Dáng/tỉ lệ nét|Điểm 0–100, thông tin nét sai; cần dữ liệu nét chuẩn tương ứng trong kho.|
|10|Nghe phát âm|Có audio mẫu tổng hợp; chưa phải toàn bộ kho thu âm người bản xứ.|
|11|Sổ tay|Lưu/bỏ lưu theo user_id, bảo vệ bằng token.|
|12|Dịch đa ngôn ngữ|Bổ sung chọn nguồn/đích Trung, Việt, Anh, Nhật, Hàn; giới hạn 5000 ký tự; gọi Gemini.|
|13|Sửa ngữ pháp|Chỉ lỗi, câu gợi ý; bổ sung dùng thử khách, không cho ngữ cảnh riêng.|
|14|Phân tích ngữ cảnh|Endpoint học viên yêu cầu phiên; khách không có trường ngữ cảnh trên UI.|
|15|Test Nghe|Audio, chọn/điền đáp án, chấm và lưu kết quả.|
|16|Giải thích bẫy nghe|Transcript, lời giải và nhận xét từ bộ chấm; Admin sửa nội dung đề.|
|17|Test Đọc|Điền từ, đọc hiểu; bổ sung dạng sắp xếp câu.|
|18|Viết sắp xếp câu|Bổ sung dạng sentence_order, Admin tạo các cụm từ và đáp án đầy đủ; học viên chạm từ theo thứ tự.|
|19|Canvas trong bài thi|Canvas, điểm nét, sửa lại bài yếu.|
|20|Đoạn văn|Rubric Gemini và kết quả lưu server; Admin có thể chỉnh điểm.|
|21|Lịch sử/Flashcard|Theo từng tài khoản, từ đã tra; có Flashcard.|
|22|Lọc chữ <80|Lấy điểm gần nhất, có danh sách ôn.|
|23|Lọc đoạn văn <80|Có danh sách bài viết yếu và góp ý.|
|24|Luyện lại chữ|Canvas luyện lại, đạt >=80 bỏ khỏi danh sách yếu.|
|25|Luyện lại đoạn văn|Nộp lại nhiều lần, đạt >=80 hoàn thành; điểm Admin đồng bộ.|
|26|Dashboard cá nhân|Streak, bài, từ, điểm; bổ sung mục tiêu ngày/tuần và tránh lỗi AI làm mất cả thống kê.|
|27|Năng lực AI|Báo cáo AI có cache; radar ba kỹ năng.|
|28|Báo cáo hệ thống|Thống kê Admin, usage AI, user, đề, kết quả.|
|29|Hồ sơ|Bổ sung trang dùng chung Admin/học viên: họ tên, số điện thoại, ngày sinh; cập nhật tên thật.|
|30|Avatar/mật khẩu|Ảnh PNG/JPEG/WebP <=5MB được giải mã/kiểm tra; đổi mật khẩu kiểm tra mật khẩu cũ và hủy phiên.|
|31|Quản lý user|Khóa/mở, phân quyền, bảo vệ Admin và kiểm tra phiên bản.|
|32|Kho từ/nét|CRUD và kiểm tra tham chiếu dữ liệu.|
|33|Ngân hàng đề|CRUD, trạng thái phát hành, HSK1–6, giữ lịch sử khi có tham chiếu. Dữ liệu mẫu không phải ngân hàng đề chính thức đầy đủ.|
|34|Cấu hình AI|Admin sửa model/prompt/temperature/token/enabled, test kết nối; key giữ ở cấu hình backend, không gửi vào Flutter.|
|35|Ghi đè điểm|Lý do, lịch sử trước/sau, phúc khảo và cập nhật kết quả học viên.|

## Ngoại lệ và phần bổ sung

- Lưu nháp bài Nghe/Đọc/tổng hợp theo ID tài khoản + ID đề + phiên bản. Khi tải lại, mở đúng đề để tiếp tục; Canvas khôi phục nét.
- Khôi phục mật khẩu không làm lộ mã qua API/log. SMTP dùng STARTTLS và cấu hình server.
- Kiểm thử API mới dùng database riêng; không thay đổi tài khoản đang sử dụng.
- Đã bổ sung sinh 1–3 bài luyện câu cá nhân hóa từ lỗi sai dưới 80 điểm, lưu đề theo chủ sở hữu; nộp bài được chấm và lưu lịch sử. Kiểm thử riêng xác nhận tài khoản khác không đọc/nộp được đề đó.
- 58 kiểm thử Python đạt; 39 kiểm thử Flutter đạt; analyze và build web đạt.
- Kiểm thử trình duyệt mobile: sửa tên/điện thoại/ngày sinh/mục tiêu, tải ảnh thật PNG, đổi mật khẩu và thu hồi phiên, trang OTP chưa cấu hình.
- Gemini thật: dịch "你好，我正在学习中文。" sang tiếng Việt trả HTTP 200 và bản dịch phù hợp. Các bài kiểm thử OCR/sửa câu/chấm và sinh bài ôn dùng provider giả lập; không khẳng định chất lượng mọi phản hồi AI chỉ từ test đó.

## Phần cần cấu hình hoặc dữ liệu bên ngoài

1. SMTP chưa được cung cấp. Luồng mã OTP đã có nhưng chưa thể gửi email thật. Cấu hình SMTP_HOST, SMTP_PORT=587, SMTP_FROM, SMTP_USERNAME, SMTP_PASSWORD trong backend/.env; không commit khóa/mật khẩu.
2. Kho từ/audio/nét/đề hiện là dữ liệu mẫu, không phải bộ đề HSK hoặc bản ghi giọng bản xứ đầy đủ. Chức năng biên soạn và chọn HSK1–6 có sẵn; cần nhập ngân hàng nội dung đã kiểm duyệt nếu dùng chính thức.
3. Kiểm chứng mobile là trình duyệt và widget test; chưa kiểm chứng bản cài Android/iOS. Trang quản lý hồ sơ/OTP dùng chung website tại /account và /recover.
4. Bài ôn cá nhân hóa hiện tạo bài luyện câu dạng văn bản từ lỗi sai; không tự tạo audio mới cho đề Nghe.
5. Lưu nháp là trên thiết bị hiện tại; không phải đồng bộ bản nháp giữa máy. Bài đã nộp, hồ sơ, sổ tay lưu backend chung.
6. API key AI tiếp tục cấu hình phía máy chủ; trang Admin sửa model/prompt và kiểm tra kết nối, không hiển thị khóa bí mật.

## Chạy và vị trí file

- Từ thư mục dự án: chạy Start-HanziGo.ps1, mở http://127.0.0.1:8010/.
- Bản web chạy: build/web. Python: backend/.venv. Dữ liệu: backend/hanzi_go.db. Log: backend/server.log và backend/server-error.log.
- Tài liệu và ảnh Excel: docs/usecase-audit/. Kết quả kiểm thử trình duyệt: test-results/.
- Đã sao lưu database trước khi nâng cấp. Không xóa tài khoản hoặc lịch sử đang sử dụng.

