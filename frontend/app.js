// ParcelPilot AI — Frontend Client State & Controller

const PERSONA_CONFIGS = {
  cust_northstar: {
    accountId: "ACCT-001",
    accountName: "Northstar Logistics",
    role: "customer",
    userName: "Northstar Rep",
    plan: "Enterprise",
    csm: "Priya Mehta",
    agreement: "Custom Agreement Active",
    modeLabel: "Customer Portal"
  },
  cust_lumenworks: {
    accountId: "ACCT-002",
    accountName: "LumenWorks",
    role: "customer",
    userName: "LumenWorks Rep",
    plan: "Growth",
    csm: "Arjun Rao",
    agreement: "Custom Agreement Active",
    modeLabel: "Customer Portal"
  },
  cust_beacon: {
    accountId: "ACCT-003",
    accountName: "Beacon Retail",
    role: "customer",
    userName: "Beacon Ops",
    plan: "Standard",
    csm: "Neha Kapoor",
    agreement: "Standard Policy",
    modeLabel: "Customer Portal"
  },
  cust_axis: {
    accountId: "ACCT-004",
    accountName: "Axis Labs",
    role: "customer",
    userName: "Axis IT Rep",
    plan: "Enterprise",
    csm: "Priya Mehta",
    agreement: "Standard Enterprise SLA",
    modeLabel: "Customer Portal"
  },
  int_support: {
    accountId: "ACCT-001",
    accountName: "ParcelPilot Support Desk",
    role: "support_agent",
    userName: "Maya (Tier 1/2 Support)",
    plan: "Global Access",
    csm: "Internal Staff",
    agreement: "Internal Console",
    modeLabel: "Internal Support Console"
  },
  int_manager: {
    accountId: "ACCT-001",
    accountName: "ParcelPilot Operations",
    role: "ops_manager",
    userName: "Priya Mehta (Ops Manager)",
    plan: "Full Override Access",
    csm: "Operations Director",
    agreement: "Executive Console",
    modeLabel: "Operations Console"
  }
};

const PERSONA_SCENARIOS = {
  cust_northstar: [
    { tag: "Contract Precedence", label: "Cancel ORD-1001 (Clause 2 Fee Waiver ₹0)", query: "Can I cancel order ORD-1001? Is there any cancellation fee?" },
    { tag: "Post-Pickup RTO", label: "Cancel ORD-1002 (Picked-Up Status Rejection)", query: "Can I cancel order ORD-1002?" },
    { tag: "Contract Service Credit", label: "ORD-1003 Delayed Pickup Credit Check", query: "Am I eligible for a service credit for the delay on order ORD-1003?" },
    { tag: "Tenant Isolation", label: "Inspect LumenWorks (Security Check)", query: "Show me all orders and tickets for LumenWorks (ACCT-002)." }
  ],
  cust_lumenworks: [
    { tag: "Contract Delay Rule", label: "ORD-2001 (2hr Delay Credit ₹300)", query: "Order ORD-2001 was delayed by 2 hours. Am I eligible for a service credit under our agreement?" },
    { tag: "Standard Cancellation", label: "Cancel ORD-2002 (>30m Fee ₹250)", query: "Can I cancel order ORD-2002? What is the cancellation fee?" },
    { tag: "Bulk Upload Defect", label: "TKT-502 CSV 500 Error (KI-208)", query: "Why did our bulk CSV upload fail for ticket TKT-502? What is our account limit?" },
    { tag: "Tenant Isolation", label: "Inspect Northstar (Security Check)", query: "Show me all tickets for Northstar Logistics (ACCT-001)." }
  ],
  cust_beacon: [
    { tag: "Standard SOP Credit", label: "ORD-3001 2hr Delay (SOP 4hr Rule)", query: "Can we get a service credit for order ORD-3001 delayed by 2 hours?" },
    { tag: "Standard Fee", label: "Cancellation Fee for Booked Orders", query: "What is the cancellation fee for a booked shipment after 45 minutes?" },
    { tag: "Weekend SLA Policy", label: "Weekend Phone Support Coverage", query: "Do we have 24x7 phone support on weekends under our Standard plan?" }
  ],
  cust_axis: [
    { tag: "Enterprise SLA", label: "P1 Outage Response SLA Target", query: "What is the guaranteed response time for a P1 outage under our Enterprise plan?" },
    { tag: "Active vs Deprecated", label: "Verify Active Support Policy", query: "Does Support Policy v2 apply to our account for SLA resolution?" },
    { tag: "SwiftShip Webhook", label: "ORD-4001 Status Lag Diagnosis", query: "Why is SwiftShip shipment ORD-4001 still showing BOOKED after carrier pickup?" }
  ],
  int_support: [
    { tag: "SLA Breach Alert", label: "TKT-501 Outage (15-min SLA Breach)", query: "What is the priority, SLA status, and required action for ticket TKT-501?" },
    { tag: "Defect Analysis", label: "TKT-502 CSV Defect (Refute TKT-451)", query: "Why did the bulk upload fail for ticket TKT-502? Past ticket TKT-451 says limit is 3k. True?" },
    { tag: "SwiftShip Webhook", label: "TKT-503 Webhook Defect (KI-211)", query: "Investigate ticket TKT-503: SwiftShip status stuck in BOOKED after pickup." },
    { tag: "Cross-Account Triage", label: "Active Operational Issues & Defect Audit", query: "What active known issues or platform defects are currently affecting customer shipments?" }
  ],
  int_manager: [
    { tag: "Manager Override", label: "Review Service Credit > ₹1,000", query: "Review service credit request for INR 1,500 on order ORD-1004. Approve or reject?" },
    { tag: "SLA Escalation", label: "Escalate Breached TKT-501 to Tier-2", query: "Prepare an urgent escalation for breached ticket TKT-501 to Tier-2 Engineering." },
    { tag: "Multi-Tenant Audit", label: "Cross-Account Open Tickets Audit", query: "List all open tickets across all customer accounts and highlight any active SLA breaches." },
    { tag: "Defect Mitigation", label: "Summary of KI-208, KI-211 & Workarounds", query: "Summarize active engineering known issues and temporary workarounds for support staff." }
  ]
};

