"""Verify the deployed app without sending any email."""
import hashlib
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import requests

ROOT=Path(__file__).resolve().parents[1]
URL='https://gzmrlkrayb3oz3qe22g2v5tv7e0qoqfa.lambda-url.us-east-1.on.aws'

def main():
    secret=json.loads((ROOT/'.secrets/aws-runtime-secret.json').read_text())
    headers={'X-StateGuard-Live-Key':secret['STATEGUARD_LIVE_DEMO_KEY']}
    def get(path):
        response=requests.get(URL+path,timeout=120); response.raise_for_status(); return response
    def post(path, body=None):
        response=requests.post(URL+path,json=body or {},headers=headers,timeout=120)
        if response.status_code != 200: raise RuntimeError(f'{path}: HTTP {response.status_code}')
        return response.json()
    assert get('/api/health').json()['status']=='ok'
    assert 'gmailAccessKey' in get('/').text
    diagram=get('/architecture').content
    assert diagram == (ROOT/'docs/architecture-diagram.html').read_bytes()
    assert requests.post(URL+'/api/gmail-demo/load',json={},timeout=30).status_code==403
    assert requests.post(URL+'/api/workflows',json={},timeout=30).status_code==403
    healthy=post('/api/workflows',{'scenario':'healthy'})
    with ThreadPoolExecutor(max_workers=4) as executor:
        runs=list(executor.map(lambda _:post(f'/api/workflows/{healthy["id"]}/tick'),range(4)))
    assert all(r['deliveries']==1 and r['status']=='completed' for r in runs)
    assert get(f'/api/workflows/{healthy["id"]}').json()['deliveries']==1
    print('Public pages, exact diagram, access controls and concurrent sandbox gate passed.',flush=True)
    run=post('/api/workflows',{'scenario':'accepted_timeout'})
    run=post(f'/api/workflows/{run["id"]}/tick')
    assert run['status']=='needs_approval' and run['deliveries']==1
    analyzed=post(f'/api/workflows/{run["id"]}/investigate')
    assert analyzed['analysis']['usage']['totalTokens']>0
    tools={t['tool'] for t in analyzed['analysis']['trace']}
    assert tools=={'inspect_worker_history','query_delivery_provider'}
    run=post(f'/api/workflows/{run["id"]}/approve',{'version':analyzed['version']})
    assert run['status']=='completed' and run['deliveries']==1
    print('Live sandbox Strands tool calls and reconciliation passed.',flush=True)
    gmail=post('/api/gmail-demo/refresh')
    assert gmail['evidence']['matching_messages']==gmail['evidence']['sent_records']==gmail['evidence']['inbox_records']==1
    gmail=post('/api/gmail-demo/investigate')
    assert gmail['analysis']['usage']['totalTokens']>0
    gmail_tools={t['tool'] for t in gmail['analysis']['trace']}
    assert gmail_tools=={'inspect_send_attempt','query_gmail_receipt'}
    gmail=post('/api/gmail-demo/approve',{'version':gmail['version']})
    assert gmail['status']=='completed' and gmail['retry_allowed'] is False
    report={'verified_at':datetime.now(timezone.utc).isoformat(),'url':URL,
        'architecture_sha256':hashlib.sha256(diagram).hexdigest(),
        'concurrent_sandbox_deliveries':1,'sandbox_model':analyzed['analysis']['model'],
        'sandbox_usage':analyzed['analysis']['usage'],'sandbox_tools':sorted(tools),
        'gmail_status':gmail['status'],'gmail_retry_allowed':False,'gmail_tools':sorted(gmail_tools),
        'new_email_sent':False}
    (ROOT/'docs/aws-live-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('Real Gmail evidence, live Strands and approved reconciliation passed. No email sent.')

if __name__=='__main__': main()
