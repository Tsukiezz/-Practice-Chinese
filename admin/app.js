const root = document.querySelector('#app');
const dialog = document.querySelector('#editor');
const pages = {
  dashboard: ['Tổng quan', 'Bức tranh học tập toàn hệ thống, cập nhật từ cơ sở dữ liệu.'],
  users: ['Người dùng', 'Quản lý quyền truy cập và trạng thái tài khoản học viên.'],
  vocabulary: ['Kho từ & nét chuẩn', 'Nguồn từ vựng và thứ tự nét dùng chung cho ứng dụng học tập.'],
  exams: ['Ngân hàng đề', 'Biên soạn bài Nghe, Đọc, Viết theo HSK 1–6.'],
  results: ['Duyệt kết quả', 'Xem bài làm, xử lý khiếu nại và theo dõi lịch sử điều chỉnh điểm.'],
  ai: ['Cấu hình AI', 'Quản lý model, hướng dẫn chấm và giới hạn xử lý tập trung.'],
  logs: ['Nhật ký quản trị', 'Các thay đổi được ghi nhận cùng người thực hiện và thời gian.'],
};
let token = sessionStorage.getItem('hanzigo_admin_token') || '';
let user = null;
let page = 'dashboard';
let loadId = 0;
let noticeTimer;
let strokes = [];
const escape = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const date = value => new Date(value * 1000).toLocaleString('vi-VN');
const brand = '<div class="brand"><span class="seal">汉</span><div>HanziGo<small>ADMIN WORKSPACE</small></div></div>';
const statusLabel = value => ({published:'Đã phát hành',draft:'Bản nháp',hidden:'Đã ẩn',admin:'Quản trị viên',student:'Học viên'}[value] || value);

// Desktop testers can use the same compact layout as a phone without DevTools.
const previewControls = document.createElement('div');
previewControls.className = 'preview-controls';
previewControls.innerHTML = '<span>HanziGo Admin</span><button type="button" aria-pressed="false">Xem giao diện điện thoại</button>';
document.body.insertBefore(previewControls, root);
previewControls.querySelector('button').onclick = event => {
  setMenu(false);
  const active = document.body.classList.toggle('preview-mobile');
  event.currentTarget.setAttribute('aria-pressed', String(active));
  event.currentTarget.textContent = active ? 'Trở về giao diện máy tính' : 'Xem giao diện điện thoại';
};

function setMenu(open, restoreFocus = false) {
  const sidebar = document.querySelector('.sidebar');
  const toggle = document.querySelector('#menu-toggle');
  if (!sidebar || !toggle) return;
  sidebar.classList.toggle('menu-open', open);
  toggle.setAttribute('aria-expanded', String(open));
  toggle.setAttribute('aria-label', open ? 'Đóng menu quản trị' : 'Mở menu quản trị');
  if (restoreFocus) toggle.focus();
}

document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && !dialog.open && document.querySelector('.sidebar.menu-open')) setMenu(false, true);
});
document.addEventListener('click', event => {
  const sidebar = document.querySelector('.sidebar.menu-open');
  if (sidebar && !sidebar.contains(event.target)) setMenu(false);
});
let compactLayout = false;
new ResizeObserver(([entry]) => {
  const compact = entry.contentRect.width <= 700;
  if (compact !== compactLayout) setMenu(false);
  compactLayout = compact;
}).observe(root);

function notify(message) {
  document.querySelector('#notice').textContent = message;
  clearTimeout(noticeTimer);
  noticeTimer = setTimeout(() => document.querySelector('#notice').textContent = '', 4500);
}

async function api(path, method = 'GET', body) {
  let response;
  try {
    response = await fetch(`/api${path}`, {
      method, headers: {'Content-Type':'application/json', ...(token ? {Authorization:`Bearer ${token}`} : {})},
      ...(body === undefined ? {} : {body:JSON.stringify(body)}),
    });
  } catch { throw new Error('Không kết nối được máy chủ. Kiểm tra kết nối rồi thử lại.'); }
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if ((response.status === 401 || response.status === 403) && user) {
      clearSession();
      loginView();
    }
    const message = Array.isArray(data.detail)
      ? data.detail.map(e => `${e.loc.slice(1).join('.')}: ${e.msg}`).join('\n')
      : data.detail;
    throw new Error(message || 'Không thực hiện được thao tác. Vui lòng thử lại.');
  }
  return data;
}

