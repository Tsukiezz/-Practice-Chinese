# Kiểm định chất lượng đánh giá HanziGo

Điểm từ thuật toán hoặc Gemini là phản hồi hỗ trợ học. Chưa có bộ bài chấm độc lập của giáo viên trong repository để công bố độ chính xác sư phạm. Kiểm thử phần mềm không thay thế kiểm định này.

## Thay đổi cách xử lý kết quả

- Nhận dạng viết tay không đoán chữ theo số nét khi Gemini lỗi. API trả 503 để người học thử lại hoặc tra bàn phím.
- Viết theo pinyin không báo đúng khi nhận dạng lỗi, không dùng điểm nét thay thế kết quả nhận dạng. Giao diện hiện tự đối chiếu và không ghi một lần đạt.
- Đánh giá phát âm cần bản thu âm và đầu ra hợp lệ từ provider. Khi chỉ có transcript hoặc dịch vụ chưa đánh giá được, API trả điểm `null` và `score_eligible=false`.
- So khớp transcript, nếu có, nằm trong `transcript_match_percent`, không được gọi là điểm thanh điệu, âm vị hoặc độ trôi chảy.
- Lần chưa đánh giá không được lưu thành điểm. Dashboard và danh sách bài yếu chỉ tính bản thu có nguồn đánh giá được ghi nhận. Lịch sử cũ không bị xóa hoặc sửa; nếu thiếu thông tin nguồn thì hiển thị chưa xác minh và không dùng cho tổng hợp điểm.
- Pending AI exams chỉ trả trường câu hỏi công khai. Đáp án, lời giải, rubric và thông tin debug giữ trên server đến khi đã nộp. Bộ chấm đối chiếu đáp án ghi `graded_by=automatic`.

## Chuẩn bị dữ liệu giáo viên

1. Chọn bài viết và bản thu từ người học được phép tham gia. Dùng mã ẩn danh, lưu dữ liệu riêng bên ngoài repository công khai.
2. Tách tập hiệu chỉnh và tập kiểm tra theo người học, tránh dùng cùng bài để chọn ngưỡng và công bố kết quả.
3. Đề nghị giáo viên chấm độc lập bằng rubric thống nhất. Nếu có nhiều người chấm, ghi nhận độ đồng thuận và quy tắc lấy điểm tham chiếu trước khi xem điểm hệ thống.
4. Ghi dự đoán gốc của phiên bản ứng dụng/model đã xác định, cùng nguồn và trạng thái đánh giá. Không đưa kết quả dự phòng hoặc chưa đánh giá vào cùng tập đo.
5. Sao chép `assessment-cases.template.jsonl` ra thư mục dữ liệu riêng và điền kết quả thật. `reviewer` là mã người chấm, không phải tên hay email cá nhân. Template để trống nhãn có chủ ý, không phải kết quả đo.

Các trường cần có: `id`, `kind`, `split=test`, `label_source=teacher`, `reviewer`, `prediction_source`, `assessment_status=assessed`. Với điểm số điền `reference_score` và `predicted_score` từ 0 đến 100. Với OCR điền `reference_hanzi` và danh sách `predictions` theo thứ tự.

## Tính báo cáo

```powershell
python backend/tools/evaluate_assessments.py --dataset C:/du-lieu-rieng/cases.jsonl --output outputs/assessment-report.json
```

Với template chưa gán nhãn, kết quả là `awaiting_teacher_labels`, không có chỉ số độ chính xác. Với dữ liệu đã cung cấp nhãn, công cụ tính MAE, RMSE, sai lệch trung bình cho điểm số và top-1/top-3 cho OCR. Công cụ không tự chứng minh giáo viên đã chấm hay dữ liệu đủ đại diện. Khi báo cáo cần kèm số mẫu, cách thu thập, điều kiện thiết bị, phiên bản model/code, tỷ lệ không đánh giá được và các ví dụ lỗi.

## Kiểm thử phần mềm

```powershell
python scripts/run_backend_tests.py
```

Runner dùng database tạm, chặn cấu hình database/AI/email production và không gửi thư thật. Các test provider dùng mock xác định. Kiểm tra browser và Flutter cần được chạy riêng; kết quả test chỉ chứng minh hành vi phần mềm trong phạm vi đã kiểm tra.

## Kết quả kiểm tra bản sửa ngày 23/11/2026

| Kiểm tra | Kết quả |
| --- | --- |
| Backend với SQLite tạm | 217 test đạt |
| Backend với libSQL tạm | 217 test đạt |
| Flutter widget/service | 81 test đạt |
| Flutter analyze và build web | Không có lỗi/cảnh báo chặn build; còn 26 gợi ý về kiểu viết và API deprecated |
| Admin trên Edge desktop/mobile | Đạt đăng nhập, từ vựng, đề thi, điều chỉnh điểm, phúc khảo, tài khoản, cấu hình AI, nhật ký, đăng xuất; không có lỗi JavaScript |
| Giao diện luyện đọc | Không hiện điểm khi thiếu đánh giá âm thanh; giữ đúng điểm 0 và thành phần chưa biết |
| Website hợp nhất trên Edge | Đạt lưu bài học, từ điển/sổ tay, audio, nộp bài nghe, tải lại, đăng xuất, đăng ký OTP và phân quyền |

Các kiểm tra trên dùng dữ liệu tạm và provider giả lập khi cần chấm bài. Chưa dùng bản thu có nhãn giáo viên. Chủ dự án đã xác nhận ngày 23/11/2026 rằng OTP đến email thật; các bài kiểm thử tự động vẫn dùng email giả lập và không gửi thư thật.

## Quản trị an toàn

Ứng dụng không tạo hoặc đặt lại mật khẩu Admin khi khởi động. `python backend/create_admin.py` hoặc `python backend/provision_admin.py` yêu cầu nhập thông tin rõ ràng và không ghi đè tài khoản có sẵn. Tài khoản quản trị còn dùng bộ thông tin đăng nhập cố định đã nghỉ sử dụng bị yêu cầu đặt lại mật khẩu qua email; tài khoản và dữ liệu học được giữ nguyên. Các phiên cũ của tài khoản đó không còn được chấp nhận.
