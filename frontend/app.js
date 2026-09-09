let incidentId = "tradeops-ambiguous-cancel-double-entry";

const timeline = document.querySelector("#timeline");
const agents = document.querySelector("#agents");
const mismatches = document.querySelector("#mismatches");
const replayBtn = document.querySelector("#replayBtn");
const approveBtn = document.querySelector("#approveBtn");
const incidentSelect = document.querySelector("#incidentSelect");
const approvalResult = document.querySelector("#approvalResult");
const decisionTitle = document.querySelector("#decisionTitle");
const decisionText = document.querySelector("#decisionText");
const severity = document.querySelector("#severity");
const mismatchCount = document.querySelector("#mismatchCount");
const adapters = document.querySelector("#adapters");
const incidentStatus = document.querySelector("#incidentStatus");
const handoff = document.querySelector("#handoff");
const tools = document.querySelector("#tools");
const trace = document.querySelector("#trace");
const structuredOutput = document.querySelector("#structuredOutput");
const observability = document.querySelector("#observability");
const beliefStatement = document.querySelector("#beliefStatement");
const realityStatement = document.querySelector("#realityStatement");
const blockedStatement = document.querySelector("#blockedStatement");

const incidentNarrative = {
  "tradeops-ambiguous-cancel-double-entry": {
    belief: "Position was zero; fresh entry was safe",
    reality: "Prior order filled after an ambiguous cancel",
    blocked: "Another autonomous entry before reconciliation",
  },
  "inbox-undelivered-followup": {
    belief: "Client follow-up was sent",
    reality: "Provider rejected the message",
    blocked: "Waiting days on an email nobody received",
  },
};

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

async function loadReplay({ animate = false } = {}) {
  replayBtn.disabled = true;
  timeline.innerHTML = "";
  agents.innerHTML = "";
  mismatches.innerHTML = "";
  trace.innerHTML = "";
  observability.innerHTML = "";
  approvalResult.textContent = "";
  handoff.textContent = "";
  structuredOutput.textContent = "";

  const response = await fetch(`/api/incidents/${incidentId}/replay`);
  const result = await response.json();
  const structuredResponse = await fetch(`/api/incidents/${incidentId}/structured-output`);
  const structuredResult = await structuredResponse.json();

  severity.textContent = result.incident.severity.toUpperCase();
  mismatchCount.textContent = result.mismatches.length;
  incidentStatus.textContent = result.incident.status.replace("_", " ");
  decisionTitle.textContent = result.decision.title;
  decisionText.textContent = result.decision.rationale;
  handoff.textContent = result.sanitized_handoff;
  structuredOutput.textContent = JSON.stringify(structuredResult, null, 2);
  const narrative = incidentNarrative[incidentId] || {
    belief: result.incident.summary,
    reality: result.mismatches[0]?.observed || "External state requires review",
    blocked: result.decision.blocked_actions[0] || result.decision.recommended_action,
  };
  beliefStatement.textContent = narrative.belief;
  realityStatement.textContent = narrative.reality;
  blockedStatement.textContent = narrative.blocked;

  for (const event of result.incident.events) {
    if (animate) await pause(170);
    const item = el("li");
    const time = el("time", "", event.ts);
    const title = el("strong", "", event.source);
    const body = el("span", "", event.summary);
    item.append(time, title, body);
    timeline.append(item);
  }

  for (const step of result.agent_steps) {
    if (animate) await pause(120);
    const card = el("div", "agent");
    card.append(
      el("strong", "", step.agent),
      el("small", "", `${step.role} / ${Math.round(step.confidence * 100)}% confidence`),
      el("p", "", step.finding)
    );
    agents.append(card);
  }

  for (const step of result.execution_trace) {
    if (animate) await pause(90);
    const row = el("div", "trace-step");
    row.append(
      el("span", "trace-index", String(step.sequence).padStart(2, "0")),
      el("strong", "", step.agent),
      el("code", "", step.tool),
      el("p", "", step.output_summary),
      el("small", "", `${step.duration_ms} ms / ${step.input_summary}`)
    );
    trace.append(row);
  }

  for (const mismatch of result.mismatches) {
    const card = el("div", "mismatch");
    card.append(
      el("strong", "", mismatch.title),
      el("p", "", `Expected: ${mismatch.expected}`),
      el("p", "", `Observed: ${mismatch.observed}`)
    );
    mismatches.append(card);
  }

  for (const event of result.observability_events) {
    const row = el("div", `event event-${event.level}`);
    row.append(
      el("span", "event-level", event.level),
      el("strong", "", event.event),
      el("small", "", `${event.source} / ${event.ts}`),
      el("p", "", event.detail)
    );
    observability.append(row);
  }

  replayBtn.disabled = false;
}

async function loadAdapters() {
  const response = await fetch("/api/adapters");
  const examples = await response.json();
  adapters.innerHTML = "";
  for (const example of examples) {
    const card = el("article", "adapter");
    card.append(
      el("h4", "", example.name),
      el("p", "", `Belief: ${example.belief}`),
      el("p", "", `Reality: ${example.reality}`),
      el("p", "", `Escalation: ${example.escalation}`)
    );
    adapters.append(card);
  }
}

async function loadIncidents() {
  const response = await fetch("/api/incidents");
  const incidents = await response.json();
  incidentSelect.innerHTML = "";
  for (const incident of incidents) {
    const option = document.createElement("option");
    option.value = incident.id;
    option.textContent = incident.title;
    incidentSelect.append(option);
  }
  incidentSelect.value = incidentId;
}

async function loadTools() {
  const response = await fetch("/api/strands-tools");
  const items = await response.json();
  tools.innerHTML = "";
  for (const item of items) {
    const card = el("div", "tool");
    const code = document.createElement("code");
    code.textContent = item.name;
    card.append(code, el("span", "", item.description));
    tools.append(card);
  }
}

async function approve() {
  const response = await fetch(`/api/incidents/${incidentId}/approve`, { method: "POST" });
  const result = await response.json();
  approvalResult.textContent = JSON.stringify(result, null, 2);
}

function pause(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

replayBtn.addEventListener("click", () => loadReplay({ animate: true }));
approveBtn.addEventListener("click", approve);
incidentSelect.addEventListener("change", () => {
  incidentId = incidentSelect.value;
  loadReplay();
});

loadIncidents().then(loadReplay);
loadAdapters();
loadTools();
