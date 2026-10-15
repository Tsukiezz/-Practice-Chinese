import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../services/web_navigation.dart';

/// Lazy-loaded editor: opening it never navigates or reloads the application.
class InlineAccount extends StatefulWidget {
  const InlineAccount(
      {super.key,
      required this.baseUrl,
      required this.token,
      this.onSaved,
      this.onPasswordChanged,
      this.client});
  final String baseUrl, token;
  final VoidCallback? onSaved, onPasswordChanged;
  final http.Client? client;
  @override
  State<InlineAccount> createState() => _InlineAccountState();
}

class _InlineAccountState extends State<InlineAccount>
    with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;
  final _form = GlobalKey<FormState>();
  final _passwordForm = GlobalKey<FormState>();
  final _name = TextEditingController(),
      _phone = TextEditingController(),
      _birth = TextEditingController(),
      _daily = TextEditingController(),
      _weekly = TextEditingController(),
      _old = TextEditingController(),
      _new = TextEditingController(),
      _confirm = TextEditingController();
  late final http.Client _client = widget.client ?? http.Client();
  bool _loading = false, _loaded = false, _busy = false;
  String _email = '', _avatar = '', _message = '';

  @override
  void dispose() {
    for (final c in [
      _name,
      _phone,
      _birth,
      _daily,
      _weekly,
      _old,
      _new,
      _confirm
    ]) {
      c.dispose();
    }
    if (widget.client == null) _client.close();
    super.dispose();
  }

  Future<Map<String, dynamic>> _request(String method, String path,
      [Map<String, dynamic>? body]) async {
    final request = http.Request(method, Uri.parse('${widget.baseUrl}$path'))
      ..headers.addAll({
        'Authorization': 'Bearer ${widget.token}',
        'Content-Type': 'application/json'
      });
    if (body != null) request.body = jsonEncode(body);
    final response = await http.Response.fromStream(
        await _client.send(request).timeout(const Duration(seconds: 25)));
    final data = response.body.isEmpty
        ? <String, dynamic>{}
        : jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    if (response.statusCode >= 400) {
      throw Exception(response.statusCode == 401
          ? 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.'
          : data['detail'] is String
              ? data['detail']
              : 'Thông tin chưa hợp lệ. Vui lòng kiểm tra lại.');
    }
    return data;
  }

  Future<void> _load() async {
    if (_loaded || _loading) return;
    setState(() {
      _loading = true;
      _message = '';
    });
    try {
      final data = await _request('GET', '/account');
      if (!mounted) return;
      _name.text = data['name'] ?? '';
      _phone.text = data['phone'] ?? '';
      _birth.text = data['birth_date'] ?? '';
      _daily.text = '${data['daily_goal'] ?? 1}';
      _weekly.text = '${data['weekly_goal'] ?? 5}';
      setState(() {
        _email = data['email'] ?? '';
        _avatar = data['avatar'] ?? '';
        _loaded = true;
      });
    } catch (e) {
      if (mounted) setState(() => _message = '$e');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _save({bool password = false}) async {
    if (_busy || !(password ? _passwordForm : _form).currentState!.validate()) {
      return;
    }
    setState(() {
      _busy = true;
      _message = '';
    });
    try {
      if (password) {
        await _request('POST', '/account/password',
            {'old_password': _old.text, 'new_password': _new.text});
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Đã đổi mật khẩu. Vui lòng đăng nhập lại.')));
        widget.onPasswordChanged?.call();
      } else {
        await _request('PUT', '/account', {
          'name': _name.text.trim(),
          'phone': _phone.text.trim(),
          'birth_date': _birth.text,
          'avatar': _avatar,
          'daily_goal': int.parse(_daily.text),
          'weekly_goal': int.parse(_weekly.text),
        });
        if (!mounted) return;
        setState(() => _message = 'Đã lưu thông tin cá nhân.');
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Đã lưu thông tin cá nhân.')));
        widget.onSaved?.call();
      }
    } catch (e) {
      if (mounted) setState(() => _message = '$e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Widget _field(TextEditingController controller, String label,
          {bool password = false, int? max, int? goal}) =>
      Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: TextFormField(
          controller: controller,
          enabled: !_busy,
          obscureText: password,
          maxLength: max,
          keyboardType: goal != null ? TextInputType.number : null,
          decoration: InputDecoration(
              labelText: label, border: const OutlineInputBorder()),
          validator: (v) {
            final value = v ?? '';
            if (controller == _name && value.trim().isEmpty) {
              return 'Vui lòng nhập họ tên.';
            }
            if (goal != null &&
                (int.tryParse(value) == null ||
                    int.parse(value) < 1 ||
                    int.parse(value) > goal)) {
              return 'Nhập số từ 1 đến $goal.';
            }
            if (password && value.isEmpty) return 'Vui lòng nhập mật khẩu.';
            if (controller == _new && value.length < 8) {
              return 'Mật khẩu cần ít nhất 8 ký tự.';
            }
            if (controller == _confirm && value != _new.text) {
              return 'Mật khẩu chưa khớp.';
            }
            return null;
          },
        ),
      );

  @override
  Widget build(BuildContext context) {
    super.build(context);
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      child: ExpansionTile(
        maintainState: true,
        leading: const Icon(Icons.manage_accounts_outlined),
        title: const Text('Thông tin cá nhân'),
        subtitle: const Text('Đổi tên, ảnh đại diện và mật khẩu'),
        onExpansionChanged: (open) {
          if (open) _load();
        },
        childrenPadding: const EdgeInsets.all(16),
        children: [
          if (_loading) const LinearProgressIndicator(),
          if (_message.isNotEmpty)
            Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Text(_message, key: const Key('account-message'))),
          if (!_loaded && !_loading)
            TextButton(onPressed: _load, child: const Text('Tải thông tin')),
          if (_loaded) ...[
            Form(
                key: _form,
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(_email),
                      const SizedBox(height: 12),
                      if (_avatar.isNotEmpty)
                        Center(
                            child: ClipOval(
                                child: _avatar.startsWith('data:')
                                    ? Image.memory(
                                        base64Decode(_avatar.split(',').last),
                                        width: 72,
                                        height: 72,
                                        fit: BoxFit.cover,
                                        errorBuilder: (_, __, ___) =>
                                            const Icon(Icons.person))
                                    : Image.network(_avatar,
                                        width: 72,
                                        height: 72,
                                        fit: BoxFit.cover,
                                        errorBuilder: (_, __, ___) =>
                                            const Icon(Icons.person)))),
                      Wrap(spacing: 8, children: [
                        TextButton.icon(
                            onPressed: _busy
                                ? null
                                : () async {
                                    try {
                                      final image = await pickAccountAvatar();
                                      if (mounted && image != null) {
                                        setState(() => _avatar = image);
                                      }
                                    } catch (_) {
                                      if (mounted) {
                                        setState(() => _message =
                                            'Chọn ảnh PNG, JPEG hoặc WebP tối đa 5MB.');
                                      }
                                    }
                                  },
                            icon: const Icon(Icons.photo_outlined),
                            label: const Text('Chọn ảnh')),
                        TextButton(
                            onPressed: _busy
                                ? null
                                : () => setState(() => _avatar = ''),
                            child: const Text('Xóa ảnh')),
                      ]),
                      _field(_name, 'Họ tên', max: 120),
                      _field(_phone, 'Số điện thoại', max: 25),
                      TextFormField(
                          controller: _birth,
                          readOnly: true,
                          decoration: InputDecoration(
                              labelText: 'Ngày sinh',
                              border: const OutlineInputBorder(),
                              suffixIcon: IconButton(
                                  onPressed:
                                      _busy ? null : () => _birth.clear(),
                                  icon: const Icon(Icons.clear))),
                          onTap: _busy
                              ? null
                              : () async {
                                  final now = DateTime.now();
                                  final date = await showDatePicker(
                                      context: context,
                                      initialDate:
                                          DateTime.tryParse(_birth.text) ??
                                              DateTime(now.year - 18),
                                      firstDate: DateTime(1900),
                                      lastDate: now);
                                  if (date != null && mounted) {
                                    _birth.text =
                                        date.toIso8601String().split('T').first;
                                  }
                                }),
                      const SizedBox(height: 12),
                      _field(_daily, 'Mục tiêu bài mỗi ngày', goal: 50),
                      _field(_weekly, 'Mục tiêu bài mỗi tuần', goal: 350),
                      FilledButton(
                          onPressed: _busy ? null : _save,
                          child: Text(_busy ? 'Đang lưu…' : 'Lưu thay đổi')),
                    ])),
            ExpansionTile(title: const Text('Đổi mật khẩu'), children: [
              const Text(
                  'Sau khi đổi mật khẩu, bạn cần đăng nhập lại trên các thiết bị.'),
              const SizedBox(height: 12),
              Form(
                  key: _passwordForm,
                  child: Column(children: [
                    _field(_old, 'Mật khẩu cũ', password: true, max: 128),
                    _field(_new, 'Mật khẩu mới', password: true, max: 128),
                    _field(_confirm, 'Nhập lại mật khẩu mới',
                        password: true, max: 128),
                    FilledButton(
                        onPressed: _busy ? null : () => _save(password: true),
                        child: const Text('Lưu mật khẩu')),
                  ])),
            ]),
          ],
        ],
      ),
    );
  }
}
