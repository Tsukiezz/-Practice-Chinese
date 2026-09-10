Cập nhật 07/09/2026: xem [đối chiếu 23 đầu việc](NGUYEN_ACCEPTANCE.md). Kết quả kiểm tra 06/09 bên dưới là lịch sử.

# Bàn giao Nguyên — Admin & tích hợp

## Phạm vi và hiện trạng

Triển khai UC-08 / 31–35 và báo cáo 28 trên web responsive với SQLite thật. Flutter học viên là nền tích hợp. Backend MobileLab và prototype React ngoài repository thuộc sản phẩm học lập trình khác nên không đưa vào nhánh này.

Khi kiểm tra GitHub: `main`, `nguyen`, `tuyen` ở `3403b81`; `kiet`, `trung`, `vy` ở `9df1a26` chỉ có README. Chưa có code module thành viên để review/hợp nhất. Không merge các nhánh chỉ có README vào Flutter.

## Xác thực

- `POST /api/auth/register`: `{name,email,password}` → tài khoản student; không nhận role, mật khẩu ít nhất 8 ký tự.
- `POST /api/auth/login`: `{email,password}` → `{token,user,expires_in:86400}`.
- Header `Authorization: Bearer <token>` cho API cần đăng nhập.
- `GET /api/me`: tài khoản hiện tại. `POST /api/auth/logout`: thu hồi token, trả 204.
- Session ngẫu nhiên lưu SHA-256 trong DB; mật khẩu PBKDF2-SHA256 với salt riêng. Không có signing secret mặc định.
- 401: chưa đăng nhập/hết phiên; 403: thiếu quyền/khóa; 404: không tồn tại; 409: trùng/ràng buộc/phiên bản cũ; 422: input sai; 502/503: lỗi/chưa cấu hình AI.
- Lỗi `{detail: ...}`; lỗi 422 có thể chứa mảng theo trường.
- `/admin` là vỏ đăng nhập công khai; chỉ tải dữ liệu sau xác nhận Admin. Mọi `/api/admin/*` kiểm tra Admin ở máy chủ.

## Endpoint Admin

| Chức năng | Endpoint | Input / output |
|---|---|---|
| Báo cáo | `GET /api/admin/dashboard` | `totals`, `recent_activity` |
| Người dùng | `GET /api/admin/users?search=&role=&active=` | Role student/admin, trạng thái boolean |
| Khóa/đổi quyền | `PATCH /api/admin/users/{id}` | `{role,is_active,version}` |
| Kho từ | `GET/POST /api/admin/vocabulary` | GET có `search`, `hsk` |
| Sửa/xóa từ | `PUT /api/admin/vocabulary/{id}`, `DELETE ...?version=N` | PUT thêm version |
| Đề | `GET/POST /api/admin/exams` | GET có hsk |
| Sửa/xóa đề | `PUT /api/admin/exams/{id}`, `DELETE ...?version=N` | PUT thêm version |
| AI | `GET/PUT /api/admin/ai-config` | Model, system_prompt, temperature, max_tokens, enabled, version |
| Kết quả | `GET /api/admin/results?user_id=&below=` | Nội dung, điểm gốc/hiện tại, feedback |
| Sửa điểm | `PATCH /api/admin/results/{id}/score` | `{score,reason,version}` |
| Lịch sử điểm | `GET /api/admin/results/{id}/history` | Điểm cũ/mới, lý do, Admin, thời gian |
| Nhật ký | `GET /api/admin/audit-logs?limit=100&offset=0` | Tối đa 500 bản ghi/lượt |

Timestamp Unix theo giây. Từ, đề, AI config, kết quả có version tăng sau mỗi lần sửa. Client tải lại khi nhận 409. Thay đổi và audit trong cùng transaction. Khóa người dùng thay vì xóa để giữ lịch sử.

## Kho từ và nét chuẩn — Vy / Trung

`GET /api/vocabulary?search=&hsk=` cho phép khách tra chữ Hán/Pinyin có dấu/tiếng Việt, trả cùng dữ liệu Admin:

```json
{
  "id": 1, "hanzi": "一", "pinyin": "yī", "meaning": "một", "hsk": 1,
  "example": "一个人", "audio_url": "", "version": 1,
  "strokes": [[{"x":180,"y":512},{"x":840,"y":512}]]
}
```

