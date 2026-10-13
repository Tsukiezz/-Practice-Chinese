# Chat học viên, khách và quản trị viên

Website hiển thị biểu tượng **💬 Hỏi HanziGo** ở góc dưới bên phải, kể cả trước khi đăng nhập. Biểu tượng chỉ mở hộp chat; bên trong, người dùng nhấn **Tôi cần hỗ trợ** để bắt đầu phiên và hiện ô nhập. Phiên khách được nhận diện bằng cookie HttpOnly cùng website, học viên dùng phiên đăng nhập hiện tại. Hết 5 phút kể từ trao đổi cuối cùng, phiên kết thúc: tin nhắn, bản nháp và tệp đang chọn được gỡ khỏi giao diện người dùng; nút **Tôi cần hỗ trợ** lại hiện bên trong hộp. Admin vẫn giữ toàn bộ lịch sử và tệp đã gửi. Backend chặn việc đọc lại tin/tệp cũ ngay cả khi người dùng sửa URL hay mở phiên mới.

AI dùng Gemini qua API, hướng dẫn hệ thống và tối đa 16 tin nhắn của **phiên đang mở** để hiểu câu hỏi tiếp nối; không dùng lịch sử phiên trước và không tự huấn luyện lại mô hình. Phạm vi hiện tại là tiếng Trung và HanziGo; chủ đề ngoài phạm vi hoặc yêu cầu người thật được chuyển quản trị viên. Dữ liệu sản phẩm được bổ sung từ backend. Khi dịch vụ AI lỗi, hệ thống dùng câu trả lời dự phòng và chuyển tiếp. Thông báo tiếp nhận không bảo đảm thời gian phản hồi của quản trị viên.

## Cập nhật tiến độ AI hỗ trợ — 13/10/2026

- Đã khôi phục biểu tượng chat ngoài trang; nút bắt đầu phiên nằm trong hộp chat.
- Đã sửa bản nháp: nhấn Gửi xóa ngay phần vừa gửi, giữ nội dung người dùng gõ tiếp trong lúc AI trả lời. Lỗi mạng có nút **Gửi lại tin trước**, dùng lại request ID để tránh ghi trùng.
- Có trạng thái thực tế khi chuẩn bị tệp, gửi yêu cầu, chờ AI và chuyển quản trị viên; không hiển thị phần trăm xử lý giả lập.
- Người dùng và admin gửi được một tệp mỗi tin: PNG, JPG/JPEG, WEBP, PDF, DOCX hoặc TXT; tối đa 2 MB/tệp và 20 MB/hội thoại trong 24 giờ. Có thể gửi tệp không kèm chữ.
- Tệp lưu bền vững trong database, không dùng ổ đĩa tạm Vercel. API chỉ trả metadata khi đọc hội thoại; tải nội dung tệp phải kiểm tra quyền. Tin nhắn hết phiên không còn tải được từ phía người dùng, admin vẫn tải được trong lịch sử.
- AI hiện trả lời phần văn bản người dùng nhập. Tệp được chuyển cho admin kiểm tra; **chưa có phân tích nội dung ảnh/PDF/Word tự động bằng AI**.
- Kiểm tra: 19 bài backend trên SQLite và libSQL; trình duyệt kiểm tra nút bắt đầu bên trong, gửi tin chậm, giữ bản nháp mới, đính kèm, hết phiên và lịch sử admin. Script: `scripts/test_support_widget_sessions.py`.

Trong Admin → **Hệ thống & Trí tuệ AI → Hộp thư hỗ trợ**:

