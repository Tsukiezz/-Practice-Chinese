/* The Flutter shell supplies the current session in memory, including non-remembered logins. */
(() => {
  const host = document.createElement('div');
  host.style.cssText = 'position:fixed;right:16px;bottom:calc(84px + env(safe-area-inset-bottom));z-index:10000';
  document.body.append(host);
  const root = host.attachShadow({mode: 'open'});
  root.innerHTML = `<style>
    :host{font:14px system-ui,sans-serif;color:var(--chat-text,#173c33)}*{box-sizing:border-box}
    button,textarea{font:inherit}button{cursor:pointer;border:0;border-radius:12px;padding:10px 14px;background:var(--chat-accent,#17634e);color:white}
    button:disabled{opacity:.55;cursor:default}button:focus-visible,textarea:focus-visible{outline:3px solid #e2ac43;outline-offset:2px}
    #launch{box-shadow:0 4px 20px #0003}#panel{width:min(380px,calc(100vw - 24px));height:min(540px,calc(100dvh - 130px));background:var(--chat-surface,#fff);border:1px solid var(--chat-border,#cee0d8);border-radius:18px;box-shadow:0 12px 45px #0003;display:flex;flex-direction:column;overflow:hidden}
    [hidden]{display:none!important}header{display:flex;align-items:center;justify-content:space-between;padding:12px;background:var(--chat-accent,#17634e);color:white}header small{display:block;margin-top:4px;font-size:11px}header button{font-size:20px}
    #messages{flex:1;overflow:auto;padding:12px;background:var(--chat-background,#f2f7f4)}.message{white-space:pre-wrap;overflow-wrap:anywhere;padding:10px 12px;border-radius:12px;background:var(--chat-surface,#fff);margin-bottom:10px;line-height:1.55}.user{background:var(--chat-bubble,#dcefe4);margin-left:26px}.admin{border:1px solid #bc9741}.label{font-size:11px;font-weight:700;display:block;margin-bottom:4px;color:var(--chat-muted,#487265)}
    #status{font-size:12px;padding:8px 12px;min-height:30px}form{display:flex;gap:8px;padding:10px;border-top:1px solid var(--chat-border,#dce7e0)}textarea{color:var(--chat-text,#173c33);background:var(--chat-surface,#fff);flex:1;min-width:0;resize:none;border:1px solid var(--chat-border,#bfd3c7);border-radius:10px;padding:10px}#retry{margin:0 10px 6px}
  </style>
  <button id="launch" aria-expanded="false" aria-controls="panel">💬 Hỏi HanziGo</button>
  <section id="panel" role="region" aria-label="Trò chuyện với HanziGo" hidden>
    <header><div><b>HanziGo · Trợ lý học tập</b><small>AI chuyên biệt tiếng Trung · Quản trị viên hỗ trợ thêm</small></div><button id="close" aria-label="Đóng trò chuyện">×</button></header>
    <div id="welcome" style="flex:1;display:grid;place-items:center"><button id="start">Tôi cần hỗ trợ</button></div>
    <div id="messages" role="log" aria-live="polite" hidden></div><div id="status" role="status"></div>
    <button id="retry" hidden>Thử tải lại</button>
    <button id="retry-send" hidden>Gửi lại tin trước</button>
    <div id="selected" hidden style="padding:6px 12px;overflow-wrap:anywhere"><span></span> <button id="remove-file" aria-label="Bỏ tệp đính kèm">×</button></div>
    <input id="file" type="file" accept=".png,.jpg,.jpeg,.webp,.pdf,.docx,.txt" hidden>
    <form hidden><button id="attach" type="button" aria-label="Đính kèm tệp" title="PNG, JPG, WEBP, PDF, DOCX, TXT · Tối đa 2 MB">📎</button><textarea aria-label="Tin nhắn" placeholder="Nhập câu hỏi hoặc đính kèm tệp…" maxlength="3000" rows="2"></textarea><button id="send">Gửi</button></form>
  </section>`;
  window.addEventListener('hanzigo-chat-theme', event => {
    let colors;
    try { colors = JSON.parse(event.detail); } catch { return; }
    for (const name of ['accent','background','surface','text','muted','border','bubble']) {
      const value = colors[name];
      if (typeof value === 'string' && /^#[0-9a-f]{6}$/i.test(value)) host.style.setProperty('--chat-'+name,value);
      else host.style.removeProperty('--chat-'+name);
    }
  });
  const $ = selector => root.querySelector(selector);
  let token = '', thread = null, last = 0, generation = 0, busy = false, loading = false;
  let pending = null, pendingAccepted = false, selectedFile = null, preparing = false;
  let sessionKey = null, expiryTimer = null;
  const examLeases = new Set();
  let examBlocked = false, guardQueue = Promise.resolve();
  function lockChat(value) {
    examBlocked = value || examLeases.size > 0;
    host.hidden = examBlocked;
    if (examBlocked) {
      reset(); $('#panel').hidden = true; $('#launch').hidden = false;
      $('#launch').setAttribute('aria-expanded', 'false');
    }
  }
  function queueGuard(lease, active) {
    const task = guardQueue.catch(() => {}).then(() => api('/exam-guard', 'POST', {lease, active}));
    guardQueue = task;
    return task;
  }
  window.hanziGoExamGuard = {
    async start(lease) {
      examLeases.add(lease); lockChat(true);
      try {
        // Establish a private guest cookie when there is no authenticated user.
        if (!token) await api('/session', 'POST');
        await queueGuard(lease, true);
        return true;
      } catch (_) {
        examLeases.delete(lease);
        // A timed-out request may already have acquired the lock.
        queueGuard(lease, false).then(data => lockChat(data.blocked)).catch(() => {});
        lockChat(false);
        return false;
      }
    },
    end(lease) {
      if (!examLeases.delete(lease)) return;
      queueGuard(lease, false).then(data => lockChat(data.blocked)).catch(() => {});
      lockChat(examLeases.size > 0);
    },
  };
  setInterval(async () => {
    try {
      for (const lease of examLeases) await queueGuard(lease, true);
      const status = await api('/exam-guard');
      lockChat(status.blocked);
    } catch (_) { /* Local lock remains active through transient network errors. */ }
  }, 30000);
  function selectFile(file) {
    selectedFile = file; $('#file').value = '';
    $('#selected').hidden = !file;
    $('#selected span').textContent = file ? '📎 ' + file.filename : '';
  }
  function controls() {
    $('#send').disabled = busy || preparing || !thread;
    $('#attach').disabled = busy || preparing || !thread;
    $('#retry-send').disabled = busy || preparing;
  }
  function reset() {
    generation++; thread = null; last = 0; pending = null; sessionKey = null;
    busy = false; loading = false; preparing = false; pendingAccepted = false;
    clearTimeout(expiryTimer); selectFile(null);
    $('#messages').replaceChildren(); $('textarea').value = ''; $('#status').textContent = '';
    $('#retry').hidden = true; $('#retry-send').hidden = true;
    $('#welcome').hidden = false; $('#start').disabled = false;
    $('#messages').hidden = true; $('form').hidden = true; controls();
  }
  window.addEventListener('hanzigo-chat-session', event => {
    const next = typeof event.detail === 'string' ? event.detail : '';
    if (next !== token) { token = next; reset(); }
  });
  async function api(path, method = 'GET', body) {
    if (examBlocked && path !== '/exam-guard' && path !== '/session') {
      throw Error('Trợ lý AI bị khóa trong khi làm bài kiểm tra.');
    }
    const response = await fetch('/api/chat' + path, {method, credentials:'same-origin',
      headers: {'Content-Type':'application/json', ...(token ? {Authorization:'Bearer ' + token} : {})},
      body: body ? JSON.stringify(body) : undefined, signal: AbortSignal.timeout(60000)});
    const data = await response.json();
    if (!response.ok) {
      if (response.status === 423) lockChat(true);
      const error = Error(typeof data.detail === 'string' ? data.detail : 'Yêu cầu không hợp lệ. Tệp tối đa 2 MB, nội dung tối đa 3.000 ký tự.');
      error.status = response.status; throw error;
    }
    return data;
  }
  async function download(file, button) {
    const version = generation; button.disabled = true;
    try {
      const data = await api('/' + thread + '/attachments/' + file.id);
      if (version !== generation) return;
      const bytes = Uint8Array.from(atob(data.data_base64), char => char.charCodeAt(0));
      const url = URL.createObjectURL(new Blob([bytes], {type:'application/octet-stream'}));
      const link = document.createElement('a'); link.href = url; link.download = data.filename;
      document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) {
      if (version === generation) { if (error.status === 410) reset(); else $('#status').textContent = error.message; }
    } finally { button.disabled = false; }
  }
  function show(data) {
    if (!data.active) { reset(); return; }
    if (sessionKey && sessionKey !== data.session_key) {
      last = 0; pending = null; pendingAccepted = false;
      $('#messages').replaceChildren(); $('textarea').value = ''; selectFile(null);
    }
    sessionKey = data.session_key;
    $('#welcome').hidden = true; $('#messages').hidden = false; $('form').hidden = false; controls();
    clearTimeout(expiryTimer);
    expiryTimer = setTimeout(reset, Math.max(0, data.expires_at - data.server_now) * 1000);
    const box = $('#messages'), atBottom = box.scrollHeight - box.scrollTop - box.clientHeight < 80;
    if (!last && !data.messages.length) box.textContent = 'Xin chào! Bạn có thể hỏi về tiếng Trung/HanziGo hoặc gửi ảnh PNG, JPG, WEBP (tối đa 2 MB) để AI đọc chữ, giải thích và hướng dẫn học. Ảnh sẽ được gửi tới dịch vụ AI; tránh gửi thông tin riêng tư. PDF/DOCX/TXT được chuyển quản trị viên.';
    for (const message of data.messages) {
      if (pending && message.request_id === pending.request_id) pendingAccepted = true;
      if (message.id <= last) continue;
      if (!last) box.replaceChildren();
      const item = document.createElement('div'); item.className = 'message ' + message.role;
      const label = document.createElement('span'); label.className = 'label';
      label.textContent = ({user:'Bạn',assistant:'Trợ lý AI',admin:'Quản trị viên'}[message.role] || message.role) + ' · ' + new Date(message.created_at * 1000).toLocaleTimeString('vi-VN',{hour:'2-digit',minute:'2-digit'});
      item.append(label, document.createTextNode(message.content));
      if (message.attachment) {
        const file = message.attachment, button = document.createElement('button'); button.type = 'button';
        button.textContent = '📎 Tải ' + file.filename + ' (' + Math.ceil(file.size / 1024) + ' KB)';
        button.style.cssText = 'display:block;max-width:100%;margin-top:8px;overflow-wrap:anywhere;text-align:left';
        button.onclick = () => download(file, button); item.append(button);
      }
      box.append(item); last = message.id;
    }
    if (atBottom) box.scrollTop = box.scrollHeight;
    $('#status').textContent = data.busy_until > data.server_now ? 'AI đang soạn trả lời…' : data.state === 'waiting' ? 'Đã chuyển yêu cầu đến quản trị viên.' : data.state === 'admin' ? 'Quản trị viên đang hỗ trợ bạn.' : 'Bạn đang trò chuyện với AI.';
    $('#retry').hidden = true;
  }
  async function refresh() {
    if (loading || !thread) return;
    const version = generation; loading = true;
    try {
      const data = await api('/' + thread + '?after=' + last);
      if (version !== generation) return;
      show(data);
      if (data.messages.length === 100) { loading = false; return refresh(); }
    } catch (error) {
      if (version === generation) {
        if ([401,403,410].includes(error.status)) reset();
        else { $('#status').textContent = error.message; $('#retry').hidden = false; }
      }
    } finally { if (version === generation) loading = false; }
  }
  $('#launch').onclick = () => {
    if (examBlocked) return;
    $('#panel').hidden = false; $('#launch').hidden = true; $('#launch').setAttribute('aria-expanded','true');
    if (thread) refresh(); else $('#start').focus();
  };
  $('#start').onclick = async () => {
    if (examBlocked) return;
    const version = generation; $('#start').disabled = true; $('#status').textContent = 'Đang mở phiên hỗ trợ…';
    try {
      const data = await api('/session','POST');
      if (version !== generation) return;
      thread = data.id; show(data); $('textarea').focus();
    } catch (error) { if (version === generation) $('#status').textContent = error.message; }
    finally { if (version === generation) $('#start').disabled = false; }
  };
  function close() { $('#panel').hidden = true; $('#launch').hidden = false; $('#launch').setAttribute('aria-expanded','false'); $('#launch').focus(); }
  $('#close').onclick = close;
  root.addEventListener('keydown', event => { if (event.key === 'Escape') close(); });
  $('#retry').onclick = refresh;
  $('#attach').onclick = () => $('#file').click();
  $('#remove-file').onclick = () => selectFile(null);
  $('#file').onchange = async () => {
    const file = $('#file').files[0]; if (!file) return;
    if (!file.size || file.size > 2 * 1024 * 1024 || !/\.(png|jpe?g|webp|pdf|docx|txt)$/i.test(file.name)) {
      $('#status').textContent = 'Chọn PNG, JPG, WEBP, PDF, DOCX hoặc TXT, tối đa 2 MB.'; $('#file').value = ''; return;
    }
    const version = generation; preparing = true; controls(); $('#status').textContent = 'Đang chuẩn bị tệp…';
    try {
      const data = await new Promise((resolve,reject) => {
        const reader = new FileReader(); reader.onload = () => resolve(String(reader.result).split(',')[1]);
        reader.onerror = () => reject(Error('Không đọc được tệp. Vui lòng chọn lại.')); reader.readAsDataURL(file);
      });
      if (version !== generation) return;
      selectFile({filename:file.name, data_base64:data}); $('#status').textContent = 'Tệp đã sẵn sàng. Nhấn Gửi để đính kèm.';
    } catch (error) { if (version === generation) $('#status').textContent = error.message; }
    finally { if (version === generation) { preparing = false; controls(); } }
  };
  async function deliver(request) {
    if (examBlocked || !thread || busy || preparing) return;
    const version = generation; busy = true; pending = request; pendingAccepted = false;
    controls(); $('#retry-send').hidden = true;
    clearTimeout(expiryTimer); expiryTimer = setTimeout(reset,300000);
    $('#status').textContent = request.attachment ? 'Đang gửi tin nhắn và tệp…' : 'Đang gửi, AI sẽ phản hồi ngay khi xử lý xong…';
    try {
      await api('/' + thread + '/messages','POST',request);
      if (version !== generation) return;
      pending = null; await refresh();
    } catch (error) {
      if (version !== generation) return;
      if ([401,403,410].includes(error.status)) { reset(); return; }
      await refresh();
      if (version !== generation) return;
      if (pendingAccepted) { pending = null; $('#status').textContent = 'Tin đã được nhận. Đang cập nhật phản hồi…'; }
      else { $('#status').textContent = error.message + ' Có thể gửi lại tin trước.'; $('#retry-send').hidden = false; }
    } finally { if (version === generation) { busy = false; controls(); } }
  }
  $('form').onsubmit = event => {
    event.preventDefault();
    const content = $('textarea').value.trim();
    if ((!content && !selectedFile) || busy || preparing || !thread) return;
    const request = {content,attachment:selectedFile,request_id:crypto.randomUUID(),session_key:sessionKey};
    // Clear only the submitted draft immediately; never erase text typed while AI is replying.
    $('textarea').value = ''; selectFile(null); deliver(request);
  };
  $('#retry-send').onclick = () => { if (pending) deliver(pending); };
  setInterval(() => { if (!$('#panel').hidden && !document.hidden) refresh(); },4000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden && thread) refresh(); });
  reset();
})();
