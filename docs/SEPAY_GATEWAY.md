# HanziGo Premium — SePay Payment Gateway

## Cấu hình production

1. Đổi Secret Key trong SePay vì khóa cũ đã xuất hiện trong source frontend/backend. Xóa khỏi source hiện tại không xóa bản trong lịch sử Git; khóa cũ cần được vô hiệu hóa.
2. Trong Vercel project `hanzigo-chinese-learning`, đặt các biến Production: `SEPAY_MERCHANT_ID`, `SEPAY_SECRET_KEY` (khóa mới), `SEPAY_PUBLIC_URL=https://hanzigo-chinese-learning.vercel.app`. Không nhập merchant secret vào ô API Key của webhook ngân hàng.
3. Triển khai code nhánh `test`: `npx vercel deploy --prod --yes --scope cdcl`. Website chưa có endpoint mới trước khi deployment này hoàn tất.
4. Trong SePay → **Cổng thanh toán → Cấu hình → IPN**, lưu `https://hanzigo-chinese-learning.vercel.app/api/payment/sepay-ipn`, chọn xác thực **SECRET_KEY**, đặt khóa trùng với `SEPAY_SECRET_KEY` của backend. SePay gửi header `X-Secret-Key`.
5. Xác nhận merchant production đã kích hoạt phương thức BANK_TRANSFER và liên kết đúng tài khoản ngân hàng.

Luồng: tạo đơn → link checkout có thời hạn 30 phút → form POST ký HMAC-SHA256/Base64 gửi tới `https://pay.sepay.vn/v1/checkout/init` → SePay nhận thanh toán → IPN xác thực và kiểm tra mã đơn/số tiền/VND/trạng thái → kích hoạt Premium → học viên kiểm tra tài khoản. Đây là mua gói một lần, không tự động trừ tiền gia hạn.

Các return URL `/payment/sepay/return` chỉ hiển thị thông báo; không cấp Premium dựa trên tham số `success` trên trình duyệt. IPN lặp được xử lý idempotent, một transaction không được dùng cho hai đơn. Đơn hết thời gian chờ được giữ để đối chiếu giao dịch đến muộn. Nếu đơn đã được xóa bởi phiên bản cũ, admin phải đối chiếu giao dịch thật trước khi cấp thủ công.

Flutter Web trên điện thoại/máy tính mở link checkout. Bản native hiện sao chép link để mở trong trình duyệt; trở lại ứng dụng và tải lại tài khoản để cập nhật Premium. Trang HTML `/account` chuyển thẳng sang checkout.

Webhook ngân hàng cũ `/api/payment/sepay-webhook` là luồng khác. Nó bắt buộc xác thực và không xử lý đơn `sepay_pg`. Giữ cấu hình API key của webhook ngân hàng riêng nếu vẫn dùng luồng QR trực tiếp; khóa này không phải merchant secret.

## Kiểm tra

```powershell
python -m unittest discover -s backend -p test_sepay_gateway.py -v
```

Kiểm thử dùng SQLite trong bộ nhớ và khóa giả; không thực hiện giao dịch thật, không cấp Premium trên database production. Đã kiểm tra sai/mất khóa, số tiền sai, NaN, currency sai, trạng thái thất bại, IPN lặp, giao dịch dùng lại và thanh toán đến muộn.

Sau triển khai: đăng nhập học viên → chọn gói → tạo đơn → mở SePay. Kiểm tra merchant, số tiền và mã đơn; sau giao dịch thật được chủ tài khoản thực hiện, xem log IPN trên SePay và trạng thái Premium. Không tự gửi IPN giả vào production để xác nhận thanh toán.

Tài liệu chính thức: [Bắt đầu nhanh](https://developer.sepay.vn/vi/cong-thanh-toan/bat-dau), [IPN](https://developer.sepay.vn/en/cong-thanh-toan/IPN), [SDK ký checkout](https://github.com/sepayvn/sepay-pg-node/blob/main/src/checkout.ts).
