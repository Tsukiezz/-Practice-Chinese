import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class AppearanceScreen extends StatelessWidget {
  const AppearanceScreen({super.key});
  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: Listenable.merge([ThemeManager.palette, ThemeManager.themeMode]),
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
        for (final palette in InterfacePalette.values)
          Card(child: ListTile(
            key: Key('palette-${palette.name}'),
            leading: CircleAvatar(backgroundColor: palette.seed),
            title: Text(palette.label),
            trailing: ThemeManager.palette.value == palette ? const Icon(Icons.check_circle) : null,
            onTap: () => ThemeManager.selectPalette(palette),
          )),
      ]),
    ),
  );
}
