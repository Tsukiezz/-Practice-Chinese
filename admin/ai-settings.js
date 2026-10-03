const escape = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const modules = {connection_test:'Kiểm tra kết nối',reading:'Chấm đọc',listening:'Chấm nghe',writing:'Chấm viết',translation:'Dịch & ngữ pháp',capability:'Báo cáo năng lực',exam:'Chấm bài thi',handwriting:'Viết tay',personalized_practice:'Luyện tập cá nhân',support_chat:'Trợ lý học tập'};

const DEFAULT_CHAT_PROMPT = `Bạn là Trợ lý AI HanziGo - AI chuyên biệt do HanziGo phát triển và huấn luyện riêng trong khuôn khổ ứng dụng học tiếng Trung HanziGo.
Bạn trả lời bằng tiếng Việt thân thiện, chuẩn mực sư phạm.

PHẠM VI NHIỆM VỤ CỦA BẠN (CHỈ TRẢ LỜI CÁC CHỦ ĐỀ NÀY):
1. Học tiếng Trung và các kỹ năng ngôn ngữ:
   - Từ vựng, chữ Hán (Hán tự), phiên âm Pinyin, phát âm chuẩn, biến điệu thanh điệu.
   - Ngữ pháp tiếng Trung, trật tự câu, cấu trúc ngữ pháp (câu chữ 把, 被, 是, 有, 在, trợ từ 的/得/地, bổ ngữ...).
   - Luyện các kỹ năng: Nghe, Nói, Đọc, Viết chữ Hán (bút thuận, số nét, bộ thủ).
   - Lộ trình học tiếng Trung từ số 0, ôn luyện thi chứng chỉ HSK 1 đến HSK 6.
   - Dịch thuật và giải thích chi tiết có chữ Hán, Pinyin, nghĩa tiếng Việt, câu ví dụ thực tế và bài tập ứng dụng.
2. Hướng dẫn sử dụng ứng dụng HanziGo:
   - Cách học các bài học, kho từ vựng, flashcards, luyện viết chữ Hán, luyện đọc, luyện nghe.
   - Tính năng tạo đề thi AI (tùy chọn 1 đến 50 câu theo kỹ năng Đọc, Nghe, Viết, Từ vựng, Ngẫu nhiên và theo Chủ đề).
   - Chế độ sáng / tối (Dark mode), quản lý tài khoản, đổi mật khẩu, cơ chế tự động đăng xuất sau 30 phút không hoạt động.
   - Chào hỏi, cảm ơn, tương tác xã giao khởi đầu buổi học.
   => Với các chủ đề trên, hãy giải thích cặn kẽ từng bước, đặt chinese_topic=true, needs_admin=false.

QUY TẮC BẮT BUỘC KHI GẶP CÂU HỎI KHÔNG LIÊN QUAN (OFF-TOPIC):
3. Khi người học hoặc khách hỏi bất kỳ câu hỏi nào KHÔNG LIÊN QUAN đến tiếng Trung hoặc ứng dụng HanziGo:
   - Các chủ đề NGOÀI LỀ bao gồm nhưng không giới hạn:
     + Nghệ sĩ, người nổi tiếng, showbiz, ca sĩ, diễn viên, hoa hậu, ngoại hình người khác (ví dụ: "hiếu thứ hai đẹp không", "ai đẹp hơn"...).
     + Ẩm thực đời sống, hỏi công thức nấu ăn, so sánh món ăn cá nhân (ví dụ: "con cá chiên hay nướng ngon hơn", "hôm nay ăn gì"...).
     + Bóng đá, thể thao, game, cầu thủ (Messi, Ronaldo...).
     + Lập trình, viết code (C, Python, Java...), giải toán, bài tập các môn học khác ngoài tiếng Trung.
     + Thời tiết, tin tức xã hội, chính trị, chứng khoán, tiền ảo, chuyện phiếm đời sống.
   - BẠN TUYỆT ĐỐI KHÔNG ĐƯỢC GIẢI ĐÁP CÂU HỎI ĐÓ.
   - TUYỆT ĐỐI KHÔNG TỰ Ý TÌM HOẶC DỊCH TỪ TIẾNG TRUNG TƯƠNG ỨNG ĐỂ TRẢ LỜI CÂU HỎI NGOÀI LỀ.
   - Hãy từ chối một cách lịch sự theo đúng mẫu: nêu rõ bạn là Trợ lý AI chuyên biệt về học tiếng Trung của HanziGo không có nghĩa vụ giải đáp câu hỏi ngoài phạm vi, và yêu cầu đã được chuyển đến Quản trị viên (Admin) để tiếp nhận hỗ trợ.
   - BẮT BUỘC ĐẶT: chinese_topic=false, needs_admin=true.

4. Nếu người học yêu cầu gặp người thật hoặc liên hệ quản trị viên: đặt needs_admin=true.
5. Không bịa thông tin tài khoản, học phí hay thời gian quản trị viên phản hồi.
6. Trả về định dạng JSON:
   - "answer": chuỗi câu trả lời (string)
   - "chinese_topic": boolean (true nếu là tiếng Trung/HanziGo, false nếu là chủ đề ngoài lề)
   - "needs_admin": boolean (true nếu cần chuyển Quản trị viên tiếp nhận)`;

