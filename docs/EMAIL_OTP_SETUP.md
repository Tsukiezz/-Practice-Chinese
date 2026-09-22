# Cấu hình gửi mã OTP qua Gmail

Trang production của HanziGo chạy trên Vercel. Để gửi mã đăng ký và quên mật khẩu từ `nguyenvovinhnguyen@gmail.com`, cần dùng **Gmail App Password** — không dùng mật khẩu đăng nhập Gmail.

1. Bật Xác minh 2 bước cho tài khoản Gmail.
2. Vào <https://myaccount.google.com/apppasswords>, tạo App Password (đặt tên `HanziGo Vercel`) và sao chép mã 16 ký tự.
3. Vào Vercel → project `hanzigo-chinese-learning` → **Settings → Environment Variables**. Thêm các biến cho môi trường **Production**:

   ```text
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_FROM=nguyenvovinhnguyen@gmail.com
   SMTP_USERNAME=nguyenvovinhnguyen@gmail.com
   SMTP_PASSWORD=<mã App Password 16 ký tự>
   ```

4. Redeploy production, sau đó thử đăng ký bằng một email khác và thử Quên mật khẩu bằng email đã có tài khoản. Kiểm tra cả mục Spam.

Không đưa App Password vào source code, Git hay tin nhắn chat. Khi SMTP chưa được cấu hình, production sẽ trả lỗi 503 thay vì báo gửi thành công sai.
