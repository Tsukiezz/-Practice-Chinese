"""SePay Payment Gateway: signed checkout and authenticated, atomic IPN."""
import base64
from decimal import Decimal, InvalidOperation
import hashlib
import hmac
import html
import os
import time
from urllib.parse import urlencode

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse
from database import database


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


def register_gateway(app):
    @app.get('/payment/sepay/checkout', response_class=HTMLResponse)
    def checkout(code: str, user_id: int, expires: int, token: str):
        if expires < int(time.time()) or not hmac.compare_digest(token, link_signature(code, user_id, expires)):
            raise HTTPException(403, 'Link thanh toán hết hạn hoặc không hợp lệ. Hãy tạo đơn mới.')
        with database() as conn:
            row = conn.execute('SELECT * FROM premium_orders WHERE order_code=? AND user_id=?', (code, user_id)).fetchone()
        if not row or row['payment_gateway'] != 'sepay_pg' or row['status'] != 'pending':
            raise HTTPException(409, 'Đơn không còn chờ thanh toán.')
        fields = checkout_fields(dict(row))
        inputs = ''.join(f'<input type="hidden" name="{key}" value="{html.escape(value, quote=True)}">' for key, value in fields.items())
        return HTMLResponse('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Thanh toán HanziGo Premium</title><h1>Thanh toán HanziGo Premium</h1>'
            f'<p>Đơn {html.escape(code)} · {row["amount"]:,} VND</p>'
            f'<form method="POST" action="https://pay.sepay.vn/v1/checkout/init">{inputs}'
            '<button type="submit">Tiếp tục thanh toán tại SePay</button></form>',
            headers={'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer'})

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
        return HTMLResponse('<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<h1>HanziGo Premium</h1><p>' + message + '</p><p>Mã đơn: ' + html.escape(code) +
            '</p><a href="/account">Kiểm tra tài khoản</a> · <a href="/">Trở về ứng dụng</a>', headers={'Cache-Control': 'no-store'})
