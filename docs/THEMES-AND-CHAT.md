# Giao diện và trợ lý HanziGo

Trong Cá nhân hoặc Thông tin cá nhân, chọn một trong sáu màu: tím pastel, đỏ đậm, xanh dương, vàng pastel, cam, tối hiện tại. Công tắc Dark mode bật màu đã chọn; tắt trở về giao diện sáng. Lựa chọn được lưu trên trình duyệt/thiết bị. Trang đăng nhập giữ giao diện mặc định.

Màu chữ, thẻ, ô nhập, hộp thoại và điều hướng dùng các vai trò màu của ColorScheme. Các trang web hồ sơ, bài thi, luyện đọc và phúc khảo đọc cùng tùy chọn. `test/theme_preferences_test.dart` kiểm tra độ tương phản tối thiểu 4,5:1 cho nội dung chính và hành vi lưu/chuyển màu.

Chatbot giải đáp tiếng Trung và cách dùng ứng dụng, trả lời các ý trước khi chuyển tiếp. Nội dung ngoài phạm vi hoặc yêu cầu gặp quản trị viên được lưu vào hội thoại chờ quản trị. Trong lúc chờ, AI vẫn trả lời; khi quản trị nhận hội thoại thì quyền trả lời thuộc quản trị cho đến khi chuyển lại AI.

Biến môi trường phía máy chủ `GEMINI_FALLBACK_API_KEYS` chứa khóa Gemini dự phòng (phân cách bằng dấu phẩy nếu nhiều khóa). Không đưa khóa vào mã nguồn, Flutter, JavaScript hay dữ liệu trả về trình duyệt. Adapter thử khóa dự phòng khi khóa chính bị lỗi xác thực, quyền truy cập hoặc 429; giữ tối đa ba lần thử và thời hạn xử lý hiện có. Khóa dự phòng không đảm bảo giảm độ trễ hoặc tăng hạn mức nếu dùng chung một dự án Google.