function clearSession() {
  token = ''; user = null; loadId++;
  sessionStorage.removeItem('hanzigo_admin_token');
  dialog.close();
}

function loginView(error = '') {
  root.innerHTML = `<div class="login"><aside class="login-art">${brand}<div><div class="character">学 · 习</div><h1>Chăm chút từng<br>hành trình học.</h1><p>Không gian quản trị dành cho đội ngũ Chinese Learning. Nội dung tốt tạo nên trải nghiệm học tốt.</p></div><small>HanziGo · Chinese Learning</small></aside><section class="login-wrap"><form id="login" class="login-form"><div><div class="eyebrow">CHÀO MỪNG TRỞ LẠI</div><h2>Đăng nhập quản trị</h2><p>Sử dụng tài khoản Admin được cấp cho dự án.</p></div><label>Email<input name="email" type="email" autocomplete="username" required maxlength="120"></label><label>Mật khẩu<input name="password" type="password" autocomplete="current-password" required maxlength="128"></label><div id="login-error" role="alert">${error ? `<div class="error">${escape(error)}</div>` : ''}</div><button class="primary">Đăng nhập →</button><small>Quyền quản trị được xác minh trên máy chủ.</small></form></section></div>`;
  document.querySelector('#login').onsubmit = async event => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector('button');
    button.disabled = true;
    try {
      const result = await api('/auth/login', 'POST', Object.fromEntries(new FormData(form)));
      token = result.token;
      if (result.user.role !== 'admin') {
        await api('/auth/logout', 'POST');
        clearSession();
        throw new Error('Tài khoản này không có quyền quản trị. Hãy đăng nhập bằng tài khoản Admin.');
      }
      user = result.user;
      sessionStorage.setItem('hanzigo_admin_token', token);
      shell();
    } catch (err) { document.querySelector('#login-error').innerHTML = `<div class="error">${escape(err.message)}</div>`; }
    finally { button.disabled = false; }
  };
}

function shell() {
  const navButton = key => `<button data-page="${key}">${pages[key][0]}</button>`;
  root.innerHTML = `<div class="layout"><aside class="sidebar">${brand}<button type="button" id="menu-toggle" class="menu-toggle" aria-label="Mở menu quản trị" aria-expanded="false" aria-controls="admin-menu"><svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button><div id="admin-menu" class="sidebar-menu"><nav aria-label="Quản trị">${navButton('dashboard')}<div class="nav-group"><span class="nav-label">Học tập</span>${['vocabulary','exams','results'].map(navButton).join('')}</div><div class="nav-group"><span class="nav-label">Hệ thống</span>${['users','ai','logs'].map(navButton).join('')}</div></nav><div class="account"><div><b>${escape(user.name)}</b><small>${escape(user.email)}</small></div><button id="logout">Đăng xuất</button></div></div></aside><main class="main"><div class="topline"><span>CHINESE LEARNING / QUẢN TRỊ</span><span class="pill">Không gian quản trị</span></div><div id="content"></div></main></div>`;
  document.querySelector('#menu-toggle').onclick = event => {
    setMenu(event.currentTarget.getAttribute('aria-expanded') !== 'true');
  };
  document.querySelectorAll('[data-page]').forEach(button => button.onclick = () => {
    page = button.dataset.page;
    setMenu(false);
    loadPage().then(() => document.querySelector('#content h1')?.focus());
  });
  document.querySelector('#logout').onclick = async () => {
    try { await api('/auth/logout', 'POST'); clearSession(); loginView(); }
    catch (err) { notify(err.message); }
  };
  loadPage();
}

function heading() {
  return `<header class="intro"><div class="eyebrow">HANZIGO CONTROL CENTER</div><h1 tabindex="-1">${pages[page][0]}</h1><p>${pages[page][1]}</p></header>`;
}

