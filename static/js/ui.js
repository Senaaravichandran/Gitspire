function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function escapeDisplayData(value) {
  if (typeof value === 'string') return escapeHtml(value);
  if (Array.isArray(value)) return value.map(escapeDisplayData);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, escapeDisplayData(item)]));
  }
  return value;
}

function renderPlainText(value) {
  return `<p>${escapeHtml(value).replaceAll('\n', '<br>')}</p>`;
}

function getRepoOwnerAndName(url) {
  if (!url) return { owner: '', repo: '' };
  try {
    const parts = new URL(url).pathname.replace(/^\/|\/$/g, '').split('/');
    if (parts.length >= 2) return { owner: parts[0], repo: parts[1].replace('.git', '') };
  } catch (e) {}
  return { owner: '', repo: '' };
}

function normalizeRiskLevel(level) {
  const normalized = String(level || 'moderate').toLowerCase();
  if (normalized === 'high') return 'high';
  if (normalized === 'medium') return 'medium';
  if (normalized === 'critical') return 'critical';
  if (normalized === 'low') return 'low';
  return 'moderate';
}

function formatStatusLabel(value) {
  return String(value || 'unknown').replace(/_/g, ' ');
}

function renderEmptyState(title, message) {
  return `
    <div class="insight-empty-state">
      <h3 class="text-heading">${title}</h3>
      <p class="text-secondary">${message}</p>
    </div>
  `;
}

function renderMetaChip(text, tone = '') {
  const toneClass = tone ? ` ${tone}` : '';
  return `<span class="meta-chip${toneClass}">${text}</span>`;
}

function renderIcon(symbolId, className = '') {
  const classes = className ? `inline-icon ${className}` : 'inline-icon';
  return `<svg class="${classes}" aria-hidden="true" focusable="false" viewBox="0 0 24 24"><use href="#${symbolId}"></use></svg>`;
}

function pluralize(count, singular, plural = `${singular}s`) {
  return count === 1 ? singular : plural;
}

