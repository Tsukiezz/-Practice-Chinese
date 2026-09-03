# HanziGo Flutter

Ứng dụng mobile học tiếng Trung cho người Việt, xây dựng bằng Flutter và Material 3.

## Tính năng hiện có

- Trang chủ theo dõi chuỗi học, XP và mục tiêu tuần
- Lộ trình bài học HSK 1–2
- Bộ từ vựng Hán tự, pinyin, nghĩa và câu ví dụ
- Bài luyện trắc nghiệm có chấm điểm
- Hồ sơ, thành tích và cài đặt học tập
- Bottom navigation và giao diện tối ưu cho điện thoại

## Chạy ứng dụng

Sau khi cài Flutter SDK:

```powershell
cd mobile
flutter create . --platforms=android,ios,web
flutter pub get
flutter run
```

Trên Windows, iOS chỉ có thể build bằng macOS/Xcode. Có thể chạy Android bằng Android Studio Emulator hoặc điện thoại bật USB debugging.
