# Số nét và chấm viết offline

Kho 5.000 mục từ HSK dùng 2.632 chữ khác nhau. Toàn bộ các chữ này có số nét từ bộ nét viết theo quy ước Trung Quốc của [Make Me a Hanzi](https://github.com/skishore/makemeahanzi). Các chữ ngoài bộ này dùng Unihan 18.0, ưu tiên biến thể G nếu có. Giấy phép được lưu cạnh dữ liệu.

`backend/data/stroke_counts.json` chỉ lưu số nét, không thay thế hoặc ghi đè mẫu tọa độ quản trị viên đã vẽ. API trả tổng số nét và số nét từng chữ; nếu thiếu một chữ thì không công bố tổng cộng thiếu. Tạo lại bằng `python backend/tools/build_stroke_counts.py Unihan.zip graphics.txt`; dấu SHA-256 của hai nguồn nằm trong JSON.

Chấm offline v2 vẫn chuẩn hóa vị trí và kích thước toàn chữ, nhưng cho điểm từng mức ở phần vị trí/thứ tự và hướng viết. Bài có nét nhận tối thiểu 5 điểm để khuyến khích luyện tập; bài rỗng vẫn bị từ chối. Viết thiếu hoặc đảo nét vẫn được nhắc sửa và bị trừ điểm. Điểm lịch sử giữ nguyên.

Dự án địa phương được hợp nhất vào `practice-chinese-test-run` để giữ đường dẫn môi trường Python, cấu hình và cơ sở dữ liệu đang dùng. Thư mục `.local-backups` chứa các phiên bản xung đột và Git cũ để khôi phục; không đưa lên Git hoặc Vercel.
