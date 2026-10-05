import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/benefits_service.dart';

class AppearanceScreen extends StatelessWidget {
  const AppearanceScreen({super.key});
  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: Listenable.merge([ThemeManager.palette, ThemeManager.themeMode, BenefitsService.instance]),
    builder: (context, _) => Scaffold(
      appBar: AppBar(title: const Text('Màu giao diện')),
      body: ListView(padding: const EdgeInsets.all(20), children: [
        SwitchListTile(
          title: const Text('Bật màu đã chọn / Dark mode'),
          subtitle: const Text('Tắt để trở về nền trắng. Trang đăng nhập giữ màu mặc định.'),
          value: ThemeManager.isDark,
          onChanged: (_) => ThemeManager.toggle(),
        ),
        const SizedBox(height: 16),
        if (!BenefitsService.instance.isPremium)
          const ListTile(leading: Icon(Icons.lock_outline), title: Text('Màu tùy chọn dành cho Premium'),
            subtitle: Text('Tài khoản miễn phí vẫn dùng được giao diện mặc định sáng / tối.')),
        ListTile(leading: const Icon(Icons.shield_outlined), title: Text('Bảo lưu còn lại: ${BenefitsService.instance.freezes}/3 lượt tháng này'),
          subtitle: const Text('Premium tự bảo lưu ngày bỏ lỡ, tối đa 3 ngày/tháng theo giờ Việt Nam. Không cộng dồn.')),
        for (final palette in InterfacePalette.values)
          Card(child: ListTile(
            key: Key('palette-${palette.name}'),
            leading: CircleAvatar(backgroundColor: palette.seed),
            title: Text(palette.label),
            trailing: !BenefitsService.instance.isPremium && palette != InterfacePalette.dark
                ? const Icon(Icons.lock_outline)
                : ThemeManager.palette.value == palette ? const Icon(Icons.check_circle) : null,
            onTap: () async {
              try {
                await BenefitsService.instance.select(palette: palette);
                if (!ThemeManager.isDark) await ThemeManager.toggle();
              } catch (e) {
                if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
              }
            },
          )),
      ]),
    ),
  );
}