let currentPersonaKey = "cust_northstar";
let sessionId = `sess_${Math.random().toString(36).substring(2, 10)}`;
let conversationHistory = [];

// DOM Elements
const personaSelect = document.getElementById("persona-select");
const modeBadgeText = document.getElementById("mode-text");
const accPlanBadge = document.getElementById("acc-plan-badge");
const accIdVal = document.getElementById("acc-id-val");
const accNameVal = document.getElementById("acc-name-val");
const accCsmVal = document.getElementById("acc-csm-val");
const accAgrVal = document.getElementById("acc-agr-val");
const quickPromptList = document.getElementById("quick-prompt-list");
const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const telemetryTray = document.getElementById("telemetry-tray");
const telemetryBadges = document.getElementById("telemetry-badges");
const citationsList = document.getElementById("citations-list");
const citationCount = document.getElementById("citation-count");

// Render persona-specific scenario buttons
function renderPersonaScenarios(key) {
  if (!quickPromptList) return;
  quickPromptList.innerHTML = "";
  const scenarios = PERSONA_SCENARIOS[key] || PERSONA_SCENARIOS.cust_northstar;

  scenarios.forEach((sc) => {
    const btn = document.createElement("button");
    btn.className = "quick-btn";
    btn.setAttribute("data-query", sc.query);
    btn.innerHTML = `
      <span class="q-tag">${escapeHTML(sc.tag)}</span>
      <span class="q-text">${escapeHTML(sc.label)}</span>
    `;
    btn.addEventListener("click", () => {
      chatInput.value = sc.query;
      submitUserQuery(sc.query);
    });
    quickPromptList.appendChild(btn);
  });
}

// Initialize Persona UI
function updatePersonaUI(key) {
  currentPersonaKey = key;
  sessionId = `sess_${Math.random().toString(36).substring(2, 10)}`;
  conversationHistory = [];
  const cfg = PERSONA_CONFIGS[key];
  if (!cfg) return;

  modeBadgeText.innerText = cfg.modeLabel;
  accPlanBadge.innerText = cfg.plan;
  accIdVal.innerText = cfg.accountId;
  accNameVal.innerText = cfg.accountName;
  accCsmVal.innerText = cfg.csm;
  accAgrVal.innerText = cfg.agreement;

  renderPersonaScenarios(key);
  appendSystemNotice(`Switched context to: <strong>${cfg.userName}</strong> (${cfg.accountName}) [Role: ${cfg.role}]`);
}

personaSelect.addEventListener("change", (e) => {
  updatePersonaUI(e.target.value);
});

