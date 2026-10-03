import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import '../services/auth_service.dart';

class HanziGoPremiumCard extends StatelessWidget {
  const HanziGoPremiumCard({
    super.key,
    required this.user,
    required this.token,
    required this.apiBaseUrl,
    this.onUserUpdated,
    this.margin,
  });

  final AuthUser? user;
  final String? token;
  final String apiBaseUrl;
  final VoidCallback? onUserUpdated;
  final EdgeInsetsGeometry? margin;

  bool get _isVip => user?.isVip ?? false;

  String _formatDate(int timestamp) {
    if (timestamp <= 0) return '';
    final dt = DateTime.fromMillisecondsSinceEpoch(timestamp * 1000);
    return '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year}';
  }

  int get _daysRemaining {
    if (!_isVip || (user?.premiumUntil ?? 0) <= 0) return 0;
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    final diff = (user!.premiumUntil - now) ~/ 86400;
    return diff > 0 ? diff : 0;
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      margin: margin ?? const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        gradient: LinearGradient(
          colors: _isVip
              ? [const Color(0xFF1E3A2F), const Color(0xFF132A22)]
              : (isDark
                  ? [const Color(0xFF2C2216), const Color(0xFF1E170F)]
                  : [const Color(0xFFFFFDF5), const Color(0xFFF9F3DF)]),
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        border: Border.all(
          color: _isVip ? const Color(0xFFFFD700) : const Color(0xFFE5C158),
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFFFFD700).withValues(alpha: _isVip ? 0.2 : 0.1),
            blurRadius: 16,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFD700).withValues(alpha: 0.2),
                    shape: BoxShape.circle,
                  ),
                  child: const Text('👑', style: TextStyle(fontSize: 24)),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 10, vertical: 3),
                            decoration: BoxDecoration(
                              color: _isVip
                                  ? const Color(0xFFFFD700)
                                  : const Color(0xFF8FA69C),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              _isVip
                                  ? '👑 HỘI VIÊN HANZI GO PREMIUM'
                                  : 'HỘI VIÊN THƯỜNG',
                              style: TextStyle(
                                fontSize: 10.5,
                                fontWeight: FontWeight.w900,
                                color: _isVip
                                    ? const Color(0xFF153E35)
                                    : Colors.white,
                                letterSpacing: 0.5,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(
                        _isVip
                            ? 'HanziGo Premium (Đang hoạt động)'
                            : 'Nâng cấp HanziGo Premium',
                        style: TextStyle(
                          fontSize: 17,
                          fontWeight: FontWeight.w800,
                          color: _isVip
                              ? Colors.white
                              : (isDark ? Colors.white : const Color(0xFF1E2824)),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _isVip
                            ? 'Hạn dùng: ${_formatDate(user!.premiumUntil)} (còn $_daysRemaining ngày) · 🛡️ ${user?.streakFreezes ?? 0} lượt Streak Freeze'
                            : 'Chỉ từ 49.000đ/tháng · Mở khóa không giới hạn AI tạo đề, cọ viết, trọn bộ HSK 1–9 & huy hiệu mạ vàng',
                        style: TextStyle(
                          fontSize: 12.5,
                          height: 1.4,
                          color: _isVip
                              ? const Color(0xFFFFD700)
                              : (isDark
                                  ? const Color(0xFFD4BDB0)
                                  : const Color(0xFF6B5843)),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            // Two clearly separated actions as required
            Row(
              children: [
                Expanded(
                  flex: 3,
                  child: FilledButton.icon(
                    onPressed: () => _openVipSubscribeDialog(context),
                    icon: const Text('👑', style: TextStyle(fontSize: 16)),
                    label: Text(
                      _isVip ? 'Gia hạn gói VIP' : 'Đăng ký Hội viên VIP',
                      style: const TextStyle(
                        fontWeight: FontWeight.w800,
                        fontSize: 13,
                        color: Color(0xFF153E35),
                      ),
                    ),
                    style: FilledButton.styleFrom(
                      backgroundColor: const Color(0xFFFFD700),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      elevation: 0,
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  flex: 2,
                  child: OutlinedButton.icon(
                    onPressed: () => _openVoucherDialog(context),
                    icon: const Icon(Icons.confirmation_number_outlined, size: 16),
                    label: const Text(
                      'Nhập mã',
                      style: TextStyle(
                        fontWeight: FontWeight.w700,
                        fontSize: 13,
                      ),
                    ),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: _isVip
                          ? Colors.white
                          : (isDark ? Colors.white : const Color(0xFF1E2824)),
                      side: BorderSide(
                        color: _isVip
                            ? Colors.white54
                            : (isDark ? Colors.white38 : const Color(0xFFB59A52)),
                        width: 1.2,
                      ),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  void _openVipSubscribeDialog(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (sheetContext) => _VipSubscribeSheet(
        apiBaseUrl: apiBaseUrl,
        token: token,
        onSuccess: () {
          Navigator.pop(sheetContext);
          onUserUpdated?.call();
        },
      ),
    );
  }

  void _openVoucherDialog(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (sheetContext) => _VoucherRedeemSheet(
        apiBaseUrl: apiBaseUrl,
        token: token,
        onSuccess: () {
          Navigator.pop(sheetContext);
          onUserUpdated?.call();
        },
        onApplyDiscount: (voucherCode, discountPercent) {
          Navigator.pop(sheetContext);
          // Open subscribe sheet with voucher applied
          showModalBottomSheet(
            context: context,
            isScrollControlled: true,
            backgroundColor: Colors.transparent,
            builder: (ctx) => _VipSubscribeSheet(
              apiBaseUrl: apiBaseUrl,
              token: token,
              initialVoucherCode: voucherCode,
              onSuccess: () {
                Navigator.pop(ctx);
                onUserUpdated?.call();
              },
            ),
          );
        },
      ),
    );
  }
}

// ==========================================
// Sheet 1: Đăng ký Hội viên VIP & Bảng So Sánh
// ==========================================
class _VipSubscribeSheet extends StatefulWidget {
  const _VipSubscribeSheet({
    required this.apiBaseUrl,
    required this.token,
    required this.onSuccess,
    this.initialVoucherCode,
  });

  final String apiBaseUrl;
  final String? token;
  final VoidCallback onSuccess;
  final String? initialVoucherCode;

  @override
  State<_VipSubscribeSheet> createState() => _VipSubscribeSheetState();
}

class _VipSubscribeSheetState extends State<_VipSubscribeSheet> {
  String _selectedPlan = '1_month';
  bool _isLoading = false;
  String? _voucherCode;

  @override
  void initState() {
    super.initState();
    _voucherCode = widget.initialVoucherCode;
  }

  Future<void> _createOrderAndPay() async {
    setState(() => _isLoading = true);
    try {
      final res = await http.post(
        Uri.parse('${widget.apiBaseUrl}/premium/orders'),
        headers: {
          'Content-Type': 'application/json',
          if (widget.token != null) 'Authorization': 'Bearer ${widget.token}',
        },
        body: jsonEncode({
          'plan_type': _selectedPlan,
          if (_voucherCode != null && _voucherCode!.isNotEmpty)
            'voucher_code': _voucherCode,
        }),
      );

      if (!mounted) return;
      setState(() => _isLoading = false);

      if (res.statusCode == 201) {
        final orderData = jsonDecode(res.body) as Map<String, dynamic>;
        _showPaymentQrDialog(orderData);
      } else {
        final err = jsonDecode(res.body);
        _showSnack(err['detail'] ?? 'Không thể tạo đơn hàng');
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        _showSnack('Lỗi kết nối: $e');
      }
    }
  }

  void _showSnack(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), behavior: SnackBarBehavior.floating),
    );
  }

  void _showPaymentQrDialog(Map<String, dynamic> order) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (dlgContext) => _PaymentQrDialog(
        order: order,
        apiBaseUrl: widget.apiBaseUrl,
        token: widget.token,
        onSuccess: () {
          Navigator.pop(dlgContext);
          widget.onSuccess();
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF1B2823) : Colors.white,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: EdgeInsets.only(
        top: 20,
        left: 20,
        right: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.9,
      ),
      child: ListView(
        shrinkWrap: true,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Row(
                children: [
                  Text('👑', style: TextStyle(fontSize: 22)),
                  SizedBox(width: 8),
                  Text(
                    'Đăng ký HanziGo Premium',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                  ),
                ],
              ),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: () => Navigator.pop(context),
              ),
            ],
          ),
          const SizedBox(height: 8),
          const Text(
            'Bảng so sánh quyền lợi HanziGo Miễn phí & HanziGo Premium:',
            style: TextStyle(fontSize: 13, color: Colors.grey),
          ),
          const SizedBox(height: 12),
          // Comparison Table from user uploaded screenshot
          Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: Colors.grey.withValues(alpha: 0.25)),
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(14),
              child: Table(
                columnWidths: const {
                  0: FlexColumnWidth(1.4),
                  1: FlexColumnWidth(1.1),
                  2: FlexColumnWidth(1.3),
                },
                border: TableBorder(
                  horizontalInside: BorderSide(
                    color: Colors.grey.withValues(alpha: 0.2),
                  ),
                  verticalInside: BorderSide(
                    color: Colors.grey.withValues(alpha: 0.2),
                  ),
                ),
                children: [
                  TableRow(
                    decoration: BoxDecoration(
                      color: isDark ? const Color(0xFF24332D) : const Color(0xFFF4F7F5),
                    ),
                    children: const [
                      Padding(
                        padding: EdgeInsets.all(8),
                        child: Text(
                          'Tính năng chi tiết',
                          style: TextStyle(fontWeight: FontWeight.w800, fontSize: 11),
                        ),
                      ),
                      Padding(
                        padding: EdgeInsets.all(8),
                        child: Text(
                          'Miễn phí',
                          textAlign: TextAlign.center,
                          style: TextStyle(fontWeight: FontWeight.w800, fontSize: 11),
                        ),
                      ),
                      Padding(
                        padding: EdgeInsets.all(8),
                        child: Text(
                          '👑 Premium',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontWeight: FontWeight.w800,
                            fontSize: 11,
                            color: Color(0xFFB06000),
                          ),
                        ),
                      ),
                    ],
                  ),
                  _buildTableRow('AI tạo đề thi', '❌ 3 đề / ngày', '🌟 Không giới hạn'),
                  _buildTableRow('Tùy biến đầu cọ', '❌ Cọ mặc định', '🌟 Mở khóa toàn bộ'),
                  _buildTableRow('Lộ trình HSK 1-9 & Giao tiếp', '❌ Chỉ HSK 1–6', '🌟 Trọn bộ HSK 1–9'),
                  _buildTableRow('Giao diện màu sắc', '❌ Không có', '🌟 Tất cả màu'),
                  _buildTableRow('Streak Freeze (Bảo lưu chuỗi)', '❌ Mất chuỗi', '🌟 Tặng 3 lượt / tháng'),
                  _buildTableRow('Huy hiệu & Khung đại diện', '❌ Thường', '🌟 Mạ vàng VIP'),
                ],
              ),
            ),
          ),
          const SizedBox(height: 18),
          const Text(
            'Chọn gói hội viên phù hợp:',
            style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: _buildPlanCard(
                  id: '1_month',
                  title: 'Gói 1 Tháng',
                  price: '49.000đ',
                  subtitle: 'Thanh toán theo tháng',
                  isGold: false,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _buildPlanCard(
                  id: '1_year',
                  title: 'Gói 1 Năm',
                  price: '490.000đ',
                  subtitle: 'Chỉ ~40.8k/tháng',
                  badge: 'TIẾT KIỆM 2 THÁNG ⭐',
                  isGold: true,
                ),
              ),
            ],
          ),
          if (_voucherCode != null) ...[
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: const Color(0xFFE8F4ED),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Row(
                children: [
                  const Icon(Icons.check_circle, size: 16, color: Color(0xFF137333)),
                  const SizedBox(width: 8),
                  Text(
                    'Đang áp dụng mã giảm giá: $_voucherCode',
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      color: Color(0xFF137333),
                    ),
                  ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 20),
          FilledButton.icon(
            onPressed: _isLoading ? null : _createOrderAndPay,
            icon: _isLoading
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.qr_code_scanner_rounded),
            label: Text(
              _isLoading ? 'Đang xử lý…' : 'Chuyển khoản VietQR SePay tự động',
              style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15),
            ),
            style: FilledButton.styleFrom(
              backgroundColor: const Color(0xFF153E35),
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            ),
          ),
        ],
      ),
    );
  }

  TableRow _buildTableRow(String feature, String free, String prem) {
    return TableRow(
      children: [
        Padding(
          padding: const EdgeInsets.all(8),
          child: Text(feature, style: const TextStyle(fontSize: 11)),
        ),
        Padding(
          padding: const EdgeInsets.all(8),
          child: Text(
            free,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 11, color: Color(0xFFC5221F)),
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(8),
          child: Text(
            prem,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w800,
              color: Color(0xFF137333),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildPlanCard({
    required String id,
    required String title,
    required String price,
    required String subtitle,
    String? badge,
    bool isGold = false,
  }) {
    final isSelected = _selectedPlan == id;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return InkWell(
      onTap: () => setState(() => _selectedPlan = id),
      borderRadius: BorderRadius.circular(14),
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: isSelected
                  ? (isGold
                      ? const Color(0xFFFFD700).withValues(alpha: 0.15)
                      : const Color(0xFF153E35).withValues(alpha: 0.1))
                  : (isDark ? const Color(0xFF24332D) : const Color(0xFFFAFAFA)),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                color: isSelected
                    ? (isGold ? const Color(0xFFFFD700) : const Color(0xFF153E35))
                    : Colors.grey.withValues(alpha: 0.3),
                width: isSelected ? 2 : 1,
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      title,
                      style: TextStyle(
                        fontWeight: FontWeight.w800,
                        fontSize: 13,
                        color: isSelected
                            ? (isGold ? const Color(0xFFB06000) : const Color(0xFF153E35))
                            : Colors.grey,
                      ),
                    ),
                    Icon(
                      isSelected ? Icons.check_circle : Icons.radio_button_unchecked,
                      size: 18,
                      color: isSelected ? const Color(0xFF153E35) : Colors.grey,
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  price,
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w900,
                    color: isGold ? const Color(0xFFB06000) : const Color(0xFF153E35),
                  ),
                ),
                Text(subtitle, style: const TextStyle(fontSize: 11, color: Colors.grey)),
              ],
            ),
          ),
          if (badge != null)
            Positioned(
              top: -8,
              right: 8,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: const Color(0xFFFFD700),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  badge,
                  style: const TextStyle(
                    fontSize: 8.5,
                    fontWeight: FontWeight.w900,
                    color: Color(0xFF153E35),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

// ==========================================
// Dialog: Hiển thị VietQR SePay & Polling
// ==========================================
class _PaymentQrDialog extends StatefulWidget {
  const _PaymentQrDialog({
    required this.order,
    required this.apiBaseUrl,
    required this.token,
    required this.onSuccess,
  });

  final Map<String, dynamic> order;
  final String apiBaseUrl;
  final String? token;
  final VoidCallback onSuccess;

  @override
  State<_PaymentQrDialog> createState() => _PaymentQrDialogState();
}

class _PaymentQrDialogState extends State<_PaymentQrDialog> {
  Timer? _pollingTimer;
  Timer? _countdownTimer;
  int _secondsRemaining = 300;
  bool _isCompleted = false;
  bool _isExpired = false;

  @override
  void initState() {
    super.initState();
    final exp = widget.order['expires_in'];
    if (exp is int && exp > 0) {
      _secondsRemaining = exp;
    }
    _startCountdown();
    _startPolling();
  }

  void _startCountdown() {
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_secondsRemaining > 1) {
        if (mounted) setState(() => _secondsRemaining--);
      } else {
        timer.cancel();
        _pollingTimer?.cancel();
        if (mounted) setState(() => _isExpired = true);
      }
    });
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    _pollingTimer?.cancel();
    super.dispose();
  }

  void _startPolling() {
    _pollingTimer = Timer.periodic(const Duration(seconds: 2), (timer) async {
      try {
        final orderCode = widget.order['order_code'];
        final res = await http.get(
          Uri.parse('${widget.apiBaseUrl}/premium/orders/$orderCode/status'),
          headers: {
            if (widget.token != null) 'Authorization': 'Bearer ${widget.token}',
          },
        );

        if (res.statusCode == 200) {
          final data = jsonDecode(res.body) as Map<String, dynamic>;
          if (data['is_completed'] == true) {
            timer.cancel();
            _countdownTimer?.cancel();
            if (mounted) {
              setState(() => _isCompleted = true);
              Future.delayed(const Duration(seconds: 2), () {
                if (mounted) widget.onSuccess();
              });
            }
          } else if (data['is_expired'] == true || data['status'] == 'expired') {
            timer.cancel();
            _countdownTimer?.cancel();
            if (mounted) setState(() => _isExpired = true);
          }
        } else if (res.statusCode == 404) {
          timer.cancel();
          _countdownTimer?.cancel();
          if (mounted) setState(() => _isExpired = true);
        }
      } catch (_) {}
    });
  }

  void _copyToClipboard(String text, String label) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Đã sao chép $label!'), duration: const Duration(seconds: 2)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final order = widget.order;
    final orderCode = order['order_code'] ?? '';
    final amount = NumberFormatCompact(order['amount'] ?? 0);

    return AlertDialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      title: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          const Text('Quét mã VietQR SePay', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
          IconButton(
            icon: const Icon(Icons.close),
            onPressed: () => Navigator.pop(context),
          ),
        ],
      ),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (_isCompleted) ...[
              const Icon(Icons.celebration, color: Color(0xFFFFD700), size: 64),
              const SizedBox(height: 12),
              const Text(
                '🎉 THANH TOÁN THÀNH CÔNG!',
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900, color: Color(0xFF137333)),
              ),
              const SizedBox(height: 6),
              const Text(
                'Chúc mừng bạn đã là Hội viên HanziGo Premium!\nTất cả đặc quyền VIP đã được kích hoạt.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 13),
              ),
            ] else if (_isExpired) ...[
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFFFDE8E8),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFFF98080)),
                ),
                child: Column(
                  children: [
                    const Icon(Icons.timer_off_rounded, color: Color(0xFFC81E1E), size: 48),
                    const SizedBox(height: 10),
                    const Text(
                      'Đơn hàng đã hết hạn (Quá 5 phút)',
                      style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16, color: Color(0xFF9B1C1C)),
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      'Dữ liệu đơn hàng chờ đã được tự động hủy sau 5 phút để bảo vệ bạn. Vui lòng tạo mã QR mới để thanh toán.',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 13, color: Color(0xFF771D1D)),
                    ),
                    const SizedBox(height: 14),
                    FilledButton.icon(
                      onPressed: () => Navigator.pop(context),
                      style: FilledButton.styleFrom(backgroundColor: const Color(0xFF153E35)),
                      icon: const Icon(Icons.refresh_rounded),
                      label: const Text('Đóng & Tạo đơn mới'),
                    ),
                  ],
                ),
              ),
            ] else ...[
              if (order['qr_url'] != null)
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFFC7DCCE), width: 1.5),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.05),
                        blurRadius: 10,
                        offset: const Offset(0, 3),
                      ),
                    ],
                  ),
                  child: Image.network(
                    order['qr_url'],
                    width: 220,
                    height: 220,
                    fit: BoxFit.contain,
                    errorBuilder: (_, __, ___) => const Icon(Icons.qr_code, size: 100),
                  ),
                ),
              Container(
                margin: const EdgeInsets.only(top: 10),
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFFFFF7DB),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFFFFD700)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.timer_outlined, size: 15, color: Color(0xFF946200)),
                    const SizedBox(width: 5),
                    Text(
                      'Thời gian giữ đơn: ${(_secondsRemaining ~/ 60).toString().padLeft(2, '0')}:${(_secondsRemaining % 60).toString().padLeft(2, '0')} (Tự hủy sau 5p)',
                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: Color(0xFF946200)),
                    ),
                  ],
                ),
              ),
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: Text(
                  '💡 Bạn có thể quét mã QR bằng ACB, MB, VCB... hoặc vào app ngân hàng chuyển khoản nhanh 24/7 theo thông tin dưới đây (hệ thống tự động kích hoạt sau 1-2 giây):',
                  style: TextStyle(fontSize: 11.5, color: Colors.grey.shade700, height: 1.35),
                  textAlign: TextAlign.center,
                ),
              ),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFFF4FBF7),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFFC7DCCE)),
                ),
                child: Column(
                  children: [
                    _infoRow('Ngân hàng:', order['bank_name'] ?? 'ACB'),
                    _infoRow(
                      'Số tài khoản:',
                      order['bank_account'] ?? '',
                      copyable: true,
                    ),
                    _infoRow('Chủ tài khoản:', order['account_holder'] ?? ''),
                    _infoRow('Số tiền:', '$amount đ', isHighlight: true),
                    const Divider(height: 14),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Nội dung CK:',
                          style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800),
                        ),
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(color: const Color(0xFF153E35)),
                              ),
                              child: Text(
                                orderCode,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w900,
                                  color: Color(0xFF153E35),
                                ),
                              ),
                            ),
                            IconButton(
                              icon: const Icon(Icons.copy, size: 16),
                              onPressed: () => _copyToClipboard(orderCode, 'Nội dung chuyển khoản'),
                              tooltip: 'Sao chép',
                            ),
                          ],
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  SizedBox(
                    width: 14,
                    height: 14,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFFB06000)),
                  ),
                  SizedBox(width: 8),
                  Text(
                    'Đang chờ nhận chuyển khoản qua SePay…',
                    style: TextStyle(fontSize: 12, color: Color(0xFFB06000), fontWeight: FontWeight.w600),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }


  Widget _infoRow(String label, String value, {bool copyable = false, bool isHighlight = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
          Row(
            children: [
              Text(
                value,
                style: TextStyle(
                  fontSize: 12.5,
                  fontWeight: isHighlight ? FontWeight.w900 : FontWeight.w700,
                  color: isHighlight ? const Color(0xFFC5221F) : const Color(0xFF153E35),
                ),
              ),
              if (copyable)
                IconButton(
                  icon: const Icon(Icons.copy, size: 14),
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                  onPressed: () => _copyToClipboard(value, label),
                ),
            ],
          ),
        ],
      ),
    );
  }

  static String NumberFormatCompact(dynamic num) {
    return NumberFormat_currency(num);
  }

  static String NumberFormat_currency(dynamic value) {
    final n = int.tryParse(value.toString()) ?? 0;
    return n.toString().replaceAllMapped(
      RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
      (Match m) => '${m[1]}.',
    );
  }
}

