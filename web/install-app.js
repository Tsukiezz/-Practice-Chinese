(() => {
  'use strict';
  let pendingPrompt = null;
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent)
    || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  let installed = window.matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
  const button = document.querySelector('[data-install-app]');
  const status = document.querySelector('[data-install-status]');
  const iosGuide = document.querySelector('#ios-install');
  const androidGuide = document.querySelector('#manual-install');
  const iosInstructions = 'Trên iPhone/iPad: nhấn Chia sẻ (ô vuông có mũi tên lên). Nếu chưa thấy, mở menu … của Safari → Chia sẻ. Chọn Thêm vào Màn hình chính → bật Mở dưới dạng ứng dụng web nếu có → Thêm.';
  if (iosGuide && androidGuide) {
    if (isIOS) androidGuide.before(iosGuide);
    else iosGuide.before(androidGuide);
  }
  const update = (message) => {
    if (status) status.textContent = message;
    if (button) {
      button.hidden = installed;
      button.textContent = 'Cài HanziGo';
    }
  };
  window.addEventListener('beforeinstallprompt', (event) => {
    if (button) event.preventDefault();
    pendingPrompt = event;
    update('Sẵn sàng cài đặt. Nhấn “Cài HanziGo” rồi xác nhận với Chrome.');
  });
  window.addEventListener('appinstalled', () => {
    installed = true;
    pendingPrompt = null;
    update('Đã cài HanziGo. Bạn có thể mở ứng dụng từ màn hình chính.');
  });
  if (button) button.addEventListener('click', async () => {
    if (isIOS) {
      update(iosInstructions);
      if (iosGuide) {
        iosGuide.classList.add('selected-guide');
        iosGuide.focus({preventScroll: true});
        iosGuide.scrollIntoView({behavior: 'smooth', block: 'start'});
      }
      return;
    }
    if (!pendingPrompt) {
      document.querySelector('#manual-install')?.scrollIntoView({behavior: 'smooth'});
      update('Trong Chrome, nhấn ⋮ → Thêm vào màn hình chính → Cài đặt. Tên mục có thể khác theo phiên bản Chrome.');
      return;
    }
    const prompt = pendingPrompt;
    pendingPrompt = null;
    button.disabled = true;
    try {
      await prompt.prompt();
      const choice = await prompt.userChoice;
      update(choice.outcome === 'accepted'
        ? 'Đã gửi yêu cầu cài đặt. Chrome sẽ thêm biểu tượng HanziGo khi hoàn tất.'
        : 'Bạn có thể cài lại bằng menu ⋮ của Chrome khi muốn.');
    } catch (_) {
      update('Hãy dùng menu ⋮ của Chrome → Thêm vào màn hình chính để cài đặt.');
    } finally {
      button.disabled = false;
    }
  });
  update(installed ? 'Bạn đang mở HanziGo trong cửa sổ ứng dụng.'
    : isIOS ? 'Cài miễn phí trên iPhone/iPad bằng Safari. Nhấn Cài HanziGo để xem các bước; Safari yêu cầu xác nhận trong menu Chia sẻ.'
    : 'Cài miễn phí trên Android bằng Chrome. Nhấn Cài HanziGo hoặc xem hướng dẫn Android và iPhone/iPad bên dưới.');
  // Live server data stays on the network. The worker only supplies an offline
  // navigation message; it never stores accounts, messages, API data or app code.
  if ('serviceWorker' in navigator && window.isSecureContext) {
    navigator.serviceWorker.register('/hanzigo-worker.js', {scope: '/', updateViaCache: 'none'})
      .catch(() => { /* Installation from Chrome's menu remains available. */ });
  }
})();