function table(headers, rows) {
  if (!rows.length) return '<div class="empty">Chưa có dữ liệu phù hợp.<br>Hãy thêm nội dung hoặc thay đổi bộ lọc.</div>';
  const element = document.createElement('table');
  element.className = 'responsive-table';
  element.setAttribute('role', 'table');
  element.innerHTML = `<thead><tr>${headers.map(h => `<th scope="col">${escape(h)}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody>`;
  for (const row of element.tBodies[0].rows) {
    row.setAttribute('role', 'row');
    [...row.cells].forEach((cell, index) => {
      cell.dataset.label = headers[index];
      cell.setAttribute('role', 'cell');
    });
  }
  return `<div class="table-wrap">${element.outerHTML}</div>`;
}

async function loadPage(params = '') {
  const id = ++loadId;
  document.querySelectorAll('[data-page]').forEach(b => {
    b.classList.toggle('active', b.dataset.page === page);
    if (b.dataset.page === page) b.setAttribute('aria-current', 'page');
    else b.removeAttribute('aria-current');
  });
  const content = document.querySelector('#content');
  if (!content) return;
  content.innerHTML = heading() + '<div class="loading" role="status">Đang tải dữ liệu…</div>';
  try {
    const endpoint = {dashboard:'/admin/dashboard',users:'/admin/users',vocabulary:'/admin/vocabulary',exams:'/admin/exams',results:'/admin/results',ai:'/admin/ai-config',logs:'/admin/audit-logs'}[page];
    const data = await api(endpoint + params);
    if (id !== loadId) return;
    content.innerHTML = heading();
    ({dashboard:renderDashboard, users:renderUsers, vocabulary:renderWords, exams:renderExams, results:renderResults, ai:renderAI, logs:renderLogs})[page](content, data, params);
  } catch (err) {
    if (id !== loadId) { notify(err.message); return; }
    content.innerHTML = heading() + `<div class="error" role="alert">${escape(err.message)}</div><button id="retry">Thử lại</button>`;
    document.querySelector('#retry').onclick = () => loadPage(params);
  }
}

function renderDashboard(content, data) {
  const t = data.totals;
  const stats = items => `<div class="stats">${items.map(([label,value]) => `<article class="stat"><small>${label}</small><b>${value}</b></article>`).join('')}</div>`;
  content.innerHTML += stats([['Người dùng',t.users],['Từ vựng',t.vocabulary],['Đề thi',t.exams],['Kết quả đã chấm',t.results]]);
  content.innerHTML += `<details class="advanced-stats"><summary>Thống kê chi tiết</summary>${stats([['Tài khoản hoạt động',t.active_users],['Điểm trung bình',t.average_score],['Lượt AI thành công',t.ai_success],['Lượt AI lỗi',t.ai_errors]])}</details><section class="panel"><h2>Hoạt động quản trị gần đây</h2>${table(['Người thực hiện','Thao tác','Dữ liệu','Thời gian'], data.recent_activity.map(r => `<tr><td>${escape(r.name)}</td><td>${escape(r.action)}</td><td>${escape(r.entity)} #${r.entity_id}</td><td>${date(r.created_at)}</td></tr>`))}</section>`;
}

function renderUsers(content, data, params) {
  const filter = new URLSearchParams(params);
  content.innerHTML += `<section class="panel"><form id="filters" class="toolbar"><label>Tìm tài khoản<input name="search" placeholder="Tên hoặc email" value="${escape(filter.get('search') || '')}"></label><label>Vai trò<select name="role"><option value="">Tất cả</option value="student">Học viên</option><option value="admin">Quản trị viên</option></select></label><label>Trạng thái<select name="active"><option value="">Tất cả</option><option value="true">Hoạt động</option><option value="false">Đã khóa</option></select></label><button>Tìm kiếm</button></form>${table(['Người dùng','Vai trò','Trạng thái','Thao tác'], data.map(r => `<tr><td><b>${escape(r.name)}</b><small>${escape(r.email)}</small></td><td>${statusLabel(r.role)}</td><td><span class="tag ${r.is_active?'':'locked'}">${r.is_active?'Hoạt động':'Đã khóa'}</span></td><td><button data-edit="${r.id}">Chỉnh sửa</button></td></tr>`))}</section>`;
  bindFilter(params);
  document.querySelectorAll('[data-edit]').forEach(b => b.onclick = () => {
    const row = data.find(r => r.id === Number(b.dataset.edit));
    openEditor('Quản lý tài khoản', `<p><b>${escape(row.name)}</b><br>${escape(row.email)}</p><label>Vai trò<select name="role"><option value="student">Học viên</option><option value="admin">Quản trị viên</option></select></label><label class="check"><input type="checkbox" name="is_active" ${row.is_active?'checked':''}> Tài khoản hoạt động</label><p class="note">Đổi vai trò hoặc khóa tài khoản sẽ thu hồi các phiên đăng nhập hiện tại.</p>`, async form => {
      await api(`/admin/users/${row.id}`, 'PATCH', {role:form.elements.role.value,is_active:form.elements.is_active.checked});
    });
    dialog.querySelector('[name=role]').value = row.role;
  });
}

function bindFilter(params) {
  const form = document.querySelector('#filters');
  const filters = new URLSearchParams(params);
  for (const select of form.querySelectorAll('select')) {
    select.value = filters.get(select.name) || '';
    select.setAttribute('aria-label',select.parentElement.firstChild.textContent.trim());
  }
  form.onsubmit = event => {
    event.preventDefault();
    const query = new URLSearchParams();
    for (const [key,value] of new FormData(form)) if (value !== '') query.set(key,value);
    loadPage(`?${query}`);
  };
}

function hskSelect(name = 'hsk') {
  return `<select name="${name}">${[1,2,3,4,5,6].map(n => `<option value="${n}">HSK ${n}</option>`).join('')}</select>`;
}

function renderWords(content, data, params) {
  const filter = new URLSearchParams(params);
  content.innerHTML += `<section class="panel"><form id="filters" class="toolbar"><label>Tìm từ<input name="search" placeholder="Chữ Hán, Pinyin, nghĩa" value="${escape(filter.get('search') || '')}"></label><label>Cấp độ<select name="hsk"><option value="">Tất cả HSK</option>${[1,2,3,4,5,6].map(n=>`<option value="${n}">HSK ${n}</option>`).join('')}</select></label><button>Tìm</button><button type="button" id="add" class="primary">+ Thêm từ</button></form>${table(['Chữ Hán','Pinyin / Nghĩa','Cấp độ','Nét chuẩn','Thao tác'],data.map(r=>`<tr><td class="hanzi">${escape(r.hanzi)}</td><td>${escape(r.pinyin)}<small>${escape(r.meaning)}</small></td><td><span class="tag">HSK ${r.hsk}</span></td><td>${r.strokes.length} nét</td><td><div class="actions"><button data-edit="${r.id}">Sửa</button><button class="danger" data-delete="${r.id}">Xóa</button></div></td></tr>`))}</section>`;
  bindFilter(params);
  document.querySelector('#add').onclick = () => wordEditor();
  document.querySelectorAll('[data-edit]').forEach(b => b.onclick = () => wordEditor(data.find(r=>r.id === Number(b.dataset.edit))));
  bindDeletes(data,'vocabulary',r=>r.hanzi);
}

function wordEditor(row) {
  const word = row || {hanzi:'',pinyin:'',meaning:'',hsk:1,example:'',audio_url:'',strokes:[]};
  strokes = structuredClone(word.strokes);
  openEditor(row ? 'Chỉnh sửa từ vựng' : 'Thêm từ vựng', `<div class="grid"><label>Chữ Hán<input name="hanzi" required maxlength="30" value="${escape(word.hanzi)}"></label><label>Pinyin<input name="pinyin" required maxlength="120" value="${escape(word.pinyin)}"></label><label>Nghĩa tiếng Việt<input name="meaning" required maxlength="300" value="${escape(word.meaning)}"></label><label>Cấp độ${hskSelect()}</label><label class="span-2">Câu ví dụ<textarea name="example" maxlength="1000">${escape(word.example)}</textarea></label><label class="span-2">Audio mẫu (URL HTTPS, tùy chọn)<input name="audio_url" type="url" value="${escape(word.audio_url)}"></label></div><fieldset><legend>Nét bút thuận</legend><div class="stroke-area"><canvas id="strokes" width="512" height="512" aria-label="Vẽ lần lượt các nét chữ chuẩn"></canvas><div class="stroke-help"><p>Vẽ từng nét đúng thứ tự bằng chuột hoặc cảm ứng. Số trên hình là thứ tự nét.</p><b id="stroke-count"></b><div><button type="button" id="undo-stroke">Bỏ nét cuối</button><button type="button" id="clear-strokes">Vẽ lại</button></div><small>Để trống nếu chưa có dữ liệu chuẩn. Chỉ lưu nét đã được kiểm tra.</small></div></div></fieldset>`, async form => {
    const body = {...Object.fromEntries(new FormData(form)),hsk:Number(form.elements.hsk.value),strokes};
    if (row) body.version = row.version;
    await api(`/admin/vocabulary${row?`/${row.id}`:''}`, row?'PUT':'POST', body);
  });
  dialog.querySelector('[name=hsk]').value = word.hsk;
  bindCanvas();
}

function bindCanvas() {
  const canvas = dialog.querySelector('canvas');
  const ctx = canvas.getContext('2d');
  let current = null;
  function draw() {
    ctx.clearRect(0,0,512,512);
    ctx.strokeStyle = '#e1e9dc'; ctx.lineWidth = 1; ctx.setLineDash([7,7]);
    for (const line of [[0,256,512,256],[256,0,256,512],[0,0,512,512],[512,0,0,512]]) {
      ctx.beginPath(); ctx.moveTo(line[0],line[1]); ctx.lineTo(line[2],line[3]); ctx.stroke();
    }
    ctx.setLineDash([]); ctx.lineWidth = 6; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    strokes.forEach((stroke,i) => {
      ctx.strokeStyle = '#176b50'; ctx.beginPath();
      stroke.forEach((p,j) => j ? ctx.lineTo(p.x/2,p.y/2) : ctx.moveTo(p.x/2,p.y/2)); ctx.stroke();
      if (stroke.length) {ctx.fillStyle = '#b54927';ctx.font='bold 20px sans-serif';ctx.fillText(String(i+1),stroke[0].x/2+8,stroke[0].y/2+8);}
    });
    document.querySelector('#stroke-count').textContent = `${strokes.length} nét đã vẽ`;
  }
  function point(event) {
    const rect = canvas.getBoundingClientRect();
    return {x:Math.round(Math.max(0,Math.min(1024,(event.clientX-rect.left)/rect.width*1024))),y:Math.round(Math.max(0,Math.min(1024,(event.clientY-rect.top)/rect.height*1024)))};
  }
  canvas.onpointerdown = event => {
    if (current || strokes.length >= 64) return;
    canvas.setPointerCapture(event.pointerId); current = [point(event)]; strokes.push(current); draw();
  };
  canvas.onpointermove = event => {if (current && current.length < 512) {current.push(point(event));draw();}};
  canvas.onpointerup = event => {
    if (!current) return;
    if (current.length < 512) current.push(point(event));
    current = null; draw();
  };
  canvas.onpointercancel = () => {if (current) {strokes.pop();current=null;draw();}};
  document.querySelector('#undo-stroke').onclick = () => {strokes.pop();draw();};
  document.querySelector('#clear-strokes').onclick = () => {strokes=[];draw();};
  draw();
}

function renderExams(content, data, params) {
  content.innerHTML += `<section class="panel"><form id="filters" class="toolbar"><label>Cấp độ<select name="hsk"><option value="">Tất cả HSK</option>${[1,2,3,4,5,6].map(n=>`<option value="${n}">HSK ${n}</option>`).join('')}</select></label><button>Lọc</button><button type="button" class="primary" id="add">+ Tạo đề thi</button></form>${table(['Đề thi','Cấp độ','Trạng thái','Nội dung','Thao tác'],data.map(r=>`<tr><td><b>${escape(r.title)}</b><small>${r.duration_minutes} phút · Phiên bản ${r.version}</small></td><td>HSK ${r.hsk}</td><td><span class="tag ${r.status}">${statusLabel(r.status)}</span></td><td>${r.questions.length} câu</td><td><div class="actions"><button data-edit="${r.id}">Biên soạn</button><button class="danger" data-delete="${r.id}">Xóa</button></div></td></tr>`))}</section>`;
  bindFilter(params);
  document.querySelector('#add').onclick = () => examEditor();
  document.querySelectorAll('[data-edit]').forEach(b => b.onclick = () => examEditor(data.find(r=>r.id===Number(b.dataset.edit))));
  bindDeletes(data,'exams',r=>r.title);
}

function newQuestionId() {
  // A local content ID, not an authentication token. HTTP on a LAN may lack randomUUID.
  return globalThis.crypto?.randomUUID?.() || `q-${Date.now().toString(36)}-${Math.random().toString(36).slice(2,10)}`;
}

function questionHTML(q = {}) {
  return `<fieldset class="question"><legend>Câu hỏi</legend><div class="grid"><label>Mã câu<input data-key="id" required maxlength="40" value="${escape(q.id || newQuestionId())}"></label><label>Kỹ năng<select data-key="section">${[['reading','Đọc'],['listening','Nghe'],['writing','Viết']].map(([v,l])=>`<option value="${v}" ${q.section===v?'selected':''}>${l}</option>`).join('')}</select></label><label class="span-2">Yêu cầu / nội dung<textarea data-key="prompt" required maxlength="5000">${escape(q.prompt || '')}</textarea></label><label>Lựa chọn (mỗi dòng một đáp án)<textarea data-key="options">${escape((q.options || []).join('\n'))}</textarea></label><label>Đáp án / rubric chấm<textarea data-key="answer" required maxlength="5000">${escape(q.answer || '')}</textarea></label><label>Audio HTTPS (bắt buộc cho Nghe)<input data-key="audio_url" type="url" value="${escape(q.audio_url || '')}"></label><label>ID từ liên quan (tùy chọn)<input data-key="word_id" type="number" min="1" value="${q.word_id || ''}"></label><label>Transcript<textarea data-key="transcript">${escape(q.transcript || '')}</textarea></label><label>Giải thích đáp án<textarea data-key="explanation">${escape(q.explanation || '')}</textarea></label></div><button type="button" class="danger remove">Bỏ câu hỏi</button></fieldset>`;
}

function examEditor(row) {
  const exam = row || {title:'',hsk:1,status:'draft',duration_minutes:15,questions:[{}]};
  openEditor(row?'Biên soạn đề thi':'Tạo đề thi', `<div class="grid"><label class="span-2">Tên đề<input name="title" required maxlength="200" value="${escape(exam.title)}"></label><label>Cấp độ${hskSelect()}</label><label>Thời lượng (phút)<input name="duration_minutes" type="number" min="1" max="240" required value="${exam.duration_minutes}"></label><label>Trạng thái<select name="status" aria-label="Trạng thái"><option value="draft">Bản nháp</option><option value="published">Phát hành</option><option value="hidden">Ẩn</option></select></label></div><p class="note">Học viên chỉ thấy đề đã phát hành. Bài viết tự do dùng rubric để module Writing chấm; trắc nghiệm chấm theo đáp án. Thay đổi đề sẽ tạo phiên bản mới.</p><div id="questions" class="questions">${exam.questions.map(questionHTML).join('')}</div><button type="button" id="add-question">+ Thêm câu hỏi</button>`, async form => {
    const questions = [...form.querySelectorAll('.question')].map(fieldset => {
      const q = {};
      fieldset.querySelectorAll('[data-key]').forEach(el=>q[el.dataset.key]=el.value.trim());
      q.options=q.options.split('\n').map(s=>s.trim()).filter(Boolean);
      q.word_id=q.word_id?Number(q.word_id):null;
      return q;
    });
    const body={...Object.fromEntries(new FormData(form)),hsk:Number(form.elements.hsk.value),duration_minutes:Number(form.elements.duration_minutes.value),questions};
    if(row) body.version=row.version;
    await api(`/admin/exams${row?`/${row.id}`:''}`,row?'PUT':'POST',body);
  });
  dialog.querySelector('[name=hsk]').value=exam.hsk;
  dialog.querySelector('[name=status]').value=exam.status;
  const questions = dialog.querySelector('#questions');
  questions.onclick = event => {if(event.target.closest('.remove')) event.target.closest('.question').remove();};
  dialog.querySelector('#add-question').onclick=()=>questions.insertAdjacentHTML('beforeend',questionHTML());
}

function bindDeletes(data, resource, label) {
  document.querySelectorAll('[data-delete]').forEach(b => b.onclick = () => {
    const row = data.find(r => r.id === Number(b.dataset.delete));
    openEditor('Xác nhận xóa', `<p>Xóa <b>${escape(label(row))}</b>?</p><p class="note">Thao tác sẽ được lưu trong nhật ký. Dữ liệu đang được tham chiếu sẽ được máy chủ bảo vệ.</p>`, async () => {
      await api(`/admin/${resource}/${row.id}?version=${row.version}`, 'DELETE');
    }, 'Xóa dữ liệu');
  });
}

function renderResults(content, data, params) {
  content.innerHTML += `<section class="panel"><form id="filters" class="toolbar"><label>Điểm dưới<select name="below"><option value="">Tất cả kết quả</option value="80">Dưới 80 điểm</option value="50">Dưới 50 điểm</option></select></label><button>Lọc</button></form>${table(['Học viên','Loại bài','Điểm hiện tại','Thời gian','Thao tác'],data.map(r=>`<tr><td>${escape(r.name)}<small>${escape(r.email)}</small></td><td>${({exam:'Bài thi',writing:'Đoạn văn',handwriting:'Viết tay'})[r.kind]}<small>Chấm bởi: ${escape(r.graded_by)}</small></td><td><span class="score">${r.score}</span><small>Điểm gốc: ${r.original_score}</small></td><td>${date(r.created_at)}</td><td><button data-review="${r.id}">Xem & duyệt</button></td></tr>`))}</section>`;
  bindFilter(params);
  document.querySelectorAll('[data-review]').forEach(b => b.onclick = async () => {
    const row=data.find(r=>r.id===Number(b.dataset.review));
    b.disabled=true;
    try {
      const history=await api(`/admin/results/${row.id}/history`);
      let content;
      try {content=JSON.stringify(JSON.parse(row.content),null,2);} catch {content=row.content;}
      openEditor(`Duyệt kết quả #${row.id}`, `<p><b>${escape(row.name)}</b> · ${escape(row.email)}</p><details open><summary>Nội dung bài làm</summary><pre>${escape(content)}</pre></details><div class="detail-text">${escape(row.feedback || 'Chưa có nhận xét.')}</div><div class="grid"><label>Điểm điều chỉnh (0–100)<input type="number" name="score" min="0" max="100" step="0.01" required value="${row.score}"></label><p class="note">Điểm gốc: ${row.original_score}<br>Điểm đang hiển thị: ${row.score}</p><label class="span-2">Lý do điều chỉnh<textarea name="reason" required minlength="5" maxlength="2000" placeholder="Ghi rõ lý do và tiêu chí đối chiếu…"></textarea></label></div><h3>Lịch sử điều chỉnh</h3>${table(['Người duyệt','Điểm','Lý do','Thời gian'],history.map(h=>`<tr><td>${escape(h.admin_name)}</td><td>${h.old_score} → ${h.new_score}</td><td>${escape(h.reason)}</td><td>${date(h.created_at)}</td></tr>`))}`, async form => {
        await api(`/admin/results/${row.id}/score`,'PATCH',{score:Number(form.elements.score.value),reason:form.elements.reason.value,version:row.version});
      },'Lưu điểm điều chỉnh');
    } catch(err){notify(err.message);} finally {b.disabled=false;}
  });
}