// ==========================================
// Sheet 2: Nhập mã Voucher (Giảm % hoặc 1 tháng free)
// ==========================================
class _VoucherRedeemSheet extends StatefulWidget {
  const _VoucherRedeemSheet({
    required this.apiBaseUrl,
    required this.token,
    required this.onSuccess,
    required this.onApplyDiscount,
  });

  final String apiBaseUrl;
  final String? token;
  final VoidCallback onSuccess;
  final void Function(String voucherCode, int discountPercent) onApplyDiscount;

  @override
  State<_VoucherRedeemSheet> createState() => _VoucherRedeemSheetState();
}

class _VoucherRedeemSheetState extends State<_VoucherRedeemSheet> {
  final _codeController = TextEditingController();
  bool _isLoading = false;
  String? _message;
  bool _isSuccess = false;

  Future<void> _redeem() async {
    final code = _codeController.text.trim().toUpperCase();
    if (code.isEmpty) return;

    setState(() {
      _isLoading = true;
      _message = null;
    });

    try {
      final res = await http.post(
        Uri.parse('${widget.apiBaseUrl}/premium/redeem-voucher'),
        headers: {
          'Content-Type': 'application/json',
          if (widget.token != null) 'Authorization': 'Bearer ${widget.token}',
        },
        body: jsonEncode({'code': code}),
      );

      final data = jsonDecode(res.body) as Map<String, dynamic>;
      if (!mounted) return;
      setState(() => _isLoading = false);

      if (res.statusCode == 200) {
        if (data['type'] == 'free_month') {
          setState(() {
            _isSuccess = true;
            _message = '🎉 Chúc mừng! Bạn đã nhận thành công 1 tháng HanziGo Premium miễn phí!';
          });
          Future.delayed(const Duration(seconds: 2), () {
            if (mounted) widget.onSuccess();
          });
        } else {
          // Discount voucher
          final discount = data['discount_percent'] ?? 0;
          setState(() {
            _isSuccess = true;
            _message = 'Mã hợp lệ! Bạn được giảm $discount% cho gói 1 tháng HanziGo Premium.';
          });
          Future.delayed(const Duration(seconds: 1), () {
            if (mounted) widget.onApplyDiscount(code, discount);
          });
        }
      } else {
        setState(() {
          _isSuccess = false;
          _message = data['detail'] ?? 'Mã voucher không hợp lệ';
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _isSuccess = false;
          _message = 'Lỗi kết nối: $e';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF1B2823) : Colors.white,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: EdgeInsets.only(
        top: 20,
        left: 20,
        right: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Row(
                children: [
                  Text('🎟️', style: TextStyle(fontSize: 22)),
                  SizedBox(width: 8),
                  Text(
                    'Nhập mã Voucher VIP',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                  ),
                ],
              ),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: () => Navigator.pop(context),
              ),
            ],
          ),
          const SizedBox(height: 8),
          const Text(
            'Nhập mã giảm giá (%) hoặc mã 1 tháng miễn phí do Quản trị viên cấp hoặc AI tặng thưởng khi đạt 100 điểm:',
            style: TextStyle(fontSize: 13, color: Colors.grey),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _codeController,
            textCapitalization: TextCapitalization.characters,
            style: const TextStyle(fontWeight: FontWeight.w800, letterSpacing: 1),
            decoration: InputDecoration(
              hintText: 'Ví dụ: HZG8392019482 hoặc VIP2026...',
              prefixIcon: const Icon(Icons.discount_outlined),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              filled: true,
              fillColor: isDark ? const Color(0xFF24332D) : const Color(0xFFF9FBF9),
            ),
          ),
          if (_message != null) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: _isSuccess
                    ? const Color(0xFFE8F4ED)
                    : const Color(0xFFFCE8E6),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Row(
                children: [
                  Icon(
                    _isSuccess ? Icons.check_circle : Icons.error_outline,
                    size: 18,
                    color: _isSuccess ? const Color(0xFF137333) : const Color(0xFFC5221F),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _message!,
                      style: TextStyle(
                        fontSize: 12.5,
                        fontWeight: FontWeight.w700,
                        color: _isSuccess ? const Color(0xFF137333) : const Color(0xFFC5221F),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 18),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              onPressed: _isLoading ? null : _redeem,
              style: FilledButton.styleFrom(
                backgroundColor: const Color(0xFF153E35),
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: _isLoading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Text(
                      'Áp dụng mã Voucher',
                      style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15),
                    ),
            ),
          ),
        ],
      ),
    );
  }
}
