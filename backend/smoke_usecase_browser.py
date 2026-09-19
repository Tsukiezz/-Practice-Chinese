"""Browser verification with a disposable database inside project test-results."""
import os,socket,subprocess,sys,tempfile,time,io
from pathlib import Path
import httpx
from PIL import Image
from playwright.sync_api import sync_playwright,expect

def run():
 artifacts=Path(__file__).resolve().parent.parent/'test-results'
 artifacts.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory(dir=artifacts) as temp:
  with socket.socket() as sock:
   sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  env={**os.environ,'DATABASE_PATH':str(Path(temp)/'browser.db'),'SMTP_HOST':'','SMTP_FROM':''}
  server=subprocess.Popen([sys.executable,'-m','uvicorn','main:app','--host','127.0.0.1','--port',str(port)],
    cwd=Path(__file__).parent,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
    creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
  base=f'http://127.0.0.1:{port}'
  try:
   for _ in range(100):
    try:
     if httpx.get(base+'/api/health',timeout=1).status_code==200:break
    except httpx.HTTPError:pass
    time.sleep(.1)
   else:raise RuntimeError('Server unavailable')
   response=httpx.post(base+'/api/auth/register',json={'name':'Browser Student','email':'browser@example.test','password':'Browser-password-123'})
   response.raise_for_status();token=response.json()['token']
   with sync_playwright() as p:
    browser=p.chromium.launch(channel=os.getenv('PLAYWRIGHT_CHANNEL','msedge'),headless=True)
    page=browser.new_page(viewport={'width':390,'height':844})
    page.goto(base+'/api/health')
    page.evaluate("(token)=>sessionStorage.setItem('hanzigo_account_token',token)",token)
    page.goto(base+'/account')
    expect(page.locator('input[name=name]')).to_have_value('Browser Student')
    page.locator('input[name=name]').fill('Tên học viên mới')
    page.locator('input[name=phone]').fill('+84 901234567')
    page.locator('input[name=birth_date]').fill('2001-02-03')
    page.locator('input[name=daily_goal]').fill('3')
    data=io.BytesIO();Image.new('RGB',(32,32),'green').save(data,format='PNG')
    page.locator('#avatar').set_input_files({'name':'avatar.png','mimeType':'image/png','buffer':data.getvalue()})
    expect(page.locator('#preview')).to_be_visible()
    page.get_by_role('button',name='Lưu thay đổi',exact=True).click()
    expect(page.locator('#message')).to_contain_text('Đã lưu thông tin')
    details=httpx.get(base+'/api/account',headers={'Authorization':'Bearer '+token}).json()
    assert details['name']=='Tên học viên mới' and details['daily_goal']==3 and details['avatar'].startswith('data:image/png')
    page.screenshot(path=str(artifacts/'account-mobile.png'),full_page=True)
    page.locator('input[name=old_password]').fill('Browser-password-123')
    page.locator('input[name=new_password]').fill('Changed-password-123')
    page.locator('input[name=confirm]').fill('Changed-password-123')
    page.get_by_role('button',name='Đổi mật khẩu',exact=True).click()
    expect(page.locator('#message')).to_contain_text('Đã đổi mật khẩu')
    assert httpx.get(base+'/api/me',headers={'Authorization':'Bearer '+token}).status_code==401
    page.goto(base+'/recover')
    expect(page.locator('#message')).to_contain_text('chưa được cấu hình')
    expect(page.get_by_role('button',name='Gửi mã xác nhận')).to_be_disabled()
    page.screenshot(path=str(artifacts/'recovery-unconfigured.png'))
    browser.close()
   print('PASS: mobile profile, avatar, goals, password revocation, recovery configuration')
  finally:
   server.terminate()
   try:server.wait(timeout=10)
   except subprocess.TimeoutExpired:server.kill();server.wait()
if __name__=='__main__':run()