function renderGuardVerdict(core) {
  const container = document.getElementById('guard-verdict-card');
  if (!container) return;

  const noCore = !core;
  const assumptions = Array.isArray(core?.assumptions) ? core.assumptions : [];
  const decisionAtoms = Array.isArray(core?.decision_atoms) ? core.decision_atoms : [];
  const ghostDecisions = Array.isArray(core?.ghost_decisions) ? core.ghost_decisions : [];
  const regrettedDecisions = Array.isArray(core?.regretted_decisions) ? core.regretted_decisions : [];
  const orphanedArchitecture = Array.isArray(core?.orphaned_architecture) ? core.orphaned_architecture : [];
  const pulseSummary = core?.pulse_report?.overall_summary || null;

  const criticalAssumptions = assumptions.filter(item => String(item.risk_level || '').toLowerCase() === 'critical').length;
  const criticalOrphans = orphanedArchitecture.filter(item => String(item.orphan_risk || '').toLowerCase() === 'critical').length;
  const elevatedRegrets = regrettedDecisions.filter(item => {
    const level = String(item.current_risk_level || '').toLowerCase();
    return level === 'high' || level === 'critical';
  }).length;
  const criticalPulse = Number(pulseSummary?.critical_decision_count || 0);
  const agingPulse = Number(pulseSummary?.aging_decision_count || 0);
  const stalePulse = Number(pulseSummary?.stale_decision_count || 0);

  let scoreLabel = 'DNA Score: Pending';
  let statusTone = 'warning';
  let statusLabel = 'Awaiting Analysis';
  let items = [
    {
      tone: 'warning',
      icon: 'icon-warning',
      message: 'Analyze a repository to generate a live architectural verdict.'
    },
    {
      tone: 'success',
      icon: 'icon-check',
      message: 'GitSpire will derive this score from decision pulse, assumptions, and ownership risk.'
    }
  ];

  if (!noCore) {
    if (Number.isFinite(Number(pulseSummary?.overall_freshness_score))) {
      scoreLabel = `DNA Score: ${Number(pulseSummary.overall_freshness_score)}/100`;
    }

    if (criticalPulse > 0 || criticalAssumptions > 0 || criticalOrphans > 0) {
      statusTone = 'danger';
      statusLabel = 'Critical Review';
    } else if (stalePulse > 0 || agingPulse > 0 || elevatedRegrets > 0 || ghostDecisions.length > 0) {
      statusTone = 'warning';
      statusLabel = 'Needs Review';
    } else {
      statusTone = 'success';
      statusLabel = 'Aligned';
    }

    items = [];

    if (decisionAtoms.length > 0) {
      items.push({
        tone: 'success',
        icon: 'icon-check',
        message: `${decisionAtoms.length} ${pluralize(decisionAtoms.length, 'decision atom')} extracted`
      });
    }

    if (criticalAssumptions > 0) {
      items.push({
        tone: 'warning',
        icon: 'icon-warning',
        message: `${criticalAssumptions} critical ${pluralize(criticalAssumptions, 'assumption')} require protection`
      });
    } else if (assumptions.length > 0) {
      items.push({
        tone: 'success',
        icon: 'icon-check',
        message: `${assumptions.length} ${pluralize(assumptions.length, 'assumption')} mapped`
      });
    }

    if (criticalPulse > 0 || stalePulse > 0 || agingPulse > 0) {
      const pulseCount = criticalPulse > 0 ? criticalPulse : stalePulse > 0 ? stalePulse : agingPulse;
      const pulseLabel = criticalPulse > 0 ? 'critical reevaluation' : stalePulse > 0 ? 'stale decision' : 'aging decision';
      items.push({
        tone: criticalPulse > 0 ? 'danger' : 'warning',
        icon: criticalPulse > 0 ? 'icon-danger' : 'icon-warning',
        message: `${pulseCount} ${pluralize(pulseCount, pulseLabel)} surfaced by decision pulse`
      });
    }

    if (criticalOrphans > 0) {
      items.push({
        tone: 'danger',
        icon: 'icon-danger',
        message: `${criticalOrphans} orphaned ${pluralize(criticalOrphans, 'subsystem')} need active ownership`
      });
    } else if (elevatedRegrets > 0) {
      items.push({
        tone: 'warning',
        icon: 'icon-warning',
        message: `${elevatedRegrets} regretted ${pluralize(elevatedRegrets, 'decision')} are still carrying risk`
      });
    } else if (ghostDecisions.length > 0) {
      items.push({
        tone: 'warning',
        icon: 'icon-warning',
        message: `${ghostDecisions.length} ${pluralize(ghostDecisions.length, 'ghost decision')} need clearer ownership`
      });
    }

    if (items.length === 0) {
      items.push({
        tone: 'success',
        icon: 'icon-check',
        message: 'This repository did not surface immediate architectural risk signals in the current analysis.'
      });
    }
  }

  const statusIcon = statusTone === 'danger'
    ? 'icon-danger'
    : statusTone === 'success'
      ? 'icon-check'
      : 'icon-warning';

  const listHtml = items.slice(0, 4).map(item => `
    <div class="guard-verdict-item ${item.tone}" role="listitem">
      ${renderIcon(item.icon, 'status-icon')}
      <span>${item.message}</span>
    </div>
  `).join('');

  container.innerHTML = `
    <div class="guard-verdict-header">
      <span class="guard-verdict-label">AI Verdict</span>
      <span class="guard-verdict-score">${scoreLabel}</span>
    </div>
    <div class="guard-verdict-status ${statusTone}">
      ${renderIcon(statusIcon, 'status-icon')}
      <span>${statusLabel}</span>
    </div>
    <div class="guard-verdict-list" role="list">
      ${listHtml}
    </div>
  `;
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
    const translationBadge = atom.translated_source
      ? `<span class="translation-badge">Source: ${String(atom.source_language || '').toUpperCase()} (translated)</span>`
    : '';
  
  return `
    <div class="decision-card">
      <div class="decision-header">
        <h3 class="text-heading">${atom.decision}</h3>
        ${translationBadge}
      </div>
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

function renderRegrettedDecision(decision) {
  const signalChips = (decision.regret_signals || []).map(renderEvidenceChip).join('');
  const confidence = Math.max(0, Math.min(100, (decision.confidence_score || 0) * 100));
  const riskClass = normalizeRiskLevel(decision.current_risk_level);

  return `
    <div class="regret-card">
      <div class="decision-header">
        <h3 class="text-heading">${decision.title}</h3>
        <span class="risk-badge ${riskClass}">${formatStatusLabel(decision.current_risk_level)} RISK</span>
      </div>
      <p class="text-secondary" style="margin-bottom: var(--space-3);">${decision.original_decision}</p>
      <div class="detail-grid" style="margin-bottom: var(--space-3);">
        <div>
          <p class="text-label" style="margin-bottom: 4px;">Why It Exists</p>
          <p class="text-secondary">${decision.why_it_exists}</p>
        </div>
        <div>
          <p class="text-label" style="margin-bottom: 4px;">Architectural Consequences</p>
          <p class="text-secondary">${decision.architectural_consequences}</p>
        </div>
      </div>
      <div class="detail-block" style="margin-bottom: var(--space-3);">
        <p class="text-label" style="margin-bottom: 4px;">Emotional Evidence</p>
        <p class="text-secondary">${decision.emotional_evidence}</p>
      </div>
      <div style="display:flex; justify-content: space-between; align-items: center; gap: var(--space-3); margin-bottom: var(--space-2); flex-wrap: wrap;">
        <span class="text-label">Confidence: ${Math.round(confidence)}%</span>
        <div style="display:flex; gap: 4px; flex-wrap: wrap;">${signalChips || renderMetaChip('No explicit signals')}</div>
      </div>
      <div class="confidence-bar">
        <div class="confidence-fill" style="width: ${confidence}%"></div>
      </div>
    </div>
  `;
}

function renderOrphanedArchitecture(orphan) {
  const hiddenAssumptions = (orphan.hidden_assumptions || []).map(item => `<li>${item}</li>`).join('');
  const stabilizationSteps = (orphan.suggested_stabilization_steps || []).map(item => `<li>${item}</li>`).join('');

  return `
    <div class="orphan-card">
      <div class="decision-header" style="justify-content: space-between; align-items: flex-start;">
        <div>
          <h3 class="text-heading">${orphan.decision_title}</h3>
          <p class="text-secondary" style="margin-top: 4px;">${orphan.subsystem}</p>
        </div>
        <div style="display:flex; gap: 4px; flex-wrap: wrap; justify-content: flex-end;">
          ${renderMetaChip(formatStatusLabel(orphan.active_status), normalizeRiskLevel(orphan.orphan_risk))}
          ${renderMetaChip(`Criticality: ${formatStatusLabel(orphan.criticality)}`, normalizeRiskLevel(orphan.criticality))}
          ${renderMetaChip(`Orphan risk: ${formatStatusLabel(orphan.orphan_risk)}`, normalizeRiskLevel(orphan.orphan_risk))}
        </div>
      </div>
      <div class="detail-grid" style="margin: var(--space-3) 0;">
        <div>
          <p class="text-label" style="margin-bottom: 4px;">Original Author</p>
          <p class="text-secondary">${orphan.original_author || 'Unknown'}</p>
        </div>
        <div>
          <p class="text-label" style="margin-bottom: 4px;">Last Seen Activity</p>
          <p class="text-secondary">${orphan.last_seen_activity || 'Unknown'}</p>
        </div>
      </div>
      <div class="detail-block" style="margin-bottom: var(--space-3);">
        <p class="text-label" style="margin-bottom: 4px;">Why Dangerous</p>
        <p class="text-secondary">${orphan.why_dangerous}</p>
      </div>
      <div class="detail-grid">
        <div class="detail-list-card">
          <p class="text-label" style="margin-bottom: var(--space-2);">Hidden Assumptions</p>
          <ul class="detail-list">
            ${hiddenAssumptions || '<li>No hidden assumptions captured.</li>'}
          </ul>
        </div>
        <div class="detail-list-card">
          <p class="text-label" style="margin-bottom: var(--space-2);">Stabilization Steps</p>
          <ul class="detail-list">
            ${stabilizationSteps || '<li>No stabilization steps suggested.</li>'}
          </ul>
        </div>
      </div>
    </div>
  `;
}

function renderPulseDecision(decision) {
  const alternatives = (decision.modern_alternatives || []).map(item => renderMetaChip(item)).join('');
  const supportingSignals = (decision.supporting_signals || []).map(item => renderMetaChip(item)).join('');
  const confidence = Math.max(0, Math.min(100, (decision.confidence_score || 0) * 100));
  const statusClass = String(decision.status || 'stable').toLowerCase().replace(/_/g, '-');

  return `
    <div class="pulse-card">
      <div class="pulse-card-header">
        <div>
          <h3 class="text-heading">${decision.decision_title}</h3>
          <p class="text-secondary" style="margin-top: 4px;">${decision.original_reasoning}</p>
        </div>
        <div style="display:flex; gap: 4px; flex-wrap: wrap; justify-content: flex-end;">
          <span class="pulse-status ${statusClass}">${formatStatusLabel(decision.status)}</span>
          ${renderMetaChip(`Freshness ${decision.freshness_score || 0}/100`, statusClass)}
        </div>
      </div>
      <div class="detail-grid" style="margin: var(--space-3) 0;">
        <div>
          <p class="text-label" style="margin-bottom: 4px;">What Changed</p>
          <p class="text-secondary">${decision.what_changed}</p>
        </div>
        <div>
          <p class="text-label" style="margin-bottom: 4px;">Current Ecosystem State</p>
          <p class="text-secondary">${decision.current_ecosystem_state}</p>
        </div>
        <div>
          <p class="text-label" style="margin-bottom: 4px;">Assumption Validity</p>
          <p class="text-secondary">${decision.assumption_validity}</p>
        </div>
        <div>
          <p class="text-label" style="margin-bottom: 4px;">Reevaluation Needed</p>
          <p class="text-secondary">${decision.reevaluation_needed ? 'Yes' : 'No'}</p>
        </div>
      </div>
      <div class="detail-block" style="margin-bottom: var(--space-3);">
        <p class="text-label" style="margin-bottom: 4px;">Risk Summary</p>
        <p class="text-secondary">${decision.risk_summary}</p>
      </div>
      <div class="detail-block" style="margin-bottom: var(--space-3);">
        <p class="text-label" style="margin-bottom: 6px;">Modern Alternatives</p>
        <div style="display:flex; gap: 4px; flex-wrap: wrap;">${alternatives || renderMetaChip('No alternatives recorded')}</div>
      </div>
      <div style="display:flex; justify-content: space-between; align-items: center; gap: var(--space-3); margin-bottom: var(--space-2); flex-wrap: wrap;">
        <div style="display:flex; gap: 4px; flex-wrap: wrap;">${supportingSignals || renderMetaChip('No supporting signals')}</div>
        <span class="text-label">Confidence: ${Math.round(confidence)}%</span>
      </div>
      <div class="confidence-bar">
        <div class="confidence-fill" style="width: ${confidence}%"></div>
      </div>
    </div>
  `;
}

function renderPulseReport(report) {
  if (!report || !Array.isArray(report.decisions) || report.decisions.length === 0) {
    return renderEmptyState(
      'No decision pulse available',
      'This analysis did not include ecosystem freshness or reevaluation signals for architectural decisions.'
    );
  }

  const overall = report.overall_summary || {};
  const summaryCard = `
    <div class="pulse-summary-card">
      <div class="pulse-card-header">
        <div>
          <p class="text-label" style="margin-bottom: 4px;">Overall Freshness</p>
          <h3 class="text-heading">${overall.overall_freshness_score || 0}/100</h3>
        </div>
        <div style="display:flex; gap: 4px; flex-wrap: wrap; justify-content: flex-end;">
          ${renderMetaChip(`${overall.aging_decision_count || 0} aging`, 'warning')}
          ${renderMetaChip(`${overall.stale_decision_count || 0} stale`, 'danger')}
          ${renderMetaChip(`${overall.critical_decision_count || 0} critical`, 'danger')}
        </div>
      </div>
      <p class="text-secondary">${overall.summary || 'No summary provided.'}</p>
    </div>
  `;

  return summaryCard + report.decisions.map(renderPulseDecision).join('');
}

function renderQueryResponse(response) {
  response = escapeDisplayData(response);
  const answerHtml = renderPlainText(response.answer || '');
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
  response = escapeDisplayData(response);
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
        <h4 style="color: var(--accent-danger); margin-bottom: var(--space-2); display:flex; align-items:center; gap: var(--space-2);">
          ${renderIcon('icon-warning', 'status-icon')}
          <span>Assumption Violated</span>
        </h4>
        <p style="font-weight: 500; margin-bottom: var(--space-2);">${statement}</p>
        <p class="text-secondary" style="font-size: 13px;">${response.explanation}</p>
        ${advisoryHtml}
      </div>
    `;
  } else {
    return `
      <div class="clear" style="padding: var(--space-3); border-radius: var(--radius-md); text-align: center;">
        <h4 style="color: var(--accent-success); display:flex; align-items:center; justify-content:center; gap: var(--space-2);">
          ${renderIcon('icon-check', 'status-icon')}
          <span>No violations detected</span>
        </h4>
        <p class="text-secondary" style="font-size: 13px; margin-top: var(--space-1);">${response.explanation || 'Code snippet aligns with extracted assumptions.'}</p>
      </div>
    `;
  }
}

function renderOnboardingChecklist(response) {
  response = escapeDisplayData(response);
  if (!response.checklist || response.checklist.length === 0) {
    return `<p class="text-secondary">No specific risks identified for this feature.</p>`;
  }

  let warningHtml = '';
  if (response.warning_count > 0) {
    warningHtml = `
      <div style="margin-bottom: var(--space-4); color: var(--accent-danger); font-size: 12px; font-weight: 600; display:flex; align-items:center; gap: var(--space-2);">
        ${renderIcon('icon-warning', 'status-icon')}
        <span>CONTAINS ${response.warning_count} CRITICAL RISK ITEM(S)</span>
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
