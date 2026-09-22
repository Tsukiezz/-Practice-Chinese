"""Email delivery service supporting standard SMTP (Gmail, Brevo, Resend, etc.) and fallback dev logging."""
import email.utils
import json
import logging
import os
import smtplib
import urllib.error
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger("hanzigo.email")


def get_email_config() -> dict:
    """Read and normalize email configuration from environment variables."""
    host = (
        os.environ.get("SMTP_HOST", "")
        or os.environ.get("MAIL_HOST", "")
        or os.environ.get("BREVO_SMTP_HOST", "")
    ).strip()

    # Clean protocol prefix if present
    for prefix in ("https://", "http://", "smtp://", "smtps://"):
        if host.lower().startswith(prefix):
            host = host[len(prefix):]
    host = host.rstrip("/")

    user = (
        os.environ.get("SMTP_USERNAME", "")
        or os.environ.get("SMTP_USER", "")
        or os.environ.get("MAIL_USERNAME", "")
        or os.environ.get("BREVO_USERNAME", "")
        or os.environ.get("BREVO_USER", "")
    ).strip()

    password = (
        os.environ.get("SMTP_PASSWORD", "")
        or os.environ.get("SMTP_PASS", "")
        or os.environ.get("MAIL_PASSWORD", "")
        or os.environ.get("BREVO_API_KEY", "")
        or os.environ.get("BREVO_SMTP_KEY", "")
        or os.environ.get("SMTP_KEY", "")
    ).strip()

    port_raw = (
        os.environ.get("SMTP_PORT", "")
        or os.environ.get("MAIL_PORT", "")
        or "587"
    ).strip()
    try:
        port = int(port_raw)
    except ValueError:
        port = 587

    from_raw = (
        os.environ.get("EMAIL_FROM", "")
        or os.environ.get("SMTP_FROM", "")
        or os.environ.get("SMTP_FROM_EMAIL", "")
        or os.environ.get("MAIL_FROM", "")
        or user
        or "noreply@hanzigo.app"
    ).strip()

    # Auto-detect host for Brevo or Gmail if missing
    if not host:
        if (
            password.startswith("xsmtpsib-")
            or password.startswith("xkeysib-")
            or "brevo" in user.lower()
            or "sendinblue" in user.lower()
            or "brevosend.com" in from_raw.lower()
        ):
            host = "smtp-relay.brevo.com"
        elif user.endswith("@gmail.com"):
            host = "smtp.gmail.com"

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "from_raw": from_raw,
    }


def smtp_is_configured() -> bool:
    """Return whether all credentials required to deliver an email are present."""
    cfg = get_email_config()
    if cfg["password"].startswith("xkeysib-") or bool(os.environ.get("BREVO_API_KEY")):
        return bool(cfg["password"] and cfg["from_raw"])
    return bool(cfg["host"] and cfg["user"] and cfg["password"])


def get_smtp_status() -> dict:
    """Return safe metadata about SMTP configuration (without exposing credentials)."""
    cfg = get_email_config()
    user = cfg["user"]
    masked_user = ""
    if user:
        if "@" in user:
            parts = user.split("@")
            prefix = parts[0]
            masked_prefix = prefix[:3] + "***" if len(prefix) > 3 else prefix + "***"
            masked_user = f"{masked_prefix}@{parts[1]}"
        else:
            masked_user = user[:3] + "***" if len(user) > 3 else user + "***"

    return {
        "configured": smtp_is_configured(),
        "host": cfg["host"],
        "port": cfg["port"],
        "user_masked": masked_user,
        "from_raw": cfg["from_raw"],
        "is_brevo": (
            "brevo" in cfg["host"].lower()
            or "sendinblue" in cfg["host"].lower()
            or cfg["password"].startswith("xsmtpsib-")
            or "brevo" in user.lower()
        ),
    }


