# Chat học viên, khách và quản trị viên

Website hiển thị nút **Hỏi HanziGo** ở góc dưới bên phải, kể cả trước khi đăng nhập. Nhấn để mở/đóng chat; nội dung tiếp tục được lưu trên database. Phiên khách được nhận diện bằng cookie HttpOnly cùng website, còn học viên dùng phiên đăng nhập hiện tại, kể cả khi không chọn ghi nhớ đăng nhập. Lịch sử khách và tài khoản được tách riêng; xóa cookie sẽ mất quyền truy cập lịch sử khách trên thiết bị đó.

AI sử dụng cấu hình Gemini hiện có trên máy chủ và 16 tin nhắn gần nhất để hiểu câu hỏi tiếp nối. Chủ đề tiếng Trung được hướng dẫn với chữ Hán, pinyin, ví dụ và bài tập. Chủ đề khác vẫn được AI thử giải đáp trước khi thêm đúng câu: **Đợi một chút, quản trị viên sẽ liên lạc lại ngay**. Các yêu cầu cần người thật, AI không chắc chắn hoặc lỗi dịch vụ cũng chuyển vào hàng chờ quản trị viên. Đây là thông báo tiếp nhận, không có cơ chế bảo đảm thời gian phản hồi của con người.

Trong Admin → **Hệ thống & Trí tuệ AI → Hộp thư hỗ trợ**:

- Tìm tên học viên/khách; lọc tất cả, chờ quản trị viên, đang hỗ trợ hoặc AI hỗ trợ; danh sách phân trang 40 hội thoại.
- Chọn hội thoại để đọc lịch sử, phân biệt người dùng, AI và quản trị viên bằng nhãn và màu. Admin mở 50 tin mới nhất; **Xem tin nhắn cũ hơn** tải tiếp 50 tin/lần, không giới hạn tổng lịch sử. Chat học viên đọc theo lô 100 tin.
- **Tiếp nhận** tạm dừng AI; gửi trả lời cũng tự tiếp nhận. **Giao lại cho AI** bật lại AI cho tin nhắn tiếp theo.
- Giao diện đang mở tự cập nhật mỗi 4 giây, giữ vị trí cuộn, bản nháp theo hội thoại và các dòng không thay đổi. Khi đang đọc tin cũ, nút **Có tin nhắn mới** giúp chuyển xuống cuối. Ctrl/Cmd + Enter gửi phản hồi. Trên điện thoại, nút **Danh sách** chuyển giữa danh sách và nội dung.

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

## Cấu hình AI và nhật ký quản trị

Trang AI hiển thị tình trạng cấu hình, model dự phòng, số lượt thành công/lỗi 24 giờ và 8 hoạt động AI đã được ghi nhận gần nhất. Lưu cấu hình tại chỗ; đánh dấu thay đổi chưa lưu; chỉ kiểm tra Gemini bằng cấu hình đã lưu và hiển thị thời gian chờ/kết quả riêng. Lỗi lưu giữ lại nội dung đã nhập. Số liệu hoạt động dựa trên bảng `ai_usage`, không phải thống kê đầy đủ mọi lượt chat khách.

Nhật ký hỗ trợ tìm theo tên/email/mã/nội dung, lọc thao tác, đối tượng, người thực hiện và khoảng ngày; có tổng số và 25/50/100 dòng mỗi trang. **Xem đầy đủ** hiển thị tác giả, thời gian, đối tượng, mọi trường trước/sau, đánh dấu trường thay đổi và cho mở dữ liệu gốc. Phân trang đi được đến hết lịch sử. Tiếp nhận/giao lại AI, trả lời chat và kết quả kiểm tra kết nối AI được ghi thêm vào nhật ký; gửi lại cùng request ID không ghi trùng.

API `GET /api/admin/audit-logs?paginated=true` trả `items,total,offset,limit,actions,entities,actors`; không truyền `paginated` vẫn giữ hợp đồng danh sách cũ. `from_ts` bao gồm thời điểm bắt đầu, `to_ts` không bao gồm thời điểm kết thúc.

Kiểm tra bổ sung: `python -m unittest -v test_admin_system`, `python smoke_admin_system.py`. Kịch bản trình duyệt dùng dữ liệu tạm, kiểm tra tải tin cũ, giữ bản nháp/cuộn, nhật ký đầy đủ và cả ba trang ở 390px/1440px.
