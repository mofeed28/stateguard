import pytest
from fastapi.testclient import TestClient
from stateguard.app import app
from stateguard import gmail_recovery as g

@pytest.fixture
def recovery(tmp_path,monkeypatch):
    monkeypatch.setenv('STATEGUARD_DB_PATH',str(tmp_path/'gmail.sqlite3'))
    monkeypatch.setattr(g,'attempt',lambda: {'message_id':'fake','created_at':'2026-09-13T00:00:00+00:00','fault':'injected','send_claimed':True})
    evidence={'matching_messages':1,'sent_records':1,'inbox_records':1,'correlation':'test','source':'test','checked_at':'now'}
    monkeypatch.setattr(g,'fresh_evidence',lambda: dict(evidence))
    return evidence

def test_gmail_reconciles_without_send(recovery):
    assert g.read()['belief']=='unknown'
    s=g.refresh(); assert s['status']=='needs_approval'
    s=g.approve(s['version']); assert s['belief']=='delivered'
    assert not s['retry_allowed']
    assert g.approve(s['version'])['version']==s['version']

def test_gmail_stale_approval_rejected(recovery):
    s=g.refresh()
    with pytest.raises(ValueError): g.approve(s['version']-1)
    assert g.read()['belief']=='unknown'

def test_gmail_missing_inbox_cannot_be_approved(recovery):
    s=g.refresh(); recovery['inbox_records']=0
    with pytest.raises(ValueError): g.approve(s['version'])
    assert g.refresh()['status']=='waiting'
    assert g.read()['belief']=='unknown'

def test_ambiguous_gmail_matches_are_held(recovery):
    recovery['matching_messages']=2
    assert g.refresh()['status']=='waiting'

def test_gmail_requires_key_even_when_llm_disabled(monkeypatch):
    monkeypatch.delenv('STATEGUARD_USE_STRANDS_LLM',raising=False)
    assert TestClient(app).post('/api/gmail-demo/load',json={}).status_code==403
