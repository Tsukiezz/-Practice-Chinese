const escape = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const modules = {connection_test:'Kiểm tra kết nối',reading:'Chấm đọc',listening:'Chấm nghe',writing:'Chấm viết',translation:'Dịch & ngữ pháp',capability:'Báo cáo năng lực',exam:'Chấm bài thi',handwriting:'Viết tay',personalized_practice:'Luyện tập cá nhân',support_chat:'Chat hỗ trợ'};

export function renderAIConfig(content, initial, api, notify) {
  let saved = initial, saving = false, testing = false;
  const panel = document.createElement('section');
  panel.className = 'ai-workspace';
  panel.innerHTML = `<div class="system-summary ai-summary"></div><div class="ai-layout">
    <section class="system-card"><div class="system-card-head"><div><h2>Cấu hình trợ lý AI</h2><p>Điều chỉnh phản hồi và lưu thay đổi ngay tại đây.</p></div><span class="ai-dirty support-badge">Đã đồng bộ</span></div>
    <form id="ai-form"><fieldset class="ai-fields"><legend class="sr-only">Cấu hình AI</legend>
      <label class="ai-switch"><span><b>Cho phép sử dụng AI</b><small>Áp dụng cho các chức năng AI sử dụng cấu hình chung.</small></span><input type="checkbox" name="enabled" role="switch"></label>
      <label>Model chính<input name="model" required maxlength="120" autocomplete="off"><small>Tên model Gemini đang được cấp quyền trên máy chủ.</small></label>
      <div class="grid"><label>Mức sáng tạo · Temperature<input name="temperature" type="number" min="0" max="2" step="0.1" required><small>Thấp: phản hồi nhất quán. Cao: đa dạng cách diễn đạt.</small></label><label>Độ dài tối đa · Token<input name="max_tokens" type="number" min="1" max="16000" required><small>Tăng khi câu trả lời thường bị cắt ngắn.</small></label></div>
      <label>Hướng dẫn chấm bài<textarea name="system_prompt" rows="9" required maxlength="10000"></textarea><small>Prompt này dùng cho chấm bài. Chat hỗ trợ có hướng dẫn riêng về tiếng Trung và chuyển quản trị viên.</small></label>
    </fieldset><div id="ai-error" role="status" aria-live="polite"></div><div class="ai-savebar"><span class="ai-save-note">Cấu hình đã được lưu.</span><div><button type="button" class="ai-reset">Bỏ thay đổi</button><button type="submit" class="primary ai-save">Lưu cấu hình</button></div></div></form></section>
    <aside class="ai-side"><section class="system-card"><div class="system-card-head"><div><h2>Kết nối Gemini</h2><p>Kiểm tra phản hồi thật từ cấu hình đã lưu.</p></div></div><div class="ai-connection-info"></div><div class="ai-connection-result" role="status">Chưa kiểm tra kết nối trong phiên này.</div><button type="button" class="ai-test">Kiểm tra kết nối</button><small class="ai-test-note">Lượt kiểm tra có thể được nhà cung cấp tính phí.</small><button type="button" class="ai-reload">↻ Tải lại cấu hình</button></section>
    <section class="system-card"><div class="system-card-head"><div><h2>Hoạt động gần đây</h2><p>8 lượt AI mới nhất đã được ghi nhận.</p></div></div><div class="ai-activity"></div></section></aside></div>`;
  content.append(panel);
  const $ = selector => panel.querySelector(selector), form = $('#ai-form');
  const values = () => ({model:form.elements.model.value.trim(),system_prompt:form.elements.system_prompt.value,
    temperature:Number(form.elements.temperature.value),max_tokens:Number(form.elements.max_tokens.value),enabled:form.elements.enabled.checked});
  const baseline = () => ({model:saved.model,system_prompt:saved.system_prompt,temperature:saved.temperature,max_tokens:saved.max_tokens,enabled:!!saved.enabled});
  const dirty = () => JSON.stringify(values()) !== JSON.stringify(baseline());
  function controls() {
    const changed = dirty();
    $('.ai-save').disabled = saving || testing || !changed;
    $('.ai-save').textContent = saving ? 'Đang lưu…' : 'Lưu cấu hình';
    $('.ai-reset').disabled = saving || testing || !changed;
    $('.ai-test').disabled = saving || testing || changed || !saved.ready;
    $('.ai-reload').disabled = saving || testing || changed;
    $('.ai-dirty').textContent = changed ? 'Chưa lưu' : 'Đã đồng bộ';
    $('.ai-dirty').classList.toggle('waiting',changed);
    $('.ai-save-note').textContent = changed ? 'Có thay đổi chưa được lưu.' : 'Cấu hình đã được lưu.';
    $('.ai-test-note').textContent = changed ? 'Lưu thay đổi trước khi kiểm tra kết nối.' : !saved.ready ? 'Bật AI, chọn model và cấu hình khóa máy chủ để kiểm tra.' : 'Lượt kiểm tra có thể được nhà cung cấp tính phí.';
  }
  function summary() {
    const usage = saved.usage_24h || {}, success = usage.success || 0, errors = usage.error || 0;
    $('.ai-summary').innerHTML = `<article><span>Trạng thái AI</span><b>${saved.enabled ? 'Đang bật' : 'Đang tắt'}</b><small>${saved.ready ? 'Cấu hình đủ điều kiện kết nối' : 'Cần kiểm tra cấu hình'}</small></article><article><span>Khóa máy chủ</span><b>${saved.key_configured ? 'Đã cấu hình' : 'Chưa cấu hình'}</b><small>Khóa được giữ riêng trên máy chủ</small></article><article><span>Lượt thành công · 24 giờ</span><b>${success.toLocaleString('vi-VN')}</b><small>Theo nhật ký sử dụng AI</small></article><article><span>Lượt lỗi · 24 giờ</span><b>${errors.toLocaleString('vi-VN')}</b><small>${success+errors ? 'Kiểm tra kết nối nếu lỗi lặp lại' : 'Chưa có lượt gọi được ghi nhận'}</small></article>`;
    $('.ai-connection-info').innerHTML = `<dl><div><dt>Model chính</dt><dd>${escape(saved.model)}</dd></div><div><dt>Model dự phòng</dt><dd>${escape(saved.fallback_model || 'Chưa cấu hình')}</dd></div></dl><p class="muted">Trạng thái cấu hình không đồng nghĩa với kết nối đang hoạt động.</p>`;
    $('.ai-activity').innerHTML = (saved.recent_usage || []).map(row => `<div class="ai-activity-row"><span class="status-dot ${row.status}"></span><div><b>${escape(modules[row.module] || row.module)}</b><small>${escape(row.name)} · ${new Date(row.created_at*1000).toLocaleString('vi-VN')}</small></div><span class="support-badge ${row.status === 'error' ? 'waiting' : 'ai'}">${row.status === 'error' ? 'Lỗi' : 'Thành công'}</span></div>`).join('') || '<p class="muted">Chưa có hoạt động AI được ghi nhận.</p>';
  }
  function fill() {
    for (const key of ['model','system_prompt','temperature','max_tokens']) form.elements[key].value = saved[key];
    form.elements.enabled.checked = !!saved.enabled; summary(); controls();
  }
  form.oninput = controls;
  $('.ai-reset').onclick = () => { fill(); $('#ai-error').textContent = ''; };
  $('.ai-reload').onclick = async () => {
    if (saving || testing || dirty()) return;
    saving = true; controls(); $('.ai-fields').disabled = true;
    try { const latest = await api('/admin/ai-config'); if (panel.isConnected) { saved = latest; fill(); $('#ai-error').textContent = 'Đã tải cấu hình mới nhất.'; } }
    catch (err) { if (panel.isConnected) $('#ai-error').textContent = err.message; }
    finally { saving = false; if (panel.isConnected) { $('.ai-fields').disabled = false; controls(); } }
  };
  form.onsubmit = async event => {
    event.preventDefault(); if (saving || testing || !dirty()) return;
    const body = {...values(),version:saved.version};
    saving = true; controls(); $('.ai-fields').disabled = true; $('#ai-error').textContent = '';
    try {
      const latest = await api('/admin/ai-config','PUT',body);
      if (!panel.isConnected) return;
      saved = latest; fill(); $('.ai-connection-result').textContent = 'Cấu hình đã thay đổi. Bạn có thể kiểm tra lại kết nối.';
      $('#ai-error').textContent = 'Đã lưu thành công.'; notify('Đã lưu cấu hình AI');
    } catch (err) { if (panel.isConnected) $('#ai-error').textContent = err.message + ' Nội dung bạn nhập vẫn được giữ lại.'; }
    finally { saving = false; if (panel.isConnected) { $('.ai-fields').disabled = false; controls(); } }
  };
  $('.ai-test').onclick = async () => {
    if (testing || saving || dirty() || !saved.ready) return;
    testing = true; controls();
    const start = Date.now(), model = saved.model, output = $('.ai-connection-result');
    output.className = 'ai-connection-result pending'; output.textContent = 'Đang kiểm tra ' + model + '…';
    const timer = setInterval(() => { if (panel.isConnected) output.textContent = 'Đang chờ Gemini · ' + Math.floor((Date.now()-start)/1000) + ' giây'; },1000);
    try {
      const response = await api('/admin/ai-config/test','POST');
      if (panel.isConnected) { output.className = 'ai-connection-result success'; output.textContent = response.message + ' (' + ((Date.now()-start)/1000).toFixed(1) + ' giây)'; }
    } catch (err) { if (panel.isConnected) { output.className = 'ai-connection-result error'; output.textContent = err.message; } }
    finally {
      clearInterval(timer); testing = false;
      if (panel.isConnected) {
        controls();
        try { const latest = await api('/admin/ai-config'); if (panel.isConnected) { saved.usage_24h = latest.usage_24h; saved.recent_usage = latest.recent_usage; summary(); } } catch {}
      }
    }
  };
  fill();
}
