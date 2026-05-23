function getRepoOwnerAndName(url) {
  if (!url) return { owner: '', repo: '' };
  try {
    const parts = new URL(url).pathname.replace(/^\/|\/$/g, '').split('/');
    if (parts.length >= 2) return { owner: parts[0], repo: parts[1].replace('.git', '') };
  } catch (e) {}
  return { owner: '', repo: '' };
}

function renderEvidenceChip(evidence) {
  const parts = evidence.split(':');
  const type = parts[0];
  const value = parts.slice(1).join(':');
  
  let href = '';
  const repoData = getRepoOwnerAndName(window._currentRepo);
  const baseUrl = `https://github.com/${repoData.owner}/${repoData.repo}`;

  if (type === 'commit' && repoData.owner) {
    href = ` data-href="${baseUrl}/commit/${value}"`;
  } else if (type === 'issue' && repoData.owner) {
    const num = value.replace('#', '');
    href = ` data-href="${baseUrl}/issues/${num}"`;
  } else if (type === 'pr' && repoData.owner) {
    const num = value.replace('#', '');
    href = ` data-href="${baseUrl}/pull/${num}"`;
  }

  return `<span class="evidence-chip"${href}>${evidence}</span>`;
}

function renderDecisionAtom(atom) {
  const chips = (atom.evidence || []).map(renderEvidenceChip).join('');
  const pct = Math.max(0, Math.min(100, (atom.confidence || 0) * 100));
  
  return `
    <div class="decision-card">
      <h3 class="text-heading" style="margin-bottom: var(--space-2);">${atom.decision}</h3>
      <p class="text-secondary" style="margin-bottom: var(--space-4);">${atom.reasoning}</p>
      <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-2);">
        <span class="text-label">Confidence: ${Math.round(pct)}%</span>
        <div style="display:flex; gap: 4px; flex-wrap: wrap;">${chips}</div>
      </div>
      <div class="confidence-bar">
        <div class="confidence-fill" style="width: ${pct}%"></div>
      </div>
    </div>
  `;
}

function renderAssumption(assumption) {
  let dependsHtml = '';
  if (assumption.depends_on && assumption.depends_on.length > 0) {
    dependsHtml = `<div style="margin-top: var(--space-3);">
      <span class="text-label">Depends on:</span> 
      <span class="text-code">${assumption.depends_on.join(', ')}</span>
    </div>`;
  }

  return `
    <div class="assumption-card" data-risk="${assumption.risk_level}">
      <div style="margin-bottom: var(--space-2);">
        <span class="risk-badge ${assumption.risk_level}">${assumption.risk_level} RISK</span>
      </div>
      <p style="font-weight: 500;">${assumption.statement}</p>
      ${dependsHtml}
    </div>
  `;
}

function renderFailureRecord(record) {
  const chips = (record.evidence || []).map(renderEvidenceChip).join('');
  return `
    <div class="failure-card">
      <h3 class="text-heading" style="margin-bottom: var(--space-2); color: var(--accent-warning);">Attempted: ${record.approach}</h3>
      <p class="text-secondary" style="margin-bottom: var(--space-3);"><strong>Failed because:</strong> ${record.reason_failed}</p>
      <div style="display:flex; gap: 4px; flex-wrap: wrap;">${chips}</div>
    </div>
  `;
}

function renderGhostDecision(ghost) {
  const reasonsHtml = (ghost.possible_reasons || []).map(r => `<li>${r}</li>`).join('');
  return `
    <div class="ghost-card">
      <div style="margin-bottom: var(--space-2);">
        <span class="text-code">${ghost.location}</span>
      </div>
      <p style="margin-bottom: var(--space-3); font-weight: 500;">${ghost.observation}</p>
      <div class="text-secondary">
        <p class="text-label" style="margin-bottom: var(--space-1);">Possible Reasons:</p>
        <ul style="list-style-type: disc; padding-left: var(--space-4); opacity: 0.8;">
          ${reasonsHtml}
        </ul>
      </div>
    </div>
  `;
}