export function renderAIConfig(content, initial, api, notify) {
  let saved = initial, saving = false, testing = false;
  const panel = document.createElement('section');
  panel.className = 'ai-workspace';
  panel.innerHTML = `<div class="system-summary ai-summary"></div><div class="ai-layout">
    <section class="system-card"><div class="system-card-head"><div><h2>Cấu hình Trợ lý AI</h2><p>Quản lý mô hình, huấn luyện Trợ lý AI học tập HanziGo và cấu hình chấm bài.</p></div><span class="ai-dirty support-badge">Đã đồng bộ</span></div>
    <form id="ai-form"><fieldset class="ai-fields"><legend class="sr-only">Cấu hình Trợ lý AI</legend>
      <label class="ai-switch"><span><b>Cho phép sử dụng AI</b><small>Áp dụng cho các chức năng Trợ lý AI sử dụng cấu hình chung.</small></span><input type="checkbox" name="enabled" role="switch"></label>
      <label>Model chính<input name="model" required maxlength="120" autocomplete="off"><small>Tên model Trợ lý AI đang được cấp quyền trên máy chủ (ví dụ: gemini-3.5-flash).</small></label>
      <div class="grid"><label>Mức sáng tạo · Temperature<input name="temperature" type="number" min="0" max="2" step="0.1" required><small>Thấp: phản hồi nhất quán. Cao: đa dạng cách diễn đạt.</small></label><label>Độ dài tối đa · Token<input name="max_tokens" type="number" min="1" max="16000" required><small>Tăng khi câu trả lời thường bị cắt ngắn.</small></label></div>
      
      <div class="ai-section-divider">
        <div>
          <h3>🤖 Huấn luyện Trợ lý AI học tập (Chatbot HanziGo)</h3>
          <p>Trợ lý AI xuất hiện ở nút "Hỏi HanziGo". Bạn có thể quản lý, chỉnh sửa quy tắc hoặc huấn luyện thêm kiến thức tại đây.</p>
        </div>
        <span class="support-badge ai">Trợ lý học tập</span>
      </div>

      <label class="ai-switch"><span><b>Chế độ lọc nghiêm ngặt (Strict Chinese & App Mode)</b><small>Bật để AI chỉ trả lời kiến thức tiếng Trung và hướng dẫn dùng HanziGo. Câu hỏi ngoài lề (showbiz, ẩm thực, thể thao, code...) sẽ tự động bị từ chối và chuyển tiếp đến Admin.</small></span><input type="checkbox" name="chat_strict_mode" role="switch"></label>

      <div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
          <label style="margin:0;font-weight:600">Lời nhắc huấn luyện Trợ lý AI (Training & System Prompt)</label>
          <button type="button" class="ai-default-prompt-btn">↻ Nạp prompt mẫu chuẩn</button>
        </div>
        <textarea name="chat_prompt" rows="11" maxlength="20000" style="font-family:monospace;font-size:12px;line-height:1.5"></textarea>
        <small style="display:block;margin-top:4px">Chỉnh sửa hoặc bổ sung quy tắc sư phạm, từ vựng trọng tâm hoặc thông tin khóa học/trung tâm để AI hướng dẫn người học.</small>
      </div>

      <label>Thông báo từ chối khi hỏi ngoài lề (Off-Topic Decline Message)<textarea name="chat_decline_message" rows="3" maxlength="2000"></textarea><small>Nội dung Trợ lý AI gửi cho học viên khi nhận câu hỏi không liên quan đến tiếng Trung hay HanziGo.</small></label>

      <div class="ai-section-divider">
        <div>
          <h3>📝 Hướng dẫn chấm bài thi & phúc khảo</h3>
          <p>Prompt áp dụng cho hệ thống tự động chấm điểm bài thi và nhận xét học viên.</p>
        </div>
      </div>

      <label>Hướng dẫn chấm bài<textarea name="system_prompt" rows="6" required maxlength="10000"></textarea><small>Prompt này dùng cho chấm bài thi viết, nghe, đọc và xử lý phúc khảo.</small></label>
    </fieldset><div id="ai-error" role="status" aria-live="polite"></div><div class="ai-savebar"><span class="ai-save-note">Cấu hình đã được lưu.</span><div><button type="button" class="ai-reset">Bỏ thay đổi</button><button type="submit" class="primary ai-save">Lưu cấu hình</button></div></div></form></section>
    <aside class="ai-side"><section class="system-card"><div class="system-card-head"><div><h2>Kết nối Trợ lý AI</h2><p>Kiểm tra phản hồi thật từ cấu hình đã lưu.</p></div></div><div class="ai-connection-info"></div><div class="ai-connection-result" role="status">Chưa kiểm tra kết nối trong phiên này.</div><button type="button" class="ai-test">Kiểm tra kết nối</button><small class="ai-test-note">Lượt kiểm tra có thể được nhà cung cấp tính phí.</small><button type="button" class="ai-reload">↻ Tải lại cấu hình</button></section>
    <section class="system-card"><div class="system-card-head"><div><h2>Hoạt động gần đây</h2><p>8 lượt AI mới nhất đã được ghi nhận.</p></div></div><div class="ai-activity"></div></section></aside></div>`;
  content.append(panel);
  const $ = selector => panel.querySelector(selector), form = $('#ai-form');
  const values = () => ({
    model: form.elements.model.value.trim(),
    system_prompt: form.elements.system_prompt.value,
    temperature: Number(form.elements.temperature.value),
    max_tokens: Number(form.elements.max_tokens.value),
    enabled: form.elements.enabled.checked,
    chat_prompt: form.elements.chat_prompt.value,
    chat_decline_message: form.elements.chat_decline_message.value,
    chat_strict_mode: form.elements.chat_strict_mode.checked,
  });
  const baseline = () => ({
    model: saved.model,
    system_prompt: saved.system_prompt,
    temperature: saved.temperature,
    max_tokens: saved.max_tokens,
    enabled: !!saved.enabled,
    chat_prompt: saved.chat_prompt || '',
    chat_decline_message: saved.chat_decline_message || '',
    chat_strict_mode: saved.chat_strict_mode !== false,
  });
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
    const chatStats = saved.chat_stats || {};
    const chatSummary = chatStats.threads !== undefined ? `${(chatStats.threads || 0).toLocaleString('vi-VN')} hội thoại` : 'Sẵn sàng tiếp nhận';
    const chatDetail = chatStats.messages !== undefined ? `${(chatStats.messages || 0).toLocaleString('vi-VN')} tin nhắn đã trao đổi` : 'Theo tiện ích Hỏi HanziGo';
    $('.ai-summary').innerHTML = `<article><span>Trạng thái AI</span><b>${saved.enabled ? 'Đang bật' : 'Đang tắt'}</b><small>${saved.ready ? 'Cấu hình đủ điều kiện kết nối' : 'Cần kiểm tra cấu hình'}</small></article><article><span>Khóa máy chủ</span><b>${saved.key_configured ? 'Đã cấu hình' : 'Chưa cấu hình'}</b><small>Khóa được giữ riêng trên máy chủ</small></article><article><span>Trợ lý học tập</span><b>${chatSummary}</b><small>${chatDetail}</small></article><article><span>Lượt AI · 24 giờ</span><b>${(success+errors).toLocaleString('vi-VN')}</b><small>${success} thành công · ${errors} lỗi</small></article>`;
    $('.ai-connection-info').innerHTML = `<dl><div><dt>Model chính</dt><dd>${escape(saved.model)}</dd></div><div><dt>Model dự phòng</dt><dd>${escape(saved.fallback_model || 'Chưa cấu hình')}</dd></div><div><dt>Lọc nghiêm ngặt</dt><dd>${saved.chat_strict_mode !== false ? 'Đang kích hoạt' : 'Đã tắt'}</dd></div></dl><p class="muted">Trạng thái cấu hình không đồng nghĩa với kết nối đang hoạt động.</p>`;
    $('.ai-activity').innerHTML = (saved.recent_usage || []).map(row => `<div class="ai-activity-row"><span class="status-dot ${row.status}"></span><div><b>${escape(modules[row.module] || row.module)}</b><small>${escape(row.name)} · ${new Date(row.created_at*1000).toLocaleString('vi-VN')}</small></div><span class="support-badge ${row.status === 'error' ? 'waiting' : 'ai'}">${row.status === 'error' ? 'Lỗi' : 'Thành công'}</span></div>`).join('') || '<p class="muted">Chưa có hoạt động AI được ghi nhận.</p>';
  }
  function fill() {
    for (const key of ['model','system_prompt','temperature','max_tokens','chat_prompt','chat_decline_message']) {
      if (form.elements[key]) form.elements[key].value = saved[key] ?? '';
    }
    form.elements.enabled.checked = !!saved.enabled;
    if (form.elements.chat_strict_mode) form.elements.chat_strict_mode.checked = saved.chat_strict_mode !== false;
    summary(); controls();
  }
  form.oninput = controls;
  const defaultPromptBtn = $('.ai-default-prompt-btn');
  if (defaultPromptBtn) {
    defaultPromptBtn.onclick = () => {
      form.elements.chat_prompt.value = DEFAULT_CHAT_PROMPT;
      controls();
      notify('Đã nạp lời nhắc huấn luyện chuẩn của HanziGo');
    };
  }
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
      $('#ai-error').textContent = 'Đã lưu thành công.'; notify('Đã lưu cấu hình và huấn luyện Trợ lý AI');
    } catch (err) { if (panel.isConnected) $('#ai-error').textContent = err.message + ' Nội dung bạn nhập vẫn được giữ lại.'; }
    finally { saving = false; if (panel.isConnected) { $('.ai-fields').disabled = false; controls(); } }
  };
  $('.ai-test').onclick = async () => {
    if (testing || saving || dirty() || !saved.ready) return;
    testing = true; controls();
    const start = Date.now(), model = saved.model, output = $('.ai-connection-result');
    output.className = 'ai-connection-result pending'; output.textContent = 'Đang kiểm tra ' + model + '…';
    const timer = setInterval(() => { if (panel.isConnected) output.textContent = 'Đang chờ Trợ lý AI · ' + Math.floor((Date.now()-start)/1000) + ' giây'; },1000);
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
