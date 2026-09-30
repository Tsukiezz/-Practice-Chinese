const escape = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const states = {ai:'AI đang hỗ trợ',waiting:'Chờ quản trị viên',admin:'Quản trị viên hỗ trợ'};
const roles = {user:'Người dùng',assistant:'Trợ lý AI',admin:'Quản trị viên'};
const stamp = value => new Date(value*1000).toLocaleString('vi-VN',{hour:'2-digit',minute:'2-digit',day:'2-digit',month:'2-digit',year:'numeric'});

export function renderChatInbox(content, initial, api) {
  const panel = document.createElement('section');
  panel.className = 'support-workspace';
  panel.innerHTML = '<div class="support-overview"><div><b>Hội thoại hỗ trợ</b><span class="chat-counts"></span></div><div class="support-sync"><span class="chat-sync" role="status">Tự cập nhật mỗi 4 giây</span><button class="chat-refresh">↻ Làm mới</button></div></div>' +
    '<div class="chat-inbox"><aside class="chat-list" aria-label="Danh sách hội thoại"><form class="chat-filter"><label>Tìm người trò chuyện<input type="search" maxlength="100" placeholder="Tên học viên hoặc mã khách…" aria-label="Tìm hội thoại"></label><div><select aria-label="Trạng thái"><option value="all">Tất cả hội thoại</option><option value="waiting">Chờ quản trị viên</option><option value="admin">Đang tiếp nhận</option><option value="ai">AI hỗ trợ</option></select><button>Tìm</button></div></form><div class="chat-threads"></div><div class="chat-paging"><button class="prev" aria-label="Trang hội thoại trước">←</button><span></span><button class="next" aria-label="Trang hội thoại sau">→</button></div></aside>' +
    '<section class="chat-detail" aria-label="Nội dung hội thoại"><header class="chat-detail-head"><button class="chat-back">← Danh sách</button><div class="chat-person"><span class="chat-avatar">聊</span><div><h2>Chọn một hội thoại</h2><p class="chat-mode">Xem lịch sử và hỗ trợ người học tại đây.</p></div></div><div class="chat-ownership"><button class="take" disabled>Tiếp nhận</button><button class="resume" disabled>Giao lại cho AI</button></div></header>' +
    '<div class="chat-history" role="log" aria-live="polite" aria-label="Lịch sử hội thoại"><button class="chat-older" hidden>Xem tin nhắn cũ hơn</button><div class="chat-messages"><div class="chat-welcome"><span>聊</span><h3>Mọi trao đổi, trong một nơi</h3><p>Chọn khách hoặc học viên bên cạnh để xem tin nhắn của người dùng, AI và quản trị viên.</p></div></div></div><button class="chat-new" hidden>↓ Có tin nhắn mới</button><div class="chat-error" role="status"></div>' +
    '<form class="chat-compose"><label class="chat-compose-label">Phản hồi của quản trị viên<textarea aria-label="Trả lời người dùng" placeholder="Nhập nội dung hỗ trợ…" maxlength="3000" rows="3" required disabled></textarea></label><div class="chat-compose-footer"><small class="chat-hint">Chọn hội thoại để bắt đầu.</small><button class="primary" disabled>Gửi trả lời</button></div></form></section></div>';
  content.append(panel);
  const $ = s => panel.querySelector(s), alive = () => panel.isConnected;
  let active = null, version = 0, first = 0, last = 0, offset = 0, search = '', filter = 'all';
  let listRequest = 0, historyRequest = null, fetching = false, olderBusy = false, changing = false, currentState = null;
  const drafts = new Map(), requests = new Map(), sending = new Set(), nodes = new Map();
  const fail = err => { if(alive()) $('.chat-error').textContent = err.message; };
  const bottom = () => { const el = $('.chat-history'); el.scrollTop = el.scrollHeight; $('.chat-new').hidden = true; };
  function controls() {
    $('.chat-compose textarea').disabled = !active;
    $('.chat-compose button').disabled = !active || sending.has(active);
    $('.chat-compose button').textContent = sending.has(active) ? 'Đang gửi…' : 'Gửi trả lời';
    $('.take').disabled = !active || changing || currentState === 'admin';
    $('.resume').disabled = !active || changing || currentState === 'ai';
    $('.chat-hint').textContent = active ? 'Ctrl + Enter để gửi · Gửi trả lời sẽ tạm dừng AI.' : 'Chọn hội thoại để bắt đầu.';
  }
  function list(data) {
    const el = $('.chat-threads'), keep = new Set();
    data.items.forEach((item,index) => {
      keep.add(item.id);
      let button = nodes.get(item.id);
      if(!button) { button = document.createElement('button'); button.type = 'button'; button.className = 'chat-thread'; button.onclick = () => select(item.id); nodes.set(item.id,button); }
      const html = '<span class="chat-avatar">'+escape(item.name.trim().slice(0,1)||'K')+'</span><span class="chat-thread-body"><span class="chat-thread-title"><strong>'+escape(item.name)+'</strong><small>'+(item.user_id?'Học viên':'Khách')+'</small></span><span class="chat-preview">'+escape(roles[item.last_role] ? roles[item.last_role]+': ' : '')+escape(item.preview||'Chưa có tin nhắn')+'</span><span class="chat-thread-meta"><span class="support-badge '+item.state+'">'+states[item.state]+'</span><time>'+stamp(item.updated_at)+'</time></span></span>';
      if(button.innerHTML !== html) button.innerHTML = html;
      button.classList.toggle('selected',item.id===active); button.setAttribute('aria-current',String(item.id===active));
      if(el.children[index] !== button) el.insertBefore(button,el.children[index]||null);
    });
    for(const [id,node] of nodes) if(!keep.has(id)) { node.remove(); nodes.delete(id); }
    el.querySelector('.chat-empty-list')?.remove();
    if(!data.items.length) { const empty=document.createElement('p'); empty.className='chat-empty-list'; empty.textContent='Không có hội thoại phù hợp với bộ lọc.'; el.append(empty); }
    $('.chat-paging span').textContent = data.total ? (offset+1)+'–'+Math.min(offset+40,data.total)+' / '+data.total : '0 hội thoại';
    $('.prev').disabled=offset===0; $('.next').disabled=offset+40>=data.total;
    const counts=data.counts||{};
    $('.chat-counts').textContent=((counts.ai||0)+(counts.waiting||0)+(counts.admin||0))+' hội thoại · '+(counts.waiting||0)+' đang chờ tiếp nhận';
  }
  async function reloadList() {
    if(!alive()) return;
    const request=++listRequest;
    const data=await api('/admin/chats?offset='+offset+'&search='+encodeURIComponent(search)+'&state='+filter);
    if(alive() && request===listRequest) list(data);
  }
  function renderMessages(data,mode) {
    const el=$('.chat-history'), box=$('.chat-messages'), nearBottom=el.scrollHeight-el.scrollTop-el.clientHeight<70, height=el.scrollHeight, top=el.scrollTop;
    $('.chat-detail h2').textContent=data.name; currentState=data.state; controls();
    $('.chat-person .chat-avatar').textContent=data.name.trim().slice(0,1)||'K';
    $('.chat-mode').textContent=data.busy_until>Date.now()/1000?'AI đang soạn trả lời…':states[data.state];
    $('.chat-mode').className='chat-mode '+data.state;
    if(mode==='initial') { box.replaceChildren(); first=0; last=0; }
    const fragment=document.createDocumentFragment();
    for(const m of data.messages) {
      if((mode==='newer' && m.id<=last)||(mode==='older' && m.id>=first)) continue;
      const bubble=document.createElement('article'); bubble.className='chat-bubble '+m.role;
      const label=document.createElement('div'); label.className='chat-message-label';
      const author=document.createElement('b'); author.textContent=roles[m.role]||m.role;
      const time=document.createElement('time'); time.textContent=stamp(m.created_at); label.append(author,time);
      const text=document.createElement('div'); text.className='chat-message-text'; text.textContent=m.content;
      bubble.append(label,text); fragment.append(bubble); if(mode!=='older') last=Math.max(last,m.id);
    }
    const added=fragment.childElementCount;
    if(mode==='older') box.prepend(fragment); else box.append(fragment);
    if(data.messages.length && mode!=='newer') first=data.messages[0].id;
    if(mode!=='newer') $('.chat-older').hidden=!data.has_older;
    if(mode==='initial' && !data.messages.length) box.innerHTML='<p class="chat-empty-list">Hội thoại chưa có tin nhắn. Bạn có thể gửi lời chào để bắt đầu.</p>';
    if(mode==='newer' && added) box.querySelector('.chat-empty-list')?.remove();
    if(mode==='older') el.scrollTop=top+el.scrollHeight-height;
    else if(mode==='initial'||nearBottom) bottom();
    else if(added) $('.chat-new').hidden=false;
  }
  async function history(initialLoad=false) {
    if(!alive() || !active || historyRequest===version) return;
    const id=active, current=version; historyRequest=current;
    try {
      let more=true, initial=initialLoad;
      while(more && alive() && current===version) {
        const data=await api('/admin/chats/'+id+'?'+(initial?'recent=true':'after='+last));
        if(!alive()||current!==version) return;
        renderMessages(data,initial?'initial':'newer');
        more=!initial && data.messages.length===100; initial=false;
      }
    } finally { if(historyRequest===current) historyRequest=null; }
  }
  async function select(id) {
    panel.classList.add('detail-open'); if(active===id) return;
    active=id; version++; first=0; last=0; currentState=null; changing=false; olderBusy=false;
    $('.chat-messages').innerHTML='<p class="chat-empty-list" role="status">Đang tải hội thoại…</p>';
    $('.chat-older').hidden=true; $('.chat-older').disabled=false; $('.chat-new').hidden=true; $('.chat-error').textContent='';
    $('.chat-compose textarea').value=drafts.get(id)||''; controls();
    for(const [key,node] of nodes) { node.classList.toggle('selected',key===id); node.setAttribute('aria-current',String(key===id)); }
    try { await history(true); } catch(err) { fail(err); }
  }
  $('.chat-compose textarea').oninput=e=>{if(active) drafts.set(active,e.target.value);};
  $('.chat-compose textarea').onkeydown=e=>{if((e.ctrlKey||e.metaKey)&&e.key==='Enter'&&!e.isComposing){e.preventDefault();$('.chat-compose').requestSubmit();}};
  $('.chat-back').onclick=()=>panel.classList.remove('detail-open');
  $('.chat-new').onclick=bottom;
  $('.chat-history').onscroll=()=>{const el=$('.chat-history');if(el.scrollHeight-el.scrollTop-el.clientHeight<70)$('.chat-new').hidden=true;};
  $('.chat-older').onclick=async()=>{
    if(!active||!first||olderBusy)return;
    olderBusy=true;$('.chat-older').disabled=true;const current=version;
    try{const data=await api('/admin/chats/'+active+'?before='+first);if(alive()&&current===version)renderMessages(data,'older');}catch(err){fail(err);}
    finally{if(current===version){olderBusy=false;$('.chat-older').disabled=false;}}
  };
  $('.chat-filter').onsubmit=e=>{e.preventDefault();search=$('.chat-filter input').value.trim();filter=$('.chat-filter select').value;offset=0;reloadList().catch(fail);};
  $('.chat-filter select').onchange=()=>$('.chat-filter').requestSubmit();
  $('.prev').onclick=()=>{offset=Math.max(0,offset-40);reloadList().catch(fail);};
  $('.next').onclick=()=>{offset+=40;reloadList().catch(fail);};
  for(const [selector,state] of [['.take','admin'],['.resume','ai']]) $(selector).onclick=async()=>{
    if(!active||changing)return;
    const current=version;changing=true;controls();$('.chat-error').textContent='';
    try{await api('/admin/chats/'+active,'PATCH',{state});if(current===version&&alive()){currentState=state;await history();}await reloadList();}catch(err){fail(err);}
    finally{if(current===version){changing=false;controls();}}
  };
  $('.chat-compose').onsubmit=async e=>{
    e.preventDefault();const text=$('.chat-compose textarea').value.trim(),id=active;
    if(!id||!text||sending.has(id))return;
    const old=requests.get(id),request=old?.content===text?old:{content:text,request_id:crypto.randomUUID()};
    requests.set(id,request);sending.add(id);controls();$('.chat-error').textContent='';
    try{
      await api('/admin/chats/'+id+'/messages','POST',request);requests.delete(id);
      if((drafts.get(id)||'').trim()===text){drafts.delete(id);if(active===id)$('.chat-compose textarea').value='';}
      if(alive()&&active===id){await history();bottom();}await reloadList();
    }catch(err){fail(err);}finally{sending.delete(id);if(alive())controls();}
  };
  async function refresh(){
    if(!alive()||fetching)return;
    fetching=true;$('.chat-refresh').disabled=true;
    const results=await Promise.allSettled([reloadList(),history(!last)]);
    if(alive()){$('.chat-sync').textContent=results.some(r=>r.status==='rejected')?'Chưa cập nhật được · Bấm làm mới để thử lại':'Đã cập nhật '+new Date().toLocaleTimeString('vi-VN');$('.chat-refresh').disabled=false;}
    fetching=false;
  }
  $('.chat-refresh').onclick=()=>{$('.chat-error').textContent='';refresh();};
  list(initial);
  async function poll(){if(!alive())return;if(!document.hidden)await refresh();if(alive())setTimeout(poll,4000);}
  setTimeout(poll,4000);
}
