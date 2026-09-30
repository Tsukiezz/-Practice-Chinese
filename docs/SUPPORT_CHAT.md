# Chat học viên, khách và quản trị viên

Website hiển thị nút **Hỏi HanziGo** ở góc dưới bên phải, kể cả trước khi đăng nhập. Nhấn để mở/đóng chat; nội dung tiếp tục được lưu trên database. Phiên khách được nhận diện bằng cookie HttpOnly cùng website, còn học viên dùng phiên đăng nhập hiện tại, kể cả khi không chọn ghi nhớ đăng nhập. Lịch sử khách và tài khoản được tách riêng; xóa cookie sẽ mất quyền truy cập lịch sử khách trên thiết bị đó.

AI sử dụng cấu hình Gemini hiện có trên máy chủ và 16 tin nhắn gần nhất để hiểu câu hỏi tiếp nối. Chủ đề tiếng Trung được hướng dẫn với chữ Hán, pinyin, ví dụ và bài tập. Chủ đề khác vẫn được AI thử giải đáp trước khi thêm đúng câu: **Đợi một chút, quản trị viên sẽ liên lạc lại ngay**. Các yêu cầu cần người thật, AI không chắc chắn hoặc lỗi dịch vụ cũng chuyển vào hàng chờ quản trị viên. Đây là thông báo tiếp nhận, không có cơ chế bảo đảm thời gian phản hồi của con người.

Trong Admin → **Hệ thống & Trí tuệ AI → Hộp thư hỗ trợ**:

- Tìm tên học viên/khách; lọc tất cả, chờ quản trị viên, đang hỗ trợ hoặc AI hỗ trợ; danh sách phân trang 40 hội thoại.
- Chọn hội thoại để đọc toàn bộ lịch sử, phân biệt người dùng, AI và quản trị viên. Lịch sử được đọc theo lô 100 tin nhắn.
- **Tiếp nhận** tạm dừng AI; gửi trả lời cũng tự tiếp nhận. **Giao lại cho AI** bật lại AI cho tin nhắn tiếp theo.
- Giao diện đang mở tự cập nhật mỗi 4 giây. Tin trả lời của quản trị viên hiển thị trong chat của khách/học viên.

Backend tự tạo hai bảng mới `chat_threads`, `chat_messages` cùng index khi khởi động, trên SQLite local hoặc Turso/Vercel. Migration chỉ bổ sung bảng, không thay đổi dữ liệu học tập. API kiểm tra quyền sở hữu ở mọi endpoint chat; chỉ admin được xem hộp thư chung. Tin nhắn tối đa 3.000 ký tự, giới hạn 6 tin/phút/hội thoại và 20 phiên khách mới/giờ/địa chỉ nguồn. Request ID chống gửi trùng khi thử lại; AI không ghi câu trả lời trễ nếu quản trị viên đã tiếp nhận.

Kiểm thử từ `backend/`:

```powershell
python -m unittest -v test_support_chat
$env:HANZIGO_DB_DRIVER = 'libsql'
python -m unittest -v test_support_chat
Remove-Item Env:HANZIGO_DB_DRIVER
$env:PLAYWRIGHT_CHANNEL = 'msedge'
python smoke_support_chat.py
```

Kiểm thử trình duyệt dùng database tạm và AI giả lập xác định; ảnh lưu trong `test-results/`. Cần kiểm tra Gemini thật trên deployment sau khi build. Không lưu khóa AI hoặc token tài khoản vào mã nguồn.
