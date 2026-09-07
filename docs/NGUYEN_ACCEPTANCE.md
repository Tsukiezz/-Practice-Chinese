# Đối chiếu phần Nguyên — 07/09/2026

Nguồn: `HanziGo_Bang_Theo_Doi_Chuc_Nang_Chi_Tiet.xlsx`, sheet **Phân rã chức năng**, lọc cột người phụ trách bằng **Nguyên**: 23 đầu việc thuộc chức năng 28 và 31–35. Sheet tổng hợp ghi Hoàn thành nhưng sheet chi tiết ghi Chưa xong; bảng này ghi bằng chứng triển khai, không suy diễn trạng thái từ một sheet. Không sửa file Excel gốc.

## Bằng chứng theo từng đầu việc

| Mã | Phạm vi được giao | Triển khai / kiểm chứng |
|---|---|---|
| F28.1 | Thống kê tổng quan | Dashboard đếm người dùng, từ, đề, kết quả, điểm trung bình, lượt AI thành công/lỗi. |
| F28.2 | Chỉ Admin xem báo cáo | `admin_user`, kiểm thử khách 401 và học viên 403. |
| F28.3 | Số liệu thực | SQL trên SQLite; test seed không tạo hoạt động/điểm giả. |
| F31.1 | Danh sách tài khoản | API chỉ trả thông tin công khai; UI có tải, rỗng, lỗi và thử lại. |
| F31.2 | Tìm kiếm/lọc | Tên/email, vai trò, trạng thái; test API và trình duyệt. |
| F31.3 | Khóa/mở, đổi quyền | Thu hồi phiên khi khóa/đổi quyền; giữ Admin hoạt động và không tự hạ quyền. |
| F31.4 | Bảo vệ Admin | Mọi dữ liệu `/api/admin/*` kiểm tra quyền phía máy chủ; shell chỉ hiện đăng nhập trước xác thực. |
| F31.5 | Audit tài khoản | Ghi trước/sau, người sửa, thời gian; không ghi hash/salt/token. Thêm version và lỗi 409 khi lưu dữ liệu cũ. |
| F32.1 | CRUD từ | Chữ Hán, Pinyin, nghĩa, ví dụ, audio HTTPS; lưu dữ liệu thật. |
| F32.2 | HSK/nét chuẩn | HSK 1–6; canvas chuột/cảm ứng, thứ tự nét, chuẩn tọa độ 0–1024. |
| F32.3 | Ràng buộc dữ liệu | Chặn trùng chữ, nét không hợp lệ, xóa từ đang nằm trong đề; có kiểm thử. |
| F33.1 | Đề HSK 1–6 | Tạo/sửa/lọc đề, thời lượng và trạng thái; kiểm tra input phía máy chủ. |
| F33.2 | Nghe/Đọc/Viết | Nghe yêu cầu audio; lưu câu hỏi, lựa chọn, đáp án/rubric, giải thích, transcript. |
| F33.3 | Sửa/ẩn/xóa đề | Version 409, không xóa đề có kết quả, học viên chỉ thấy đề published. |
| F33.4 | Hợp đồng tích hợp | `ADMIN_HANDOFF.md`, OpenAPI `/docs`; endpoint học viên loại đáp án và lưu snapshot khi nộp. Đã kiểm thử API; chưa thay cho review trực tiếp với Kiệt/Trung. |
| F34.1 | Cấu hình AI | Model, prompt, temperature, max_tokens, bật/tắt và version. |
| F34.2 | Giữ khóa trên server | Chỉ đọc `AI_API_KEY`, UI chỉ nhận boolean; test không rò khóa qua lỗi/audit. |
| F34.3 | Trạng thái/lỗi | Nút test Gemini qua API Admin; timeout, tối đa một lần retry lỗi mạng/429/5xx; kiểm tra output. Test dùng HTTP transport giả lập, chưa gọi Gemini thật. |
| F34.4 | Chuẩn request/response | Adapter mặc định trong `ai_provider.py`; dịch vụ nhận user từ phiên, trả kết quả thật score 0–100/feedback và ghi usage. Có thể truyền adapter tin cậy từ module Trung. |
| F35.1 | Xem bài AI/thi | Danh sách kết quả có kind, content, feedback, điểm gốc/hiện tại và lịch sử. |
| F35.2 | Phúc khảo có lý do | `/review` cho học viên; Admin xử lý tại Duyệt kết quả → Yêu cầu phúc khảo. Có thể giữ điểm hoặc sửa, bắt buộc phản hồi. |
| F35.3 | Đồng bộ kết quả | Transaction cập nhật điểm, lịch sử, trạng thái yêu cầu, phản hồi và audit; dashboard học viên đọc điểm mới. |
| F35.4 | Lịch sử | Điểm trước/sau, lý do, Admin và thời gian; version bảo vệ cả yêu cầu lẫn kết quả. |

