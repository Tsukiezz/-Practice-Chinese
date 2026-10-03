const escape = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const date = value => value ? new Date(value * 1000).toLocaleString('vi-VN') : '—';
const money = value => Number(value || 0).toLocaleString('vi-VN') + ' đ';

export function renderPremiumManagement(content, initialData, api, notify, dialog) {
  const panel = document.createElement('section');
  panel.className = 'premium-workspace';

  panel.innerHTML = `
    <div class="system-card" style="margin-bottom:20px;background:linear-gradient(135deg,#153e35,#1d574a);color:#fff;border-radius:18px;padding:24px">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px">
        <div>
          <span style="background:rgba(255,215,0,0.2);color:#ffd700;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700;letter-spacing:1px;text-transform:uppercase">👑 Trung tâm Quản trị HanziGo Premium</span>
          <h2 style="margin:8px 0 4px;font-size:24px;color:#fff">Quản lý Hội viên VIP & Giao dịch SePay VietQR</h2>
          <p style="margin:0;opacity:0.85;font-size:14px">Theo dõi danh sách người chuyển khoản và quản lý mã Voucher ưu đãi (Admin & AI).</p>
        </div>
        <button id="prem-refresh-btn" class="primary" style="background:#ffd700;color:#153e35;font-weight:700;border:none">↻ Tải lại dữ liệu</button>
      </div>
    </div>

    <!-- Quick Stats Overview -->
    <div class="stats" id="prem-stats-container" style="margin-bottom:24px">
      <article class="stat" style="border-top:4px solid #ffd700">
        <small>Doanh thu đã nhận</small>
        <b id="stat-revenue" style="color:#d4af37">${money(initialData.total_revenue)}</b>
      </article>
      <article class="stat" style="border-top:4px solid #28a745">
        <small>Hội viên VIP đang hoạt động</small>
        <b id="stat-active" style="color:#28a745">${initialData.active_subscribers}</b>
      </article>
      <article class="stat" style="border-top:4px solid #ff9800">
        <small>Đơn chờ chuyển khoản</small>
        <b id="stat-pending" style="color:#ff9800">${initialData.pending_orders}</b>
      </article>
      <article class="stat" style="border-top:4px solid #17a2b8">
        <small>Mã Voucher (Admin + AI)</small>
        <b id="stat-vouchers">${initialData.total_vouchers} <span style="font-size:12px;font-weight:400;color:var(--muted)">(${initialData.ai_vouchers} do AI tạo)</span></b>
      </article>
    </div>

    <!-- Navigation Tabs -->
    <div class="admin-tabs" style="display:flex;gap:10px;margin-bottom:20px;border-bottom:2px solid #e0e8e4;padding-bottom:12px">
      <button type="button" class="tab-btn active" data-prem-tab="transactions" style="padding:10px 18px;border-radius:10px;border:none;cursor:pointer;font-weight:700">💳 Người chuyển khoản & Giao dịch</button>
      <button type="button" class="tab-btn" data-prem-tab="vouchers" style="padding:10px 18px;border-radius:10px;border:none;cursor:pointer;font-weight:700">🎟️ Quản lý Mã Voucher (Admin & AI)</button>
    </div>

    <!-- Tab 1: Transactions -->
    <div id="tab-transactions" class="tab-pane active">
      <section class="system-card">
        <div class="system-card-head" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
          <div>
            <h3 style="margin:0 0 4px">Lịch sử người chuyển khoản & Đơn mua VIP</h3>
            <p style="margin:0;font-size:13px;color:var(--muted)">Hệ thống tự động kích hoạt VIP khi SePay nhận đúng tiền thật vào tài khoản ngân hàng.</p>
          </div>
          <div style="display:flex;gap:8px">
            <select id="filter-tx-status" style="padding:8px 12px;border-radius:8px;border:1px solid #cbd7ce">
              <option value="">Tất cả trạng thái</option>
              <option value="completed">Đã thanh toán (Thành công)</option>
              <option value="pending">Chờ chuyển khoản</option>
            </select>
          </div>
        </div>
        <div id="tx-table-container">
          <p class="loading">Đang tải danh sách người chuyển khoản…</p>
        </div>
      </section>
    </div>

    <!-- Tab 2: Voucher Management -->
    <div id="tab-vouchers" class="tab-pane" style="display:none">
      <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(360px, 1fr));gap:20px;margin-bottom:20px">
        <!-- Create Voucher Card -->
        <section class="system-card">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
            <span style="font-size:22px">🎁</span>
            <h3 style="margin:0">Tạo mã Voucher HanziGo Premium</h3>
          </div>
          <p style="color:var(--muted);font-size:13px">Tạo mã giảm giá theo phần trăm (%) hoặc mã tặng 1 tháng miễn phí.</p>
          <form id="create-voucher-form">
            <label style="display:block;margin:10px 0 4px;font-weight:600">Mã Voucher (Để trống để tự tạo mã VIP ngẫu nhiên)
              <div style="display:flex;gap:8px;margin-top:4px">
                <input name="code" placeholder="Ví dụ: VIP2026, CHAOHE30..." style="flex:1;padding:10px;border-radius:8px;border:1px solid #cbd7ce;text-transform:uppercase">
                <button type="button" id="btn-gen-rand-code" style="padding:10px 14px;border:1px solid #153e35;background:#fff;border-radius:8px;cursor:pointer">🎲 Tự sinh mã</button>
              </div>
            </label>
            <label style="display:block;margin:12px 0 6px;font-weight:600">Loại ưu đãi
              <select name="voucher_type" id="sel-voucher-type" style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd7ce;margin-top:4px">
                <option value="percent">Giảm giá theo phần trăm (%)</option>
                <option value="free_month">🌟 1 Tháng HanziGo Premium Miễn Phí (Kích hoạt ngay)</option>
              </select>
            </label>
            <div id="voucher-percent-group">
              <label style="display:block;margin:12px 0 6px;font-weight:600">Mức giảm giá (%)
                <div style="display:flex;align-items:center;gap:10px;margin-top:4px">
                  <input type="number" name="discount_percent" min="1" max="100" value="20" style="width:120px;padding:10px;border-radius:8px;border:1px solid #cbd7ce">
                  <span style="font-size:13px;color:var(--muted)">Ví dụ: 10%, 20%, 30%, 50%</span>
                </div>
              </label>
            </div>
            <label style="display:block;margin:12px 0 6px;font-weight:600">Số lượt sử dụng tối đa
              <input type="number" name="max_uses" min="1" max="100000" value="1" style="width:120px;padding:10px;border-radius:8px;border:1px solid #cbd7ce;margin-top:4px">
            </label>
            <label style="display:block;margin:12px 0 6px;font-weight:600">Ghi chú / Mô tả
              <input name="description" placeholder="Ví dụ: Tặng quà sinh nhật học viên, quà mini game..." style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd7ce;margin-top:4px">
            </label>
            <button type="submit" class="primary" style="width:100%;padding:12px;border-radius:10px;font-weight:700;margin-top:14px">✨ Tạo mã Voucher</button>
          </form>
        </section>

        <!-- AI Voucher Explainer Card -->
        <section class="system-card" style="background:#f4f9f6;border:1px solid #b7d8c4">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
            <span style="font-size:22px">🤖</span>
            <h3 style="margin:0">Mã tự động do AI tạo (Thưởng 100 điểm)</h3>
          </div>
          <p style="color:#24332e;font-size:14px;line-height:1.6">
            Mỗi khi <b>bất kỳ học viên nào làm bài kiểm tra và đạt 100 điểm tuyệt đối</b>:
          </p>
          <div style="background:#fff;border-radius:12px;padding:16px;border:1px solid #c2e0cf;margin-bottom:12px">
            <p style="margin:0 0 6px;font-weight:700;color:#153e35">Định dạng mã AI tạo chuẩn:</p>
            <code style="font-size:16px;color:#d9534f;font-weight:700;display:block;margin-bottom:6px">HZG__________ (10 chữ số ngẫu nhiên)</code>
            <small style="color:var(--muted)">Ví dụ: <code>HZG8391029482</code>, <code>HZG1029481729</code></small>
            <ul style="padding-left:18px;margin:10px 0 0;font-size:13px;line-height:1.6">
              <li><b>Mức ưu đãi:</b> Giảm 30% cho gói 1 tháng HanziGo Premium (từ 49.000đ còn 34.300đ).</li>
              <li><b>Nguồn tạo:</b> Tự động bởi Trí tuệ AI hệ thống khi nộp bài đạt 100 điểm.</li>
              <li><b>Tự động ghi nhận:</b> Danh sách mã AI sẽ tự động xuất hiện ở bảng bên dưới kèm nhãn <b>"🤖 AI tạo"</b>.</li>
            </ul>
          </div>
        </section>
      </div>

      <!-- Vouchers List Table -->
      <section class="system-card">
        <div class="system-card-head" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
          <div>
            <h3 style="margin:0 0 4px">Danh sách Mã Voucher hệ thống</h3>
            <p style="margin:0;font-size:13px;color:var(--muted)">Quản lý và tra cứu mã do Quản trị viên cấp hoặc AI tự động tạo.</p>
          </div>
          <select id="filter-voucher-creator" style="padding:8px 12px;border-radius:8px;border:1px solid #cbd7ce">
            <option value="">Tất cả nguồn tạo</option>
            <option value="admin">Chỉ mã do Admin tạo</option>
            <option value="ai">Chỉ mã do AI tạo (100 điểm)</option>
          </select>
        </div>
        <div id="vouchers-table-container">
          <p class="loading">Đang tải danh sách voucher…</p>
        </div>
      </section>
    </div>
  `;

  content.innerHTML = '';
  content.appendChild(panel);

  // Tab switching logic
  const tabButtons = panel.querySelectorAll('[data-prem-tab]');
  const tabPanes = {
    'transactions': panel.querySelector('#tab-transactions'),
    'vouchers': panel.querySelector('#tab-vouchers')
  };

  tabButtons.forEach(btn => {
    btn.onclick = () => {
      tabButtons.forEach(b => {
        b.classList.remove('active');
        b.style.background = 'transparent';
        b.style.color = 'inherit';
      });
      btn.classList.add('active');
      btn.style.background = '#153e35';
      btn.style.color = '#fff';

      const target = btn.dataset.premTab;
      Object.entries(tabPanes).forEach(([k, pane]) => {
        if (pane) pane.style.display = (k === target) ? 'block' : 'none';
      });
      if (target === 'transactions') loadTransactions();
      else if (target === 'vouchers') loadVouchers();
    };
  });

  // Activate first tab style
  const activeBtn = panel.querySelector('[data-prem-tab="transactions"]');
  if (activeBtn) {
    activeBtn.style.background = '#153e35';
    activeBtn.style.color = '#fff';
  }

  // Generate random voucher code
  panel.querySelector('#btn-gen-rand-code').onclick = () => {
    const rand = 'VIP' + Math.floor(10000 + Math.random() * 90000);
    panel.querySelector('[name="code"]').value = rand;
  };

  // Voucher type change handler
  panel.querySelector('#sel-voucher-type').onchange = (e) => {
    const isFree = e.target.value === 'free_month';
    panel.querySelector('#voucher-percent-group').style.display = isFree ? 'none' : 'block';
  };

  // Load transactions (Strictly read-only for Admin, real money verified by SePay)
  async function loadTransactions() {
    const container = panel.querySelector('#tx-table-container');
    container.innerHTML = '<p class="loading">Đang tải danh sách người chuyển khoản…</p>';
    const statusFilter = panel.querySelector('#filter-tx-status').value;
    const url = `/admin/premium/transactions?limit=100` + (statusFilter ? `&status=${statusFilter}` : '');
    try {
      const res = await api(url);
      if (!res.items || res.items.length === 0) {
        container.innerHTML = '<div class="empty"><h3>Chưa có giao dịch chuyển khoản nào</h3><p>Khi học viên chuyển tiền qua SePay, đơn hàng sẽ hiển thị tại đây.</p></div>';
        return;
      }
      container.innerHTML = `
        <div class="table-wrap">
          <table class="responsive-table">
            <thead>
              <tr>
                <th>Mã đơn hàng</th>
                <th>Người chuyển</th>
                <th>Gói đăng ký</th>
                <th>Số tiền</th>
                <th>Voucher</th>
                <th>Trạng thái</th>
                <th>Mã GD SePay</th>
                <th>Thời gian</th>
                <th>Xác nhận SePay</th>
              </tr>
            </thead>
            <tbody>
              ${res.items.map(order => {
                const isPaid = order.status === 'completed';
                const statusBadge = isPaid
                  ? '<span class="support-badge resolved" style="background:#e6f4ea;color:#137333;font-weight:700">✓ Đã thanh toán</span>'
                  : '<span class="support-badge waiting" style="background:#fef7e0;color:#b06000;font-weight:700">⏳ Chờ chuyển tiền</span>';
                const planLabel = order.plan_type === '1_year' ? 'Gói 1 Năm (490k)' : 'Gói 1 Tháng (49k)';
                return `
                  <tr>
                    <td data-label="Mã đơn"><b>${escape(order.order_code)}</b></td>
                    <td data-label="Người chuyển">
                      <b>${escape(order.user_name || 'Học viên #' + order.user_id)}</b>
                      <small style="color:var(--muted)">${escape(order.user_email || '')}</small>
                    </td>
                    <td data-label="Gói">${planLabel}</td>
                    <td data-label="Số tiền"><b style="color:#153e35">${money(order.amount)}</b></td>
                    <td data-label="Voucher">${order.voucher_code ? `<span class="support-badge ai">${escape(order.voucher_code)} (-${order.discount_percent}%)</span>` : '—'}</td>
                    <td data-label="Trạng thái">${statusBadge}</td>
                    <td data-label="Mã GD">${escape(order.sepay_reference_code || order.sepay_transaction_id || '—')}</td>
                    <td data-label="Thời gian">
                      <small>${date(order.created_at)}</small>
                      ${order.completed_at ? `<small style="color:#137333;display:block">Hoàn thành: ${date(order.completed_at)}</small>` : ''}
                    </td>
                    <td data-label="Xác nhận SePay">
                      ${isPaid
                        ? '<span style="color:#137333;font-weight:700;display:inline-flex;align-items:center;gap:4px">✓ Đã nhận tiền THẬT</span>'
                        : '<span style="color:#b06000;font-size:12px;font-style:italic">⏳ Đang chờ SePay nhận tiền thật…</span>'}
                    </td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="error">${escape(err.message)}</div>`;
    }
  }

  panel.querySelector('#filter-tx-status').onchange = loadTransactions;

  // Load Vouchers
  async function loadVouchers() {
    const container = panel.querySelector('#vouchers-table-container');
    container.innerHTML = '<p class="loading">Đang tải danh sách voucher…</p>';
    const creatorFilter = panel.querySelector('#filter-voucher-creator').value;
    const url = `/admin/premium/vouchers?limit=150` + (creatorFilter ? `&created_by=${creatorFilter}` : '');
    try {
      const res = await api(url);
      if (!res.items || res.items.length === 0) {
        container.innerHTML = '<div class="empty"><h3>Chưa có mã voucher nào</h3><p>Hãy tạo mã giảm giá mới ở biểu mẫu phía trên.</p></div>';
        return;
      }
      container.innerHTML = `
        <div class="table-wrap">
          <table class="responsive-table">
            <thead>
              <tr>
                <th>Mã Voucher</th>
                <th>Nguồn tạo</th>
                <th>Ưu đãi</th>
                <th>Lượt sử dụng</th>
                <th>Mô tả / Ghi chú</th>
                <th>Thời gian tạo</th>
                <th>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              ${res.items.map(v => {
                const isAi = v.created_by === 'ai';
                const creatorBadge = isAi
                  ? '<span class="support-badge ai" style="background:#e8f0fe;color:#1967d2;font-weight:700">🤖 AI tạo (100 điểm)</span>'
                  : '<span class="support-badge staff" style="background:#fef7e0;color:#b06000;font-weight:700">👑 Admin tạo</span>';
                const benefitLabel = v.is_free_month
                  ? '<b style="color:#d4af37">🌟 1 Tháng VIP Miễn Phí</b>'
                  : `<b style="color:#137333">Giảm ${v.discount_percent}%</b>`;
                const isExhausted = v.used_count >= v.max_uses;
                const usageBadge = isExhausted
                  ? `<span style="color:#c5221f;font-weight:700">${v.used_count}/${v.max_uses} (Đã dùng hết)</span>`
                  : `<span style="color:#137333;font-weight:700">${v.used_count}/${v.max_uses} (Còn hiệu lực)</span>`;

                return `
                  <tr>
                    <td data-label="Mã">
                      <code style="font-size:15px;font-weight:700;color:#153e35;background:#f0f4f1;padding:4px 8px;border-radius:6px">${escape(v.code)}</code>
                    </td>
                    <td data-label="Nguồn tạo">${creatorBadge}</td>
                    <td data-label="Ưu đãi">${benefitLabel}</td>
                    <td data-label="Lượt dùng">${usageBadge}</td>
                    <td data-label="Mô tả"><small>${escape(v.description || '—')}</small></td>
                    <td data-label="Thời gian"><small>${date(v.created_at)}</small></td>
                    <td data-label="Thao tác">
                      <button class="danger" style="padding:6px 10px;font-size:12px;border-radius:6px" data-del-voucher="${v.id}">Xóa mã</button>
                    </td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      `;

      container.querySelectorAll('[data-del-voucher]').forEach(btn => {
        btn.onclick = async () => {
          if (!confirm('Bạn có chắc muốn xóa mã voucher này?')) return;
          try {
            await api(`/admin/premium/vouchers/${btn.dataset.delVoucher}`, 'DELETE');
            notify('Đã xóa mã voucher thành công!');
            loadVouchers();
            refreshDashboardStats();
          } catch (e) {
            notify(e.message);
          }
        };
      });
    } catch (err) {
      container.innerHTML = `<div class="error">${escape(err.message)}</div>`;
    }
  }

  panel.querySelector('#filter-voucher-creator').onchange = loadVouchers;

  // Submit Create Voucher Form
  panel.querySelector('#create-voucher-form').onsubmit = async (e) => {
    e.preventDefault();
    const form = e.target;
    const isFreeMonth = form.elements.voucher_type.value === 'free_month';
    const body = {
      code: form.elements.code.value.trim().toUpperCase() || null,
      discount_percent: isFreeMonth ? 100 : Number(form.elements.discount_percent.value || 0),
      is_free_month: isFreeMonth,
      max_uses: Number(form.elements.max_uses.value || 1),
      description: form.elements.description.value.trim()
    };
    try {
      const created = await api('/admin/premium/vouchers', 'POST', body);
      notify(`Đã tạo thành công voucher: ${created.code}!`);
      form.reset();
      panel.querySelector('#sel-voucher-type').value = 'percent';
      panel.querySelector('#voucher-percent-group').style.display = 'block';
      loadVouchers();
      refreshDashboardStats();
    } catch (err) {
      notify(err.message);
    }
  };

  // Refresh overall dashboard stats
  async function refreshDashboardStats() {
    try {
      const data = await api('/admin/premium/dashboard');
      panel.querySelector('#stat-revenue').textContent = money(data.total_revenue);
      panel.querySelector('#stat-active').textContent = data.active_subscribers;
      panel.querySelector('#stat-pending').textContent = data.pending_orders;
      panel.querySelector('#stat-vouchers').innerHTML = `${data.total_vouchers} <span style="font-size:12px;font-weight:400;color:var(--muted)">(${data.ai_vouchers} do AI tạo)</span>`;
    } catch (_) {}
  }

  panel.querySelector('#prem-refresh-btn').onclick = () => {
    refreshDashboardStats();
    loadTransactions();
  };

  // Initial load
  loadTransactions();
}
