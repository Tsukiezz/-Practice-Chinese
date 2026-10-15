import 'package:flutter/material.dart';
import '../services/web_navigation.dart';

class InlineInstall extends StatefulWidget {
  const InlineInstall({super.key});
  @override
  State<InlineInstall> createState() => _InlineInstallState();
}

class _InlineInstallState extends State<InlineInstall> {
  bool _busy = false;
  String _status = '';
  @override
  Widget build(BuildContext context) => Card(
        margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
        child: ExpansionTile(
          leading: const Icon(Icons.install_mobile_rounded),
          title: const Text('Cài HanziGo trên Android / iOS'),
          childrenPadding: const EdgeInsets.all(16),
          children: [
            const Text(
                'Cài miễn phí lên màn hình chính, dùng tài khoản hiện có để tiếp tục học.'),
            const SizedBox(height: 12),
            FilledButton.icon(
                onPressed: _busy
                    ? null
                    : () async {
                        setState(() => _busy = true);
                        try {
                          final message = await installHanziGo();
                          if (mounted) setState(() => _status = message);
                        } catch (_) {
                          if (mounted) {
                            setState(() => _status =
                                'Hãy làm theo hướng dẫn bên dưới để cài từ trình duyệt.');
                          }
                        } finally {
                          if (mounted) setState(() => _busy = false);
                        }
                      },
                icon: const Icon(Icons.download_outlined),
                label: const Text('Cài HanziGo')),
            if (_status.isNotEmpty)
              Padding(padding: const EdgeInsets.all(12), child: Text(_status)),
            const ExpansionTile(
                title: Text('iPhone / iPad · Safari'),
                childrenPadding: EdgeInsets.all(12),
                children: [
                  Text(
                      '1. Mở HanziGo bằng Safari (không dùng trình duyệt trong Zalo/Facebook).\n\n'
                      '2. Nhấn Chia sẻ (ô vuông có mũi tên lên); nếu chưa thấy, mở menu … → Chia sẻ.\n\n'
                      '3. Chọn Thêm vào Màn hình chính. Bật Mở dưới dạng ứng dụng web nếu có, rồi nhấn Thêm.\n\n'
                      '4. Mở biểu tượng HanziGo trên màn hình chính. Safari yêu cầu bạn tự xác nhận, không cần App Store.')
                ]),
            const ExpansionTile(
                title: Text('Android · Google Chrome'),
                childrenPadding: EdgeInsets.all(12),
                children: [
                  Text('1. Mở HanziGo bằng Google Chrome.\n\n'
                      '2. Nhấn Cài HanziGo ở trên, hoặc menu ⋮ → Thêm vào màn hình chính → Cài đặt (có máy hiện Cài ứng dụng).\n\n'
                      '3. Xác nhận và mở biểu tượng HanziGo. Nếu chỉ có Tạo lối tắt, bạn vẫn có thể dùng để mở nhanh. Không cần APK.')
                ]),
            const SizedBox(height: 12),
            const Text(
                'Cần Internet để đồng bộ và dùng AI. Cài đặt không tự mở khóa Premium. Khi luyện đọc, cho phép micro nếu được hỏi.'),
          ],
        ),
      );
}
