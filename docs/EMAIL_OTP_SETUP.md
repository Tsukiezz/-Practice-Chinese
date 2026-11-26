# Gửi email OTP trên production

Đăng ký và quên mật khẩu dùng chung `backend/email_service.py`. Chỉ mã được nhà cung cấp chấp nhận gửi mới có hiệu lực. Nếu gửi thất bại, API trả 503, mã mới không được kích hoạt và mã đã gửi thành công trước đó vẫn còn hiệu lực đến khi hết hạn hoặc được sử dụng.

## Brevo REST API

Cấu hình các biến sau cho môi trường Production của project Vercel:

```text
BREVO_API_KEY=<khóa API Brevo dành cho tích hợp này>
SMTP_FROM=HanziGo <địa chỉ người gửi đã được Brevo xác minh>
```

Khóa `BREVO_API_KEY` được dùng riêng cho HTTPS API. Nó được ưu tiên ngay cả khi có `SMTP_PASSWORD`; hệ thống không dùng mật khẩu SMTP làm header `api-key`. Cấu hình cũ đặt khóa bắt đầu bằng `xkeysib-` trong `SMTP_PASSWORD` vẫn được nhận dạng để tương thích.

Các biến được đánh dấu Sensitive trên Vercel không được trả lại dưới dạng khóa thật khi tải cấu hình. Không dùng giá trị che từ một file tải về để kiểm tra khóa của môi trường đang chạy.

Sau khi thay đổi cấu hình, triển khai lại production. Không đưa khóa vào mã nguồn, Git, log hoặc tin nhắn.

## Chặn IP và môi trường serverless

Brevo có thể chặn IP gọi API mới dù khóa còn hợp lệ. Vercel mặc định sử dụng IP đầu ra có thể thay đổi, nên duyệt một IP chưa bảo đảm những instance tiếp theo sẽ được phép.

Các lựa chọn vận hành cần được chủ tài khoản quyết định:

- Dùng đầu ra IP cố định và cho phép đúng những IP đó trong Brevo. Static IP của Vercel là tính năng có phí; không bật gói hoặc tính năng trả phí khi chưa được chủ dự án chấp thuận.
- Điều chỉnh chính sách IP của Brevo cho tích hợp serverless. Việc tắt chặn IP giảm một lớp bảo vệ và cần được chủ tài khoản cân nhắc; khóa API vẫn phải bí mật và chỉ có quyền cần thiết.
- Dùng SMTP với khóa SMTP riêng khi chính sách và kết nối SMTP cho phép. Không dùng khóa SMTP cho API và không dùng khóa API như mật khẩu đăng nhập SMTP.

Tài liệu chính thức: [Brevo IP security](https://developers.brevo.com/docs/ip-security), [Vercel Static IPs](https://vercel.com/docs/networking/static-ips).

## SMTP

Nếu không cấu hình `BREVO_API_KEY`, có thể dùng SMTP:

```text
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USERNAME=<SMTP login từ Brevo>
SMTP_PASSWORD=<khóa SMTP Brevo>
SMTP_FROM=HanziGo <địa chỉ người gửi đã xác minh>
```

Với Gmail, dùng `smtp.gmail.com`, tài khoản gửi và Gmail App Password; không dùng mật khẩu đăng nhập Gmail thông thường.

## Chẩn đoán và kiểm chứng

`GET /api/auth/email-status` cho biết cấu hình và transport nhưng không trả khóa. Log gửi mail chỉ ghi phân loại lỗi an toàn, chẳng hạn `ip_not_authorized`, `invalid_api_key`, `sender_not_verified` hoặc `rate_limited`. Với lỗi IP, log có thể ghi IP nguồn được Brevo thông báo để đối chiếu; không ghi phản hồi thô, khóa hay mã OTP trên production.

Chạy kiểm thử trên dữ liệu tạm:

```text
python scripts/run_backend_tests.py test_email_delivery test_auth_otp
```

Sau triển khai, kiểm tra một yêu cầu quên mật khẩu bằng email được chủ tài khoản cho phép. HTTP 200 chỉ xác nhận nhà cung cấp đã chấp nhận email; cần kiểm tra sự kiện giao nhận hoặc hộp thư để xác nhận nhận được mã. Không đọc mã từ database production hoặc bỏ qua OTP để thay mật khẩu.