Nét đúng thứ tự, mỗi nét 2–512 điểm, tọa độ 0–1024, gốc trái trên, tối đa 64 nét. Mảng rỗng là chưa có chuẩn, không coi là điểm 0. Admin chọn **Từ vựng → Sửa**, vẽ từng nét chuẩn theo đúng thứ tự trên Canvas rồi lưu; có thể dùng **Bỏ nét cuối** hoặc **Vẽ lại** trước khi lưu. Luyện nét chỉ nhận một chữ Hán và chấm offline theo số nét, vị trí/thứ tự và hướng đi.

`POST /api/handwriting/submit` chấm offline theo trọng số 30% số nét, 40% đúng nét tại đúng thứ tự/vị trí và 30% hướng đầu-cuối. Response dùng contract chung:

```json
{"score": 70, "feedback": "Cần kiểm tra lại nét 1.", "details": {"wrong_strokes": [1]}}
```

Chỉ số nét bắt đầu từ 1. Kết quả vẫn được lưu vào `results` với `kind=handwriting` và `graded_by=automatic`; endpoint tra từ `/api/handwriting/recognize` là luồng riêng.

Không xóa từ có word_id trong đề. Lịch sử tra từ đã liên kết tới `vocabulary(id)`
và được cách ly theo tài khoản học viên.

## Đề và kết quả — Kiệt / Trung

`GET /api/exams?hsk=` cần đăng nhập, chỉ trả đề published, loại answer/transcript/explanation trước nộp.

```json
{
  "title": "HSK 1 · Bài đọc", "hsk": 1, "status": "published", "duration_minutes": 15,
  "questions": [{
    "id": "q1", "section": "reading", "prompt": "一 có nghĩa là gì?",
    "options": ["một", "hai"], "answer": "một", "audio_url": "",
    "transcript": "", "explanation": "一 nghĩa là một.", "word_id": 1
  }]
}
```

- section: listening/reading/writing. Mã câu duy nhất trong đề.
- Câu Nghe cần URL HTTPS; module học viên phát audio và xử lý lỗi tải. Admin không xác minh nguồn bên ngoài.
- Trắc nghiệm ít nhất 2 lựa chọn khác nhau, answer nằm trong lựa chọn.
- Viết tự do: options rỗng, answer là rubric/đáp án mẫu, do module Writing chấm.
- `POST /api/exams/{id}/submit`: `{version,answers:{q1:"một"}}`. Server kiểm tra đầy đủ mã câu, bắt buộc Gemini chấm, lưu lời giải từng câu và điểm theo từng kỹ năng trong snapshot. Không nhận score từ client.
- Đề tổng hợp Nghe–Đọc–Viết và câu Viết tự do dùng rubric/đáp án mẫu để Gemini chấm ngữ cảnh.
- `duration_minutes` hiện được hiển thị trên danh sách đề; quản lý phiên thi có đồng hồ đếm ngược là phần mở rộng tiếp theo nếu nhóm yêu cầu.
- Đề có kết quả chỉ được ẩn/sửa, không xóa. Snapshot giữ nội dung/đáp án lúc nộp dù đề đã sửa.

`GET /api/me/results`, `/api/me/dashboard` và `/api/me/capability` lấy user_id từ session. Dashboard dùng dữ liệu thật, streak, từ đã tra, điểm bốn kỹ năng và tiến trình ôn tập hiện tại. Điểm Admin sửa hiển thị ngay; lịch sử lý do cũng trả cho học viên.

## Adapter AI — Trung / Kiệt

Key ưu tiên `GEMINI_API_KEY`, fallback `AI_API_KEY`. Dùng `verify_gemini.py` để xác minh thật bài Đọc và ảnh viết tay mà không in khóa.

`services.grade_with_ai(user_id, kind, content, provider=gemini_grade)` dùng adapter Gemini REST trong `ai_provider.py`: HTTPS cố định, timeout đọc 20s/kết nối 5s, tối đa hai lần gửi khi lỗi mạng/429/5xx. Output score hữu hạn 0–100/feedback, lỗi 502 đã ẩn chi tiết, AI chưa cấu hình 503. Không tạo điểm giả. Nhận dạng ảnh/nét viết vẫn thuộc module Trung.

`POST /api/admin/ai-config/test` chỉ Admin, gọi bài mẫu ngắn, ghi usage nhưng không tạo điểm học viên; có thể phát sinh phí. Kiểm thử dùng HTTP giả lập; cần khóa/model thật để xác minh kết nối.

## Phúc khảo

