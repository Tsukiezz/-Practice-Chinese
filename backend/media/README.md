# Âm thanh bài Nghe mẫu

`word-*.mp3`: 33 tệp phát âm từ vựng mẫu, tên tệp là mã Unicode của từng Hán tự. Tạo bằng `generate_vocabulary_audio.py` từ `seed.WORDS`, giọng tổng hợp `zh-CN-XiaoxiaoNeural`, tốc độ -15%. `seed.py` liên kết audio vào từ chỉ khi URL còn trống. Dùng `edge-tts==7.2.8` khi cần tạo lại; ứng dụng phát MP3 đi kèm, không cần cài edge-tts khi chạy backend.

Ba tệp MP3 chứa giọng đọc tổng hợp tiếng Trung (`zh-CN-XiaoxiaoNeural`, tốc độ -15%), tạo từ đúng transcript trong `listening_demo.py`. Đây là bài mẫu HSK 1 để thử ứng dụng, không phải đề thi HSK chính thức hay bản ghi người thật.

Chạy lại khi cần biên soạn: cài `edge-tts==7.2.8` trong môi trường riêng rồi chạy `python generate_listening_audio.py`. Backend phát tệp có sẵn qua `/media/`, không gọi dịch vụ giọng đọc lúc học viên nghe.
