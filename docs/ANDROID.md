# HanziGo trên Android (PWA)

Cập nhật: 15/10/2026.

Phương án đã chọn: cài từ Chrome lên màn hình chính, mở trong cửa sổ ứng dụng.
Không cần APK, Android Studio hay tài khoản phát hành Google Play để cài theo cách này.

## Cách cài

1. Mở https://hanzigo-chinese-learning.vercel.app/install-android.html bằng Chrome trên Android.
2. Nhấn **Cài HanziGo** nếu trình duyệt cung cấp lời mời cài đặt. Nếu chưa có, dùng menu **⋮ → Thêm vào màn hình chính → Cài đặt**.
3. Mở biểu tượng HanziGo trên điện thoại và đăng nhập bằng tài khoản hiện có.

Trong ứng dụng có đường dẫn **Cá nhân → Cài HanziGo trên Android**. Quay lại từ trang cài đặt sẽ giữ tab Cá nhân của phiên trình duyệt.
Trình duyệt trong Zalo/Facebook có thể không hỗ trợ cài; mở trang bằng Chrome bên ngoài.
Trên một số máy/trình duyệt chỉ có “Tạo lối tắt”, khi đó đây là lối tắt mở web, chưa phải cửa sổ ứng dụng độc lập.

## Phạm vi và chi phí

- Cài đặt miễn phí; dùng cùng website, API, tài khoản, dữ liệu và quyền lợi hiện có.
- Viết tay dùng thao tác chạm; đọc phát âm cần cấp quyền micro cho trình duyệt.
- Cần Internet. Đây không phải bản học hoàn toàn offline; “chấm nét offline” chỉ có nghĩa thuật toán chấm không gọi mô hình AI, các bước tải/lưu vẫn có thể cần mạng.
- Cài đặt không tự mở khóa Premium hoặc bỏ hạn mức AI. Phí máy chủ/nhà cung cấp AI (nếu phát sinh vượt gói đang dùng) vẫn là chi phí vận hành dự án.
- Chưa tạo APK, chưa đăng lên Google Play, chưa chứng nhận trên thiết bị Android thật.

## Triển khai

- `web/manifest.json`: ID và scope `/`, start URL `/`, standalone, icon 192/512, ngôn ngữ Việt, hỗ trợ xoay màn hình.
- `web/install-android.html`: hướng dẫn và nút cài. `install-app.js` quản lý sự kiện trình duyệt `beforeinstallprompt`/`appinstalled`, chỉ mở lời mời sau khi người dùng nhấn nút.
- `web/hanzigo-worker.js`: lấy trang trực tiếp từ mạng; khi mất kết nối chỉ hiển thị trang thông báo có nút thử lại. Không dùng Cache Storage, không lưu token, API, tin nhắn hay tệp cá nhân.
- Worker không xử lý API/upload/audio. Không phục hồi worker Flutter cache-first đã được gỡ trước đó; cập nhật giao diện vẫn qua cơ chế versioned assets của backend.
- Build Vercel hiện có tự sao chép các file web mới. Không thêm dịch vụ trả phí hoặc bí mật vào client.

## Kiểm tra

Chạy `backend/.venv/Scripts/python.exe scripts/test_android_install.py` (Windows, Edge) để kiểm tra giao diện hẹp, fallback menu, lời mời cài bị từ chối/chấp nhận, chế độ standalone, mất mạng và API không bị trả nhầm HTML.
Chạy Flutter build web để xác nhận mục cài trong trang Cá nhân biên dịch được.
Kiểm tra thực tế cần một điện thoại Android: cài từ Chrome, mở icon, đăng nhập, vẽ chữ, cho phép micro, nghe audio, gửi tệp hỗ trợ và đóng/mở ứng dụng.

Tài liệu: [Chrome – dùng ứng dụng web](https://support.google.com/chrome/answer/9658361?co=GENIE.Platform%3DAndroid&hl=vi), [PWA – lời mời cài đặt](https://web.dev/learn/pwa/installation-prompt).
