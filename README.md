# HanziGo · Chinese Learning

Ứng dụng học tiếng Trung cho người Việt. Nhánh `nguyen` bổ sung phần **Admin của Nguyên** theo phân công: UC-08, chức năng 28 và 31–35.

## Cấu trúc

- `lib/`, `android/`, `ios/`, `web/`: ứng dụng học viên Flutter hiện có.
- `admin/`: trang quản trị responsive HTML/CSS/JavaScript tại `/admin`.
- `backend/`: FastAPI, SQLite, phân quyền và kiểm thử tích hợp.
- `docs/ADMIN_HANDOFF.md`: API, dữ liệu, cách kết nối và tình trạng tích hợp.

## Chạy Admin trên Windows

Cần Python 3.11 trở lên. Từ thư mục gốc repository:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe seed.py
.venv\Scripts\python.exe create_admin.py
.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8010
```

Mở **http://127.0.0.1:8010/admin** và đăng nhập bằng tài khoản vừa tạo. API tương tác: **http://127.0.0.1:8010/docs**.

Trên điện thoại, nhấn nút **☰** để mở menu gồm nhóm Học tập/Hệ thống. Menu tự đóng khi chọn trang; có thể đóng bằng nút ☰, chạm bên ngoài hoặc Escape trên bàn phím. Tổng quan chỉ hiển thị 4 chỉ số chính; mở **Thống kê chi tiết** để xem thêm. Danh sách dùng thẻ có nhãn và biểu mẫu một cột. Trên máy tính, bấm **Xem giao diện điện thoại** để kiểm thử cùng bố cục và menu ☰ trong khung 440px; bấm **Trở về giao diện máy tính** để mở lại bố cục rộng.

Để kiểm tra trên điện thoại thật cùng Wi-Fi với máy tính, chạy backend từ `backend/` bằng:

```powershell
.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8010
```

Mở `http://<IPv4-cua-may-tinh>:8010/admin` trên điện thoại (xem IPv4 bằng `ipconfig`). Trên máy tính vẫn mở `http://127.0.0.1:8010/admin`. Dừng tiến trình cũ trên cổng 8010 trước khi đổi lệnh chạy. Nếu không kết nối được từ điện thoại, kiểm tra cùng mạng và quyền kết nối mạng riêng của Python trong Windows Firewall. Đây là bản web responsive, chưa phải màn hình Admin native trong Flutter.

`seed.py` thêm 8 từ và 6 đề Đọc mẫu HSK 1–6; chạy lại không tạo trùng. Đề minh họa ở trạng thái nháp để Admin kiểm tra trước khi phát hành. Không tạo tài khoản/mật khẩu mặc định, điểm hay lịch sử AI giả. Có thể tạo câu Nghe/Viết trong trang ngân hàng đề; câu Nghe cần audio HTTPS thật.

Database mặc định: `backend/hanzi_go.db`. Trang Admin và API chạy chung máy chủ, không cần Node.js để sử dụng.

## Chức năng Admin

- Người dùng: tìm/lọc, đổi vai trò, khóa/mở khóa, thu hồi phiên; bảo vệ Admin đang dùng và quản trị viên cuối cùng.
- Kho từ: CRUD chữ Hán, Pinyin, nghĩa, ví dụ, audio, HSK; vẽ nét theo thứ tự; kiểm tra trùng và liên kết đề thi.
- Ngân hàng đề: câu Nghe/Đọc/Viết, đáp án/rubric, audio/transcript, giải thích; nháp/phát hành/ẩn; bảo vệ đề đã có kết quả.
- Cấu hình AI: model, prompt, temperature, giới hạn token và bật/tắt; khóa chỉ nằm trên máy chủ.
- Duyệt điểm: xem bài, sửa điểm 0–100 kèm lý do, giữ điểm gốc và lịch sử; kết quả/dashboard học viên lấy ngay điểm mới.
- Báo cáo và nhật ký: số liệu từ SQLite, người thực hiện, thời gian, dữ liệu trước/sau. Kiểm tra phiên bản tránh ghi đè thay đổi của người khác.

## Môi trường

Tham khảo `backend/.env.example`. Máy chủ đọc biến môi trường, không tự nạp `.env`:

```powershell
$env:DATABASE_PATH = 'C:\duong-dan-du-lieu\hanzi_go.db'
$env:FRONTEND_ORIGINS = 'http://localhost:5173,http://localhost:8080'
```

Đặt `AI_API_KEY` riêng trên máy chủ khi tích hợp nhà cung cấp AI. Trang Admin chỉ báo khóa đã/chưa cấu hình; trạng thái sẵn sàng kiểm tra cấu hình nội bộ, chưa xác minh nhà cung cấp. Adapter của Trung/Kiệt gọi qua `backend/services.py` để dùng cấu hình, lưu kết quả thật và xử lý lỗi.

Demo mặc định chạy localhost. Khi triển khai, đặt sau HTTPS, giới hạn đăng nhập ở reverse proxy, cấp quyền thư mục dữ liệu và sao lưu SQLite. Không commit `.env`, database hoặc khóa.

## Kiểm thử

Từ `backend/`:

```powershell
.venv\Scripts\python.exe -m unittest -v test_admin
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:PLAYWRIGHT_CHANNEL = 'msedge'
.venv\Scripts\python.exe smoke_browser.py
```

Nếu không có Edge: cài bằng `.venv\Scripts\python.exe -m playwright install chromium` và bỏ biến `PLAYWRIGHT_CHANNEL`.

Kiểm thử dùng database tạm, tự dọn sau khi chạy. Test trình duyệt kiểm tra desktop 1440px, mobile 390px, vẽ nét, tạo đề, nộp bài, sửa điểm, khóa tài khoản, AI config, nhật ký và phiên đăng nhập. Ảnh lưu tại `test-results/`, không commit.

## Flutter và tích hợp

```powershell
flutter pub get
flutter run -d chrome --web-port 8080
flutter analyze
flutter test
```

Flutter vẫn là bản học viên offline từ `main`, chưa nối với backend mới. Phần Nguyên chạy qua `/admin`. Tích hợp Auth/Profile, từ điển, AI/Writing và Test/Review vào Flutter cần module của Tuyến, Vy, Trung, Kiệt; xem tài liệu bàn giao. Không cần chạy lại `flutter create .` vì đã có cấu hình nền tảng. iOS cần macOS/Xcode.

## Git

Làm phần Nguyên trên `nguyen`, kiểm thử trước commit/push:

```powershell
git switch nguyen
git add <cac-file-thay-doi>
git commit -m "feat(admin): describe the completed change"
git push origin HEAD:nguyen
```

PR cần nêu chức năng, API và kết quả test. Nguyên review quyền, dữ liệu và luồng tích hợp trước merge. Không tự merge hoặc push vào `main`.

## Cập nhật theo Excel của Nguyên

Xem [đối chiếu 23 đầu việc](docs/NGUYEN_ACCEPTANCE.md). Bổ sung chống ghi đè tài khoản, adapter Gemini có timeout/retry, kiểm tra kết nối AI và phúc khảo. Học viên mở `/review`; Admin xử lý trong **Duyệt kết quả → Yêu cầu phúc khảo**. Khởi động lại backend để tự nâng cấp DB cũ. Có 19 bài kiểm thử API và kiểm thử phúc khảo trên trình duyệt mobile. Gemini thật cần AI_API_KEY và model hợp lệ trên máy chủ.