- Tìm tên học viên/khách; lọc tất cả, chờ quản trị viên, đang hỗ trợ, AI hỗ trợ hoặc đã kết thúc; danh sách phân trang 40 hội thoại.
- Chọn hội thoại để đọc lịch sử, phân biệt người dùng, AI và quản trị viên bằng nhãn và màu. Admin mở 50 tin mới nhất; **Xem tin nhắn cũ hơn** tải tiếp 50 tin/lần, không giới hạn tổng lịch sử. Chat học viên đọc theo lô 100 tin.
- **Tiếp nhận** tạm dừng AI; gửi trả lời cũng tự tiếp nhận. **Giao lại cho AI** bật lại AI cho tin nhắn tiếp theo.
- Giao diện đang mở tự cập nhật mỗi 4 giây, giữ vị trí cuộn, bản nháp theo hội thoại và các dòng không thay đổi. Khi đang đọc tin cũ, nút **Có tin nhắn mới** giúp chuyển xuống cuối. Ctrl/Cmd + Enter gửi phản hồi. Trên điện thoại, nút **Danh sách** chuyển giữa danh sách và nội dung.

Backend tự tạo các bảng `chat_threads`, `chat_messages`, `chat_sessions`, `chat_attachments` cùng index khi khởi động, trên SQLite local hoặc Turso/Vercel. Migration chỉ bổ sung bảng, không thay đổi dữ liệu học tập. API kiểm tra quyền sở hữu ở mọi endpoint chat; chỉ admin được xem hộp thư chung. Tin nhắn tối đa 3.000 ký tự, giới hạn 6 tin/phút/hội thoại và 20 khách mới/giờ/địa chỉ nguồn. Request ID chống gửi trùng khi thử lại; AI không ghi câu trả lời trễ nếu quản trị viên đã tiếp nhận hoặc phiên đã thay đổi.

Kiểm thử từ `backend/`:

```powershell
python -m unittest -v test_support_chat
$env:HANZIGO_DB_DRIVER = 'libsql'
python -m unittest -v test_support_chat
Remove-Item Env:HANZIGO_DB_DRIVER
Set-Location ..
backend/.venv/Scripts/python.exe scripts/test_support_widget_sessions.py
```

Kiểm thử trình duyệt dùng database tạm và AI giả lập xác định; ảnh lưu trong `test-results/`. Cần kiểm tra Gemini thật trên deployment sau khi build. Không lưu khóa AI hoặc token tài khoản vào mã nguồn.

## Cấu hình AI và nhật ký quản trị

Trang AI hiển thị tình trạng cấu hình, model dự phòng, số lượt thành công/lỗi 24 giờ và 8 hoạt động AI đã được ghi nhận gần nhất. Lưu cấu hình tại chỗ; đánh dấu thay đổi chưa lưu; chỉ kiểm tra Gemini bằng cấu hình đã lưu và hiển thị thời gian chờ/kết quả riêng. Lỗi lưu giữ lại nội dung đã nhập. Số liệu hoạt động dựa trên bảng `ai_usage`, không phải thống kê đầy đủ mọi lượt chat khách.

Nhật ký hỗ trợ tìm theo tên/email/mã/nội dung, lọc thao tác, đối tượng, người thực hiện và khoảng ngày; có tổng số và 25/50/100 dòng mỗi trang. **Xem đầy đủ** hiển thị tác giả, thời gian, đối tượng, mọi trường trước/sau, đánh dấu trường thay đổi và cho mở dữ liệu gốc. Phân trang đi được đến hết lịch sử. Tiếp nhận/giao lại AI, trả lời chat và kết quả kiểm tra kết nối AI được ghi thêm vào nhật ký; gửi lại cùng request ID không ghi trùng.

API `GET /api/admin/audit-logs?paginated=true` trả `items,total,offset,limit,actions,entities,actors`; không truyền `paginated` vẫn giữ hợp đồng danh sách cũ. `from_ts` bao gồm thời điểm bắt đầu, `to_ts` không bao gồm thời điểm kết thúc.

Kiểm tra bổ sung: `python -m unittest -v test_admin_system`, `python smoke_admin_system.py`. Kịch bản trình duyệt dùng dữ liệu tạm, kiểm tra tải tin cũ, giữ bản nháp/cuộn, nhật ký đầy đủ và cả ba trang ở 390px/1440px.