function renderAI(content, data) {
  content.innerHTML += `<section class="panel"><form id="ai-form" class="dialog-body"><div class="note"><b>${data.ready?'Cấu hình sẵn sàng cho module AI':'AI chưa sẵn sàng'}</b><br>Khóa máy chủ: ${data.key_configured?'Đã cấu hình':'Chưa cấu hình'}. Trạng thái này kiểm tra cấu hình nội bộ, chưa xác minh kết nối với nhà cung cấp.</div><div class="grid"><label>Model<input name="model" required maxlength="120" value="${escape(data.model)}"></label><label>Giới hạn token<input name="max_tokens" type="number" min="1" max="16000" required value="${data.max_tokens}"></label><label>Temperature (0–2)<input name="temperature" type="number" min="0" max="2" step="0.1" required value="${data.temperature}"></label><label class="check"><input name="enabled" type="checkbox" ${data.enabled?'checked':''}> Bật AI</label><label class="span-2">Hướng dẫn hệ thống / prompt mẫu<textarea name="system_prompt" required maxlength="10000" rows="7">${escape(data.system_prompt)}</textarea></label></div><small>Khóa API được cấu hình bằng biến môi trường AI_API_KEY trên máy chủ; không nhập hoặc hiển thị khóa ở trang này.</small><div id="ai-error" role="alert"></div><div><button class="primary">Lưu cấu hình</button></div></form></section>`;
  document.querySelector('#ai-form').onsubmit=async event=>{
    event.preventDefault(); const form=event.currentTarget; const button=form.querySelector('button'); button.disabled=true;
    try {
      await api('/admin/ai-config','PUT',{model:form.elements.model.value,system_prompt:form.elements.system_prompt.value,max_tokens:Number(form.elements.max_tokens.value),temperature:Number(form.elements.temperature.value),enabled:form.elements.enabled.checked,version:data.version});
      notify('Đã lưu cấu hình AI'); loadPage();
    } catch(err){if(document.querySelector('#ai-error'))document.querySelector('#ai-error').innerHTML=`<div class="error">${escape(err.message)}</div>`;} finally {button.disabled=false;}
  };
}

