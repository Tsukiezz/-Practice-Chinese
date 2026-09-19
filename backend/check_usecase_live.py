import httpx,json
with httpx.Client(timeout=60) as client:
 r=client.post('http://127.0.0.1:8010/api/translation/text',json={'text':'你好，我正在学习中文。','source':'zh','target':'vi'})
 print('translation_status:',r.status_code)
 data=r.json()
 print(json.dumps(data,ensure_ascii=True)[:600])
 print('recovery_configured:',client.get('http://127.0.0.1:8010/api/auth/recovery-status').json()['configured'])
