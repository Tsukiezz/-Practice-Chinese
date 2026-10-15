/**
 * HanziGo - Google Identity Services (OAuth 2.0) Integration
 * Kết nối tài khoản Google chính thức qua popup accounts.google.com
 */
(function() {
  'use strict';

  window.hanziGoGoogle = {
    /**
     * Mở popup đăng nhập chính thức của Google (accounts.google.com).
     * Yêu cầu người dùng chọn tài khoản và chấp nhận quyền đăng nhập.
     * @param {string} clientId - Google OAuth 2.0 Client ID
     * @returns {Promise<Object>} { success, email, name, avatar, accessToken, googleId }
     */
    signIn: function(clientId) {
      return new Promise(function(resolve, reject) {
        if (!clientId || clientId.trim() === '') {
          reject({
            code: 'CLIENT_ID_MISSING',
            message: 'Chưa cấu hình Google Client ID trên hệ thống.'
          });
          return;
        }

        var cid = clientId.trim();

        function runTokenClient() {
          if (!window.google || !window.google.accounts || !window.google.accounts.oauth2) {
            reject({
              code: 'SDK_NOT_LOADED',
              message: 'Thư viện Google Identity chưa sẵn sàng. Vui lòng thử lại.'
            });
            return;
          }

          try {
            var client = window.google.accounts.oauth2.initTokenClient({
              client_id: cid,
              scope: 'email profile openid',
              prompt: 'select_account',
              error_callback: function(err) {
                var popupBlocked = err.type === 'popup_failed_to_open';
                reject({
                  code: err.type || 'POPUP_ERROR',
                  message: popupBlocked
                    ? 'Không mở được cửa sổ Google. Hãy bấm Đăng nhập với Google lần nữa. Nếu iPhone vẫn chặn, mở HanziGo bằng Safari để đăng nhập.'
                    : err.type === 'popup_closed'
                      ? 'Bạn đã đóng cửa sổ Google. Bấm đăng nhập để thử lại.'
                      : 'Không thể mở đăng nhập Google. Vui lòng thử lại.'
                });
              },
              callback: function(tokenResponse) {
                if (!tokenResponse || tokenResponse.error) {
                  var errMsg = tokenResponse ? (tokenResponse.error_description || tokenResponse.error) : 'Người dùng hủy thao tác.';
                  reject({
                    code: tokenResponse ? tokenResponse.error : 'USER_CANCELLED',
                    message: errMsg
                  });
                  return;
                }

                // Lấy thông tin tài khoản Google đã được Google xác thực
                fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
                  headers: {
                    'Authorization': 'Bearer ' + tokenResponse.access_token
                  }
                })
                .then(function(res) {
                  if (!res.ok) {
                    throw new Error('Không thể lấy hồ sơ từ Google (mã lỗi ' + res.status + ')');
                  }
                  return res.json();
                })
                .then(function(profile) {
                  resolve({
                    success: true,
                    email: profile.email || '',
                    name: profile.name || '',
                    avatar: profile.picture || '',
                    accessToken: tokenResponse.access_token,
                    googleId: profile.sub || ''
                  });
                })
                .catch(function(fetchErr) {
                  reject({
                    code: 'USERINFO_FAILED',
                    message: fetchErr.message || 'Lỗi khi lấy thông tin tài khoản Google.'
                  });
                });
              }
            });

            // Kích hoạt mở popup đăng nhập chính thức từ accounts.google.com
            client.requestAccessToken({ prompt: 'select_account' });
          } catch (initErr) {
            reject({
              code: 'INIT_EXCEPTION',
              message: initErr.message || String(initErr)
            });
          }
        }

        // Never defer popup creation to a timer: Safari/PWA user activation
        // may expire. A fresh user tap is required when the SDK is ready.
        runTokenClient();
      });
    }
  };

  // Lắng nghe sự kiện từ Flutter Web
  window.addEventListener('hanzigo-google-signin-request', function(event) {
    var clientId = '';
    try {
      if (event.detail) {
        var parsed = typeof event.detail === 'string' ? JSON.parse(event.detail) : event.detail;
        clientId = parsed.clientId || '';
      }
    } catch (_) {}

    window.hanziGoGoogle.signIn(clientId)
      .then(function(result) {
        window.dispatchEvent(new CustomEvent('hanzigo-google-signin-response', {
          detail: JSON.stringify({
            success: true,
            data: result
          })
        }));
      })
      .catch(function(err) {
        window.dispatchEvent(new CustomEvent('hanzigo-google-signin-response', {
          detail: JSON.stringify({
            success: false,
            error: err.message || 'Đăng nhập Google không thành công.',
            code: err.code || 'UNKNOWN'
          })
        }));
      });
  });
})();