## Cách chạy và kiểm tra

Từ thư mục `backend`, chạy:

```powershell
.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8010
```

- Máy tính: `http://localhost:8010/admin`; có nút xem giao diện điện thoại.
- Điện thoại cùng Wi-Fi: `http://<IPv4-máy-tính>:8010/admin`. Menu ☰ giữ các chức năng trong nhóm gọn.
- Học viên: `/review`, đăng nhập tài khoản đã có kết quả; gửi lý do, đợi Admin xử lý, bấm Tải lại để thấy phản hồi/điểm mới.
- Tạo tài khoản Admin bằng `backend/create_admin.py`; không có mật khẩu mặc định trong Git.
- API/Swagger: `/docs`. Dữ liệu mới tạo được lưu trong SQLite, không dùng số liệu giả ở dashboard.

19 bài kiểm thử API trong `test_admin.py`: phân quyền, session, dữ liệu, xung đột, phúc khảo, adapter AI, migration lặp lại. `smoke_browser.py` kiểm thử cả gửi phúc khảo bằng học viên và duyệt bằng Admin ở 320px, ngoài bộ kiểm thử desktop/390px/phone preview hiện có. Các bài kiểm thử dùng DB tạm, không sửa dữ liệu cá nhân.

## AI và giới hạn tích hợp

Adapter mặc định sử dụng Gemini REST, endpoint cố định HTTPS, khóa trong header, không theo redirect. Model do Admin nhập theo model được cấp cho khóa; không tự chọn model trả phí. Cấu hình `AI_API_KEY` trong môi trường server rồi lưu model/prompt và bật AI. Nút kiểm tra gửi một bài mẫu ngắn và có thể phát sinh phí nhà cung cấp; không tạo điểm học viên. Trạng thái ready chỉ cho biết đủ cấu hình, không đồng nghĩa kết nối đã được xác minh.

Tham khảo giao thức [Gemini structured output](https://ai.google.dev/gemini-api/docs/generate-content/structured-output). Test mô phỏng các phản hồi HTTP thành công/lỗi, không dùng khóa thật. Cần khóa hợp lệ để xác minh kết nối và chất lượng chấm thực tế.

Hàm `grade_with_ai(user_id, kind, content)` có adapter mặc định cho nội dung văn bản. Nhận dạng ảnh/nét viết và xây dựng ngữ cảnh/rubric từ bài học vẫn thuộc module Trung; chấm Writing trong đề cần module đó. Không tuyên bố OCR/chấm ảnh đã hoàn thành. Module thi tính giờ và Flutter học viên thuộc các thành viên khác. Admin responsive và trang phúc khảo chạy web mobile; không phải màn hình Admin native Flutter.

## Dữ liệu và Git

`init_db()` tự thêm cột users.version vào DB cũ, tạo bảng appeals và unique index chống hai yêu cầu pending cho cùng bài. Migration có thể chạy lại, giữ tài khoản/phiên/kết quả cũ. Sau cập nhật phải khởi động lại backend.

Chỉ đưa source, test và tài liệu lên nhánh **nguyen**. Không đưa SQLite, `.env`, mật khẩu, venv hay ảnh kiểm thử lên Git. Không push hoặc merge main. Việc phối hợp/review PR của các thành viên khác cần thực hiện khi có code tương ứng; không đánh dấu đã review thay người thật.
