const escape = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const actions = {create:'Tạo mới',update:'Cập nhật',delete:'Xóa',override:'Điều chỉnh điểm',resolve:'Xử lý phúc khảo',reset_password:'Đặt lại mật khẩu',password_change:'Đổi mật khẩu',password_recovery:'Khôi phục mật khẩu',update_profile:'Cập nhật hồ sơ',reply:'Trả lời hội thoại',takeover:'Tiếp nhận hội thoại',resume_ai:'Giao lại cho AI',connection_test:'Kiểm tra kết nối AI'};
const entities = {user:'Tài khoản',vocabulary:'Từ vựng',exam:'Đề thi',result:'Kết quả học tập',appeal:'Phúc khảo',ai_config:'Cấu hình AI',student_ai_exam:'Đề thi AI học viên',chat:'Hội thoại'};
const fields = {name:'Họ tên',email:'Email',role:'Vai trò',is_active:'Đang hoạt động',model:'Model',system_prompt:'Hướng dẫn hệ thống',temperature:'Mức sáng tạo',max_tokens:'Giới hạn token',enabled:'Bật AI',version:'Phiên bản',score:'Điểm',reason:'Lý do',state:'Trạng thái',status:'Trạng thái xử lý',content:'Nội dung',message_id:'Mã tin nhắn',hanzi:'Chữ Hán',pinyin:'Pinyin',meaning:'Nghĩa',hsk:'Cấp HSK',title:'Tiêu đề',response:'Phản hồi',id:'Mã dữ liệu',created_at:'Thời gian tạo',avatar_changed:'Đổi ảnh đại diện'};
const date = value => new Date(value*1000).toLocaleString('vi-VN');
function parse(value) { try { return JSON.parse(value); } catch { return value; } }
function display(value) {
  if (value === undefined || value === null) return '—';
  if (typeof value === 'boolean') return value ? 'Có' : 'Không';
  return typeof value === 'object' ? JSON.stringify(value,null,2) : String(value);
}
function changes(row) {
  const before = parse(row.before_json), after = parse(row.after_json);
  const object = value => value && typeof value === 'object' && !Array.isArray(value);
  if (!object(before) && !object(after)) return [{key:'content',before,after,changed:JSON.stringify(before)!==JSON.stringify(after)}];
  const left = object(before) ? before : before == null ? {} : {content:before};
  const right = object(after) ? after : after == null ? {} : {content:after};
  return [...new Set([...Object.keys(left),...Object.keys(right)])].map(key => ({
    key,before:left[key],after:right[key],changed:JSON.stringify(left[key])!==JSON.stringify(right[key])
  }));
}