- `POST /api/me/results/{id}/appeals`: `{reason}` dài 5–2000, chỉ bài của người đăng nhập; trùng yêu cầu pending trả 409.
- `GET /api/me/appeals`: lịch sử và phản hồi của học viên hiện tại.
- `GET /api/admin/appeals?status=pending`: lọc pending/resolved, trả bài làm, lý do, điểm, version/result_version.
- `PATCH /api/admin/appeals/{id}`: `{version,result_version,score,response}`; phản hồi 5–2000 ký tự. Lưu điểm/lịch sử/trạng thái/audit trong transaction; bản cũ hoặc đã xử lý trả 409.
- Web học viên `/review`; Admin: Duyệt kết quả → Yêu cầu phúc khảo.
- Restart backend để migration tự thêm users.version và bảng appeals, giữ dữ liệu cũ.

```python
from services import grade_with_ai, gemini_provider

# Trong endpoint Writing đã xác thực:
# result = grade_with_ai(user['id'], 'writing', body.content, gemini_provider)

# Adapter có sẵn trong services.py; không cần định nghĩa lại.
# settings: model, system_prompt, temperature, max_tokens, api_key.
# Trả {'score': <điểm thật 0..100>, 'feedback': <nhận xét thật>}.
```

Các provider Gemini dùng timeout, retry có giới hạn và structured JSON schema. Chấm
viết tay dựng ảnh PNG từ Canvas, gửi ảnh học viên, ảnh chuẩn và tọa độ thứ tự nét.

Hàm `evaluate_with_ai` kiểm tra điểm dạng số hữu hạn 0–100 (không nhận boolean/chuỗi), nhận xét không rỗng và ghi lượt dùng. `grade_with_ai` hoặc endpoint thi lưu kết quả `graded_by=ai`; lỗi provider thành 502 không lộ exception/key. AI tắt/chưa cấu hình trả 503, không tạo điểm giả. Provider phải đặt timeout mạng và do code máy chủ cung cấp.

## Demo và review

1. Tạo Admin, chạy seed và đăng nhập /admin.
2. Thêm từ/vẽ nét; thử từ trùng để thấy lỗi.
3. Tạo đề Đọc có word_id và phát hành; xóa từ tham chiếu phải bị chặn.
4. Đăng ký học viên qua /docs, lấy đề/nộp bằng token học viên.
5. Xem kết quả, sửa điểm/lý do; kiểm tra /api/me/results và dashboard học viên.
6. Khóa học viên, xác minh token cũ không dùng được.
7. Xem audit và AI config; không nhập key thật vào giao diện/prompt.

Test API và trình duyệt theo README dùng DB tạm, không thay dữ liệu demo. Không commit DB, môi trường ảo, ảnh test, secrets.

### Kết quả kiểm tra ngày 09/09/2026

- 38 unit/integration tests FastAPI/SQLite đạt: phân quyền, session, CRUD, bài Nghe/Đọc/tổng hợp, lịch sử từ, thuật toán viết tay offline, đoạn văn dưới 80, Dashboard, báo cáo AI, retry Gemini và dựng ảnh OCR.
- Playwright trên Microsoft Edge: desktop 1440px và mobile 390px đạt; không có lỗi JavaScript; kiểm tra cả điểm học viên sau khi Admin duyệt.
- `node --check admin/app.js`: đạt.
- `flutter analyze`: không có vấn đề.
- `flutter test`: 20 kiểm thử service/widget đạt cho đề Nghe/Đọc/tổng hợp, từ điển, Flashcard, Canvas, ôn tập và Dashboard.
- Workflow `Admin integration tests` được thêm để GitHub chạy lại kiểm thử API và Chromium. Trạng thái GitHub Actions phải xem trên repository; kết quả local không thay cho kết quả CI.

## Tích hợp toàn nhóm còn cần

- Tuyến: đăng nhập/đăng ký/hồ sơ Flutter, khôi phục mật khẩu, avatar và session thống nhất.
- Vy: kho cá nhân ngoài phạm vi lịch sử tra từ/Flashcard đã tích hợp.
- Trung: OCR nhận diện chữ tự do ngoài luồng chấm Canvas theo chữ mục tiêu đã tích hợp.
- Kiệt: F15, F16, F17, F21, F22, F23, F25, F26 và F27 đã có luồng mobile/backend; đồng hồ phiên thi là phần mở rộng nếu nhóm bổ sung yêu cầu.
- Nguyên: review PR về quyền, dữ liệu, lỗi API, đồng bộ điểm và kiểm thử tích hợp; chỉ merge main khi được yêu cầu.
