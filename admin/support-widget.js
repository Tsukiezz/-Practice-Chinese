/* The Flutter shell supplies the current session in memory, including non-remembered logins. */
(() => {
  const host = document.createElement('div');
  host.style.cssText = 'position:fixed;right:16px;bottom:calc(84px + env(safe-area-inset-bottom));z-index:10000';
  document.body.append(host);
  const root = host.attachShadow({mode: 'open'});
  root.innerHTML = `<style>
    :host{font:14px system-ui,sans-serif;color:#173c33}*{box-sizing:border-box}
    button,textarea{font:inherit}button{cursor:pointer;border:0;border-radius:12px;padding:10px 14px;background:#17634e;color:white}
    button:disabled{opacity:.55;cursor:wait}button:focus-visible,textarea:focus-visible{outline:3px solid #e2ac43;outline-offset:2px}
    #launch{box-shadow:0 4px 20px #0003}#panel{width:min(380px,calc(100vw - 24px));height:min(540px,calc(100dvh - 130px));background:#fff;border:1px solid #cee0d8;border-radius:18px;box-shadow:0 12px 45px #0003;display:flex;flex-direction:column;overflow:hidden}
    [hidden]{display:none!important}header{display:flex;align-items:center;justify-content:space-between;padding:12px;background:#17634e;color:white}header small{display:block;margin-top:4px;font-size:11px}header button{font-size:20px}
    #messages{flex:1;overflow:auto;padding:12px;background:#f2f7f4}.message{white-space:pre-wrap;overflow-wrap:anywhere;padding:10px 12px;border-radius:12px;background:white;margin-bottom:10px;line-height:1.55}.user{background:#dcefe4;margin-left:26px}.admin{border:1px solid #bc9741}.label{font-size:11px;font-weight:700;display:block;margin-bottom:4px;color:#487265}
    #status{font-size:12px;padding:8px 12px;min-height:30px}form{display:flex;gap:8px;padding:10px;border-top:1px solid #dce7e0}textarea{flex:1;min-width:0;resize:none;border:1px solid #bfd3c7;border-radius:10px;padding:10px}#retry{margin:0 10px 6px}
  </style>
  <button id="launch" aria-expanded="false" aria-controls="panel">💬 Hỏi HanziGo</button>
  <section id="panel" role="region" aria-label="Trò chuyện với HanziGo" hidden>
    <header><div><b>HanziGo · Trợ lý học tập</b><small>AI hỗ trợ tiếng Trung · Quản trị viên hỗ trợ thêm</small></div><button id="close" aria-label="Đóng trò chuyện">×</button></header>
    <div id="messages" role="log" aria-live="polite"></div><div id="status" role="status"></div>
    <button id="retry" hidden>Thử tải lại</button>
    <form><textarea aria-label="Tin nhắn" placeholder="Hỏi về tiếng Trung hoặc cần hỗ trợ…" maxlength="3000" rows="2" required></textarea><button id="send">Gửi</button></form>
  </section>`;
  const $ = s => root.querySelector(s);
  let token = '', thread = null, last = 0, generation = 0, busy = false, loading = false;
  let pending = null;
  window.addEventListener('hanzigo-chat-session', event => {
    const next = typeof event.detail === 'string' ? event.detail : '';
    if (next === token) return;
    token = next; generation++; thread = null; last = 0; pending = null; busy = false; loading = false;
    $('#messages').replaceChildren(); $('textarea').value = ''; $('#send').disabled = false;
    if (!$('#panel').hidden) refresh();
  });
  async function api(path, method = 'GET', body) {
    const response = await fetch('/api/chat' + path, {method, credentials:'same-origin',
      headers: {'Content-Type':'application/json', ...(token ? {Authorization:'Bearer ' + token} : {})},
      body: body ? JSON.stringify(body) : undefined, signal: AbortSignal.timeout(60000)});
    const data = await response.json();
    if (!response.ok) throw Error(typeof data.detail === 'string' ? data.detail : 'Không thể gửi tin nhắn. Vui lòng thử lại.');
    return data;
  }
  function show(data) {
    const box = $('#messages'), atBottom = box.scrollHeight - box.scrollTop - box.clientHeight < 80;
    if (!last && !data.messages.length) box.textContent = 'Xin chào! Bạn muốn học tiếng Trung từ đâu? Hãy cho biết trình độ hoặc gửi câu hỏi của bạn. Lịch sử được lưu để quản trị viên có thể hỗ trợ.';
    for (const m of data.messages) {
      if (m.id <= last) continue;
      if (!last) box.replaceChildren();
      const item = document.createElement('div'); item.className = 'message ' + m.role;
      const label = document.createElement('span'); label.className = 'label';
      label.textContent = ({user:'Bạn',assistant:'Trợ lý AI',admin:'Quản trị viên'}[m.role] || m.role) + ' · ' + new Date(m.created_at * 1000).toLocaleTimeString('vi-VN',{hour:'2-digit',minute:'2-digit'});
      item.append(label, document.createTextNode(m.content)); box.append(item); last = m.id;
    }
    if (atBottom) box.scrollTop = box.scrollHeight;
    $('#status').textContent = data.busy_until > Date.now()/1000 ? 'AI đang soạn trả lời…' : data.state === 'waiting' ? 'Đã chuyển yêu cầu đến quản trị viên.' : data.state === 'admin' ? 'Quản trị viên đang hỗ trợ bạn.' : 'Bạn đang trò chuyện với AI.';
    $('#retry').hidden = true;
  }
  async function refresh() {
    if (loading) return;
    const version = generation; loading = true;
    try {
      let data;
      if (!thread) {
        data = await api('/session', 'POST');
        if (version !== generation) return;
        thread = data.id;
      } else data = await api('/' + thread + '?after=' + last);
      if (version !== generation) return;
      show(data);
      if (data.messages.length === 100) { loading = false; return refresh(); }
    } catch (err) {
      if (version === generation) { $('#status').textContent = err.message; $('#retry').hidden = false; }
    } finally { if (version === generation) loading = false; }
  }
  $('#launch').onclick = () => { $('#panel').hidden = false; $('#launch').hidden = true; $('#launch').setAttribute('aria-expanded','true'); refresh(); $('textarea').focus(); };
  function close() { $('#panel').hidden = true; $('#launch').hidden = false; $('#launch').setAttribute('aria-expanded','false'); $('#launch').focus(); }
  $('#close').onclick = close;
  root.addEventListener('keydown', e => { if(e.key === 'Escape') close(); });
  $('#retry').onclick = refresh;
  $('form').onsubmit = async event => {
    event.preventDefault();
    const content = $('textarea').value.trim();
    if (!content || busy) return;
    const version = generation; busy = true; $('#send').disabled = true;
    try {
      if (!thread) await refresh();
      if (!thread || version !== generation) return;
      pending = pending && pending.content === content ? pending : {content,request_id:crypto.randomUUID()};
      $('#status').textContent = 'Đang gửi và chờ trả lời…';
      await api('/' + thread + '/messages', 'POST', pending);
      if (version !== generation) return;
      $('textarea').value = ''; pending = null;
      await refresh();
    } catch (err) { if (version === generation) $('#status').textContent = err.message + ' Nội dung vẫn được giữ để gửi lại.'; }
    finally { if (version === generation) { busy = false; $('#send').disabled = false; } }
  };
  setInterval(() => { if (!$('#panel').hidden && !document.hidden) refresh(); }, 4000);
})();