function renderLogs(content,data,params) {
  const offset=Number(new URLSearchParams(params).get('offset') || 0);
  content.innerHTML+=`<section class="panel">${table(['Người thực hiện','Thao tác','Đối tượng','Thời gian','Chi tiết'],data.map(r=>`<tr><td>${escape(r.name)}</td><td>${escape(r.action)}</td><td>${escape(r.entity)} #${escape(r.entity_id)}</td><td>${date(r.created_at)}</td><td><button data-log="${r.id}">Xem</button></td></tr>`))}<div class="toolbar"><button id="previous" ${offset===0?'disabled':''}>Trang trước</button><span>${offset+1}–${offset+data.length}</span><button id="next" ${data.length<100?'disabled':''}>Trang sau</button></div></section>`;
  document.querySelector('#previous').onclick=()=>loadPage(`?offset=${Math.max(0,offset-100)}`);
  document.querySelector('#next').onclick=()=>loadPage(`?offset=${offset+100}`);
  document.querySelectorAll('[data-log]').forEach(b=>b.onclick=()=>{
    const row=data.find(r=>r.id===Number(b.dataset.log));
    dialog.innerHTML=`<div class="dialog-head"><h2>Chi tiết thay đổi #${row.id}</h2><button id="close">Đóng</button></div><div class="dialog-body"><h3>Trước thay đổi</h3><pre>${escape(JSON.stringify(JSON.parse(row.before_json),null,2))}</pre><h3>Sau thay đổi</h3><pre>${escape(JSON.stringify(JSON.parse(row.after_json),null,2))}</pre></div>`;
    dialog.querySelector('#close').onclick=()=>dialog.close();dialog.showModal();
  });
}

