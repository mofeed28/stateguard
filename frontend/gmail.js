(() => {
  const $ = id => document.getElementById(id);
  const names = ['gmailLoad','gmailRefresh','gmailInvestigate','gmailApprove'];
  let state;
  const node = (tag,text) => { const n=document.createElement(tag); n.textContent=text; return n; };
  function render() {
    $('gmailLoad').disabled=false;
    $('gmailRefresh').disabled=!state;
    $('gmailInvestigate').disabled=!state || state.status==='completed';
    $('gmailApprove').disabled=!state || state.status!=='needs_approval';
    if(!state) return;
    const e=state.evidence;
    const cards=node('div',''); cards.className='metrics';
    for(const [label,value] of [['Worker belief',state.belief],['Retry allowed','No'],['Gmail Inbox matches',e.inbox_records ?? 'Not checked'],['Recovery',state.status]]) {
      const c=node('article',''); c.append(node('span',label),node('strong',String(value).replaceAll('_',' '))); cards.append(c);
    }
    $('gmailState').replaceChildren(cards,node('p',state.status==='completed'?'Local state reconciled after a fresh Gmail check. No resend occurred.':'Retry held because a durable send attempt already exists.'));
    if(e.source) $('gmailState').append(node('p',`${e.source} · Sent: ${e.sent_records} · Inbox: ${e.inbox_records} · Matches: ${e.matching_messages}`),node('p',`Checked: ${e.checked_at}`),node('p',`Correlation: ${e.correlation}`));
    $('gmailEvents').replaceChildren(...state.events.map(e=>node('li',`${e.ts} · ${e.event}: ${e.detail}`)));
    const a=state.analysis;
    $('gmailAnalysis').replaceChildren(node('p',a?a.summary:'No model analysis recorded.'));
    if(a) {
      $('gmailAnalysis').append(node('p',`Live Strands · ${a.model} · ${a.duration_ms} ms · ${a.usage.totalTokens} tokens`));
      a.evidence.forEach(t=>$('gmailAnalysis').append(node('p',t)));
      const d=node('details',''); d.append(node('summary','Real tool calls and Gmail evidence'),node('pre',JSON.stringify(a.trace,null,2))); $('gmailAnalysis').append(d);
    }
  }
  async function act(action) {
    names.forEach(n=>$(n).disabled=true); $('gmailError').textContent='';
    try {
      const key=$('gmailAccessKey').value.trim(); if(!key) throw new Error('Enter the local demo access key.');
      const response=await fetch(`/api/gmail-demo/${action}`,{method:'POST',headers:{'Content-Type':'application/json','X-StateGuard-Live-Key':key},body:JSON.stringify({version:state?.version})});
      const body=await response.json(); if(!response.ok) throw new Error(body.detail); state=body;
    } catch(e) { $('gmailError').textContent=e.message; } finally { render(); }
  }
  names.forEach((id,i)=>$(id).onclick=()=>act(['load','refresh','investigate','approve'][i]));
})();
