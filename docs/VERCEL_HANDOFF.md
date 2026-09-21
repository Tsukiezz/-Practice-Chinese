# Bàn giao HanziGo trên Vercel

Website: https://hanzigo-chinese-learning.vercel.app

Admin: https://hanzigo-chinese-learning.vercel.app/admin

## Hạ tầng

- Repository: `Tsukiezz/-Practice-Chinese`, nhánh triển khai: `test`.
- Vercel: team `cdcl`, project `hanzigo-chinese-learning`, gói Hobby.
- Database: Turso `hanzigo-data`, region Tokyo `hnd1`, gói Starter miễn phí.
- Flutter Web và FastAPI dùng chung domain; backend chạy Python 3.13.
- Database lưu trên Turso, không ghi SQLite vào filesystem tạm của Vercel.
- Git auto-deployment được tắt trong `vercel.json`. Triển khai thủ công từ `test` để tránh tự triển khai code trên `main`.

## Cấu hình riêng tư

Production cần `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`, `GEMINI_API_KEY`, `GEMINI_MODEL`.
Turso integration cung cấp hai biến database. Khóa Gemini chỉ có ở backend.
Không commit `.env`, `.vercel`, file database, mật khẩu hoặc token.
Các tài khoản và mật khẩu hiện có được giữ lại khi chuyển dữ liệu; session cũ không được chuyển, cần đăng nhập lại.

## Chuyển dữ liệu lần đầu

Database đích phải trống. Script từ chối ghi đè database đã có bảng:

```powershell
npx vercel env pull .vercel/.env.production.local --environment production --scope cdcl
backend/.venv/Scripts/python.exe backend/tools/migrate_to_turso.py --source backend/hanzi_go.db --env-file .vercel/.env.production.local
```

Script tạo snapshot nhất quán, cập nhật schema trên snapshot, bỏ session/recovery code/rate limit tạm, chuyển schema và dữ liệu trong một transaction, rồi đối chiếu số dòng và khóa ngoại. Database gốc không bị sửa.

Dữ liệu đã chuyển: 6 tài khoản, 4.999 thẻ từ vựng (4.993 mục từ trong bộ HSK 2.0), 10 đề thi và lịch sử hiện có. Bộ nguồn có 5.000 mục nghĩa; số mục từ khác số mục nghĩa do từ đa âm/đa nghĩa. 48 bài học được đóng gói trong `backend/data/lessons.json`.

## Cập nhật ứng dụng

```powershell
git switch test
git pull --ff-only origin test
npx vercel link --project hanzigo-chinese-learning --scope cdcl
npx vercel deploy --prod --yes --scope cdcl
```

Vercel cài dependencies từ `pyproject.toml`, build Flutter 3.47.2 bằng `scripts/vercel_build.sh`, phục vụ file tĩnh từ `public/` và API từ `api/index.py`. Không chạy lại script chuyển dữ liệu khi cập nhật code. Thay đổi schema về sau cần migration riêng và bản sao lưu trước khi áp dụng.

## Kiểm tra và vận hành

Đã kiểm tra trên URL production ngày 21/09/2026: đăng nhập cả hai vai trò bằng trình duyệt, màn hình 390×844 và 1280×900, 48 bài học, phân trang/tìm kiếm từ vựng, audio, chặn học viên truy cập API admin, lưu tiến độ bài đầu và đọc lại sau đăng nhập mới. Endpoint kiểm tra kết nối Gemini trả `200` / `ok`. Các kiểm thử backend hiện có đạt trên SQLite và libSQL; thêm kiểm thử adapter về đọc hàng, lỗi ràng buộc và rollback.

Có thể chạy lại `backend/smoke_deployed.py` với các biến `DEMO_URL`, `DEMO_ADMIN_EMAIL`, `DEMO_ADMIN_PASSWORD`, `DEMO_STUDENT_EMAIL`, `DEMO_STUDENT_PASSWORD`. Thêm `--write-check` để lưu bước đầu bài học cho tài khoản demo học viên. Mật khẩu không nằm trong tài liệu/source code.

- Kiểm tra `/api/lessons` có 48 bài, `/api/vocabulary/page?limit=1` có dữ liệu.
- Đăng nhập học viên và admin; xác nhận quyền admin không mở cho học viên.
- Học bài, tải lại và xác nhận tiến độ còn được lưu.
- Kiểm tra giao diện ở màn hình điện thoại và máy tính.
- Xem lỗi runtime tại Vercel project > Logs; quản lý database tại integration Turso của project.
- Rollback code bằng chức năng rollback deployment trên Vercel. Rollback deployment không khôi phục database.
- SQLite local và Turso online là hai database riêng, không tự đồng bộ sau lần chuyển đầu.

Chủ dự án đã đồng ý mở link công khai ngày 21/09/2026. Vercel SSO đã được tắt riêng cho project này. Đăng nhập HanziGo và phân quyền admin/học viên vẫn được thực thi ở backend.
