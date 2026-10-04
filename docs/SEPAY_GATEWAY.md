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

Webhook ngân hàng `/api/payment/sepay-webhook` bắt buộc xác thực bằng API key riêng, tiền vào đúng tài khoản, mã đơn và đủ số tiền. Nó hỗ trợ cả đơn `sepay_pg` khi người dùng thanh toán QR trực tiếp. Nếu nhận payload IPN tại URL này, backend kiểm tra `X-Secret-Key` bằng merchant secret và xử lý như `/api/payment/sepay-ipn`.

Nếu IPN bị chậm hoặc thất lạc, backend gọi `GET https://pgapi.sepay.vn/v1/order/detail/{order_invoice_number}` bằng Basic Auth. API live nhận invoice HZG, không phải `order_id` PAY. Đơn chuyển khoản có thể CAPTURED nhưng `transactions=[]`; chỉ phản hồi API server-to-server được xác thực, có đúng invoice, ID SePay, VND và số tiền đơn mới được dùng để cấp gói trong transaction database. IPN vẫn kiểm tra chữ ký/secret và giao dịch như trước; tham số trình duyệt `result=success` không cấp quyền.

Trang trả về và hộp thanh toán kiểm tra mỗi 5 giây khi đang mở (có thể trễ khi mạng chậm/tab bị trình duyệt tạm dừng); backend giới hạn truy vấn mỗi 5 giây/đơn/instance. Khi đóng trang, webhook/IPN tiếp tục cấp gói khi SePay gửi thông báo; không có tiến trình Vercel chạy nền vô hạn. Không lọc ngân hàng gửi: tiền phải được SePay ghi nhận vào đúng tài khoản nhận và đúng đơn. Chuyển khoản không có mã đơn không thể xác định an toàn người mua chỉ từ số tiền.

Tải lại tài khoản đối soát đơn gateway chưa hoàn tất mới nhất, kể cả đơn hết thời gian chờ. `/account` dùng được phiên Flutter; nếu phiên hết hạn, trang có liên kết đăng nhập lại. Gói 1_month cấp 30 ngày, 1_year cấp 365 ngày, nối tiếp hạn Premium còn lại; giá thanh toán lấy từ đơn đã áp dụng voucher.

Khôi phục có kiểm chứng một đơn: `python backend/tools/reconcile_sepay_order.py HZGxxxxxx` để xem, thêm `--apply` để gọi API SePay và đối soát. Không tự cấp gói nếu API không xác nhận. Công cụ dùng cấu hình database production trong `.vercel/.env.production.local` và merchant credentials phía backend, không in secret.

## Kiểm tra

```powershell
python -m unittest discover -s backend -p test_sepay_gateway.py -v
```

Kiểm thử dùng SQLite trong bộ nhớ và khóa giả; không thực hiện giao dịch thật, không cấp Premium trên database production. Đã kiểm tra sai/mất khóa, số tiền sai, NaN, currency sai, trạng thái thất bại, IPN lặp, giao dịch dùng lại và thanh toán đến muộn.

Sau triển khai: đăng nhập học viên → chọn gói → tạo đơn → mở SePay. Kiểm tra merchant, số tiền và mã đơn; sau giao dịch thật được chủ tài khoản thực hiện, xem log IPN trên SePay và trạng thái Premium. Không tự gửi IPN giả vào production để xác nhận thanh toán.

Tài liệu chính thức: [Bắt đầu nhanh](https://developer.sepay.vn/vi/cong-thanh-toan/bat-dau), [IPN](https://developer.sepay.vn/en/cong-thanh-toan/IPN), [SDK ký checkout](https://github.com/sepayvn/sepay-pg-node/blob/main/src/checkout.ts).
