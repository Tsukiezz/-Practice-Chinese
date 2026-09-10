# HanziGo · Chinese Learning

Ứng dụng học tiếng Trung cho người Việt. Nhánh `test` tích hợp **Admin của Nguyên** (UC-08, chức năng 28 và 31–35) với ứng dụng học viên và backend của **Kiệt**. Xem [biên bản tích hợp](docs/INTEGRATION_TEST.md).

## Chạy một website cho Admin và học viên

Build Flutter (`flutter pub get`, `flutter build web --no-wasm-dry-run`) rồi chạy từ `backend/`:

```powershell
python -m pip install -r requirements.txt
python seed.py
python listening_demo.py --publish
$env:WEB_APP_DIR = (Resolve-Path ../build/web).Path
python -m uvicorn main:app --host 127.0.0.1 --port 8010
```

Mở **http://127.0.0.1:8010/** cho cả hai loại tài khoản. Đăng nhập bằng tài khoản Admin sẽ chuyển sang `/admin`; học viên vào ứng dụng Flutter. Khi đăng xuất, cả hai trở về cùng trang đăng nhập. API kiểm tra vai trò trên máy chủ. Không cần chạy web-server Flutter trên cổng riêng.

Trên Windows nên đặt SDK và thư mục build ở đường dẫn không dấu/không khoảng trắng. Nếu build ở thư mục khác, đặt `WEB_APP_DIR` tới đúng `build/web` đó. Khi build cùng website, không truyền `HANZIGO_API_URL` để Flutter tự lấy `/api` trên cùng địa chỉ. Mỗi người dùng cần tài khoản riêng; tạo Admin bằng `create_admin.py`, học viên bằng `register_student.py`.

Ba bài Nghe HSK 1 mẫu (Chào hỏi, Thời gian, Mua sắm) có MP3 đi kèm, transcript và đáp án khớp văn bản đọc. `listening_demo.py --publish` chỉ phát hành bài mẫu mới, không ghi đè hoặc tự phát hành lại đề đã chỉnh sửa/ẩn. Đây là dữ liệu mẫu bổ sung, không phải lịch sử/điểm cá nhân của Kiệt. Các đề Nghe cũ ở trạng thái nháp vẫn cần Admin kiểm tra trước khi phát hành. Nghe audio không cần khóa AI; chấm bài bằng Gemini cần khóa/model hợp lệ như phần cấu hình bên dưới.

## Thư mục

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

## Môi trường và Gemini

Sao chép `backend/.env.example` thành `backend/.env`. Backend tự nạp file này khi
khởi động; không commit `.env` hoặc đưa API key vào Flutter:

```powershell
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-3.5-flash
```

Trong trang Admin, mở **Cấu hình AI**, kiểm tra model rồi bật AI. Backend gọi
Gemini, bắt buộc JSON theo schema, tự thử lại lỗi mạng/429/5xx hoặc JSON bị cắt,
chuẩn hóa điểm/nhận xét và lưu trạng thái usage. Tra từ viết tay dùng Gemini OCR;
chế độ Luyện nét so sánh tọa độ với nét chuẩn hoàn toàn offline và không cần API key.

Có thể bật và kiểm tra kết nối từ thư mục `backend` bằng `python configure_gemini.py`, sau đó `python verify_gemini.py`. Hai lệnh không hiển thị API key; lệnh kiểm tra không lưu kết quả mẫu vào CSDL.

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

## Chạy ứng dụng Flutter

Giữ backend đang chạy ở terminal thứ nhất. Ở terminal thứ hai, từ thư mục gốc:

```powershell
flutter pub get
flutter run -d chrome --web-port 8080 `
  --dart-define=HANZIGO_API_URL=http://localhost:8010/api
flutter analyze
flutter test
```

Ứng dụng có màn hình đăng nhập và tự dùng token phiên hiện tại; không truyền token
qua `--dart-define`. Với Android emulator:

```powershell
flutter run -d emulator-5554 `
  --dart-define=HANZIGO_API_URL=http://10.0.2.2:8010/api
```

Trên điện thoại thật, chạy Uvicorn với `--host 0.0.0.0`, thay URL bằng IPv4 của
máy tính cùng Wi-Fi và cho phép cổng 8010 qua Windows Firewall. Production phải
dùng HTTPS. Dữ liệu seed là bản nháp; Admin cần kiểm tra và chuyển đề sang
`published` trước khi học viên nhìn thấy.

## Phần Kiệt đã tích hợp

- F15–F16: Test Nghe, audio thật, nộp bài, Gemini chấm và giải thích transcript/bẫy nghe.
- F17: Test Đọc gồm trắc nghiệm/điền từ/đọc hiểu; bài tổng hợp Nghe–Đọc–Viết và điểm theo từng kỹ năng.
- F21: lịch sử tra từ riêng theo tài khoản và Flashcard.
- F22–F23–F25: tự lọc chữ viết tay/đoạn văn dưới 80, nộp lại nhiều lần và tự hoàn thành khi đạt từ 80.
- F26–F27: dashboard dữ liệu thật, streak, tiến độ, radar bốn kỹ năng và báo cáo năng lực Gemini có cache.

Các màn hình đều có trạng thái tải, rỗng, lỗi/thử lại. Không cần chạy lại
`flutter create .`; iOS cần macOS/Xcode.

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