function renderQueryResponse(response) {
  const answerHtml = marked.parse(response.answer || "");
  const chips = (response.citations || []).map(renderEvidenceChip).join('');
  
  let confColor = 'var(--text-secondary)';
  if (response.confidence === 'high') confColor = 'var(--accent-success)';
  if (response.confidence === 'medium') confColor = 'var(--accent-warning)';
  if (response.confidence === 'low') confColor = 'var(--accent-danger)';

  return `
    <div style="margin-bottom: var(--space-3); border-bottom: 1px solid var(--border-subtle); padding-bottom: var(--space-3);">
      ${answerHtml}
    </div>
    <div style="display:flex; justify-content: space-between; align-items: center;">
      <div style="display:flex; gap: 4px; flex-wrap: wrap;">${chips}</div>
      <span class="badge" style="color: ${confColor}; border: 1px solid ${confColor}; background: transparent;">
        ${(response.confidence || 'unknown').toUpperCase()} CONFIDENCE
      </span>
    </div>
  `;
}

function renderAlarmResponse(response) {
  if (response.violation_detected) {
    let advisoryHtml = '';
    if (response.new_assumption_introduced && response.new_assumption_introduced !== "null") {
      advisoryHtml = `
        <div class="warning-advisory">
          <strong style="color: var(--accent-warning); font-size: 12px;">NEW ASSUMPTION DETECTED:</strong><br>
          <span class="text-secondary" style="font-size: 12px;">${response.new_assumption_introduced}</span>
        </div>
      `;
    }
    
    const statement = response.violated_assumption ? response.violated_assumption.statement : 'Unknown assumption';
    
    return `
      <div class="violation" style="padding: var(--space-3); border-radius: var(--radius-md);">
        <h4 style="color: var(--accent-danger); margin-bottom: var(--space-2);">⚠ Assumption Violated</h4>
        <p style="font-weight: 500; margin-bottom: var(--space-2);">${statement}</p>
        <p class="text-secondary" style="font-size: 13px;">${response.explanation}</p>
        ${advisoryHtml}
      </div>
    `;
  } else {
    return `
      <div class="clear" style="padding: var(--space-3); border-radius: var(--radius-md); text-align: center;">
        <h4 style="color: var(--accent-success);">✓ No violations detected</h4>
        <p class="text-secondary" style="font-size: 13px; margin-top: var(--space-1);">${response.explanation || 'Code snippet aligns with extracted assumptions.'}</p>
      </div>
    `;
  }
}

function renderOnboardingChecklist(response) {
  if (!response.checklist || response.checklist.length === 0) {
    return `<p class="text-secondary">No specific risks identified for this feature.</p>`;
  }

  let warningHtml = '';
  if (response.warning_count > 0) {
    warningHtml = `
      <div style="margin-bottom: var(--space-4); color: var(--accent-danger); font-size: 12px; font-weight: 600;">
        ⚠ CONTAINS ${response.warning_count} CRITICAL RISK ITEM(S)
      </div>
    `;
  }

  const listHtml = response.checklist.map(item => `
    <div style="margin-bottom: var(--space-3); padding-bottom: var(--space-3); border-bottom: 1px solid var(--border-subtle);">
      <div style="display:flex; align-items:baseline; gap: var(--space-2); margin-bottom: var(--space-1);">
        <span class="badge">${item.priority}</span>
        <strong style="color: var(--text-primary);">${item.topic}</strong>
      </div>
      <p class="text-secondary" style="font-size: 13px; margin-bottom: var(--space-2); padding-left: 30px;">${item.why}</p>
      <div style="padding-left: 30px;">${renderEvidenceChip(item.evidence)}</div>
    </div>
  `).join('');

  return warningHtml + listHtml;
}