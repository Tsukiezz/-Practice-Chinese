/* SharedPreferences-compatible preferences for the standalone learner pages. */
(() => {
  const palettes = {
    dark: ['Tối hiện tại','#101916','#1a2924','#f0fdf4','#b4c8be','#4db697','#244436'],
    purple: ['Tím pastel','#e5d5f4','#f3eafa','#30243c','#62536e','#70489c','#e5d5f6'],
    red: ['Đỏ đậm','#280e17','#3d1824','#fff0f3','#e2bdc7','#ffb1c5','#643042'],
    blue: ['Xanh dương','#d3e4f8','#ebf3fc','#152b47','#4c607a','#175bbb','#d4e4fc'],
    yellow: ['Vàng pastel','#f5e8af','#fbf5db','#352c0d','#6b5d32','#795b00','#eee0a6'],
    orange: ['Cam','#f7dcc5','#fbefe5','#3e2719','#765640','#a6430b','#f7d9c0'],
    pink: ['Hồng cánh bướm','#f3d2e5','#fbeaf3','#402234','#70445f','#9c306b','#e5b8d1'],
    pastelRed: ['Đỏ pastel','#f4d2d1','#fceceb','#452526','#755051','#a13b43','#e8b8b7'],
    light: ['Sáng','#f5f7f4','#ffffff','#24332e','#52665c','#235546','#e4ece7'],
  };
  const read = (key, fallback) => {
    try { const value = localStorage.getItem('flutter.'+key); return value ? JSON.parse(value) : fallback; }
    catch { return fallback; }
  };
  // Never grant a paid palette from editable browser storage.
  let choice = 'dark';
  let entitlement = null;
  const token = sessionStorage.getItem('hanzigo_account_token') || read('auth_token', '');
  const premium = () => entitlement && entitlement.premium_until > Date.now()/1000;
  let enabled = read('app_theme_mode','light') === 'dark';
  function apply() {
    const p=palettes[enabled && location.pathname !== '/recover' ? choice : 'light'];
    const brand={dark:'#235546',red:'#831d38',purple:'#70489c',blue:'#175bbb',yellow:'#795b00',orange:'#a6430b',pink:'#9c306b',pastelRed:'#a13b43',light:'#235546'}[enabled && location.pathname !== '/recover' ? choice : 'light'];
    const vars={'primary':brand,'primary-light':brand,'jade':brand,'bg':p[1],'card-bg':p[2],'text':p[3],'text-muted':p[4],
      'accent':p[5],'border':p[6],'surface-soft':p[6],
      'ink':p[3],'muted':p[4],'paper':p[2]};
    for (const [name,value] of Object.entries(vars)) document.documentElement.style.setProperty('--'+name,value);
    document.documentElement.dataset.learnerTheme = p===palettes.light?'light':choice;
    document.documentElement.style.colorScheme = enabled && ['dark','red'].includes(choice) && location.pathname !== '/recover' ? 'dark':'light';
  }
  apply();
  const target=document.getElementById('interface-preferences');
  if (target) {
    target.innerHTML='<h2>Màu giao diện</h2><label>Màu khi bật Dark mode<select id="palette-choice">'+Object.entries(palettes).filter(([k])=>k!=='light').map(([k,p])=>`<option value="${k}">${p[0]}</option>`).join('')+'</select></label><label class="theme-switch"><input id="palette-enabled" type="checkbox"> Bật Dark mode / màu đã chọn</label><p class="hint">Tắt để trở về màu sáng. Trang đăng nhập luôn dùng màu mặc định.</p>';
    const select=target.querySelector('select'),toggle=target.querySelector('input');
    const status=document.createElement('p');status.id='palette-status';status.setAttribute('role','status');target.appendChild(status);
    select.disabled=true;
    select.value=choice;toggle.checked=enabled;
    async function save() {
      const selected=select.value;
      select.disabled=true;
      try {
        if(selected!=='dark' && !premium()) throw new Error('Màu này dành cho HanziGo Premium.');
        if(token) {
          const response=await fetch('/api/me/benefits/preferences',{
            method:'PUT',headers:{'Authorization':'Bearer '+token,'Content-Type':'application/json'},
            body:JSON.stringify({palette:selected,brush:premium()?entitlement.brush:'default'})
          });
          const data=await response.json();
          if(!response.ok) throw new Error(typeof data.detail==='string'?data.detail:'Không lưu được tùy chọn.');
          entitlement=data;
        }
        choice=selected;enabled=toggle.checked;
        localStorage.setItem('flutter.app_theme_palette',JSON.stringify(choice));
        localStorage.setItem('flutter.app_theme_mode',JSON.stringify(enabled?'dark':'light'));
        status.textContent='Đã lưu màu giao diện.';
        apply();
      } catch(error) {
        select.value=choice;toggle.checked=enabled;status.textContent=error.message;
      } finally {select.disabled=false;}
    }
    select.addEventListener('change',save);toggle.addEventListener('change',save);
  }
  async function loadEntitlement() {
    if(token) {
      try {
        const response=await fetch('/api/me/benefits',{headers:{'Authorization':'Bearer '+token}});
        if(response.ok) entitlement=await response.json();
      } catch (_) { /* Keep default colors when verification is unavailable. */ }
    }
    choice=premium() && palettes[entitlement.palette]?entitlement.palette:'dark';
    apply();
    if(target) {
      const select=target.querySelector('select');select.value=choice;select.disabled=false;
      for(const option of select.options) option.disabled=option.value!=='dark'&&!premium();
      target.querySelector('#palette-status').textContent=premium()?'Premium: toàn bộ màu đã mở khóa.':'Tài khoản thường: giao diện mặc định sáng / tối. Nâng cấp Premium để chọn màu khác.';
    }
  }
  loadEntitlement();
  setInterval(() => {
    if(choice!=='dark' && !premium()) {
      choice='dark';apply();
      if(target) {
        const select=target.querySelector('select');select.value='dark';
        for(const option of select.options) option.disabled=option.value!=='dark';
        target.querySelector('#palette-status').textContent='Premium đã hết hạn. Đã trở về màu mặc định.';
      }
    }
  }, 30000);
})();
