const host=document.querySelector('#learner');
const message=document.querySelector('#message');
let learnerToken=sessionStorage.getItem('hanzigo_learner_token')||'';
const safe=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
async function request(path,method='GET',body){
  const response=await fetch('/api'+path,{method,headers:{'Content-Type':'application/json',Authorization:'Bearer '+learnerToken},...(body?{body:JSON.stringify(body)}:{})});
  if(response.status===204)return;
  const data=await response.json();
  if(!response.ok){
    if(response.status===401){learnerToken='';sessionStorage.removeItem('hanzigo_learner_token');login();}
    throw Error(typeof data.detail==='string'?data.detail:'Dữ liệu chưa hợp lệ. Vui lòng kiểm tra lại.');
  }
  return data;
}
function login(){
  host.innerHTML='<form id="signin" class="panel review-card"><label>Email<input name="email" type="email" autocomplete="username" required></label><label>Mật khẩu<input name="password" type="password" autocomplete="current-password" required></label><button class="primary">Đăng nhập</button></form>';
  host.querySelector('form').onsubmit=async event=>{
    event.preventDefault();const button=event.currentTarget.querySelector('button');button.disabled=true;
    try{const data=await request('/auth/login','POST',Object.fromEntries(new FormData(event.currentTarget)));learnerToken=data.token;sessionStorage.setItem('hanzigo_learner_token',learnerToken);await results();}
    catch(err){message.textContent=err.message;}finally{button.disabled=false;}
  };
}
async function results(){
  message.textContent='Đang tải…';
  try{
    const [rows,appeals]=await Promise.all([request('/me/results'),request('/me/appeals')]);
    message.textContent='';
    host.innerHTML='<div class="toolbar"><button id="refresh">Tải lại</button><button id="signout">Đăng xuất</button></div>'+(rows.length?rows.map(row=>{
      const history=appeals.filter(a=>a.result_id===row.id);
      return `<article class="panel review-card"><h2>Bài #${row.id} · ${row.score} điểm</h2><p>Điểm gốc: ${row.original_score}</p><details><summary>Bài làm và nhận xét</summary><pre>${safe(row.content)}</pre><p>${safe(row.feedback)}</p></details>${history.map(a=>`<p><b>${a.status==='pending'?'Đang chờ xử lý':'Đã xử lý'}</b>: ${safe(a.reason)}${a.response?`<br>Phản hồi: ${safe(a.response)}`:''}</p>`).join('')}${history.some(a=>a.status==='pending')?'':`<form data-result="${row.id}"><label>Lý do phúc khảo<textarea name="reason" required minlength="5" maxlength="2000"></textarea></label><button>Gửi yêu cầu</button></form>`}</article>`;
    }).join(''):'<p>Chưa có kết quả. Các bài đã chấm sẽ xuất hiện ở đây.</p>');
    document.querySelector('#refresh').onclick=results;
    document.querySelector('#signout').onclick=async()=>{try{await request('/auth/logout','POST');learnerToken='';sessionStorage.removeItem('hanzigo_learner_token');login();}catch(err){message.textContent=err.message;}};
    host.querySelectorAll('[data-result]').forEach(form=>form.onsubmit=async event=>{
      event.preventDefault();const button=form.querySelector('button');button.disabled=true;
      try{await request(`/me/results/${form.dataset.result}/appeals`,'POST',{reason:form.elements.reason.value});await results();message.textContent='Đã gửi yêu cầu phúc khảo.';}
      catch(err){message.textContent=err.message;}finally{button.disabled=false;}
    });
  }catch(err){message.textContent=err.message;if(learnerToken){host.innerHTML='<button id="retry">Thử lại</button>';host.querySelector('button').onclick=results;}}
}
if(learnerToken)results();else login();
