class ChineseWord {
  const ChineseWord({required this.hanzi, required this.pinyin, required this.meaning, required this.example, required this.translation, this.category = 'Cơ bản'});
  final String hanzi, pinyin, meaning, example, translation, category;
}

class Lesson {
  const Lesson({required this.title, required this.subtitle, required this.level, required this.progress, required this.icon, required this.color});
  final String title, subtitle, level, icon;
  final double progress;
  final int color;
}

const dailyWord = ChineseWord(hanzi: '坚持', pinyin: 'jiān chí', meaning: 'kiên trì', example: '坚持学习，你一定会进步。', translation: 'Kiên trì học tập, bạn nhất định sẽ tiến bộ.', category: 'Động từ');

const words = [
  ChineseWord(hanzi: '你好', pinyin: 'nǐ hǎo', meaning: 'xin chào', example: '你好，很高兴认识你。', translation: 'Xin chào, rất vui được gặp bạn.'),
  ChineseWord(hanzi: '谢谢', pinyin: 'xiè xie', meaning: 'cảm ơn', example: '谢谢你的帮助。', translation: 'Cảm ơn sự giúp đỡ của bạn.'),
  ChineseWord(hanzi: '学习', pinyin: 'xué xí', meaning: 'học tập', example: '我每天学习中文。', translation: 'Tôi học tiếng Trung mỗi ngày.'),
  ChineseWord(hanzi: '朋友', pinyin: 'péng you', meaning: 'bạn bè', example: '他是我的好朋友。', translation: 'Anh ấy là bạn tốt của tôi.'),
  ChineseWord(hanzi: '喜欢', pinyin: 'xǐ huan', meaning: 'yêu thích', example: '我喜欢喝茶。', translation: 'Tôi thích uống trà.'),
  ChineseWord(hanzi: '再见', pinyin: 'zài jiàn', meaning: 'tạm biệt', example: '明天见，再见！', translation: 'Hẹn gặp ngày mai, tạm biệt!'),
];

const lessons = [
  Lesson(title: 'Chào hỏi cơ bản', subtitle: 'Làm quen và giới thiệu bản thân', level: 'HSK 1 · 8 phút', progress: 1, icon: '你', color: 0xFFE9F3ED),
  Lesson(title: 'Số đếm & thời gian', subtitle: 'Hỏi giờ, ngày và giá tiền', level: 'HSK 1 · 12 phút', progress: .65, icon: '时', color: 0xFFFFEEE2),
  Lesson(title: 'Gọi món ăn', subtitle: 'Giao tiếp tự nhiên tại nhà hàng', level: 'HSK 2 · 15 phút', progress: .2, icon: '吃', color: 0xFFE8EFFA),
  Lesson(title: 'Gia đình của tôi', subtitle: 'Giới thiệu các thành viên', level: 'HSK 2 · 14 phút', progress: 0, icon: '家', color: 0xFFF3E9F4),
  Lesson(title: 'Hỏi đường', subtitle: 'Phương hướng và di chuyển', level: 'HSK 2 · 18 phút', progress: 0, icon: '路', color: 0xFFFFF3D9),
];