function openEditor(title,html,save,label='Lưu thay đổi') {
  dialog.innerHTML=`<div class="dialog-head"><h2>${escape(title)}</h2><button type="button" id="close" aria-label="Đóng hộp thoại">✕</button></div><form class="dialog-body">${html}<div id="form-error" role="alert"></div><div class="dialog-footer"><button type="button" id="cancel">Hủy</button><button class="primary" type="submit">${label}</button></div></form>`;
  let busy=false;
  dialog.querySelectorAll('select').forEach(select=>select.setAttribute('aria-label',select.parentElement.firstChild.textContent.trim()));
  dialog.querySelector('#close').onclick=dialog.querySelector('#cancel').onclick=()=>{if(!busy)dialog.close();};
  dialog.oncancel=event=>{if(busy)event.preventDefault();};
  dialog.querySelector('form').onsubmit=async event=>{
    event.preventDefault();if(busy)return;busy=true;
    const form=event.currentTarget;const submit=form.querySelector('[type=submit]');submit.disabled=true;
    dialog.querySelector('#form-error').textContent='';
    try {await save(form);dialog.close();notify('Đã lưu thay đổi');if(user)await loadPage();}
    catch(err){const error=dialog.querySelector('#form-error');if(dialog.open&&error)error.innerHTML=`<div class="error">${escape(err.message)}</div>`;else notify(err.message);}
    finally{busy=false;submit.disabled=false;}
  };
  dialog.showModal();
}

async function boot() {
  if (!token) return loginView();
  try {
    user=await api('/me');
    if(user.role!=='admin'){clearSession();return loginView('Bạn cần tài khoản quản trị.');}
    shell();
  } catch(err){clearSession();loginView(err.message);}
}
boot();
