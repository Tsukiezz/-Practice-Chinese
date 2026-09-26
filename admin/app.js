const root = document.querySelector('#app');
const dialog = document.querySelector('#editor');
const pages = {
  dashboard: ['Tổng quan', 'Bức tranh học tập toàn hệ thống, cập nhật từ cơ sở dữ liệu.'],
  users: ['Quản lý tài khoản', 'Quản lý tài khoản học viên và quản trị viên, thêm mới, chỉnh sửa, xóa và phân quyền.'],
  student_lessons: ['Tiến độ 48 Bài học', 'Theo dõi tiến trình 48 bài học theo 4 giai đoạn chuẩn sư phạm và điểm số.'],
  student_reading: ['Luyện Đọc Phát Âm AI', 'Lịch sử phát âm qua mic, độ chính xác AI và phân tích lỗi đọc của học viên.'],
  student_writing: ['Luyện Viết Canvas & Tự luận', 'Theo dõi nét vẽ chữ Hán trên canvas và các bài tập viết tự luận của học viên.'],
  student_vocab: ['Sổ tay & Tra từ', 'Từ vựng học viên đã lưu vào sổ tay cá nhân và các từ được tra cứu nhiều nhất.'],
  student_ai_exams: ['Đề thi AI Học viên', 'Quản lý lịch sử tạo đề thi AI của từng học viên, trạng thái nộp bài và kết quả.'],
  results: ['Duyệt bài thi & Khiếu nại', 'Xem bài làm đề thi HSK 1–6, xử lý khiếu nại và lịch sử điều chỉnh điểm.'],
  vocabulary: ['Kho 5.000 từ & nét chuẩn', 'Nguồn 5.000 từ vựng HSK 1–6 và thứ tự nét canvas chuẩn.'],
  exams: ['Ngân hàng đề thi HSK', 'Biên soạn và quản lý đề thi Nghe, Đọc, Viết theo chuẩn HSK 1–6.'],
  lessons: ['Lộ trình 48 bài học', 'Danh mục bài học giáo trình HanziGo và mục tiêu từng cấp độ.'],
  ai: ['Cấu hình Trợ lý AI', 'Quản lý model Gemini, hướng dẫn chấm bài thi và giới hạn xử lý.'],
  logs: ['Nhật ký quản trị', 'Các thay đổi được ghi nhận cùng người thực hiện và thời gian minh bạch.'],
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
  root.innerHTML = `<div class="login"><aside class="login-art">${brand}<div><div class="character">学 · 习</div><h1>Chăm chút từng<br>hành trình học.</h1><p>Không gian quản trị dành cho đội ngũ Chinese Learning. Nội dung tốt tạo nên trải nghiệm học tốt.</p></div><small>HanziGo · Chinese Learning</small></aside><section class="login-wrap"><form id="login" class="login-form"><div><div class="eyebrow">CHÀO MỪNG TRỞ LẠI</div><h2>Đăng nhập quản trị</h2><p>Sử dụng tài khoản Admin được cấp cho dự án.</p></div><label>Email<input name="email" type="email" autocomplete="username" required maxlength="120"></label><label>Mật khẩu<input name="password" type="password" autocomplete="current-password" required maxlength="128"></label><div id="login-error" role="alert">${error ? `<div class="error">${escape(error)}</div>` : ''}</div><button class="primary">Đăng nhập →</button><a href="/" style="display:inline-block;margin-top:16px;color:#2c7a3f;text-decoration:none;font-weight:600;text-align:center">← Trở về ứng dụng học tập HanziGo</a><small>Quyền quản trị được xác minh trên máy chủ.</small></form></section></div>`;
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
  root.innerHTML = `<div class="layout"><aside class="sidebar">${brand}<button type="button" id="menu-toggle" class="menu-toggle" aria-label="Mở menu quản trị" aria-expanded="false" aria-controls="admin-menu"><svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button><div id="admin-menu" class="sidebar-menu"><a href="/" class="app-return-link" style="display:flex;align-items:center;gap:8px;padding:9px 12px;margin:4px 8px 10px;background:#eef6ee;color:#1e5e2e;border:1px solid #cce5cc;border-radius:8px;font-weight:600;font-size:13px;text-decoration:none">← Về ứng dụng HanziGo</a><nav aria-label="Quản trị">${navButton('dashboard')}<div class="nav-group"><span class="nav-label">🎓 Quản trị Chức năng Học viên</span>${['users','student_lessons','student_reading','student_writing','student_vocab','student_ai_exams','results'].map(navButton).join('')}</div><div class="nav-group"><span class="nav-label">📚 Kho Học liệu & Đề thi</span>${['vocabulary','exams','lessons'].map(navButton).join('')}</div><div class="nav-group"><span class="nav-label">⚙️ Hệ thống & Trí tuệ AI</span>${['ai','logs'].map(navButton).join('')}</div></nav><div class="account"><div><b>${escape(user.name)}</b><small>${escape(user.email)}</small></div><a href="/">← Về trang học viên</a><button id="logout">Đăng xuất</button></div></div></aside><main class="main"><div class="topline"><span>CHINESE LEARNING / QUẢN TRỊ</span><a href="/" style="font-size:12px;color:#2c7a3f;text-decoration:none;font-weight:600;margin-right:12px">← Mở ứng dụng học tập</a><span class="pill">Không gian quản trị</span></div><div id="content"></div></main></div>`;
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
    const endpoint = {
      dashboard: '/admin/dashboard',
      users: '/admin/users',
      student_lessons: '/admin/student-lessons',
      student_reading: '/admin/student-reading',
      student_writing: '/admin/student-writing',
      student_vocab: '/admin/student-vocab',
      student_ai_exams: '/admin/student-ai-exams',
      results: '/admin/results',
      vocabulary: '/admin/vocabulary',
      exams: '/admin/exams',
      lessons: '/lessons',
      ai: '/admin/ai-config',
      logs: '/admin/audit-logs'
    }[page];
    const data = await api(endpoint + params);
    if (id !== loadId) return;
    content.innerHTML = heading();
    ({
      dashboard: renderDashboard,
      users: renderUsers,
      student_lessons: renderStudentLessons,
      student_reading: renderStudentReading,
      student_writing: renderStudentWriting,
      student_vocab: renderStudentVocab,
      student_ai_exams: renderStudentAiExams,
      results: renderResults,
      vocabulary: renderWords,
      exams: renderExams,
      lessons: renderLessonsCatalog,
      ai: renderAI,
      logs: renderLogs
    })[page](content, data, params);
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
  content.innerHTML += `<section class="panel">
    <form id="filters" class="toolbar">
      <label>Tìm tài khoản<input name="search" placeholder="Tên hoặc email" value="${escape(filter.get('search') || '')}"></label>
      <label>Vai trò
        <select name="role">
          <option value="">Tất cả</option>
          <option value="student">Học viên</option>
          <option value="admin">Quản trị viên</option>
        </select>
      </label>
      <label>Trạng thái
        <select name="active">
          <option value="">Tất cả</option>
          <option value="true">Hoạt động</option>
          <option value="false">Đã khóa</option>
        </select>
      </label>
      <button>Tìm kiếm</button>
      <button type="button" id="add-user" class="primary">+ Thêm tài khoản</button>
    </form>
    ${table(['Người dùng', 'Vai trò', 'Trạng thái', 'Thao tác'], data.map(r => `<tr>
      <td><b>${escape(r.name)}</b><br><small>${escape(r.email)}</small></td>
      <td><span class="tag ${r.role === 'admin' ? 'published' : ''}">${statusLabel(r.role)}</span></td>
      <td><span class="tag ${r.is_active ? '' : 'locked'}">${r.is_active ? 'Hoạt động' : 'Đã khóa'}</span></td>
      <td>
        <div class="actions">
          <button data-edit-user="${r.id}">Sửa</button>
          <button class="danger" data-delete-user="${r.id}">Xóa</button>
          <button data-reset-pw="${r.id}">Đổi MK</button>
          <button data-user-ai-exams="${r.id}">Đề thi AI</button>
        </div>
      </td>
    </tr>`))}
  </section>`;
  bindFilter(params);

  // Add User
  document.querySelector('#add-user').onclick = () => {
    openEditor('Thêm tài khoản mới', `
      <div class="grid">
        <label>Họ và tên<input name="name" required maxlength="100" placeholder="Nguyễn Văn A"></label>
        <label>Email đăng nhập<input name="email" type="email" required maxlength="120" placeholder="user@hanzigo.com"></label>
        <label>Mật khẩu ban đầu (tối thiểu 8 ký tự)<input name="password" type="password" required minlength="8" maxlength="128" placeholder="Nhập mật khẩu"></label>
        <label>Vai trò
          <select name="role">
            <option value="student">Học viên</option>
            <option value="admin">Quản trị viên</option>
          </select>
        </label>
      </div>
      <label class="check" style="margin-top:12px">
        <input type="checkbox" name="is_active" checked> Kích hoạt tài khoản ngay
      </label>
    `, async form => {
      const body = {
        name: form.elements.name.value.trim(),
        email: form.elements.email.value.trim().toLowerCase(),
        password: form.elements.password.value,
        role: form.elements.role.value,
        is_active: form.elements.is_active.checked,
      };
      await api('/admin/users', 'POST', body);
      notify('Tạo tài khoản mới thành công');
    }, '+ Tạo tài khoản');
  };

  // Edit User
  document.querySelectorAll('[data-edit-user]').forEach(b => b.onclick = () => {
    const row = data.find(r => r.id === Number(b.dataset.editUser));
    openEditor(`Chỉnh sửa tài khoản: ${escape(row.name)}`, `
      <div class="grid">
        <label>Họ và tên<input name="name" required maxlength="100" value="${escape(row.name)}"></label>
        <label>Email đăng nhập<input name="email" type="email" required maxlength="120" value="${escape(row.email)}"></label>
        <label>Vai trò
          <select name="role">
            <option value="student" ${row.role === 'student' ? 'selected' : ''}>Học viên</option>
            <option value="admin" ${row.role === 'admin' ? 'selected' : ''}>Quản trị viên</option>
          </select>
        </label>
        <label>Mật khẩu mới (tùy chọn)
          <input name="password" type="password" minlength="8" maxlength="128" placeholder="Để trống nếu không đổi">
        </label>
      </div>
      <label class="check" style="margin-top:12px">
        <input type="checkbox" name="is_active" ${row.is_active ? 'checked' : ''}> Tài khoản hoạt động
      </label>
      <p class="note">Thay đổi quyền hoặc khóa tài khoản sẽ tự động thu hồi các phiên đăng nhập đang hoạt động của người dùng.</p>
    `, async form => {
      const body = {
        name: form.elements.name.value.trim(),
        email: form.elements.email.value.trim().toLowerCase(),
        role: form.elements.role.value,
        is_active: form.elements.is_active.checked,
        version: row.version,
      };
      if (form.elements.password && form.elements.password.value.trim()) {
        body.password = form.elements.password.value.trim();
      }
      await api(`/admin/users/${row.id}`, 'PUT', body);
      notify(`Đã cập nhật tài khoản ${row.name}`);
    });
  });

  // Delete User
  document.querySelectorAll('[data-delete-user]').forEach(b => b.onclick = async () => {
    const row = data.find(r => r.id === Number(b.dataset.deleteUser));
    if (user && row.id === user.id) {
      alert('Không thể tự xóa tài khoản của chính bạn!');
      return;
    }
    const confirmed = confirm(`Bạn có chắc chắn muốn xóa tài khoản "${row.name}" (${row.email})?\n\nToàn bộ dữ liệu tiến độ bài học, bài thi và lịch sử học tập của tài khoản này sẽ được xóa khỏi hệ thống.`);
    if (!confirmed) return;
    try {
      await api(`/admin/users/${row.id}`, 'DELETE');
      notify(`Đã xóa tài khoản ${row.name} thành công`);
      loadPage(params);
    } catch (err) {
      notify(err.message);
    }
  });

  // Reset Password quick button
  document.querySelectorAll('[data-reset-pw]').forEach(b => b.onclick = () => {
    const row = data.find(r => r.id === Number(b.dataset.resetPw));
    openEditor(`Đặt lại mật khẩu cho ${escape(row.name)}`, `
      <p>Tài khoản: <b>${escape(row.email)}</b></p>
      <label>Mật khẩu mới (tối thiểu 8 ký tự)
        <input name="new_password" type="password" required minlength="8" maxlength="128" placeholder="Nhập mật khẩu mới">
      </label>
      <p class="note">Sau khi đặt lại thành công, tài khoản này sẽ được cập nhật mật khẩu mới trên hệ thống.</p>
    `, async form => {
      await api(`/admin/users/${row.id}/reset-password`, 'POST', {new_password: form.elements.new_password.value});
    }, 'Cập nhật mật khẩu');
  });

  // Go to student's AI exams
  document.querySelectorAll('[data-user-ai-exams]').forEach(b => b.onclick = () => {
    const uid = b.dataset.userAiExams;
    page = 'student_ai_exams';
    loadPage(`?user_id=${uid}`);
  });
}

