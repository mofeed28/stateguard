"""Gmail-backed recovery for one existing self-email. No send capability."""
import os
import time
from datetime import datetime, timezone
from .workflow import Analysis
from . import storage
from .runtime_config import gmail_document
from .gmail_evidence import check_evidence

def attempt():
    value = gmail_document('gmail-demo-attempt.json')
    if value.get('send_claimed') is not True:
        raise RuntimeError('A durable authorized send claim is required.')
    return value


def fresh_evidence():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    claim = attempt()
    credentials = Credentials.from_authorized_user_info(gmail_document('gmail-token.json'))
    service = build('gmail', 'v1', credentials=credentials, cache_discovery=False)
    account = service.users().getProfile(userId='me').execute(num_retries=0)['emailAddress']
    if account != claim['account']:
        raise RuntimeError('Mailbox does not match the existing send claim.')
    data = check_evidence(service, claim)
    # Do not expose mailbox address, provider IDs, headers or message bodies.
    data.pop('records', None)
    data['checked_at'] = datetime.now(timezone.utc).isoformat()
    data['source'] = 'Gmail API: existing self-email'
    return data


def verified(e):
    return e.get('matching_messages') == e.get('sent_records') == e.get('inbox_records') == 1


def fingerprint(e):
    return {k: v for k, v in e.items() if k != 'checked_at'}


def event(s, name, detail):
    s['events'].append({'ts': datetime.now(timezone.utc).isoformat(), 'event': name, 'detail': detail})


def mutate(action):
    claim = attempt()
    def initial():
        state = {'version': 0, 'belief': 'unknown', 'status': 'ready',
            'retry_allowed': False, 'analysis': None, 'evidence': {}, 'events': [],
            'scope': 'Existing real self-email; acknowledgment loss was deliberately injected. No new mail is sent.'}
        event(state, 'send.claim.loaded', 'Persisted send attempt found. Worker acknowledgment is unknown; retries are held.')
        return state
    return storage.mutate('gmail_recovery', claim['message_id'], action, initial=initial)


def read():
    return mutate(lambda s: None)


def refresh():
    evidence = fresh_evidence()
    def update(s):
        if fingerprint(evidence) != fingerprint(s['evidence']):
            s['version'] += 1
            s['analysis'] = None
        s['evidence'] = evidence
        if not verified(evidence):
            s['status'] = 'waiting'
        elif s['belief'] == 'delivered':
            s['status'] = 'completed'
        else:
            s['status'] = 'needs_approval'
        event(s, 'gmail.evidence.checked', 'Fresh Gmail metadata checked. Retry remains disabled.')
    return mutate(update)


def investigate():
    if os.getenv('STATEGUARD_USE_STRANDS_LLM') != '1':
        raise RuntimeError('Live Strands is disabled.')
    from strands import Agent, tool
    from .model import create_model
    before = read()
    trace = []
    def record(name, callback):
        start = time.perf_counter()
        value = callback()
        trace.append({'tool': name, 'duration_ms': round((time.perf_counter()-start)*1000), 'output': value})
        return value
    @tool
    def inspect_send_attempt() -> dict:
        """Inspect the existing durable send claim and injected acknowledgment loss."""
        def evidence():
            claim = attempt()
            return {'send_claimed': True, 'worker_belief': before['belief'],
                'created_at': claim['created_at'], 'fault': claim['fault'], 'retry_allowed': False}
        return record('inspect_send_attempt', evidence)
    @tool
    def query_gmail_receipt() -> dict:
        """Query fresh Sent and Inbox evidence for only the approved self-test email."""
        return record('query_gmail_receipt', fresh_evidence)
    model, model_id, provider = create_model()
    agent = Agent(model=model, tools=[inspect_send_attempt, query_gmail_receipt], callback_handler=None,
        retry_strategy=None, system_prompt='Investigate the existing real Gmail self-email. Call BOTH tools. '
        'The acknowledgment loss was deliberately injected, not a real Gmail outage. '
        'One matching message in SENT and INBOX proves receipt for this self-email only. '
        'If verified and worker belief is unknown, recommend reconcile; otherwise wait. '
        'A subject/account/time fallback is weaker correlation because Gmail rewrites Message-ID. '
        'Explain only observed evidence, never invent events. Never recommend resending. '
        'You cannot send or approve. Human approval updates local state only.')
    started = time.perf_counter()
    result = agent('Investigate and explain whether the existing self-email can be reconciled.',
        structured_output_model=Analysis, limits={'turns': 6, 'output_tokens': 4000})
    if {t['tool'] for t in trace} != {'inspect_send_attempt', 'query_gmail_receipt'}:
        raise RuntimeError('Both evidence tools are required.')
    last = [t['output'] for t in trace if t['tool']=='query_gmail_receipt'][-1]
    report = {'model': model_id, 'provider': provider, 'trace': trace,
        'duration_ms': round((time.perf_counter()-started)*1000),
        'usage': dict(result.metrics.accumulated_usage), **Analysis.model_validate(result.structured_output).model_dump()}
    def save(s):
        if s['version'] != before['version']:
            raise ValueError('State changed during investigation. Refresh and investigate again.')
        if fingerprint(last) != fingerprint(s['evidence']):
            s['version'] += 1
        s['evidence'] = last
        s['status'] = 'needs_approval' if verified(last) and s['belief'] != 'delivered' else ('completed' if verified(last) else 'waiting')
        s['analysis'] = report
        event(s, 'strands.investigation.completed', 'Both tools executed; fresh Gmail evidence recorded. Agent has no send or approval tool.')
    return mutate(save)


def approve(version):
    evidence = fresh_evidence()  # Revalidate externally before the local transaction.
    def accept(s):
        if s['version'] != version or not verified(evidence) or fingerprint(evidence) != fingerprint(s['evidence']):
            raise ValueError('Evidence or decision version changed. Refresh before approving.')
        if s['status'] == 'completed':
            return
        if s['status'] != 'needs_approval':
            raise ValueError('No verified receipt is awaiting approval.')
        s['belief'] = 'delivered'
        s['status'] = 'completed'
        s['version'] += 1
        s['evidence'] = evidence
        event(s, 'approval.reconciled', 'Operator reconciled local belief after fresh Gmail verification. No resend occurred.')
    return mutate(accept)
