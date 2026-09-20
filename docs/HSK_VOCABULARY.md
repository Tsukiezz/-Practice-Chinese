# Kho từ HSK 1–6 theo chủ đề

## Phạm vi và nguồn

Bộ được nhập là **HSK 2.0 (HSK 1–6 truyền thống)**, không trộn với danh sách HSK 3.0/HSK 2026.
Nguồn: [clem109/hsk-vocabulary](https://github.com/clem109/hsk-vocabulary), commit
`f3dc9d12ae00d04fa3676b0bd4c43cd58de2c264`, MIT, Copyright 2018 Clement Venard.
Giấy phép đi kèm tại `backend/data/LICENSE-HSK.txt`; phiên bản, số lượng và SHA-256 tại `backend/data/manifest.json`.

| Cấp | Mục nguồn | Cách viết khác nhau |
|---|---:|---:|
| 1 | 150 | 150 |
| 2 | 150 | 147 |
| 3 | 299 | 298 |
| 4 | 601 | 598 |
| 5 | 1.300 | 1.300 |
| 6 | 2.500 | 2.500 |
| Tổng | **5.000** | **4.993** |

Số liệu trên theo đúng các tệp của nguồn đã cố định phiên bản (nguồn xếp 299 mục vào cấp 3 và 601 vào cấp 4). Không thêm mục giả để làm tròn số cấp.
Các chữ như 长, 得, 还, 只 có nhiều cách đọc; 等, 对, 过 có các mục nghĩa riêng.
Giao diện gộp cách viết vào một thẻ, nhưng giữ đủ `source_id`, pinyin và nghĩa từng mục trong phần chi tiết.
Các từ bổ sung sẵn có của dự án được giữ lại nên tổng số thẻ trong database có thể lớn hơn 4.993.

## Tiếng Việt và chủ đề

`hsk20_source.json` giữ Hán tự, pinyin, cấp và định nghĩa tiếng Anh của nguồn.
`hsk20_vi.json` bổ sung nghĩa tiếng Việt và 22 chủ đề, được biên soạn với hỗ trợ AI,
kiểm tra tự động về đủ mục/không trùng/không rỗng và rà soát mẫu; **chưa phải toàn bộ bản dịch đã được giáo viên duyệt**.
Các hiệu chỉnh đã rà soát nằm trong `hsk20_vi_overrides.json`.
Chủ đề là cách tổ chức nội dung của ứng dụng, không phải phân loại chủ đề chính thức của kỳ thi HSK.

Gia đình, ăn uống, nhà cửa, học tập, công việc, du lịch, mua sắm, sức khỏe,
thiên nhiên, thời gian, số lượng, địa điểm, cảm xúc, giao tiếp, văn hóa, thể thao,
công nghệ, xã hội, hành động, đặc điểm, ngữ pháp và tư duy.

Mỗi mục nghĩa có một chủ đề chính. Từ nhiều nghĩa có thể xuất hiện ở nhiều chủ đề.
Không tạo câu ví dụ, bản thu âm hay nét viết giả: giữ nguyên dữ liệu đã có;
từ mới chưa có audio sẽ vô hiệu hóa nút loa và ghi rõ “Chưa có bản thu âm”.

Font chữ Hán được đóng gói cùng ứng dụng (HanziGo HSK, dẫn xuất Noto Sans SC, SIL OFL 1.1), khoảng 1,2 MB và bao phủ toàn bộ Hán tự trong bộ từ. Xem `assets/fonts/README.md`; không cần tải Google Fonts để đọc bộ HSK.

## Cách dùng

Trong **Từ vựng**, bấm **HSK 1–6 · Chọn chủ đề**, chọn cấp và chủ đề rồi **Áp dụng**.
Ví dụ: HSK 1 + Ăn uống. Bấm Xóa bộ lọc rồi Áp dụng để trở lại toàn bộ.
Tìm kiếm hỗ trợ Hán tự, pinyin có/không dấu và nghĩa Việt có/không dấu.
Mỗi trang tải tối đa 40 từ; nút Trang trước/Trang sau ở cuối danh sách.
Đổi bộ lọc hoặc từ khóa tự trở về trang đầu. Lịch sử, sổ tay, flashcard và chế độ khách vẫn hoạt động.

## Nhập lại hoặc cài trên máy khác

Từ `backend/`, dùng Python trong môi trường đã cài `requirements.txt`:

```powershell
python seed.py
python vocabulary_catalog.py
```

Lệnh thứ hai sao lưu SQLite vào `hanzi_go.before-hsk20.db` nếu chưa có, kiểm tra đầy đủ bộ dữ liệu rồi nhập trong một transaction.
Chạy lại không nhân đôi từ. Không đổi ID, nghĩa, pinyin, audio, ví dụ, nét viết hoặc phiên bản nội dung do Admin đã lưu;
không xóa người dùng, lịch sử, sổ tay, đề hoặc kết quả.
Cấp HSK chuẩn và các nghĩa theo nguồn nằm trong bảng catalog riêng; màn hình tra cứu dùng cấp của catalog cho từ thuộc bộ HSK.
Việc dùng/nhập bộ từ đã đóng gói **không cần Gemini và không gọi mạng**.

`tools/localize_hsk.py` chỉ là công cụ biên soạn lại dữ liệu, cần API key cục bộ và có thể phát sinh usage.
Không chạy công cụ này trong startup, CI hoặc mỗi lần mở từ điển.

## API

`GET /api/vocabulary/page?search=&hsk=1&topic=food&offset=0&limit=40`

- Công khai, dùng được cho khách; `limit` từ 1 đến 100, `offset` không âm.
- Trả `items`, `total`, `offset`, `limit`, `edition`, `topics`.
- `topics` gồm ID, nhãn Việt, số thẻ phù hợp với từ khóa/cấp hiện tại, trước khi áp dụng chủ đề.
- Mỗi từ có `senses` để giữ đủ các cách đọc/nghĩa và `topics` tương ứng.
- API `/api/vocabulary` cũ được giữ tương thích với Admin và các chức năng khác.

## Kiểm chứng

`python -m unittest test_vocabulary_catalog -v` kiểm tra đủ 5.000 mục/4.993 thẻ,
nhập lặp, giữ nội dung cũ, từ nhiều cách đọc, tìm không dấu, phân trang không trùng và lọc HSK + chủ đề.
Các kiểm thử Flutter kiểm tra tham số service, lọc/chuyển trang/tìm kiếm trên màn hình 320 px,
bàn phím mở, tra cứu khách và sổ tay.
`smoke_unified.py` nhập toàn bộ bộ từ vào database tạm và kiểm tra bộ lọc/chuyển trang ở viewport điện thoại cùng các luồng học hiện có.
