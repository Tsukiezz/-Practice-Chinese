// Facebook SDK runs only after this provider is configured and the screen loads.
(() => {
  'use strict';
  let preparing = null, ready = false;
  window.hanziGoFacebook = {
    prepare(baseUrl) {
      if (preparing) return preparing;
      preparing = (async () => {
        const response = await fetch(baseUrl.replace(/\/$/, '') + '/auth/facebook-config');
        if (!response.ok) return false;
        const config = await response.json();
        if (!config.enabled) return false;
        await new Promise((resolve, reject) => {
          if (window.FB) return resolve();
          const script = document.createElement('script');
          script.src = 'https://connect.facebook.net/vi_VN/sdk.js';
          script.async = true;
          script.onload = () => window.FB ? resolve() : reject(Error('Facebook SDK chưa sẵn sàng.'));
          script.onerror = () => reject(Error('Không tải được Facebook SDK.'));
          document.head.append(script);
        });
        window.FB.init({appId: config.app_id, version: config.version, cookie: false, xfbml: false});
        ready = true;
        return true;
      })().catch(() => false).finally(() => { if (!ready) preparing = null; });
      return preparing;
    },
    signIn() {
      return new Promise((resolve, reject) => {
        if (!ready || !window.FB) return reject(Error('Facebook chưa được cấu hình hoặc chưa sẵn sàng.'));
        // Synchronous invocation from the user's tap; no fetch/timer before FB.login.
        window.FB.login(response => {
          const token = response && response.authResponse && response.authResponse.accessToken;
          if (token) resolve(token);
          else reject(Error('Bạn đã hủy hoặc chưa cấp quyền đăng nhập Facebook.'));
        }, {scope: 'public_profile,email', return_scopes: true});
      });
    },
  };
})();
