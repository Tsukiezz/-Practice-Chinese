# Sửa lỗi chấm bài AI

## Lỗi đã xác định ngày 21/09/2026

Model `gemini-3.5-flash` trả HTTP 503 / `UNAVAILABLE` với thông báo quá tải. Kiểm tra kết nối, dịch và sửa câu trên Vercel đều thất bại cùng thời điểm. Khóa được nhận; đây không phải bằng chứng khóa sai. `gemini-3.5-flash-lite` đã phản hồi được bằng cùng khóa.

Một lỗi khác ở frontend: chấm đề Nghe/Đọc và viết tự do chỉ chờ 15 giây, nên có thể báo lỗi mạng dù backend vẫn đang chấm. Bản sửa chờ 75 giây cho yêu cầu AI; backend giới hạn vòng thử lại, tự thử model dự phòng khi quá tải/timeout và trả thông báo theo nguyên nhân. Không tạo điểm giả khi AI thất bại.

## Cách kiểm tra trên Vercel

1. Vào HanziGo bằng tài khoản admin → menu ba gạch → **Cấu hình AI** → **Kiểm tra kết nối Gemini**. “Đã cấu hình khóa” chỉ xác nhận có biến môi trường; nút kiểm tra mới gửi yêu cầu thật.
2. Nếu báo quá tải: cấu hình `GEMINI_FALLBACK_MODEL=gemini-3.5-flash-lite` tại Vercel → project `hanzigo-chinese-learning` → Settings → Environment Variables → Production. Bản triển khai hiện tại đã có biến này. Đổi tên model dự phòng nếu nhà cung cấp ngừng hỗ trợ model đó.
3. Nếu báo khóa không hợp lệ/không có quyền: kiểm tra `GEMINI_API_KEY` trong cùng trang Environment Variables. Khóa chỉ ở backend, không nhập vào source Flutter hay ô model.
4. Nếu báo hết hạn mức (429): kiểm tra quota/rate limit của project Gemini trên Google AI Studio; chờ hạn mức phục hồi hoặc điều chỉnh giới hạn trong tài khoản của chủ dự án. Đổi model không bảo đảm khắc phục quota chung của project.
5. Sau khi sửa biến môi trường, **Redeploy** để deployment mới nhận giá trị. Sau đó dùng nút kiểm tra và nộp một bài mẫu ngắn.
6. Nếu vẫn lỗi, xem Vercel Logs. Các mã an toàn gồm `overloaded`, `quota`, `credentials`, `model`, `timeout`, `invalid_response`; không cần gửi khóa API để chẩn đoán.

Model chính được lưu trong **Admin → Cấu hình AI**. Giá trị này được ưu tiên hơn `GEMINI_MODEL` khi đã cấu hình trong database. Muốn đổi model chính, sửa ở trang admin rồi lưu, không chỉ sửa biến `GEMINI_MODEL`.

Trên local, đặt `GEMINI_API_KEY` và `GEMINI_FALLBACK_MODEL` trong `backend/.env`, khởi động lại backend. Model dự phòng tùy chọn; bỏ trống sẽ chỉ thử lại model chính.

Nếu màn hình đã báo hết thời gian chờ sau khi nộp, kiểm tra **Lịch sử bài làm** trước khi nộp lại vì yêu cầu ở máy chủ có thể đã hoàn tất. Tải lại bằng `/update-app` để nhận bản Flutter mới khi trình duyệt còn giữ bản cũ.

Tài liệu nhà cung cấp: [xử lý lỗi Gemini](https://ai.google.dev/gemini-api/docs/troubleshooting), [định dạng phản hồi và finishReason](https://ai.google.dev/api/generate-content).

## Phân quyền tạo đề và ngôn ngữ

Học viên không còn mục tạo đề trong hồ sơ. Admin vào **Ngân hàng đề → + Đề Nghe / + Đề Đọc**, nhập câu hỏi, đáp án, audio HTTPS cho đề Nghe và chọn **Phát hành** khi sẵn sàng. Đề được lưu trên backend; API tạo/sửa đề chỉ cho phép admin. Lịch sử đề tùy chỉnh cũ trên thiết bị vẫn được giữ.

Dịch văn bản chỉ cho phép `zh` (tiếng Trung) và `vi` (tiếng Việt), được kiểm tra cả ở giao diện và backend.
