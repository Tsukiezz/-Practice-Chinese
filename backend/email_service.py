"""Email delivery service supporting standard SMTP (Gmail, Brevo, Resend, etc.) and fallback dev logging."""
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger("hanzigo.email")


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


def send_verification_email(to_email: str, code: str, purpose: str = "register") -> bool:
    """Send verification OTP to user's real email address via SMTP or log in dev mode."""
    to_email = to_email.strip().lower()
    if purpose == "register":
        subject = f"[HanziGo] Mã xác thực đăng ký tài khoản: {code}"
        purpose_label = "Xác thực đăng ký tài khoản mới"
    else:
        subject = f"[HanziGo] Mã xác thực đặt lại mật khẩu: {code}"
        purpose_label = "Yêu cầu đặt lại mật khẩu"

    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_user = os.environ.get("SMTP_USER", "").strip() or os.environ.get("SMTP_USERNAME", "").strip()
    smtp_pass = os.environ.get("SMTP_PASSWORD", "").strip()
    smtp_port = int(os.environ.get("SMTP_PORT", "587").strip() or 587)
    from_email = (
        os.environ.get("SMTP_FROM_EMAIL", "").strip()
        or os.environ.get("SMTP_FROM", "").strip()
        or smtp_user
        or "noreply@hanzigo.app"
    )

    # Also support auto-detecting gmail if SMTP_USER is @gmail.com
    if not smtp_host and smtp_user.endswith("@gmail.com"):
        smtp_host = "smtp.gmail.com"

    html_content = _render_html_template(to_email, code, purpose_label)
    text_content = f"{purpose_label}\n\nMã xác thực HanziGo của bạn là: {code}\nMã có hiệu lực trong vòng 10 phút.\nKhông chia sẻ mã này với bất kỳ ai."

    if not smtp_host or not smtp_user or not smtp_pass:
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

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"HanziGo <{from_email}>"
    msg["To"] = to_email

    msg.attach(MIMEText(text_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        logger.info(f"Sent OTP email to {to_email}")
        return True
    except Exception as exc:
        logger.error(f"Failed to send email to {to_email}: {exc}")
        # Always print fallback to console so user/tester is never stranded
        print(f"[EMAIL ERROR - FALLBACK CODE]: {code} for {to_email}")
        raise RuntimeError(f"Không thể gửi email xác thực: {exc}")