export function renderAuditLog(content, initial, api, dialog) {
  const panel = document.createElement('section');
  panel.className = 'audit-workspace';
  panel.innerHTML = `<section class="system-card"><div class="system-card-head"><div><h2>Lịch sử hoạt động</h2><p>Tra cứu người thực hiện, thời điểm và toàn bộ dữ liệu trước / sau thay đổi.</p></div><button class="audit-refresh">↻ Làm mới</button></div>
    <form class="audit-filters"><label class="audit-search">Tìm trong nhật ký<input name="search" type="search" maxlength="200" placeholder="Tên, email, mã đối tượng hoặc nội dung…" aria-label="Tìm trong nhật ký"></label><label>Thao tác<select name="action"></select></label><label>Đối tượng<select name="entity"></select></label><label>Người thực hiện<select name="actor_id"></select></label><label>Từ ngày<input name="from_date" type="date"></label><label>Đến ngày<input name="to_date" type="date"></label><div class="audit-filter-buttons"><button type="submit" class="primary">Áp dụng bộ lọc</button><button type="button" class="audit-clear">Xóa bộ lọc</button></div></form></section>
    <section class="system-card audit-results"><div class="audit-results-head"><p class="audit-count" role="status"></p><label>Số dòng / trang<select class="audit-limit"><option>25</option><option selected>50</option><option>100</option></select></label></div><div class="audit-error" role="status"></div><div class="audit-table"></div><div class="audit-pagination"><button class="audit-prev">← Trang trước</button><span></span><button class="audit-next">Trang sau →</button></div></section>`;
  content.append(panel);
  const $ = selector => panel.querySelector(selector), form = $('.audit-filters');
  let data = initial, offset = initial.offset || 0, limit = initial.limit || 50, query = {}, requestId = 0, loading = false;
  function options(name, values, label, key, text) {
    const select = form.elements[name], selected = select.value;
    select.innerHTML = '<option value="">' + label + '</option>' + values.map(value =>
      '<option value="' + escape(key(value)) + '">' + escape(text(value)) + '</option>').join('');
    select.value = selected;
  }
  function controls() {
    $('.audit-prev').disabled = loading || offset === 0;
    $('.audit-next').disabled = loading || offset+limit >= data.total;
    $('.audit-refresh').disabled = loading;
    $('.audit-results').setAttribute('aria-busy',String(loading));
  }
  function render() {
    options('action',data.actions || [],'Tất cả thao tác',value=>value,value=>actions[value] || value);
    options('entity',data.entities || [],'Tất cả đối tượng',value=>value,value=>entities[value] || value);
    options('actor_id',data.actors || [],'Tất cả người thực hiện',value=>value.id,value=>value.name+' · #'+value.id);
    $('.audit-limit').value = String(limit);
    $('.audit-count').textContent = data.total.toLocaleString('vi-VN')+' bản ghi phù hợp' + (Object.keys(query).length ? ' · Đang áp dụng bộ lọc' : ' · Toàn bộ nhật ký');
    const rows = data.items.map(row => {
      const changed = changes(row).filter(field => field.changed);
      return `<tr><td data-label="Thời gian"><b>${date(row.created_at)}</b><small>Nhật ký #${row.id}</small></td><td data-label="Người thực hiện"><b>${escape(row.name)}</b><small>${escape(row.email || 'Tài khoản #' + row.actor_id)}</small></td><td data-label="Thao tác"><span class="support-badge ${row.action === 'delete' ? 'waiting' : 'ai'}">${escape(actions[row.action] || row.action)}</span><small>${escape(entities[row.entity] || row.entity)} · #${escape(row.entity_id)}</small></td><td data-label="Nội dung"><span class="audit-change-summary">${changed.length ? escape(changed.map(field=>fields[field.key] || field.key).join(', ')) : 'Không có thay đổi dữ liệu'}</span><small>${changed.length} trường thay đổi</small></td><td data-label="Chi tiết"><button data-log="${row.id}">Xem đầy đủ</button></td></tr>`;
    }).join('');
    $('.audit-table').innerHTML = rows ? '<div class="table-wrap"><table class="responsive-table"><thead><tr><th>Thời gian</th><th>Người thực hiện</th><th>Thao tác / đối tượng</th><th>Nội dung thay đổi</th><th>Chi tiết</th></tr></thead><tbody>'+rows+'</tbody></table></div>' : '<div class="empty"><h3>Không có nhật ký phù hợp</h3><p>Thử thay đổi khoảng ngày hoặc xóa bộ lọc để xem toàn bộ lịch sử.</p></div>';
    $('.audit-pagination span').textContent = data.total ? (offset+1)+'–'+Math.min(offset+data.items.length,data.total)+' / '+data.total : '0 / 0';
    panel.querySelectorAll('[data-log]').forEach(button => button.onclick = () => detail(data.items.find(row=>row.id===Number(button.dataset.log)),button));
    controls();
  }
  function detail(row, opener) {
    const before = parse(row.before_json), after = parse(row.after_json);
    dialog.oncancel = null;
    dialog.classList.add('audit-dialog');
    dialog.innerHTML = `<div class="dialog-head"><div><small>NHẬT KÝ #${row.id}</small><h2>${escape(actions[row.action] || row.action)}</h2></div><button type="button" class="audit-close" aria-label="Đóng chi tiết nhật ký">Đóng</button></div><div class="dialog-body">
      <dl class="audit-metadata"><div><dt>Người thực hiện</dt><dd>${escape(row.name)}<small>${escape(row.email || '')} · #${row.actor_id}</small></dd></div><div><dt>Thời điểm</dt><dd>${date(row.created_at)}</dd></div><div><dt>Đối tượng</dt><dd>${escape(entities[row.entity] || row.entity)}<small>Mã: ${escape(row.entity_id)}</small></dd></div><div><dt>Mã thao tác</dt><dd>${escape(row.action)}</dd></div></dl>
      <div><h3>Đối chiếu thay đổi</h3><p class="muted">Các dòng được tô màu là dữ liệu đã thay đổi.</p><div class="audit-diff">${changes(row).map(field=>`<article class="${field.changed?'changed':''}"><h4>${escape(fields[field.key] || field.key)} <small>${escape(field.key)}</small></h4><div><section><small>TRƯỚC</small><pre>${escape(display(field.before))}</pre></section><section><small>SAU</small><pre>${escape(display(field.after))}</pre></section></div></article>`).join('')}</div></div>
      <details><summary>Xem toàn bộ dữ liệu gốc</summary><h3>Trước thay đổi</h3><pre>${escape(display(before))}</pre><h3>Sau thay đổi</h3><pre>${escape(display(after))}</pre></details></div>`;
    dialog.querySelector('.audit-close').onclick = () => dialog.close();
    dialog.addEventListener('close',()=>{dialog.classList.remove('audit-dialog');if(opener.isConnected)opener.focus();},{once:true});
    dialog.showModal();
  }
  async function reload() {
    const current = ++requestId; loading = true; controls(); $('.audit-error').textContent = '';
    try {
      const params = new URLSearchParams({...query,paginated:'true',limit:String(limit),offset:String(offset)});
      const next = await api('/admin/audit-logs?'+params);
      if (!panel.isConnected || current !== requestId) return;
      data = next;
      if (data.total && offset >= data.total) { offset = Math.floor((data.total-1)/limit)*limit; return reload(); }
      render();
    } catch (err) { if (panel.isConnected && current === requestId) $('.audit-error').textContent = err.message + ' Bấm Làm mới để thử lại.'; }
    finally { if (panel.isConnected && current === requestId) { loading = false; controls(); } }
  }
  form.onsubmit = event => {
    event.preventDefault();
    const from = form.elements.from_date.value, to = form.elements.to_date.value;
    if (from && to && from > to) { $('.audit-error').textContent = 'Ngày kết thúc phải bằng hoặc sau ngày bắt đầu.'; return; }
    query = {};
    for (const key of ['search','action','entity','actor_id']) if (form.elements[key].value.trim()) query[key] = form.elements[key].value.trim();
    if (from) query.from_ts = String(Math.floor(new Date(from+'T00:00:00').getTime()/1000));
    if (to) { const end = new Date(to+'T00:00:00'); end.setDate(end.getDate()+1); query.to_ts = String(Math.floor(end.getTime()/1000)); }
    offset = 0; reload();
  };
  $('.audit-clear').onclick = () => { form.reset(); query = {}; offset = 0; reload(); };
  $('.audit-refresh').onclick = reload;
  $('.audit-prev').onclick = () => { offset = Math.max(0,offset-limit); reload(); };
  $('.audit-next').onclick = () => { offset += limit; reload(); };
  $('.audit-limit').onchange = event => { limit = Number(event.target.value); offset = 0; reload(); };
  render();
}
