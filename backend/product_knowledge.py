"""Canonical release knowledge shared by live AI prompts and offline answers."""
from premium_service import PLAN_PRICES, COMPARISON_FEATURES
import re


def local_product_answer(normalized):
    lines = product_knowledge().splitlines()
    groups = [
        (r'sepay|thanh toan|chuyen khoan', ('- Thanh toán:', '- Nếu chuyển tiền', '- Trợ lý')),
        (r'hsk\s*[789]', ('- Bài học:', '- Nghe và Đọc:', '- Luyện đọc phát âm:', '- Kiểm tra:')),
        (r'dong ho|gio viet nam|loi chao', ('- Đồng hồ và lời chào:',)),
        (r'bao luu|streak|chuoi ngay', ('- Chuỗi ngày học:', '- Streak Freeze:')),
        (r'but long|but muc|thu phap', ('- Bút:',)),
        (r'mau giao dien|mau sac', ('- Màu:',)),
    ]
    prefixes = next((prefix for pattern, prefix in groups if re.search(pattern, normalized)), None)
    if prefixes:
        return '\n\n'.join(line[2:] for line in lines if line.startswith(prefixes))
    return 'Quyền lợi HanziGo hiện tại:\n' + '\n'.join(lines[1:8]) + '\nBạn có thể xem gói tại Cá nhân → HanziGo Premium.'


def product_knowledge():
    comparisons = '\n'.join(f"- {f['feature']}: miễn phí {f['free']}; Premium {f['premium']}." for f in COMPARISON_FEATURES)
    return f'''THÔNG TIN SẢN PHẨM HANZIGO HIỆN HÀNH (ưu tiên hơn mô tả cũ):
{comparisons}
- Giá gói 1 tháng: {PLAN_PRICES['1_month']['price']:,} VNĐ, 30 ngày; 1 năm: {PLAN_PRICES['1_year']['price']:,} VNĐ, 365 ngày. Gia hạn nối tiếp hạn còn lại.
- AI tạo đề: miễn phí 3 đề/ngày theo giờ Việt Nam UTC+7; đề mẫu không tính lượt, xóa đề không trả lượt. Premium không giới hạn số đề, mỗi đề 1–50 câu; lỗi AI vẫn có thể xảy ra.
- Bài học: 48 bài bổ trợ HSK 1–6; Premium thêm 2 bài/cấp HSK 7, 8, 9 và 1 bài giao tiếp thương lượng. Có từ vựng, mẫu câu, đoạn đọc, 4 câu hỏi và tiến độ riêng theo tài khoản.
- Nghe và Đọc: chọn HSK 7/8/9 có nhãn Premium; mỗi cấp có 2 bài nghe và 2 bài đọc, mỗi bài 2 câu hỏi. Nghe dùng giọng đọc tổng hợp. Bài HSK nâng cao do HanziGo biên soạn, không phải bộ đề chính thức hay giáo trình đầy đủ. Kỳ thi chính thức HSK 7–9 là kỳ thi chung; các nhãn 7/8/9 ở đây là lộ trình luyện tập tăng độ khó của app.
- Luyện đọc phát âm: trang /reading dùng chung giao diện nghe mẫu, thu âm micro, AI chấm và lịch sử cho HSK 1–9. HSK 7–9 cần Premium còn hạn, mỗi cấp hiện có 6 từ và 2 câu ví dụ bổ trợ; chưa phải toàn bộ từ vựng HSK. Chọn cấp trong app được giữ khi mở trang luyện phát âm.
- Đồng hồ và lời chào: trang chủ hiện giờ Việt Nam UTC+7 và tên người dùng. Từ 06:00 đến trước 18:00 chào buổi sáng; từ 18:00 đến trước 06:00 chào buổi tối.
- Kiểm tra: có nút Kiểm tra HSK 7/8/9 · Premium, bộ luyện 8 câu Nghe + Đọc, 20 phút, tự chấm và lưu kết quả. AI tạo đề cho phép chọn HSK 7–9 khi Premium còn hạn; nếu AI lỗi sẽ báo thử lại, không thay bằng câu HSK thấp hơn.
- Bút: ngay trên khung luyện viết có Mặc định / Bút lông / Bút mực / Thư pháp. Ba kiểu sau cần Premium; lựa chọn lưu theo tài khoản.
- Màu: Cá nhân → Màu giao diện, Premium chọn toàn bộ bảng màu. Tài khoản miễn phí vẫn có sáng/tối mặc định. Hết hạn Premium trở về cọ và màu mặc định; huy hiệu vàng cũng hết hiệu lực.
- Chuỗi ngày học: Cá nhân chỉ hiện mục gọn Chuỗi ngày học & bảo lưu, bấm mới mở chi tiết. Ngọn lửa và số chuỗi nằm cạnh nút sáng/tối trên thanh trên cùng, bấm cũng mở chi tiết; số lấy từ máy chủ. Trang chi tiết có chuỗi hiện tại, kỷ lục, tổng ngày đã học, mốc tiếp theo và lịch 28 ngày theo UTC+7. Lịch phân biệt đã học, bảo lưu và chưa học. Mở Cá nhân không tính là học; kết quả luyện tập, tiến độ bài học, đọc và tra từ mới ghi nhận hoạt động. Ngày bảo lưu giữ chuỗi nhưng không tăng tổng ngày thực học. Nút cập nhật tải lại dữ liệu từ máy chủ; trợ lý không được tự ghi nhận ngày học.
- Streak Freeze: tự bảo lưu ngày bỏ lỡ cho chuỗi học đang có, tối đa 3 ngày mỗi tháng lịch UTC+7, không cộng dồn. Xử lý khi tải thống kê học tập; không tạo ngày học giả và không phục hồi khoảng trống trước khi bật quyền bảo lưu. Gói năm cũng nhận hạn mức 3/tháng, không phải 12 lượt một lần.
- Thanh toán: SePay xác nhận ở máy chủ bằng giao dịch/đơn hợp lệ rồi mới cấp đúng gói của đơn (có thể có voucher). Trang chờ kiểm tra mỗi 5 giây khi còn mở; webhook có thể xử lý khi đã đóng trang. Chu kỳ 5 giây không phải cam kết tiền được ngân hàng xác nhận trong 5 giây.
- Nếu chuyển tiền nhưng chưa có Premium: không yêu cầu thanh toán lại; kiểm tra đúng tài khoản đăng nhập, mã đơn, nội dung chuyển khoản, rồi chuyển Admin kiểm tra. Không yêu cầu mật khẩu, OTP hoặc khóa API. Không cấp gói chỉ từ ảnh biên lai hoặc tham số result=success.
- Trợ lý không có quyền tự xác nhận tiền, thay đổi gói hay khẳng định trạng thái tài khoản nếu chưa có dữ liệu xác thực. Hỗ trợ các câu hỏi Premium, SePay, voucher, màu, cọ, bảo lưu và nội dung nâng cao là đúng phạm vi HanziGo.
'''
