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
| Khóa/đổi quyền | `PATCH /api/admin/users/{id}` | `{role,is_active}` |
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

Nét đúng thứ tự, mỗi nét 2–512 điểm, tọa độ 0–1024, gốc trái trên, tối đa 64 nét. Mảng rỗng là chưa có chuẩn, không coi là điểm 0. Admin vẽ/bỏ nét cuối/vẽ lại; đây là dữ liệu biên soạn, không phải thuật toán OCR/chấm nét.

Không xóa từ có word_id trong đề. Module kho cá nhân/lịch sử của Vy cần thêm khóa ngoại tới vocabulary(id) để tiếp tục bảo vệ tham chiếu.

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
- `POST /api/exams/{id}/submit`: `{version,answers:{q1:"một"}}`. Server chấm theo đáp án chính xác, điểm 0–100 chia đều các câu; lưu snapshot đề/bài làm. Không nhận score từ client.
- Đề có Viết tự do trả 422 để tránh chấm sai bằng so khớp văn bản; cần module Writing cho đề tổng hợp.
- duration_minutes là thông tin giao diện; phiên thi tính giờ/chống nộp lại thuộc luồng thi Kiệt cần bổ sung.
- Đề có kết quả chỉ được ẩn/sửa, không xóa. Snapshot giữ nội dung/đáp án lúc nộp dù đề đã sửa.

`GET /api/me/results` và `/api/me/dashboard` lấy user_id từ session. Dashboard tính results, average_score, needs_review (score < 80). Điểm Admin sửa hiển thị ngay ở cả hai API; lịch sử lý do cũng trả cho học viên. Ôn tập lọc theo score, không theo original_score.

## Adapter AI — Trung / Kiệt

Key chỉ đọc từ AI_API_KEY. ready là kiểm tra nội bộ, chưa xác minh nhà cung cấp.

`services.grade_with_ai(user_id, kind, content, provider)` là hàm nội bộ máy chủ, không phải endpoint tự nộp điểm:

```python
from services import grade_with_ai

# Trong endpoint Writing đã xác thực:
# result = grade_with_ai(user['id'], 'writing', body.content, provider_adapter)

def provider_adapter(settings, content):
    # Triển khai lời gọi nhà cung cấp với timeout và chuẩn hóa response.
    # settings: model, system_prompt, temperature, max_tokens, api_key.
    # Trả {'score': <điểm thật 0..100>, 'feedback': <nhận xét thật>}.
    raise NotImplementedError('Kết nối adapter AI của Trung/Kiệt')
```

Hàm kiểm tra điểm hữu hạn 0–100, lưu kết quả thật graded_by=ai và lượt dùng; lỗi provider thành 502 không lộ exception/key. AI tắt/chưa cấu hình trả 503, không tạo điểm giả. Adapter phải đặt timeout mạng và do code máy chủ cung cấp. Chưa có provider trực tiếp trong nhánh Admin; provider giả lập chỉ dùng trong test.

## Demo và review

1. Tạo Admin, chạy seed và đăng nhập /admin.
2. Thêm từ/vẽ nét; thử từ trùng để thấy lỗi.
3. Tạo đề Đọc có word_id và phát hành; xóa từ tham chiếu phải bị chặn.
4. Đăng ký học viên qua /docs, lấy đề/nộp bằng token học viên.
5. Xem kết quả, sửa điểm/lý do; kiểm tra /api/me/results và dashboard học viên.
6. Khóa học viên, xác minh token cũ không dùng được.
7. Xem audit và AI config; không nhập key thật vào giao diện/prompt.

Test API và trình duyệt theo README dùng DB tạm, không thay dữ liệu demo. Không commit DB, môi trường ảo, ảnh test, secrets.

### Kết quả kiểm tra ngày 06/09/2026

- 15 integration tests FastAPI/SQLite đạt: phân quyền, session, CRUD, xung đột phiên bản, ràng buộc xóa, chấm bài, ghi đè điểm, cách ly dữ liệu học viên, AI config/adapter và seed.
- Playwright trên Microsoft Edge: desktop 1440px và mobile 390px đạt; không có lỗi JavaScript; kiểm tra cả điểm học viên sau khi Admin duyệt.
- `node --check admin/app.js`: đạt.
- `flutter analyze`: không có vấn đề.
- `flutter test`: 1 widget test đạt trên bản sao mã nguồn sạch trong thư mục tạm. SDK dùng đường dẫn ổ đĩa tạm không dấu để tránh lỗi shader trên đường dẫn tiếng Việt; thư mục build cũ trong OneDrive bị khóa nên không dùng lại. Không thay mã Flutter để né lỗi kiểm thử.
- Workflow `Admin integration tests` được thêm để GitHub chạy lại kiểm thử API và Chromium. Trạng thái GitHub Actions phải xem trên repository; kết quả local không thay cho kết quả CI.

## Tích hợp toàn nhóm còn cần

- Tuyến: đăng nhập/đăng ký/hồ sơ Flutter, khôi phục mật khẩu, avatar và session thống nhất.
- Vy: giao diện API từ điển, audio, kho cá nhân.
- Trung: adapter AI thật, OCR/Canvas học viên/chấm nét/bài viết.
- Kiệt: giao diện thi, phiên thi, ôn tập, dashboard, kết quả Writing và bộ lọc dưới 80.
- Nguyên: review PR về quyền, dữ liệu, lỗi API, đồng bộ điểm và kiểm thử tích hợp; chỉ merge main khi được yêu cầu.
