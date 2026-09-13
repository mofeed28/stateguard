(() => {
  let run = null;
  let busy = false;
  const $ = (id) => document.getElementById(id);
  const controls = ['startWorkflow', 'tickWorkflow', 'investigateWorkflow', 'approveWorkflow', 'changeProvider'];
  function node(tag, text) { const n = document.createElement(tag); n.textContent = text; return n; }
  function render() {
    $('tickWorkflow').disabled = !run || run.status === 'completed';
    $('investigateWorkflow').disabled = !run;
    $('approveWorkflow').disabled = !run || run.status !== 'needs_approval';
    $('changeProvider').disabled = !run || run.status === 'completed';
    if (!run) return;
    const state = $('workflowState'); state.replaceChildren();
    const metrics = node('div', ''); metrics.className = 'metrics';
    for (const [label, value] of [['Worker believes', run.belief], ['Provider evidence', run.provider], ['Actual deliveries', run.deliveries], ['Workflow', run.status]]) {
      const card = node('article', ''); card.append(node('span', label), node('strong', String(value).replaceAll('_', ' '))); metrics.append(card);
    }
    state.append(metrics);
    const explanation = {
      ready: 'Worker has not attempted its retry yet.',
      waiting: 'Retry held: evidence is uncertain. Change the provider state, then refresh. No human interruption yet.',
      needs_approval: 'Retry blocked. Approving will update the worker to match confirmed delivery, without sending again.',
      completed: `Verified recovery: ${run.deliveries} delivery recorded. Repeated worker calls or approvals cannot send another message.`
    };
    state.append(node('p', explanation[run.status]));
    $('workflowEvents').replaceChildren(...run.events.map(e => {
      const item = node('li', ''); item.append(node('time', e.ts), node('strong', e.event), node('span', e.detail)); return item;
    }));
    const report = $('workflowAnalysis'); report.replaceChildren();
    if (run.analysis) {
      report.append(node('p', run.analysis.summary), node('p', `Live Strands · ${run.analysis.model} · ${run.analysis.duration_ms} ms`));
      if (run.analysis.usage?.totalTokens) report.append(node('p', `Reported model usage: ${run.analysis.usage.totalTokens} tokens`));
      for (const evidence of run.analysis.evidence) report.append(node('p', evidence));
      const details = node('details', ''); details.append(node('summary', 'Actual tool calls and evidence'), node('pre', JSON.stringify(run.analysis.trace, null, 2))); report.append(details);
    } else report.append(node('p', 'No model has run. The deterministic gate works without model access.'));
    sessionStorage.setItem('stateguardWorkflow', run.id);
  }
  async function request(path, body, live = false, method = 'POST') {
    busy = true;
    $('workflowError').textContent = '';
    controls.forEach(id => $(id).disabled = true);
    try {
      const headers = {'Content-Type': 'application/json'};
      if (live) {
        const key = $('workflowAccessKey').value.trim();
        if (!key) throw new Error('Enter the local demo access key above the investigation button.');
        headers['X-StateGuard-Live-Key'] = key;
      }
      const response = await fetch(path, {method, headers, ...(body ? {body: JSON.stringify(body)} : {})});
      const payload = await response.json();
      if (!response.ok) throw new Error(typeof payload.detail === 'string' ? payload.detail : 'Request failed');
      run = payload;
    } catch (err) { $('workflowError').textContent = err.message; }
    finally { busy = false; $('startWorkflow').disabled = false; render(); }
  }
  $('startWorkflow').onclick = () => request('/api/workflows', {scenario: $('workflowScenario').value});
  $('tickWorkflow').onclick = () => request(`/api/workflows/${run.id}/tick`);
  $('approveWorkflow').onclick = () => request(`/api/workflows/${run.id}/approve`, {version: run.version});
  $('changeProvider').onclick = () => request(`/api/workflows/${run.id}/provider`, {state: $('providerState').value});
  $('investigateWorkflow').onclick = () => request(`/api/workflows/${run.id}/investigate`, null, true);
  const saved = sessionStorage.getItem('stateguardWorkflow');
  if (saved) request(`/api/workflows/${encodeURIComponent(saved)}`, null, false, 'GET');
  setInterval(async () => {
    if (!run || busy || document.hidden) return;
    const id = run.id;
    try {
      const response = await fetch(`/api/workflows/${id}`);
      if (!response.ok) return;
      const latest = await response.json();
      if (!busy && run.id === id && (latest.version > run.version || (latest.analysis && !run.analysis))) {
        run = latest; render();
      }
    } catch (_) { /* Manual controls surface connection errors when requested. */ }
  }, 5000);
})();