function renderStudentAiExams(content, data, params) {
  const filter = new URLSearchParams(params);
  content.innerHTML += `<section class="panel">
    <form id="filters" class="toolbar">
      <label>Tìm kiếm<input name="search" placeholder="Học viên, email, tên đề, chủ đề..." value="${escape(filter.get('search') || '')}"></label>
      <label>Cấp độ
        <select name="hsk">
          <option value="">Tất cả HSK</option>
          ${[1,2,3,4,5,6].map(n => `<option value="${n}">HSK ${n}</option>`).join('')}
        </select>
      </label>
      <label>Trạng thái
        <select name="status">
          <option value="">Tất cả trạng thái</option>
          <option value="completed">Đã nộp bài</option>
          <option value="pending">Đang làm</option>
        </select>
      </label>
      <button>Tìm kiếm</button>
      <span class="pill" style="margin-left:auto">${data.length} đề thi AI</span>
    </form>
    ${table(['Học viên', 'Đề thi AI', 'Cấp độ', 'Số câu / Thời gian', 'Trạng thái', 'Điểm số', 'Thời gian', 'Thao tác'],
      data.map(r => `<tr>
        <td><b>${escape(r.student_name)}</b><br><small>${escape(r.student_email)}</small></td>
        <td><b>${escape(r.title)}</b><br><small>${r.content_type === 'vocabulary' ? '📖 Ôn từ vựng' : '🎲 Đề ngẫu nhiên'}${r.topic ? ' · Chủ đề: ' + escape(r.topic) : ''}</small></td>
        <td><span class="tag">HSK ${r.hsk_level || '1'}</span></td>
        <td>${r.question_count} câu · ${r.duration_minutes} phút</td>
        <td><span class="tag ${r.status === 'completed' ? 'published' : 'draft'}">${r.status === 'completed' ? 'Đã nộp bài' : 'Đang làm'}</span></td>
        <td>${r.score != null ? `<b style="color:${r.score >= 80 ? '#1b4d3e' : '#c53030'};font-size:14px">${r.score}</b>/100` : '<span style="color:#888">—</span>'}</td>
        <td><small>Tạo: ${date(r.created_at)}${r.submitted_at ? `<br>Nộp: ${date(r.submitted_at)}` : ''}</small></td>
        <td>
          <div class="actions">
            <button data-view-exam="${r.id}">Chi tiết</button>
            <button class="danger" data-delete-exam="${r.id}">Xóa</button>
          </div>
        </td>
      </tr>`))}
  </section>`;
  bindFilter(params);

  document.querySelectorAll('[data-view-exam]').forEach(b => {
    b.onclick = async () => {
      const examId = Number(b.dataset.viewExam);
      try {
        const detail = await api(`/admin/student-ai-exams/${examId}`);
        showStudentAiExamModal(detail);
      } catch (err) {
        notify(err.message);
      }
    };
  });

  document.querySelectorAll('[data-delete-exam]').forEach(b => {
    b.onclick = async () => {
      const examId = Number(b.dataset.deleteExam);
      if (!confirm(`Bạn có chắc muốn xóa đề thi AI #${examId} này không?`)) return;
      try {
        await api(`/admin/student-ai-exams/${examId}`, 'DELETE');
        notify(`Đã xóa đề thi AI #${examId} thành công`);
        loadPage(params);
      } catch (err) {
        notify(err.message);
      }
    };
  });
}

