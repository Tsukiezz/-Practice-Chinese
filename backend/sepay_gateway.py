"""SePay Payment Gateway: signed checkout and authenticated, atomic IPN."""
import base64
from decimal import Decimal, InvalidOperation
import hashlib
import hmac
import html
import json
import os
import time
from urllib.parse import urlencode, quote
import logging
import threading
import httpx

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse
from database import database

_checks = {}
_check_lock = threading.Lock()
logger = logging.getLogger(__name__)


def reconcile_recent_orders(user_id):
    """Recover the most recent unpaid checkout when the learner returns later."""
    with database() as conn:
        row = conn.execute("SELECT order_code FROM premium_orders WHERE user_id=? AND payment_gateway='sepay_pg' AND status IN ('pending','cancelled') ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()
    if row:
        reconcile_order(row['order_code'], user_id)


def reconcile_order(code, user_id):
    """Recover missed IPNs using authenticated SePay API data, never browser claims."""
    with database() as conn:
        row = conn.execute('SELECT * FROM premium_orders WHERE order_code=? AND user_id=?',
                           (code, user_id)).fetchone()
    if not row or row['status'] == 'completed' or row['payment_gateway'] != 'sepay_pg':
        return
    with _check_lock:
        now = time.monotonic()
        if now - _checks.get(code, -30) < 5:
            return
        if len(_checks) >= 2000:
            _checks.clear()
        _checks[code] = now
    try:
        merchant, secret, _ = settings()
        with httpx.Client(auth=(merchant, secret), timeout=8, follow_redirects=False) as client:
            # The live API accepts the merchant invoice, not the PAY... order_id.
            response = client.get('https://pgapi.sepay.vn/v1/order/detail/' + quote(code, safe=''))
            response.raise_for_status()
            detail = response.json()['data']
            # Bank-transfer orders can be CAPTURED with transactions=[].
            # This evidence comes exclusively from the authenticated server API;
            # browser returns and webhook payloads still require their own auth.
            if detail.get('order_invoice_number') != code or detail.get('order_status') != 'CAPTURED':
                return
            amount = Decimal(str(detail.get('order_amount')))
            if detail.get('order_currency') != 'VND' or not amount.is_finite() or amount != Decimal(row['amount']):
                raise ValueError('Order amount/currency mismatch')
            remote_id = detail.get('id')
            if not isinstance(remote_id, str) or not 1 <= len(remote_id) <= 200:
                raise ValueError('Missing provider order identity')
            with database() as conn:
                conn.execute('BEGIN IMMEDIATE')
                used = conn.execute("SELECT order_code FROM premium_orders WHERE sepay_reference_code=? AND status='completed'", (remote_id,)).fetchone()
                if used and used['order_code'] != code:
                    raise ValueError('Provider order already used')
                from premium_service import complete_premium_order
                complete_premium_order(conn, code, 'pg-order:' + remote_id, remote_id)
    except (httpx.HTTPError, ValueError, InvalidOperation, KeyError, TypeError, AttributeError, HTTPException) as error:
        # Polling stays usable during provider outages; retry after the cooldown.
        logger.warning('SePay reconciliation failed for %s (%s)', code, type(error).__name__)


def settings():
    merchant = os.getenv('SEPAY_MERCHANT_ID', '').strip()
    secret = os.getenv('SEPAY_SECRET_KEY', '').strip()
    base = os.getenv('SEPAY_PUBLIC_URL', '').rstrip('/')
    if not merchant or not secret or not base.startswith('https://'):
        raise HTTPException(503, 'Cổng thanh toán chưa được cấu hình trên máy chủ.')
    return merchant, secret, base


def link_signature(code, user_id, expires):
    _, secret, _ = settings()
    return hmac.new(secret.encode(), f'checkout:{code}:{user_id}:{expires}'.encode(), hashlib.sha256).hexdigest()


def checkout_link(code, user_id):
    _, _, base = settings()
    expires = int(time.time()) + 1800
    return base + '/payment/sepay/checkout?' + urlencode({
        'code': code, 'user_id': user_id, 'expires': expires,
        'token': link_signature(code, user_id, expires)})


def checkout_fields(order):
    merchant, secret, base = settings()
    code = order['order_code']
    # Keep this order when rendering: SePay signs the ordered key=value list.
    fields = {'merchant': merchant, 'operation': 'PURCHASE',
              'payment_method': 'BANK_TRANSFER', 'order_invoice_number': code,
              'order_amount': str(order['amount']), 'currency': 'VND',
              'order_description': 'HanziGo Premium ' + order['plan_type'],
              'success_url': base + '/payment/sepay/return?' + urlencode({'code': code, 'result': 'success'}),
              'error_url': base + '/payment/sepay/return?' + urlencode({'code': code, 'result': 'error'}),
              'cancel_url': base + '/payment/sepay/return?' + urlencode({'code': code, 'result': 'cancel'})}
    message = ','.join(f'{key}={value}' for key, value in fields.items())
    fields['signature'] = base64.b64encode(hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()).decode()
    return fields


def process_ipn(conn, payload, supplied_secret):
    _, secret, _ = settings()
    if not supplied_secret or not hmac.compare_digest(supplied_secret, secret):
        raise HTTPException(401, 'IPN không được xác thực.')
    if not isinstance(payload, dict):
        raise HTTPException(400, 'IPN không hợp lệ.')
    if payload.get('notification_type') != 'ORDER_PAID':
        return {'success': True, 'ignored': True}
    order, transaction = payload.get('order'), payload.get('transaction')
    if not isinstance(order, dict) or not isinstance(transaction, dict):
        raise HTTPException(400, 'Thiếu đơn hoặc giao dịch.')
    if (order.get('order_status') != 'CAPTURED' or transaction.get('transaction_status') != 'APPROVED'
            or transaction.get('transaction_type') != 'PAYMENT'):
        raise HTTPException(400, 'Giao dịch chưa thanh toán thành công.')
    if order.get('order_currency') != 'VND' or transaction.get('transaction_currency') != 'VND':
        raise HTTPException(400, 'Sai đơn vị tiền tệ.')
    code = order.get('order_invoice_number')
    row = conn.execute('SELECT * FROM premium_orders WHERE order_code=?', (code,)).fetchone()
    if not row or row['payment_gateway'] != 'sepay_pg':
        raise HTTPException(404, 'Không tìm thấy đơn cổng thanh toán.')
    try:
        amounts = [Decimal(str(order['order_amount'])), Decimal(str(transaction['transaction_amount']))]
        if any(not value.is_finite() or value != Decimal(row['amount']) for value in amounts):
            raise ValueError()
    except (KeyError, InvalidOperation, ValueError):
        raise HTTPException(400, 'Số tiền không khớp đơn hàng.') from None
    transaction_id = transaction.get('id')
    if not isinstance(transaction_id, str) or not 1 <= len(transaction_id) <= 200:
        raise HTTPException(400, 'Thiếu mã giao dịch.')
    used = conn.execute("SELECT order_code FROM premium_orders WHERE sepay_transaction_id=? AND status='completed'", (transaction_id,)).fetchone()
    if used and used['order_code'] != code:
        raise HTTPException(409, 'Giao dịch đã được dùng cho đơn khác.')
    from premium_service import complete_premium_order
    complete_premium_order(conn, code, transaction_id, str(order.get('id', '')))
    return {'success': True}


def payment_page(title, content):
    """Shared, self-contained HanziGo shell; content is server-rendered escaped HTML."""
    return HTMLResponse("""<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>""" + html.escape(title) + """ · HanziGo</title><style>
:root{color-scheme:light;--green:#235546;--ink:#24332e;--muted:#60736a;--line:#e2e9e3}
*{box-sizing:border-box}body{margin:0;background:#f5f7f4;color:var(--ink);font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--green);text-decoration:none}header{max-width:1040px;margin:auto;padding:24px;display:flex;justify-content:space-between;align-items:center;gap:16px}.brand{display:flex;align-items:center;gap:10px;font-size:22px;font-weight:800}.logo{width:42px;height:42px;border-radius:50%;object-fit:contain}.back{font-size:14px;font-weight:600;min-height:44px;display:flex;align-items:center}
main{max-width:900px;margin:26px auto 60px;padding:0 24px}.eyebrow{font-size:12px;letter-spacing:2px;font-weight:700;color:var(--green);text-transform:uppercase}h1{font-size:clamp(26px,5vw,36px);line-height:1.25;margin:12px 0}h2{font-size:24px;margin:12px 0}.intro{color:var(--muted);margin:0 0 28px}.layout{display:grid;grid-template-columns:1fr 1.15fr;gap:22px}.card{background:white;border:1px solid var(--line);border-radius:24px;padding:28px;min-width:0;box-shadow:0 8px 30px #24332e05}.premium{background:linear-gradient(145deg,#235546,#153e35);color:white;border-color:#235546}.badge{display:inline-block;background:#f7dfa0;color:#493c19;border-radius:20px;padding:5px 12px;font-size:12px;font-weight:800}.premium p{color:#d8e8df}.features{padding:0;list-style:none;margin:24px 0 0}.features li{padding:10px 0;border-top:1px solid #ffffff24}.features li::before{content:'✓';color:#f7dfa0;margin-right:10px}
dl{margin:0}dl>div{display:flex;justify-content:space-between;gap:16px;padding:13px 0;border-bottom:1px solid var(--line)}dt{color:var(--muted)}dd{margin:0;text-align:right;font-weight:600;overflow-wrap:anywhere;min-width:0}.total{align-items:center;border:0!important;padding:22px 0!important}.total dd{color:var(--green);font-size:28px;font-weight:800;line-height:1.25}.button{display:block;width:100%;min-height:52px;border:0;border-radius:14px;background:var(--green);color:white;font:700 16px/1.4 system-ui;padding:16px;text-align:center;cursor:pointer}.button:hover{background:#193f34}a:focus-visible,button:focus-visible{outline:3px solid #bc8a23;outline-offset:4px}.note{font-size:13px;color:var(--muted);margin:16px 0 0}.footer{text-align:center;font-size:13px;color:var(--muted);margin-top:26px}.status{max-width:580px;margin:0 auto}.status p{color:var(--muted)}.status .button{margin-top:24px}
@media(max-width:640px){header{padding:16px}.brand{font-size:20px}main{margin:16px auto 32px;padding:0 16px}.layout{grid-template-columns:1fr;gap:16px}.card{padding:22px;border-radius:20px}.features{margin-top:16px}.intro{margin-bottom:22px}.total dd{font-size:26px}}
</style></head><body><header><a class="brand" href="/" aria-label="HanziGo, trang chủ"><img class="logo" src="/logo.png" alt="HanziGo">HanziGo</a><a class="back" href="/account">← Tài khoản</a></header><main>""" + content + """<p class="footer">HanziGo · Đồng hành cùng bạn trên hành trình học tiếng Trung</p></main></body></html>""",
        headers={'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer'})


def register_gateway(app):
    @app.get('/payment/sepay/checkout', response_class=HTMLResponse)
    def checkout(code: str, user_id: int, expires: int, token: str):
        if expires < int(time.time()) or not hmac.compare_digest(token, link_signature(code, user_id, expires)):
            raise HTTPException(403, 'Link thanh toán hết hạn hoặc không hợp lệ. Hãy tạo đơn mới.')
        with database() as conn:
            from premium_service import cleanup_expired_pending_orders
            cleanup_expired_pending_orders(conn)
            row = conn.execute('SELECT * FROM premium_orders WHERE order_code=? AND user_id=?', (code, user_id)).fetchone()
        if not row or row['payment_gateway'] != 'sepay_pg' or row['status'] != 'pending':
            raise HTTPException(409, 'Đơn không còn chờ thanh toán.')
        fields = checkout_fields(dict(row))
        inputs = ''.join(f'<input type="hidden" name="{key}" value="{html.escape(value, quote=True)}">' for key, value in fields.items())
        status_url = '/api/payment/sepay-status?' + urlencode({'code': code, 'user_id': user_id, 'expires': expires, 'token': token})
        watch = '<script>try { sessionStorage.setItem("hanzigo_payment_status", ' + json.dumps(status_url).replace('<', chr(92) + 'u003c') + '); } catch (e) {}</script>'
        plan = {'1_month': '1 tháng', '1_year': '1 năm'}.get(row['plan_type'], 'Premium')
        amount = f"{row['amount']:,}".replace(',', '.')
        return payment_page('Thanh toán Premium', f'''<div class="eyebrow">HanziGo Premium</div>
<h1>Tiếp bước hành trình học tập</h1><p class="intro">Kiểm tra thông tin gói trước khi tiếp tục thanh toán.</p>
<div class="layout"><section class="card premium" aria-label="Gói đã chọn"><span class="badge">PREMIUM</span>
<h2>Học cùng HanziGo</h2><p>Gói hội viên {plan}, dành cho hành trình chinh phục tiếng Trung của bạn.</p>
<ul class="features"><li>Thời hạn gói: {plan}</li><li>Thanh toán một lần</li><li>Không tự động gia hạn</li></ul></section>
<section class="card" aria-label="Chi tiết thanh toán"><dl><div><dt>Mã đơn</dt><dd>{html.escape(code)}</dd></div>
<div><dt>Gói đăng ký</dt><dd>Premium · {plan}</dd></div><div><dt>Thanh toán qua</dt><dd>SePay</dd></div>
<div class="total"><dt>Tổng thanh toán</dt><dd>{amount} ₫</dd></div></dl>
<form method="POST" action="https://pay.sepay.vn/v1/checkout/init">{inputs}<button class="button" type="submit">Tiếp tục thanh toán tại SePay →</button></form>
<p class="note">Bạn sẽ chuyển đến SePay để thanh toán. Premium được kích hoạt sau khi HanziGo nhận xác nhận giao dịch.</p>
<p class="note">Đơn chờ thanh toán có hiệu lực 10 phút kể từ khi tạo. Nếu đã chuyển tiền, hãy kiểm tra tài khoản trước khi tạo đơn mới.</p></section></div>{watch}''')

    @app.get('/api/payment/sepay-status')
    def payment_status(code: str, user_id: int, expires: int, token: str):
        if expires < int(time.time()) or not hmac.compare_digest(token, link_signature(code, user_id, expires)):
            raise HTTPException(403, 'Phiên kiểm tra hết hạn. Hãy mở tài khoản để xem Premium.')
        reconcile_order(code, user_id)
        with database() as conn:
            from premium_service import cleanup_expired_pending_orders
            cleanup_expired_pending_orders(conn)
            row = conn.execute("SELECT status FROM premium_orders WHERE order_code=? AND user_id=? AND payment_gateway='sepay_pg'", (code, user_id)).fetchone()
        if not row:
            raise HTTPException(404, 'Không tìm thấy đơn hàng.')
        from fastapi.responses import JSONResponse
        return JSONResponse({'is_completed': row['status'] == 'completed', 'is_expired': row['status'] == 'cancelled'}, headers={'Cache-Control': 'no-store'})

    @app.post('/api/payment/sepay-ipn')
    async def ipn(request: Request):
        try:
            payload = await request.json()
        except ValueError:
            raise HTTPException(400, 'JSON không hợp lệ.') from None
        with database() as conn:
            conn.execute('BEGIN IMMEDIATE')
            return process_ipn(conn, payload, request.headers.get('x-secret-key'))

    @app.get('/payment/sepay/return', response_class=HTMLResponse)
    def payment_return(code: str = '', result: str = ''):
        # A browser redirect never proves payment; only authenticated IPN grants Premium.
        message = 'Đã quay lại từ SePay. Hãy mở tài khoản để kiểm tra xác nhận thanh toán.'
        if result == 'cancel':
            message = 'Bạn đã rời trang thanh toán. Nếu đã chuyển tiền, hãy kiểm tra trạng thái đơn.'
        elif result == 'error':
            message = 'SePay báo thanh toán chưa hoàn tất. Hãy kiểm tra lại trạng thái đơn.'
        return payment_page('Kiểm tra thanh toán', '<section class="card status"><div class="eyebrow">HanziGo Premium</div>'
            '<h1 id="payment-title">Thông tin thanh toán</h1><p id="payment-message" role="status" aria-live="polite">' + message + '</p><dl><div><dt>Mã đơn</dt><dd>' + html.escape(code) +
            '</dd></div></dl><a class="button" href="/account">Kiểm tra tài khoản</a><a class="back" href="/">Trở về HanziGo</a></section>' + payment_watch_script(code))


def payment_watch_script(code):
    expected = json.dumps(code).replace('<', chr(92) + 'u003c')
    return '<script>const expectedCode=' + expected + ';' + r"""
(() => {
 const title=document.getElementById('payment-title'), message=document.getElementById('payment-message');
 let endpoint, authToken='';
 try { authToken=sessionStorage.getItem('hanzigo_account_token')||JSON.parse(localStorage.getItem('flutter.auth_token')||'null')||''; } catch(e) {}
 function useAccountSession(){
   if(!authToken)return false;
   endpoint=new URL('/api/premium/orders/'+encodeURIComponent(expectedCode)+'/status',location.origin);
   return true;
 }
 try {
   endpoint=new URL(sessionStorage.getItem('hanzigo_payment_status') || '', location.origin);
   if(endpoint.origin!==location.origin || endpoint.pathname!=='/api/payment/sepay-status' || endpoint.searchParams.get('code')!==expectedCode) throw Error();
 } catch(e) { if(!useAccountSession()){message.textContent='Vui lòng trở về HanziGo và đăng nhập tài khoản đã mua để kiểm tra Premium. Không chuyển tiền lại.'; return;} }
 let attempts=0;
 async function check() {
   const started=Date.now();
   try {
     const response=await fetch(endpoint.href,{cache:'no-store',signal:AbortSignal.timeout(10000),headers:authToken?{Authorization:'Bearer '+authToken}:{}});
     if(response.status===403 || response.status===404) {
       if(endpoint.pathname==='/api/payment/sepay-status' && useAccountSession()){setTimeout(check,5000);return;}
       message.textContent='Phiên theo dõi kết thúc. Mở tài khoản để kiểm tra Premium; không chuyển tiền lại.'; return;
     }
     if(!response.ok) throw Error();
     const data=await response.json();
     if(data.is_completed===true) {
       title.textContent='Premium đã được kích hoạt!';
       message.textContent='HanziGo đã nhận xác nhận từ SePay. Trở về ứng dụng để sử dụng Premium.';
       sessionStorage.removeItem('hanzigo_payment_status'); return;
     }
     message.textContent=data.is_expired ? 'Đơn đã hết hạn chờ 10 phút. Nếu đã chuyển tiền, trang vẫn kiểm tra xác nhận SePay; không chuyển lại.' : 'Đang chờ SePay xác nhận. Trang tự cập nhật, bạn không cần thanh toán lại.';
   } catch(e) { message.textContent='Kết nối tạm gián đoạn. Hệ thống sẽ tự kiểm tra lại; đừng thanh toán thêm.'; }
   if(++attempts<360) setTimeout(check,Math.max(0,5000-(Date.now()-started)));
   else message.textContent='Chưa nhận xác nhận. Hãy kiểm tra tài khoản hoặc liên hệ hỗ trợ với mã đơn; không thanh toán lại.';
 }
 check();
})();</script>"""
