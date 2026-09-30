export function renderChatInbox(content, initial, api) {
  const panel = document.createElement('section');
  panel.className = 'chat-inbox';
  panel.innerHTML = `<aside class="chat-list"><form class="chat-filter"><input aria-label="Tìm hội thoại" placeholder="Tên học viên / khách"><select aria-label="Trạng thái"><option value="all">Tất cả hội thoại</option><option value="waiting">Chờ quản trị viên</option><option value="admin">Đang hỗ trợ</option><option value="ai">AI hỗ trợ</option></select><button>Tìm</button></form><div class="chat-threads"></div><div class="chat-paging"><button class="prev">Trước</button><span></span><button class="next">Sau</button></div></aside>
    <div class="chat-detail"><header><h2>Chọn cuộc trò chuyện</h2><p class="chat-mode"></p><button class="take" disabled>Tiếp nhận</button> <button class="resume" disabled>Giao lại cho AI</button></header><div class="chat-history" role="log" aria-live="polite"></div><p class="chat-error" role="status"></p><form class="chat-compose"><textarea aria-label="Trả lời người dùng" placeholder="Nhập phản hồi của quản trị viên…" maxlength="3000" rows="3" required disabled></textarea><button disabled>Gửi trả lời</button></form></div>`;
  content.append(panel);
  const $ = s => panel.querySelector(s);
  const labels = {ai:'AI hỗ trợ',waiting:'Chờ quản trị viên',admin:'Quản trị viên đang hỗ trợ'};
  let active = null, last = 0, offset = 0, search = '', filter = 'all', fetching = false, sending = false, pending = null;
  function fail(err) { if(panel.isConnected) $('.chat-error').textContent = err.message; }
  function list(data) {
    const el = $('.chat-threads'); el.replaceChildren();
    if(!data.items.length) el.textContent = 'Chưa có hội thoại phù hợp.';
    for(const item of data.items) {
      const button = document.createElement('button'); button.className = 'chat-thread' + (item.id === active ? ' selected' : '');
      const title = document.createElement('strong'); title.textContent = item.name + (item.user_id ? ' · Học viên' : ' · Khách');
      const status = document.createElement('small'); status.textContent = labels[item.state] + ' · ' + new Date(item.updated_at*1000).toLocaleString('vi-VN');
      const preview = document.createElement('span'); preview.textContent = (item.preview || 'Chưa có tin nhắn').slice(0,120);
      button.append(title,status,preview); button.onclick = () => select(item.id); el.append(button);
    }
    $('.chat-paging span').textContent = data.total ? `${offset+1}–${Math.min(offset+40,data.total)} / ${data.total}` : '0';
    $('.prev').disabled = offset === 0; $('.next').disabled = offset + 40 >= data.total;
  }
  async function reloadList() {
    const key = `${offset}|${search}|${filter}`;
    const data = await api(`/admin/chats?offset=${offset}&search=${encodeURIComponent(search)}&state=${filter}`);
    if(panel.isConnected && key === `${offset}|${search}|${filter}`) list(data);
  }
  async function history() {
    const id = active;
    if(!id) return;
    let more = true;
    while(more && active === id && panel.isConnected) {
      const data = await api(`/admin/chats/${id}?after=${last}`);
      if(active !== id || !panel.isConnected) return;
      $('.chat-detail h2').textContent = data.name;
      $('.chat-mode').textContent = labels[data.state];
      const el = $('.chat-history'), bottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
      for(const m of data.messages) {
        if(m.id <= last) continue;
        const bubble = document.createElement('article'); bubble.className = 'chat-bubble ' + m.role;
        const label = document.createElement('small'); label.textContent = ({user:'Người dùng',assistant:'Trợ lý AI',admin:'Quản trị viên'}[m.role]) + ' · ' + new Date(m.created_at*1000).toLocaleString('vi-VN');
        const text = document.createElement('div'); text.textContent = m.content;
        bubble.append(label,text); el.append(bubble); last = m.id;
      }
      if(bottom) el.scrollTop = el.scrollHeight;
      more = data.messages.length === 100;
    }
  }
  async function select(id) {
    if(sending) return;
    active = id; last = 0; pending = null;
    $('.chat-history').replaceChildren(); $('.chat-error').textContent = ''; $('.chat-compose textarea').value = '';
    panel.querySelectorAll('.chat-detail button,.chat-compose textarea').forEach(el => el.disabled = false);
    try { await history(); await reloadList(); } catch(err) { fail(err); }
  }
  $('.chat-filter').onsubmit = e => { e.preventDefault(); search = $('.chat-filter input').value.trim(); filter = $('.chat-filter select').value; offset = 0; reloadList().catch(fail); };
  $('.prev').onclick = () => { offset = Math.max(0,offset-40); reloadList().catch(fail); };
  $('.next').onclick = () => { offset += 40; reloadList().catch(fail); };
  for(const [selector,state] of [['.take','admin'],['.resume','ai']]) $(selector).onclick = async () => {
    if(!active) return;
    try { await api(`/admin/chats/${active}`,'PATCH',{state}); await history(); await reloadList(); } catch(err) { fail(err); }
  };
  $('.chat-compose').onsubmit = async e => {
    e.preventDefault(); const text = $('.chat-compose textarea').value.trim();
    if(!active || !text || sending) return;
    const id = active; sending = true; $('.chat-compose button').disabled = true;
    pending = pending && pending.content === text ? pending : {content:text,request_id:crypto.randomUUID()};
    try {
      await api(`/admin/chats/${id}/messages`,'POST',pending);
      if(active === id && panel.isConnected) { $('.chat-compose textarea').value = ''; pending = null; $('.chat-error').textContent = ''; await history(); await reloadList(); }
    } catch(err) { fail(err); }
    finally { sending = false; $('.chat-compose button').disabled = false; }
  };
  list(initial);
  const timer = setInterval(async () => {
    if(!panel.isConnected) { clearInterval(timer); return; }
    if(document.hidden || fetching) return;
    fetching = true;
    try { await reloadList(); await history(); } catch(err) { fail(err); }
    finally { fetching = false; }
  },4000);
}