function showStudentAiExamModal(detail) {
  const qs = detail.questions || [];
  const userAnswers = detail.user_answers || {};
  const feedback = detail.ai_feedback || {};

  let html = `
    <div style="margin-bottom:16px;padding:12px 16px;background:#f5f8f6;border-radius:8px">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
        <div>
          <b>Học viên: ${escape(detail.student_name)}</b> (${escape(detail.student_email)})<br>
          <small>Đề thi: ${escape(detail.title)} · Cấp độ: HSK ${detail.hsk_level || 1} · ${detail.question_count} câu · ${detail.duration_minutes} phút</small>
        </div>
        <div>
          <span class="tag ${detail.status === 'completed' ? 'published' : 'draft'}">${detail.status === 'completed' ? 'Đã nộp bài' : 'Đang làm'}</span>
          ${detail.score != null ? `<b style="font-size:16px;margin-left:8px;color:${detail.score >= 80 ? '#1b4d3e' : '#c53030'}">${detail.score} / 100 điểm</b>` : ''}
        </div>
      </div>
      ${feedback.summary ? `<p style="margin:8px 0 0;font-size:13px;color:#2c5234"><b>Nhận xét AI:</b> ${escape(feedback.summary)}</p>` : ''}
    </div>
    <div style="max-height:480px;overflow-y:auto;padding-right:8px">
  `;

  if (qs.length === 0) {
    html += '<p>Không có câu hỏi nào trong đề thi này.</p>';
  } else {
    qs.forEach((q, idx) => {
      const userAns = userAnswers[String(idx)] || userAnswers[q.id] || '';
      const isCorrect = userAns && (userAns === q.correct_answer || userAns === q.answer);
      const correctAns = q.correct_answer || q.answer || '';
      html += `
        <div style="margin-bottom:14px;padding:12px;border:1px solid #e2e8e4;border-radius:8px;background:#fff">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
            <b>Câu ${idx + 1}: ${escape(q.prompt || q.question || '')}</b>
            ${detail.status === 'completed' ? `
              <span class="tag ${isCorrect ? 'published' : 'locked'}" style="font-size:11px">
                ${isCorrect ? '✓ Đúng' : (userAns ? '✗ Sai' : 'Chưa làm')}
              </span>
            ` : ''}
          </div>
          ${q.pinyin ? `<div style="font-size:12px;color:#666;margin-bottom:6px">${escape(q.pinyin)}</div>` : ''}
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px">
            ${(q.options || []).map(opt => {
              const isSelected = userAns === opt || (userAns && opt && userAns.trim().startsWith(opt.trim().slice(0, 1)));
              const isRight = opt === correctAns || (correctAns && opt && correctAns.trim().startsWith(opt.trim().slice(0, 1)));
              let bg = '#fafafa';
              let border = '#eee';
              if (detail.status === 'completed') {
                if (isRight) { bg = '#eaf7ed'; border = '#68d391'; }
                else if (isSelected) { bg = '#fff5f5'; border = '#fc8181'; }
              } else if (isSelected) {
                bg = '#eef6ee'; border = '#1b4d3e';
              }
              return `<div style="padding:6px 10px;border-radius:6px;font-size:13px;border:1px solid ${border};background:${bg}">
                ${escape(opt)} ${isSelected ? '<b>(Đã chọn)</b>' : ''} ${isRight && detail.status === 'completed' ? '<b>(Đáp án đúng)</b>' : ''}
              </div>`;
            }).join('')}
          </div>
          ${q.explanation ? `<div style="font-size:12px;color:#4a5568;background:#f7fafc;padding:6px 10px;border-radius:6px">💡 <b>Giải thích:</b> ${escape(q.explanation)}</div>` : ''}
        </div>
      `;
    });
  }

  html += '</div>';

  openEditor(`Chi tiết Đề thi AI #${detail.id}`, html, null, 'Đóng');
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

function renderStudentLessons(content, data) {
  const stageLabels = {0:'Chưa bắt đầu', 1:'1. Khám phá từ vựng', 2:'2. Ngữ pháp & Mẫu câu', 3:'3. Luyện tập trắc nghiệm', 4:'4. Đã hoàn thành'};
  content.innerHTML += `<section class="panel">
    <div class="toolbar">
      <input id="filter-user-lesson" placeholder="Lọc theo tên, email học viên hoặc mã bài học..." aria-label="Lọc tiến độ học viên" style="flex:1;max-width:400px">
      <span class="pill">${data.length} tiến trình học tập</span>
    </div>
    <div id="lessons-table-wrap">
      ${table(['Học viên', 'Email', 'Mã bài học', 'Giai đoạn', 'Điểm cao nhất', 'Số lần nộp', 'Hoàn thành lúc', 'Cập nhật'],
        data.map(r => `<tr>
          <td><b>${escape(r.name)}</b></td>
          <td>${escape(r.email)}</td>
          <td><code>${escape(r.lesson_id)}</code></td>
          <td><span class="tag ${r.stage === 4 ? 'published' : 'draft'}">${stageLabels[r.stage] || ('Giai đoạn ' + r.stage)}</span></td>
          <td><b>${r.best_score ?? 0}</b>/100</td>
          <td>${r.attempts ?? 0}</td>
          <td>${r.completed_at ? date(r.completed_at) : '—'}</td>
          <td>${date(r.updated_at)}</td>
        </tr>`))}
    </div>
  </section>`;
  const input = document.querySelector('#filter-user-lesson');
  if (input) input.oninput = e => {
    const q = e.target.value.toLowerCase().trim();
    const rows = data.filter(r => (r.name + ' ' + r.email + ' ' + r.lesson_id).toLowerCase().includes(q));
    document.querySelector('#lessons-table-wrap').innerHTML = table(
      ['Học viên', 'Email', 'Mã bài học', 'Giai đoạn', 'Điểm cao nhất', 'Số lần nộp', 'Hoàn thành lúc', 'Cập nhật'],
      rows.map(r => `<tr>
        <td><b>${escape(r.name)}</b></td>
        <td>${escape(r.email)}</td>
        <td><code>${escape(r.lesson_id)}</code></td>
        <td><span class="tag ${r.stage === 4 ? 'published' : 'draft'}">${stageLabels[r.stage] || ('Giai đoạn ' + r.stage)}</span></td>
        <td><b>${r.best_score ?? 0}</b>/100</td>
        <td>${r.attempts ?? 0}</td>
        <td>${r.completed_at ? date(r.completed_at) : '—'}</td>
        <td>${date(r.updated_at)}</td>
      </tr>`)
    );
  };
}

function renderStudentReading(content, data) {
  content.innerHTML += `<section class="panel">
    <div class="toolbar">
      <input id="filter-user-reading" placeholder="Lọc theo học viên, chữ Hán hoặc pinyin..." aria-label="Lọc luyện đọc" style="flex:1;max-width:400px">
      <span class="pill">${data.length} lượt luyện đọc AI</span>
    </div>
    <div id="reading-table-wrap">
      ${table(['Học viên', 'Chữ Hán', 'Pinyin', 'Ý nghĩa', 'Độ chính xác', 'Đánh giá AI', 'Phát âm ghi nhận', 'Thời gian'],
        data.map(r => `<tr>
          <td><b>${escape(r.name)}</b><br><small>${escape(r.email)}</small></td>
          <td><b style="font-size:18px">${escape(r.hanzi)}</b></td>
          <td>${escape(r.pinyin)}</td>
          <td>${escape(r.meaning || '—')}</td>
          <td><b>${Number(r.accuracy_percent).toFixed(1)}%</b></td>
          <td><span class="tag ${r.accuracy_percent >= 80 ? 'published' : (r.accuracy_percent >= 60 ? 'draft' : 'hidden')}">${escape(r.rating || 'Đã chấm')}</span></td>
          <td>${escape(r.spoken_text || '—')}</td>
          <td>${date(r.created_at)}</td>
        </tr>`))}
    </div>
  </section>`;
  const input = document.querySelector('#filter-user-reading');
  if (input) input.oninput = e => {
    const q = e.target.value.toLowerCase().trim();
    const rows = data.filter(r => (r.name + ' ' + r.email + ' ' + r.hanzi + ' ' + r.pinyin + ' ' + (r.meaning || '')).toLowerCase().includes(q));
    document.querySelector('#reading-table-wrap').innerHTML = table(
      ['Học viên', 'Chữ Hán', 'Pinyin', 'Ý nghĩa', 'Độ chính xác', 'Đánh giá AI', 'Phát âm ghi nhận', 'Thời gian'],
      rows.map(r => `<tr>
        <td><b>${escape(r.name)}</b><br><small>${escape(r.email)}</small></td>
        <td><b style="font-size:18px">${escape(r.hanzi)}</b></td>
        <td>${escape(r.pinyin)}</td>
        <td>${escape(r.meaning || '—')}</td>
        <td><b>${Number(r.accuracy_percent).toFixed(1)}%</b></td>
        <td><span class="tag ${r.accuracy_percent >= 80 ? 'published' : (r.accuracy_percent >= 60 ? 'draft' : 'hidden')}">${escape(r.rating || 'Đã chấm')}</span></td>
        <td>${escape(r.spoken_text || '—')}</td>
        <td>${date(r.created_at)}</td>
      </tr>`)
    );
  };
}

function renderStudentWriting(content, data) {
  content.innerHTML += `<section class="panel">
    <div class="toolbar">
      <input id="filter-user-writing" placeholder="Lọc theo học viên, email hoặc loại bài..." aria-label="Lọc luyện viết" style="flex:1;max-width:400px">
      <span class="pill">${data.length} bài luyện viết & tự luận</span>
    </div>
    <div id="writing-table-wrap">
      ${table(['Học viên', 'Kỹ năng', 'Điểm số', 'Người chấm', 'Nhận xét', 'Thời gian nộp', 'Thao tác'],
        data.map(r => `<tr>
          <td><b>${escape(r.name)}</b><br><small>${escape(r.email)}</small></td>
          <td><span class="tag ${r.kind === 'handwriting' ? 'published' : 'draft'}">${r.kind === 'handwriting' ? '✍️ Nét chữ Canvas' : '📝 Viết tự luận'}</span></td>
          <td><b style="font-size:16px">${r.score}</b>/100<br><small>Gốc: ${r.original_score}</small></td>
          <td><span class="tag">${escape(r.graded_by || 'Tự động')}</span></td>
          <td style="max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escape(r.feedback || '—')}</td>
          <td>${date(r.created_at)}</td>
          <td><button data-view-writing="${r.id}">Xem bài làm</button></td>
        </tr>`))}
    </div>
  </section>`;
  const input = document.querySelector('#filter-user-writing');
  if (input) input.oninput = e => {
    const q = e.target.value.toLowerCase().trim();
    const rows = data.filter(r => (r.name + ' ' + r.email + ' ' + r.kind + ' ' + (r.feedback || '')).toLowerCase().includes(q));
    document.querySelector('#writing-table-wrap').innerHTML = table(
      ['Học viên', 'Kỹ năng', 'Điểm số', 'Người chấm', 'Nhận xét', 'Thời gian nộp', 'Thao tác'],
      rows.map(r => `<tr>
        <td><b>${escape(r.name)}</b><br><small>${escape(r.email)}</small></td>
        <td><span class="tag ${r.kind === 'handwriting' ? 'published' : 'draft'}">${r.kind === 'handwriting' ? '✍️ Nét chữ Canvas' : '📝 Viết tự luận'}</span></td>
        <td><b style="font-size:16px">${r.score}</b>/100<br><small>Gốc: ${r.original_score}</small></td>
        <td><span class="tag">${escape(r.graded_by || 'Tự động')}</span></td>
        <td style="max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escape(r.feedback || '—')}</td>
        <td>${date(r.created_at)}</td>
        <td><button data-view-writing="${r.id}">Xem bài làm</button></td>
      </tr>`)
    );
    bindWritingView(rows);
  };
  bindWritingView(data);
}

function bindWritingView(rows) {
  document.querySelectorAll('[data-view-writing]').forEach(b => b.onclick = () => {
    const row = rows.find(r => r.id === Number(b.dataset.viewWriting));
    if (!row) return;
    let formattedContent;
    try { formattedContent = JSON.stringify(JSON.parse(row.content), null, 2); }
    catch { formattedContent = row.content; }
    openEditor(`Chi tiết bài làm #${row.id} - ${row.kind === 'handwriting' ? 'Luyện nét chữ Canvas' : 'Bài viết tự luận'}`, `
      <p><b>Học viên:</b> ${escape(row.name)} (${escape(row.email)})</p>
      <p><b>Điểm số:</b> <span class="score">${row.score}</span> / 100 (Điểm gốc: ${row.original_score})</p>
      <p><b>Người chấm:</b> ${escape(row.graded_by)}</p>
      <details open><summary>Nội dung bài làm (Dữ liệu nét vẽ / Bài viết)</summary><pre style="max-height:220px;overflow:auto;background:#f5f7f5;padding:10px;border-radius:6px">${escape(formattedContent)}</pre></details>
      <div class="detail-text" style="margin-top:10px"><b>Nhận xét:</b><br>${escape(row.feedback || 'Chưa có nhận xét.')}</div>
    `, () => {}, 'Đóng');
  });
}

function renderStudentVocab(content, data) {
  const saved = data.saved_words || [];
  const topWords = data.top_looked_up || [];
  content.innerHTML += `
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin-bottom:20px">
      <article class="stat"><small>Học viên đã lưu vào sổ tay</small><b>${saved.length}</b></article>
      <article class="stat"><small>Từ tra cứu nhiều trong từ điển</small><b>${topWords.length}</b></article>
    </div>
    <section class="panel" style="margin-bottom:24px">
      <h2>Sổ tay từ vựng học viên đã lưu</h2>
      <div class="toolbar">
        <input id="filter-saved-words" placeholder="Lọc theo học viên, chữ Hán, pinyin..." aria-label="Lọc sổ tay từ vựng" style="flex:1;max-width:400px">
        <span class="pill">${saved.length} mục đã lưu</span>
      </div>
      <div id="saved-words-wrap">
        ${table(['Học viên', 'Chữ Hán', 'Pinyin', 'Ý nghĩa', 'HSK', 'Thời gian lưu'],
          saved.map(s => `<tr>
            <td><b>${escape(s.name)}</b><br><small>${escape(s.email)}</small></td>
            <td><b style="font-size:18px">${escape(s.hanzi)}</b></td>
            <td>${escape(s.pinyin)}</td>
            <td>${escape(s.meaning)}</td>
            <td><span class="tag published">HSK ${s.hsk}</span></td>
            <td>${date(s.created_at)}</td>
          </tr>`))}
      </div>
    </section>
    <section class="panel">
      <h2>Top từ vựng học viên tra cứu nhiều nhất trong từ điển</h2>
      <div class="toolbar">
        <input id="filter-top-lookup" placeholder="Lọc theo chữ Hán, pinyin..." aria-label="Lọc tra cứu" style="flex:1;max-width:400px">
        <span class="pill">${topWords.length} từ phổ biến</span>
      </div>
      <div id="top-lookup-wrap">
        ${table(['Chữ Hán', 'Pinyin', 'Ý nghĩa', 'Cấp độ', 'Tổng lượt tra', 'Số học viên'],
          topWords.map(w => `<tr>
            <td><b style="font-size:18px">${escape(w.hanzi)}</b></td>
            <td>${escape(w.pinyin)}</td>
            <td>${escape(w.meaning)}</td>
            <td><span class="tag published">HSK ${w.hsk}</span></td>
            <td><b>${w.total_lookups}</b> lần</td>
            <td>${w.student_count} học viên</td>
          </tr>`))}
      </div>
    </section>
  `;
  const inputSaved = document.querySelector('#filter-saved-words');
  if (inputSaved) inputSaved.oninput = e => {
    const q = e.target.value.toLowerCase().trim();
    const rows = saved.filter(s => (s.name + ' ' + s.email + ' ' + s.hanzi + ' ' + s.pinyin + ' ' + s.meaning).toLowerCase().includes(q));
    document.querySelector('#saved-words-wrap').innerHTML = table(
      ['Học viên', 'Chữ Hán', 'Pinyin', 'Ý nghĩa', 'HSK', 'Thời gian lưu'],
      rows.map(s => `<tr>
        <td><b>${escape(s.name)}</b><br><small>${escape(s.email)}</small></td>
        <td><b style="font-size:18px">${escape(s.hanzi)}</b></td>
        <td>${escape(s.pinyin)}</td>
        <td>${escape(s.meaning)}</td>
        <td><span class="tag published">HSK ${s.hsk}</span></td>
        <td>${date(s.created_at)}</td>
      </tr>`)
    );
  };
  const inputTop = document.querySelector('#filter-top-lookup');
  if (inputTop) inputTop.oninput = e => {
    const q = e.target.value.toLowerCase().trim();
    const rows = topWords.filter(w => (w.hanzi + ' ' + w.pinyin + ' ' + w.meaning).toLowerCase().includes(q));
    document.querySelector('#top-lookup-wrap').innerHTML = table(
      ['Chữ Hán', 'Pinyin', 'Ý nghĩa', 'Cấp độ', 'Tổng lượt tra', 'Số học viên'],
      rows.map(w => `<tr>
        <td><b style="font-size:18px">${escape(w.hanzi)}</b></td>
        <td>${escape(w.pinyin)}</td>
        <td>${escape(w.meaning)}</td>
        <td><span class="tag published">HSK ${w.hsk}</span></td>
        <td><b>${w.total_lookups}</b> lần</td>
        <td>${w.student_count} học viên</td>
      </tr>`)
    );
  };
}

function renderLessonsCatalog(content, data) {
  const items = data.items || [];
  content.innerHTML += `<section class="panel">
    <div class="toolbar">
      <input id="filter-lessons-cat" placeholder="Tìm theo tên bài học hoặc mục tiêu..." aria-label="Tìm bài học" style="flex:1;max-width:400px">
      <span class="pill">Tổng số ${items.length} bài học lộ trình</span>
    </div>
    <div id="lessons-cat-wrap">
      ${table(['Cấp độ', 'Mã bài', 'Tên bài học', 'Thời lượng', 'Mục tiêu bài học'],
        items.map(l => `<tr>
          <td><span class="tag published">HSK ${l.hsk}</span></td>
          <td><code>${escape(l.id)}</code></td>
          <td><b>${escape(l.title)}</b></td>
          <td>${l.minutes} phút</td>
          <td>${escape(l.objective || '—')}</td>
        </tr>`))}
    </div>
  </section>`;
  const input = document.querySelector('#filter-lessons-cat');
  if (input) input.oninput = e => {
    const q = e.target.value.toLowerCase().trim();
    const rows = items.filter(l => (l.title + ' ' + l.id + ' ' + (l.objective || '')).toLowerCase().includes(q));
    document.querySelector('#lessons-cat-wrap').innerHTML = table(
      ['Cấp độ', 'Mã bài', 'Tên bài học', 'Thời lượng', 'Mục tiêu bài học'],
      rows.map(l => `<tr>
        <td><span class="tag published">HSK ${l.hsk}</span></td>
        <td><code>${escape(l.id)}</code></td>
        <td><b>${escape(l.title)}</b></td>
        <td>${l.minutes} phút</td>
        <td>${escape(l.objective || '—')}</td>
      </tr>`)
    );
  };
}

function hskSelect(name = 'hsk') {
  return `<select name="${name}">${[1,2,3,4,5,6].map(n => `<option value="${n}">HSK ${n}</option>`).join('')}</select>`;
}

const HANZI_STROKE_MAP = {
  '爱':10,'八':2,'爸':8,'杯':8,'子':3,'北':5,'京':8,'本':5,'不':4,'客':9,'气':4,'菜':11,'茶':9,'吃':6,'出':5,'租':10,'车':7,'点':9,'电':5,'脑':13,'视':9,'影':15,'东':5,'西':6,'都':10,'读':10,'对':5,'起':10,'多':6,'少':4,'儿':2,'二':2,'饭':7,'馆':11,'高':10,'兴':6,'个':3,'工':3,'作':7,'狗':8,'语':9,'汉':5,'好':6,'喝':12,'和':8,'很':9,'后':6,'面':9,'回':6,'会':6,'几':2,'家':10,'叫':5,'今':4,'天':4,'九':2,'开':4,'看':9,'见':4,'块':7,'来':7,'老':6,'师':6,'了':2,'冷':7,'里':7,'零':13,'六':4,'妈':6,'吗':6,'买':6,'猫':11,'没':7,'关':6,'系':7,'米':6,'明':8,'名':6,'字':6,'哪':9,'那':6,'呢':8,'能':10,'你':7,'年':6,'朋':8,'友':4,'漂':14,'亮':9,'苹':8,'果':8,'七':2,'钱':10,'前':9,'请':10,'去':5,'热':10,'人':2,'认':4,'识':7,'日':4,'三':3,'商':11,'店':8,'上':3,'午':4,'谁':10,'什':4,'么':3,'十':2,'时':7,'候':10,'是':9,'书':4,'水':4,'果':8,'睡':13,'觉':9,'说':9,'话':8,'四':5,'岁':6,'他':5,'她':6,'太':4,'听':7,'同':6,'喂':12,'我':7,'们':5,'五':4,'喜':12,'欢':6,'下':3,'雨':8,'先':6,'生':5,'现':8,'在':6,'想':13,'小':3,'姐':8,'些':8,'写':5,'谢':12,'星':9,'期':12,'学':8,'习':3,'校':10,'一':1,'衣':6,'服':8,'医':7,'院':9,'椅':12,'有':6,'月':4,'再':6,'怎':9,'样':10,'这':7,'中':4,'国':8,'住':7,'桌':10,'昨':9,'坐':7,'做':11,'帮':17,'助':7,'环':8,'境':14,'经':8,'验':10,'效':10,'率':11,'毅':15,'力':2
};

function getStrokeCountLabel(r) {
  if (r.strokes && r.strokes.length > 0) return `${r.strokes.length} nét`;
  let total = 0;
  for (const ch of (r.hanzi || '')) {
    total += HANZI_STROKE_MAP[ch] || 0;
  }
  return total > 0 ? `${total} nét` : 'Chưa có nét';
}

function renderWords(content, data, params) {
  const filter = new URLSearchParams(params);
  content.innerHTML += `<section class="panel"><form id="filters" class="toolbar"><label>Tìm từ<input name="search" placeholder="Chữ Hán, Pinyin, nghĩa" value="${escape(filter.get('search') || '')}"></label><label>Cấp độ<select name="hsk"><option value="">Tất cả HSK</option>${[1,2,3,4,5,6].map(n=>`<option value="${n}">HSK ${n}</option>`).join('')}</select></label><button>Tìm</button><button type="button" id="add" class="primary">+ Thêm từ</button></form>${table(['Chữ Hán','Pinyin / Nghĩa','Cấp độ','Nét chuẩn','Thao tác'],data.map(r=>`<tr><td class="hanzi">${escape(r.hanzi)}</td><td>${escape(r.pinyin)}<small>${escape(r.meaning)}</small></td><td><span class="tag">HSK ${r.hsk}</span></td><td>${getStrokeCountLabel(r)}</td><td><div class="actions"><button data-edit="${r.id}">Sửa</button><button class="danger" data-delete="${r.id}">Xóa</button></div></td></tr>`))}</section>`;
  bindFilter(params);
  document.querySelector('#add').onclick = () => wordEditor();
  document.querySelectorAll('[data-edit]').forEach(b => b.onclick = () => wordEditor(data.find(r=>r.id === Number(b.dataset.edit))));
  bindDeletes(data,'vocabulary',r=>r.hanzi);
}

function wordEditor(row) {
  const word = row || {hanzi:'',pinyin:'',meaning:'',hsk:1,example:'',audio_url:'',strokes:[]};
  strokes = structuredClone(word.strokes);
  openEditor(row ? 'Chỉnh sửa từ vựng' : 'Thêm từ vựng', `<div class="grid"><label>Chữ Hán<input name="hanzi" required maxlength="30" value="${escape(word.hanzi)}"></label><label>Pinyin<input name="pinyin" required maxlength="120" value="${escape(word.pinyin)}"></label><label>Nghĩa tiếng Việt<input name="meaning" required maxlength="300" value="${escape(word.meaning)}"></label><label>Cấp độ${hskSelect()}</label><label class="span-2">Câu ví dụ<textarea name="example" maxlength="1000">${escape(word.example)}</textarea></label><label class="span-2">Audio mẫu (URL HTTPS, tùy chọn)<input name="audio_url" type="text" value="${escape(word.audio_url)}"></label></div><fieldset><legend>Nét bút thuận</legend><div class="stroke-area"><canvas id="strokes" width="512" height="512" aria-label="Vẽ lần lượt các nét chữ chuẩn"></canvas><div class="stroke-help"><p>Vẽ từng nét đúng thứ tự bằng chuột hoặc cảm ứng. Số trên hình là thứ tự nét.</p><b id="stroke-count"></b><div><button type="button" id="undo-stroke">Bỏ nét cuối</button><button type="button" id="clear-strokes">Vẽ lại</button></div><small>Để trống nếu chưa có dữ liệu chuẩn. Chỉ lưu nét đã được kiểm tra.</small></div></div></fieldset>`, async form => {
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
  content.innerHTML += `<section class="panel"><form id="filters" class="toolbar"><label>Cấp độ<select name="hsk"><option value="">Tất cả HSK</option>${[1,2,3,4,5,6].map(n=>`<option value="${n}">HSK ${n}</option>`).join('')}</select></label><button>Lọc</button><button type="button" class="primary" id="add">+ Tạo đề thi</button><button type="button" id="add-listening">+ Đề Nghe</button><button type="button" id="add-reading">+ Đề Đọc</button></form>${table(['Đề thi','Cấp độ','Trạng thái','Nội dung','Thao tác'],data.map(r=>`<tr><td><b>${escape(r.title)}</b><small>${r.duration_minutes} phút · Phiên bản ${r.version}</small></td><td>HSK ${r.hsk}</td><td><span class="tag ${r.status}">${statusLabel(r.status)}</span></td><td>${r.questions.length} câu</td><td><div class="actions"><button data-edit="${r.id}">Biên soạn</button><button class="danger" data-delete="${r.id}">Xóa</button></div></td></tr>`))}</section>`;
  bindFilter(params);
  document.querySelector('#add').onclick = () => examEditor();
  document.querySelector('#add-listening').onclick = () => examEditor(null, 'listening');
  document.querySelector('#add-reading').onclick = () => examEditor(null, 'reading');
  document.querySelectorAll('[data-edit]').forEach(b => b.onclick = () => examEditor(data.find(r=>r.id===Number(b.dataset.edit))));
  bindDeletes(data,'exams',r=>r.title);
}

function newQuestionId() {
  // A local content ID, not an authentication token. HTTP on a LAN may lack randomUUID.
  return globalThis.crypto?.randomUUID?.() || `q-${Date.now().toString(36)}-${Math.random().toString(36).slice(2,10)}`;
}

function questionHTML(q = {}) {
  const questionType = q.question_type || '';
  return `<fieldset class="question"><legend>Câu hỏi</legend><div class="grid">
    <label>Mã câu<input data-key="id" required maxlength="40" value="${escape(q.id || newQuestionId())}"></label>
    <label>Kỹ năng<select data-key="section">${[['reading','Đọc'],['listening','Nghe'],['writing','Viết']].map(([v,l])=>`<option value="${v}" ${q.section===v?'selected':''}>${l}</option>`).join('')}</select></label>
    <label>Loại câu hỏi (tùy chọn)<select data-key="question_type"><option value="">Loại cũ / mặc định</option><option value="sentence_order" ${questionType==='sentence_order'?'selected':''}>Sắp xếp câu</option><option value="hanzi_canvas"  ${questionType==='hanzi_canvas'?'selected':''}>Canvas viết chữ Hán</option><option value="essay" ${questionType==='essay'?'selected':''}>Đoạn văn tự luận</option></select></label>
    <label>Trọng số<input data-key="weight" type="number" min="0.01" max="100" step="0.01" value="${q.weight || 1}"></label>
    <label class="span-2">Yêu cầu / nội dung<textarea data-key="prompt" required maxlength="5000">${escape(q.prompt || '')}</textarea></label>
    <label>Lựa chọn (mỗi dòng một đáp án)<textarea data-key="options">${escape((q.options || []).join('\n'))}</textarea></label>
    <label>Đáp án / rubric chấm<textarea data-key="answer" required maxlength="5000">${escape(q.answer || '')}</textarea></label>
    <label>Audio HTTPS (bắt buộc cho Nghe)<input data-key="audio_url" type="text" value="${escape(q.audio_url || '')}"></label>
    <label>ID từ liên quan (tùy chọn)<input data-key="word_id" type="number" min="1" value="${q.word_id || ''}"></label>
    <label>Transcript<textarea data-key="transcript">${escape(q.transcript || '')}</textarea></label>
    <label>Giải thích đáp án<textarea data-key="explanation">${escape(q.explanation || '')}</textarea></label>
    <p class="note span-2">Canvas: chọn kỹ năng Viết và nhập đúng một chữ Hán ở ô đáp án; máy chủ tự liên kết strokes_json trong Từ vựng. Essay: prompt là đề bài, ô đáp án là rubric bổ sung.</p>
  </div><button type="button" class="danger remove">Bỏ câu hỏi</button></fieldset>`;
}

function examEditor(row, section = 'reading') {
  const exam = row || {title:'',hsk:1,status:'draft',duration_minutes:15,questions:[{section}]};
  openEditor(row?'Biên soạn đề thi':'Tạo đề thi', `<div class="grid"><label class="span-2">Tên đề<input name="title" required maxlength="200" value="${escape(exam.title)}"></label><label>Cấp độ${hskSelect()}</label><label>Thời lượng (phút)<input name="duration_minutes" type="number" min="1" max="240" required value="${exam.duration_minutes}"></label><label>Trạng thái<select name="status" aria-label="Trạng thái"><option value="draft">Bản nháp</option><option value="published">Phát hành</option><option value="hidden">Ẩn</option></select></label></div><p class="note">Học viên chỉ thấy đề đã phát hành. Bài viết tự do dùng rubric để module Writing chấm; trắc nghiệm chấm theo đáp án. Thay đổi đề sẽ tạo phiên bản mới.</p><div id="questions" class="questions">${exam.questions.map(questionHTML).join('')}</div><button type="button" id="add-question">+ Thêm câu hỏi</button>`, async form => {
    const questions = [...form.querySelectorAll('.question')].map(fieldset => {
      const q = {};
      fieldset.querySelectorAll('[data-key]').forEach(el=>q[el.dataset.key]=el.value.trim());
      q.options=q.options.split('\n').map(s=>s.trim()).filter(Boolean);
      q.word_id=q.word_id?Number(q.word_id):null;
      q.question_type=q.question_type || null;
      q.weight=Number(q.weight || 1);
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
  content.innerHTML += '<div class="toolbar"><button id="show-appeals">Yêu cầu phúc khảo</button><a href="/review" target="_blank" rel="noopener">Trang kết quả học viên ↗</a></div>';
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
  document.querySelector('#show-appeals').onclick = () => showAppeals(content);
}

function renderAI(content, data) {
  content.innerHTML += `<section class="panel"><form id="ai-form" class="dialog-body"><div class="note"><b>${data.ready?'Cấu hình sẵn sàng cho module AI':'AI chưa sẵn sàng'}</b><br>Khóa máy chủ: ${data.key_configured?'Đã cấu hình':'Chưa cấu hình'}. Model dự phòng: ${escape(data.fallback_model || 'Chưa cấu hình')}. Trạng thái này kiểm tra cấu hình nội bộ, chưa xác minh kết nối với nhà cung cấp.</div><div class="grid"><label>Model<input name="model" required maxlength="120" value="${escape(data.model)}"></label><label>Giới hạn token<input name="max_tokens" type="number" min="1" max="16000" required value="${data.max_tokens}"></label><label>Temperature (0–2)<input name="temperature" type="number" min="0" max="2" step="0.1" required value="${data.temperature}"></label><label class="check"><input name="enabled" type="checkbox" ${data.enabled?'checked':''}> Bật AI</label><label class="span-2">Hướng dẫn hệ thống / prompt mẫu<textarea name="system_prompt" required maxlength="10000" rows="7">${escape(data.system_prompt)}</textarea></label></div><small>Khóa API được cấu hình bằng biến môi trường GEMINI_API_KEY trên máy chủ; không nhập hoặc hiển thị khóa ở trang này.</small><div id="ai-error" role="alert"></div><div><button class="primary">Lưu cấu hình</button></div></form></section>`;
  const testButton = document.createElement('button');
  testButton.type = 'button';
  testButton.textContent = 'Kiểm tra kết nối Gemini (có thể tính phí)';
  testButton.disabled = !data.ready;
  document.querySelector('#ai-form').append(testButton);
  testButton.onclick = async () => {
    testButton.disabled = true;
    const message = document.querySelector('#ai-error');
    message.textContent = 'Đang kiểm tra cấu hình đã lưu…';
    try { message.textContent = (await api('/admin/ai-config/test','POST')).message; }
    catch (err) { message.textContent = err.message; }
    finally { testButton.disabled = false; }
  };
  document.querySelector('#ai-form').onsubmit=async event=>{
    event.preventDefault(); const form=event.currentTarget; const button=form.querySelector('button'); button.disabled=true;
    try {
      await api('/admin/ai-config','PUT',{model:form.elements.model.value,system_prompt:form.elements.system_prompt.value,max_tokens:Number(form.elements.max_tokens.value),temperature:Number(form.elements.temperature.value),enabled:form.elements.enabled.checked,version:data.version});
      notify('Đã lưu cấu hình AI'); loadPage();
    } catch(err){if(document.querySelector('#ai-error'))document.querySelector('#ai-error').innerHTML=`<div class="error">${escape(err.message)}</div>`;} finally {button.disabled=false;}
  };
}

async function showAppeals(content, status='pending') {
  const id = ++loadId;
  content.innerHTML = heading() + '<p role="status">Đang tải yêu cầu…</p>';
  try {
    const rows = await api(`/admin/appeals?status=${status}`);
    if (id !== loadId) return;
    content.innerHTML = heading() + `<div class="toolbar"><button id="back-results">Tất cả kết quả</button><button id="pending-appeals" aria-pressed="${status==='pending'}">Chờ xử lý</button><button id="resolved-appeals" aria-pressed="${status==='resolved'}">Đã xử lý</button></div><section class="panel">${table(['Học viên','Yêu cầu','Thời gian','Thao tác'],rows.map(r=>`<tr><td>${escape(r.name)}<small>${escape(r.email)}</small></td><td>Bài #${r.result_id} · ${r.score} điểm<small>${escape(r.reason)}</small>${r.response?`<p>Phản hồi: ${escape(r.response)}</p>`:''}</td><td>${date(r.created_at)}</td><td>${r.status==='pending'?`<button data-appeal="${r.id}">Xử lý</button>`:'Đã phản hồi'}</td></tr>`))}</section>`;
    document.querySelector('#back-results').onclick=()=>loadPage();
    document.querySelector('#pending-appeals').onclick=()=>showAppeals(content,'pending');
    document.querySelector('#resolved-appeals').onclick=()=>showAppeals(content,'resolved');
    content.querySelectorAll('[data-appeal]').forEach(button=>button.onclick=()=>{
      const row=rows.find(r=>r.id===Number(button.dataset.appeal));
      openEditor(`Phúc khảo #${row.id}`, `<p><b>${escape(row.name)}</b></p><p>${escape(row.reason)}</p><details><summary>Bài làm và nhận xét</summary><pre>${escape(row.content)}</pre><p>${escape(row.feedback)}</p></details><label>Điểm sau phúc khảo<input name="score" type="number" min="0" max="100" step="0.01" required value="${row.score}"></label><p class="note">Giữ nguyên điểm nếu kết quả ban đầu đúng.</p><label>Phản hồi cho học viên<textarea name="response" required minlength="5" maxlength="2000"></textarea></label>`, async form=>{
        await api(`/admin/appeals/${row.id}`,'PATCH',{version:row.version,result_version:row.result_version,score:Number(form.elements.score.value),response:form.elements.response.value});
      },'Hoàn tất phúc khảo');
    });
  } catch (err) {
    if (id !== loadId) return;
    content.innerHTML=heading()+`<p role="alert">${escape(err.message)}</p><button id="appeals-retry">Thử lại</button>`;
    document.querySelector('#appeals-retry').onclick=()=>showAppeals(content,status);
  }
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
  if (!token) {
    const sharedToken = localStorage.getItem('auth_token') || localStorage.getItem('hanzigo_token');
    if (sharedToken) {
      token = sharedToken;
    } else {
      return loginView();
    }
  }
  try {
    user = await api('/me');
    if (user.role !== 'admin') {
      clearSession();
      return loginView('Tài khoản này không có quyền quản trị. Hãy đăng nhập bằng tài khoản Admin.');
    }
    sessionStorage.setItem('hanzigo_admin_token', token);
    shell();
  } catch (err) {
    clearSession();
    loginView(err.message);
  }
}
boot();
