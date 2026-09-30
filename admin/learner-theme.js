/* SharedPreferences-compatible preferences for the standalone learner pages. */
(() => {
  const palettes = {
    dark: ['Tối hiện tại','#101916','#1a2924','#f0fdf4','#b4c8be','#4db697','#244436'],
    purple: ['Tím pastel','#f3eaff','#fffbff','#30243c','#62536e','#70489c','#e5d5f6'],
    red: ['Đỏ đậm','#280e17','#3d1824','#fff0f3','#e2bdc7','#ffb1c5','#643042'],
    blue: ['Xanh dương','#eaf2ff','#fafdff','#152b47','#4c607a','#175bbb','#d4e4fc'],
    yellow: ['Vàng pastel','#fff8d6','#fffdf4','#352c0d','#6b5d32','#795b00','#eee0a6'],
    orange: ['Cam','#fff0e2','#fffbf6','#3e2719','#765640','#a6430b','#f7d9c0'],
    light: ['Sáng','#f5f7f4','#ffffff','#24332e','#52665c','#235546','#e4ece7'],
  };
  const read = (key, fallback) => {
    try { const value = localStorage.getItem('flutter.'+key); return value ? JSON.parse(value) : fallback; }
    catch { return fallback; }
  };
  let choice = read('app_theme_palette','dark');
  if (!palettes[choice]) choice='dark';
  let enabled = read('app_theme_mode','light') === 'dark';
  function apply() {
    const p=palettes[enabled && location.pathname !== '/recover' ? choice : 'light'];
    const vars={'bg':p[1],'card-bg':p[2],'text':p[3],'text-muted':p[4],
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
    select.value=choice;toggle.checked=enabled;
    function save() {
      choice=select.value;enabled=toggle.checked;
      localStorage.setItem('flutter.app_theme_palette',JSON.stringify(choice));
      localStorage.setItem('flutter.app_theme_mode',JSON.stringify(enabled?'dark':'light'));
      apply();
    }
    select.addEventListener('change',save);toggle.addEventListener('change',save);
  }
})();