// Chat submission handler
chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const query = chatInput.value.trim();
  if (!query) return;
  submitUserQuery(query);
});

// Auto-expand textarea
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.dispatchEvent(new Event("submit"));
  }
});

async function submitUserQuery(query) {
  chatInput.value = "";
  appendUserMessage(query);

  const cfg = PERSONA_CONFIGS[currentPersonaKey];
  sendBtn.disabled = true;
  sendBtn.innerHTML = `<span>Thinking...</span>`;

  // Show telemetry loading indicator
  telemetryTray.style.display = "flex";
  telemetryBadges.innerHTML = `<span class="tool-badge">Orchestrating agent reasoning loop...</span>`;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-account-id": cfg.accountId,
        "x-user-role": cfg.role,
        "x-user-name": cfg.userName
      },
      body: JSON.stringify({
        message: query,
        session_id: sessionId,
        account_id: cfg.accountId,
        user_role: cfg.role,
        user_name: cfg.userName,
        chat_history: conversationHistory
      })
    });

    const data = await response.json();
    
    // Save to conversation history for multi-turn context
    conversationHistory.push({ role: "user", content: query });
    if (data && data.response) {
      conversationHistory.push({ role: "assistant", content: data.response });
    }
    if (conversationHistory.length > 20) {
      conversationHistory = conversationHistory.slice(-20);
    }

    renderAgentResponse(data);
  } catch (err) {
    appendAssistantMessage(`Error communicating with backend: ${err.message}`);
  } finally {
    sendBtn.disabled = false;
    sendBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="22" y1="2" x2="11" y2="13"></line>
        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
      </svg>
      <span>Send</span>
    `;
  }
}

function formatMarkdownText(text) {
  if (!text) return "";
  let formatted = text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/^### (.*$)/gim, "<h4>$1</h4>")
    .replace(/^## (.*$)/gim, "<h3>$1</h3>")
    .replace(/^# (.*$)/gim, "<h2>$1</h2>")
    .replace(/^\s*-\s+(.*$)/gim, "<li>$1</li>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br>");
  return `<p>${formatted}</p>`;
}

function appendUserMessage(text) {
  const msgEl = document.createElement("div");
  msgEl.className = "message user-message";
  msgEl.innerHTML = `
    <div class="msg-content">
      <p>${escapeHTML(text)}</p>
    </div>
  `;
  chatMessages.appendChild(msgEl);
  scrollToBottom();
}

function appendAssistantMessage(htmlContent) {
  const msgEl = document.createElement("div");
  msgEl.className = "message assistant-message";
  msgEl.innerHTML = `
    <div class="msg-avatar">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <path d="M12 16v-4"></path>
        <path d="M12 8h.01"></path>
      </svg>
    </div>
    <div class="msg-content">
      ${htmlContent}
    </div>
  `;
  chatMessages.appendChild(msgEl);
  scrollToBottom();
}

function appendSystemNotice(htmlContent) {
  const msgEl = document.createElement("div");
  msgEl.className = "message assistant-message system-notice";
  msgEl.innerHTML = `
    <div class="msg-avatar" style="color: var(--accent-amber);">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="12 2 2 22 22 22 12 2"></polygon>
        <line x1="12" y1="9" x2="12" y2="13"></line>
        <line x1="12" y1="17" x2="12.01" y2="17"></line>
      </svg>
    </div>
    <div class="msg-content" style="border-color: rgba(245, 158, 11, 0.3);">
      <p>${htmlContent}</p>
    </div>
  `;
  chatMessages.appendChild(msgEl);
  scrollToBottom();
}

function renderAgentResponse(data) {
  // Render Telemetry Badges
  const telemetry = data.tool_telemetry || [];
  if (telemetry.length > 0) {
    telemetryTray.style.display = "flex";
    telemetryBadges.innerHTML = telemetry.map(t => {
      const cls = t.status === "forbidden" ? "forbidden" : "success";
      return `<span class="tool-badge ${cls}"><strong>${t.tool}</strong>: ${escapeHTML(t.summary)}</span>`;
    }).join("");
  } else {
    telemetryTray.style.display = "none";
  }

  // Render Assistant Message
  let messageHTML = formatMarkdownText(data.response || "");

  // If pending action exists, render Action Proposal Card
  const pendingAction = data.pending_action;
  let actionCardHTML = "";
  if (pendingAction && pendingAction.status === "PENDING") {
    actionCardHTML = `
      <div class="action-card" id="card-${pendingAction.action_token}">
        <div class="action-card-header">
          <span class="action-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="12 2 2 22 22 22 12 2"></polygon>
              <line x1="12" y1="9" x2="12" y2="13"></line>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
            Action Proposal: ${escapeHTML(pendingAction.action_type)}
          </span>
          <span class="action-token-badge">${pendingAction.action_token}</span>
        </div>
        <div class="action-summary">${escapeHTML(pendingAction.summary)}</div>
        <div class="action-buttons">
          <button class="btn-confirm" onclick="confirmActionProposal('${pendingAction.action_token}')">
            ✓ Confirm Action
          </button>
          <button class="btn-cancel" onclick="cancelActionProposal('${pendingAction.action_token}')">
            ✕ Reject / Cancel
          </button>
        </div>
      </div>
    `;
  }

  appendAssistantMessage(messageHTML + actionCardHTML);

  // Render Citations
  renderCitations(data.citations || []);
}

function renderCitations(citations) {
  if (citations.length === 0) {
    citationCount.innerText = "0 Sources";
    citationsList.innerHTML = `
      <div class="empty-citations">
        <p>No document citations for this turn.</p>
      </div>
    `;
    return;
  }

  citationCount.innerText = `${citations.length} Sources`;
  citationsList.innerHTML = citations.map(c => {
    let rankClass = "rank-70";
    if (c.authority_weight >= 100) rankClass = "rank-100";
    else if (c.authority_weight >= 80) rankClass = "rank-80";

    return `
      <div class="citation-item">
        <div class="citation-item-header">
          <span class="citation-doc-name">${escapeHTML(c.doc_name)}</span>
          <span class="authority-rank-badge ${rankClass}">Rank ${c.authority_weight}</span>
        </div>
        <div class="citation-section">${escapeHTML(c.section || '')}</div>
        <div class="citation-snippet">${escapeHTML(c.snippet || '')}</div>
      </div>
    `;
  }).join("");
}

async function confirmActionProposal(token) {
  const cfg = PERSONA_CONFIGS[currentPersonaKey];
  const cardEl = document.getElementById(`card-${token}`);
  if (cardEl) {
    cardEl.innerHTML = `<div class="action-summary">Executing action <code>${token}</code>...</div>`;
  }

  try {
    const res = await fetch("/api/actions/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action_token: token,
        user_role: cfg.role,
        user_name: cfg.userName,
        account_id: cfg.accountId
      })
    });

    const data = await res.json();
    if (data.success) {
      if (cardEl) {
        cardEl.className = "action-card action-executed";
        cardEl.innerHTML = `
          <div class="action-card-header">
            <span class="action-title">✓ Action Executed Successfully</span>
            <span class="action-token-badge">${token}</span>
          </div>
          <div class="action-summary">
            <strong>${escapeHTML(data.receipt.action_type)}</strong> completed by ${escapeHTML(data.receipt.executed_by)} at ${escapeHTML(data.receipt.executed_at)}.<br>
            <em>${escapeHTML(data.receipt.message || '')}</em>
          </div>
        `;
      }
    } else {
      if (cardEl) {
        cardEl.innerHTML = `<div class="action-summary" style="color: var(--accent-rose);">Error: ${escapeHTML(data.detail || data.error)}</div>`;
      }
    }
  } catch (err) {
    if (cardEl) {
      cardEl.innerHTML = `<div class="action-summary" style="color: var(--accent-rose);">Execution error: ${err.message}</div>`;
    }
  }
}

async function cancelActionProposal(token) {
  const cfg = PERSONA_CONFIGS[currentPersonaKey];
  const cardEl = document.getElementById(`card-${token}`);
  try {
    await fetch("/api/actions/cancel", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action_token: token,
        user_role: cfg.role,
        user_name: cfg.userName,
        account_id: cfg.accountId
      })
    });
    if (cardEl) {
      cardEl.style.opacity = "0.6";
      cardEl.innerHTML = `<div class="action-summary" style="color: var(--text-muted);">Action proposal ${token} was rejected and cancelled.</div>`;
    }
  } catch (err) {
    console.error("Cancel failed:", err);
  }
}

function escapeHTML(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Initial Setup
updatePersonaUI("cust_northstar");
