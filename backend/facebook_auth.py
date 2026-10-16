"""Facebook Login: verify app-scoped identity server-side before issuing a session."""
import hashlib
import hmac
import os
import re
import secrets
import time
import httpx
from fastapi import HTTPException
from pydantic import BaseModel, Field
from database import database


class FacebookLogin(BaseModel):
    access_token: str = Field(min_length=1, max_length=4096)


def config():
    app_id = os.getenv('FACEBOOK_APP_ID', '').strip()
    secret = os.getenv('FACEBOOK_APP_SECRET', '').strip()
    version = os.getenv('FACEBOOK_GRAPH_VERSION', '').strip()
    enabled = bool(re.fullmatch(r'\d+', app_id) and secret and re.fullmatch(r'v\d+\.\d+', version))
    return app_id, secret, version, enabled


def verify_identity(token):
    app_id, secret, version, enabled = config()
    if not enabled:
        raise HTTPException(503, 'Đăng nhập Facebook chưa được cấu hình. Bạn vẫn có thể dùng Google hoặc email.')
    try:
        with httpx.Client(timeout=12) as client:
            checked = client.get(f'https://graph.facebook.com/{version}/debug_token',
                params={'input_token': token}, headers={'Authorization': f'Bearer {app_id}|{secret}'})
            if checked.status_code != 200:
                raise HTTPException(401, 'Không xác thực được tài khoản Facebook.')
            data = checked.json().get('data', {})
            now = int(time.time())
            if (data.get('is_valid') is not True or str(data.get('app_id')) != app_id
                    or not data.get('user_id') or data.get('type') != 'USER'
                    or int(data.get('expires_at') or 0) <= now
                    or (data.get('data_access_expires_at') and int(data['data_access_expires_at']) <= now)):
                raise HTTPException(401, 'Phiên Facebook không hợp lệ hoặc đã hết hạn.')
            proof = hmac.new(secret.encode(), token.encode(), hashlib.sha256).hexdigest()
            response = client.get(f'https://graph.facebook.com/{version}/me',
                params={'fields': 'id,name,email', 'appsecret_proof': proof},
                headers={'Authorization': 'Bearer ' + token})
            if response.status_code != 200:
                raise HTTPException(401, 'Không đọc được hồ sơ Facebook.')
            profile = response.json()
            if str(profile.get('id', '')) != str(data['user_id']):
                raise HTTPException(401, 'Danh tính Facebook không khớp.')
            return profile
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError, TypeError):
        # Never expose provider request URLs, access tokens or app secrets.
        raise HTTPException(502, 'Không kết nối được Facebook. Vui lòng thử lại.') from None


def register_facebook_auth(app, session, hash_password):
    @app.get('/api/auth/facebook-config')
    def facebook_config():
        app_id, _, version, enabled = config()
        return {'app_id': app_id if enabled else '', 'version': version if enabled else '', 'enabled': enabled}

    @app.post('/api/auth/facebook-login')
    def facebook_login(body: FacebookLogin):
        profile = verify_identity(body.access_token)
        provider_id = str(profile['id'])
        with database() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS facebook_identities(
                facebook_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL UNIQUE
                REFERENCES users(id) ON DELETE CASCADE)''')
            conn.execute('BEGIN IMMEDIATE')
            user = conn.execute('''SELECT u.* FROM users u JOIN facebook_identities f
                ON u.id=f.user_id WHERE f.facebook_id=?''', (provider_id,)).fetchone()
            if user is None:
                email = str(profile.get('email') or '').strip().lower()
                if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email) or len(email) > 120:
                    raise HTTPException(422, 'Facebook chưa cung cấp email. Hãy cho phép quyền email hoặc dùng Google/email để đăng nhập.')
                if conn.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone():
                    # Do not silently link or take over an existing account by email.
                    raise HTTPException(409, 'Email này đã có tài khoản HanziGo. Hãy đăng nhập bằng Google hoặc email đã dùng trước đó.')
                salt = secrets.token_hex(16)
                uid = conn.execute('''INSERT INTO users(name,email,password_hash,salt,role,is_active,created_at)
                    VALUES(?,?,?,?,'student',1,?)''', (
                        str(profile.get('name') or 'Học viên')[:100], email,
                        hash_password(secrets.token_urlsafe(32), salt), salt, int(time.time()))).lastrowid
                conn.execute('INSERT INTO facebook_identities VALUES(?,?)', (provider_id, uid))
                user = conn.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
            if not user['is_active'] or user['role'] != 'student':
                raise HTTPException(403, 'Tài khoản không được phép đăng nhập tại đây.')
            return session(conn, user)