def _render_html_template(email: str, code: str, purpose_label: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mã xác thực HanziGo</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f6f7f4; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #191c1b;">
  <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f6f7f4; padding: 30px 15px;">
    <tr>
      <td align="center">
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 520px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.06);">
          <!-- Header -->
          <tr>
            <td style="background-color: #1B4D3E; padding: 28px 24px; text-align: center;">
              <div style="display: inline-block; background: rgba(255,255,255,0.15); border-radius: 12px; padding: 10px 14px; margin-bottom: 12px;">
                <span style="font-size: 26px; color: #ffffff; font-weight: bold;">汉</span>
              </div>
              <h1 style="margin: 0; color: #ffffff; font-size: 22px; font-weight: 800; letter-spacing: 0.5px;">HanziGo · Hán Ngữ Xanh</h1>
              <p style="margin: 6px 0 0; color: #E2C391; font-size: 13px; font-weight: 500;">Học tiếng Trung theo cách đơn giản và hiệu quả</p>
            </td>
          </tr>
          <!-- Body Content -->
          <tr>
            <td style="padding: 32px 28px;">
              <h2 style="margin: 0 0 12px; color: #1B4D3E; font-size: 18px; font-weight: 700;">{purpose_label}</h2>
              <p style="margin: 0 0 20px; color: #4b5563; font-size: 14px; line-height: 1.6;">
                Xin chào, chúng tôi nhận được yêu cầu xác thực cho tài khoản email <strong>{email}</strong>. Vui lòng nhập mã OTP dưới đây để tiếp tục:
              </p>
              <!-- OTP Code Box -->
              <div style="text-align: center; margin: 28px 0;">
                <div style="display: inline-block; background-color: #F0F7F4; border: 2px dashed #1B4D3E; border-radius: 12px; padding: 14px 28px;">
                  <span style="font-family: monospace, Consolas, Courier; font-size: 34px; font-weight: 800; letter-spacing: 8px; color: #1B4D3E;">{code}</span>
                </div>
              </div>
              <p style="margin: 0 0 16px; color: #dc2626; font-size: 13px; font-weight: 600; text-align: center;">
                ⏱ Mã này có hiệu lực trong vòng 10 phút.
              </p>
              <div style="background-color: #FFFBEB; border-left: 4px solid #D97706; padding: 12px 16px; border-radius: 6px; margin: 20px 0 0;">
                <p style="margin: 0; color: #92400E; font-size: 12px; line-height: 1.5;">
                  <strong>Lưu ý bảo mật:</strong> Tuyệt đối không chia sẻ mã xác thực này cho bất kỳ ai. Nếu bạn không thực hiện yêu cầu này, hãy bỏ qua email này.
                </p>
              </div>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background-color: #f9fafb; padding: 20px 24px; text-align: center; border-top: 1px solid #f3f4f6;">
              <p style="margin: 0; color: #9ca3af; font-size: 12px;">© HanziGo · Tất cả các quyền được bảo lưu.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _send_via_smtp(cfg: dict, to_email: str, subject: str, text_content: str, html_content: str) -> bool:
    """Send email through standard SMTP connection."""
    host = cfg["host"]
    port = cfg["port"]
    user = cfg["user"]
    password = cfg["password"]
    from_raw = cfg["from_raw"]

    parsed_name, parsed_addr = email.utils.parseaddr(from_raw)
    clean_from_email = parsed_addr if parsed_addr else from_raw
    from_name = parsed_name if parsed_name else "HanziGo · Hán Ngữ Xanh"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = email.utils.formataddr((from_name, clean_from_email))
    msg["To"] = to_email
    msg["Reply-To"] = clean_from_email

    msg.attach(MIMEText(text_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=10) as server:
            server.login(user, password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(user, password)
            server.send_message(msg)
    return True


def _send_via_brevo_api(cfg: dict, to_email: str, subject: str, text_content: str, html_content: str) -> bool:
    """Fallback sending via Brevo REST API v3 (HTTPS 443) if SMTP ports are blocked."""
    api_key = cfg["password"]
    if not api_key:
        return False

    parsed_name, parsed_addr = email.utils.parseaddr(cfg["from_raw"])
    from_email = parsed_addr if parsed_addr else cfg["from_raw"]
    from_name = parsed_name if parsed_name else "HanziGo · Hán Ngữ Xanh"

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json",
        "User-Agent": "HanziGo-Backend/1.0",
    }
    payload = {
        "sender": {"name": from_name, "email": from_email},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content,
        "textContent": text_content,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        if 200 <= resp.status < 300:
            return True
    return False


def send_verification_email(to_email: str, code: str, purpose: str = "register") -> bool:
    """Send verification OTP to user's real email address via SMTP with Brevo API fallback or log in dev mode."""
    to_email = to_email.strip().lower()
    if purpose == "register":
        subject = f"[HanziGo] Mã xác thực đăng ký tài khoản: {code}"
        purpose_label = "Xác thực đăng ký tài khoản mới"
    else:
        subject = f"[HanziGo] Mã xác thực đặt lại mật khẩu: {code}"
        purpose_label = "Yêu cầu đặt lại mật khẩu"

    cfg = get_email_config()
    html_content = _render_html_template(to_email, code, purpose_label)
    text_content = (
        f"{purpose_label}\n\n"
        f"Mã xác thực HanziGo của bạn là: {code}\n"
        f"Mã có hiệu lực trong vòng 10 phút.\n"
        f"Không chia sẻ mã này với bất kỳ ai."
    )

    if not smtp_is_configured():
        if os.environ.get("VERCEL"):
            raise RuntimeError("Dịch vụ SMTP chưa được cấu hình trên môi trường Vercel.")
        logger.warning(
            f"[EMAIL_DEV_MODE] No SMTP configured. Code for {to_email} ({purpose}): {code}"
        )
        try:
            print(f"\n==========================================")
            print(f"[HANZIGO EMAIL] Gui ma toi: {to_email}")
            print(f"[HANZIGO EMAIL] Muc dich: {purpose}")
            print(f"[HANZIGO EMAIL] MA XAC THUC (OTP): {code}")
            print(f"==========================================\n", flush=True)
        except Exception:
            pass
        return True

    # 1. If Brevo API key is provided (starts with xkeysib- or BREVO_API_KEY env), use REST API directly (like CDTV project)
    is_brevo_api_key = cfg["password"].startswith("xkeysib-") or bool(os.environ.get("BREVO_API_KEY"))
    if is_brevo_api_key:
        try:
            if _send_via_brevo_api(cfg, to_email, subject, text_content, html_content):
                logger.info(f"Successfully sent OTP email to {to_email} via Brevo REST API v3")
                return True
        except Exception as api_exc:
            logger.error(f"Brevo REST API failed: {api_exc}")
            raise RuntimeError(f"Gửi email qua Brevo REST API thất bại: {api_exc}")

    # 2. Try standard SMTP
    smtp_err = None
    try:
        _send_via_smtp(cfg, to_email, subject, text_content, html_content)
        logger.info(f"Successfully sent OTP email to {to_email} via SMTP ({cfg['host']}:{cfg['port']})")
        return True
    except Exception as exc:
        smtp_err = exc
        logger.warning(f"SMTP send failed ({exc}), checking Brevo REST API fallback...")

    # 3. Fallback to Brevo REST API v3 if applicable
    is_brevo = (
        "brevo" in cfg["host"].lower()
        or "sendinblue" in cfg["host"].lower()
        or cfg["password"].startswith("xsmtpsib-")
        or "brevo" in cfg["user"].lower()
        or "brevosend.com" in cfg["from_raw"].lower()
    )
    if is_brevo:
        try:
            if _send_via_brevo_api(cfg, to_email, subject, text_content, html_content):
                logger.info(f"Successfully sent OTP email to {to_email} via Brevo REST API v3")
                return True
        except Exception as api_exc:
            logger.error(f"Brevo REST API fallback also failed: {api_exc}")
            raise RuntimeError(f"Gửi email qua Brevo thất bại (SMTP: {smtp_err} | REST API: {api_exc})")

    raise RuntimeError(f"Không thể gửi email xác thực qua SMTP: {smtp_err}")

