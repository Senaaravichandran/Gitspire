const AppState = { 
  IDLE: 'idle', ANALYZING: 'analyzing', READY: 'ready',
  QUERYING: 'querying', ALARMING: 'alarming', ONBOARDING: 'onboarding'
};

const state = { current: AppState.IDLE, repo: null, core: null };
window._currentRepo = null;

const initializedLottieContainers = new Set();
let loadingAnimationDataPromise = null;

async function getLoadingAnimationData(urlOverride) {
  if (urlOverride) {
    try {
      const res = await fetch(urlOverride);
      if (res.ok) return await res.json();
    } catch (error) {
      return null;
    }
  }

  if (loadingAnimationDataPromise) return loadingAnimationDataPromise;

  loadingAnimationDataPromise = (async () => {
    const candidates = [
      '/gemini.json',
      '/static/gemini.json',
      'gemini.json'
    ];

    for (const url of candidates) {
      try {
        const res = await fetch(url);
        if (!res.ok) continue;
        return await res.json();
      } catch (error) {
        continue;
      }
    }

    return null;
  })();

  return loadingAnimationDataPromise;
}

async function initLoadingLottie(containerId) {
  if (initializedLottieContainers.has(containerId)) return;
  if (!window.lottie) return;
  const container = document.getElementById(containerId);
  if (!container) return;

  const animationData = await getLoadingAnimationData(container.dataset.lottieSrc);
  if (!animationData) return;

  const animationPayload = typeof structuredClone === 'function'
    ? structuredClone(animationData)
    : JSON.parse(JSON.stringify(animationData));

  window.lottie.loadAnimation({
    container,
    renderer: 'svg',
    loop: true,
    autoplay: true,
    animationData: animationPayload
  });

  initializedLottieContainers.add(containerId);
}

async function loadRuntimeMeta() {
  const badge = document.getElementById('model-badge');
  if (!badge) return;

  try {
    const meta = await API.getMeta();
    window.GITSPIRE_FRONTEND_URL = meta.frontend_url || null;
    badge.textContent = meta.model_display_name
      ? `Powered by ${meta.model_display_name}`
      : 'Powered by Gemini';
  } catch (error) {
    badge.textContent = 'Powered by Gemini';
  }
}

function transition(newState) {
  state.current = newState;
  
  const hero         = document.getElementById('hero');
  const progressView = document.getElementById('progress-view');
  const knowledgeCore= document.getElementById('knowledge-core');
  const analyzeBtn   = document.getElementById('analyze-btn');

  if (newState === AppState.IDLE) {
    hero.classList.remove('hidden');
    hero.style.animation = '';
    hero.style.opacity = '1';
    hero.style.transform = 'translateY(0)';
    progressView.classList.add('hidden');
    knowledgeCore.classList.add('hidden');
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = 'Analyze Repository';
  }
  if (newState === AppState.ANALYZING) {
    progressView.classList.remove('hidden');
    hero.style.animation = 'slideUp 400ms ease forwards';
    setTimeout(() => hero.classList.add('hidden'), 380);
    analyzeBtn.disabled = true;
    startProgressSimulation();
  }
  if (newState === AppState.READY) {
    progressView.classList.add('hidden');
    knowledgeCore.classList.remove('hidden');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initLoadingLottie('gemini-lottie');
  initLoadingLottie('progress-lottie');
  loadRuntimeMeta();
  renderGuardVerdict(null);
});

let progressTimer = null;
function startProgressSimulation() {
  const steps = ['step-fetch','step-gemini','step-extract','step-store'];
  let i = 0;
  steps.forEach(id => {
    document.getElementById(id).classList.remove('active','done');
  });
  document.getElementById(steps[0]).classList.add('active');
  progressTimer = setInterval(() => {
    if (i < steps.length - 1) {
      document.getElementById(steps[i]).classList.replace('active','done');
      i++;
      document.getElementById(steps[i]).classList.add('active');
    }
  }, 8000);
}

function stopProgressSimulation() {
  clearInterval(progressTimer);
}

function renderKnowledgeCore(core) {
  window._currentRepo = core.repo_url;
  document.getElementById('summary-card').textContent = core.summary;
  renderGuardVerdict(core);
  
  // Decision Atoms tab
  document.getElementById('tab-decisions').innerHTML = 
    (core.decision_atoms || []).map(renderDecisionAtom).join('');
  document.getElementById('badge-decisions').textContent = 
    (core.decision_atoms || []).length;
  
  // Assumptions tab
  document.getElementById('tab-assumptions').innerHTML = 
    (core.assumptions || []).map(renderAssumption).join('');
  document.getElementById('badge-assumptions').textContent = 
    (core.assumptions || []).length;
  
  // Failure Memory tab
  document.getElementById('tab-failures').innerHTML = 
    (core.failure_memory || []).map(renderFailureRecord).join('');
  document.getElementById('badge-failures').textContent = 
    (core.failure_memory || []).length;
  
  // Ghost Decisions tab
  document.getElementById('tab-ghosts').innerHTML = 
    (core.ghost_decisions || []).map(renderGhostDecision).join('');
  document.getElementById('badge-ghosts').textContent = 
    (core.ghost_decisions || []).length;

  // Regretted Decisions tab
  document.getElementById('tab-regrets').innerHTML =
    (core.regretted_decisions || []).length > 0
      ? (core.regretted_decisions || []).map(renderRegrettedDecision).join('')
      : renderEmptyState(
          'No regretted decisions detected',
          'Gemini did not infer any high-confidence architectural regrets for this repository analysis.'
        );
  document.getElementById('badge-regrets').textContent =
    (core.regretted_decisions || []).length;

  // Orphaned Architecture tab
  document.getElementById('tab-orphans').innerHTML =
    (core.orphaned_architecture || []).length > 0
      ? (core.orphaned_architecture || []).map(renderOrphanedArchitecture).join('')
      : renderEmptyState(
          'No orphaned architecture flagged',
          'This analysis did not identify architecture that appears to have lost an active owner.'
        );
  document.getElementById('badge-orphans').textContent =
    (core.orphaned_architecture || []).length;

  // Decision Pulse tab
  document.getElementById('tab-pulse').innerHTML = renderPulseReport(core.pulse_report);
  document.getElementById('badge-pulse').textContent =
    Array.isArray(core.pulse_report?.decisions) ? core.pulse_report.decisions.length : 0;
  
  // Repo bar
    const langs = (core.languages_detected || []).map(l => l.toUpperCase()).join(' | ');
  const langLine = core.languages_detected && core.languages_detected.length > 0
    ? `
      <div class="lang-row">
        <span class="lang-icon">${renderIcon('icon-globe', 'lang-icon-svg')}</span>
        <span class="text-label">${core.languages_detected.length} languages detected</span>
        <span class="lang-codes">${langs}</span>
        <span class="text-label">${core.translated_artifact_count || 0} artifacts translated</span>
      </div>
    `
    : '';

  document.getElementById('repo-bar').innerHTML = `
    <div class="repo-main">
      <strong>${core.repo_url.replace('https://github.com/','')}</strong>
      <span class="text-label">Analyzed ${new Date(core.analyzed_at).toLocaleString()}</span>
    </div>
    ${langLine}
  `;
}

// MAIN ANALYZE FLOW
document.getElementById('analyze-btn').addEventListener('click', async () => {
  const url = document.getElementById('repo-url').value.trim();
  if (!url) return;
  
  const errorEl = document.getElementById('hero-error');
  errorEl.classList.add('hidden');
  errorEl.innerHTML = '';
  transition(AppState.ANALYZING);
  
  try {
    const data = await API.analyze(url);
    stopProgressSimulation();
    if (!data.success) throw new APIError(data.error || 'Analysis failed', data.error_code || 'UNKNOWN', data);
    state.core = data.knowledge_core;
    state.repo = url;
    window._currentRepo = url;
    renderKnowledgeCore(data.knowledge_core);
    transition(AppState.READY);
  } catch (e) {
    stopProgressSimulation();
    transition(AppState.IDLE);
    
    if (e.code === 'RATE_LIMITED') {
      let seconds = 60;
      errorEl.innerHTML = `GitHub rate limit hit. Try again in <span id="rl-timer">${seconds}</span> seconds.`;
      errorEl.classList.remove('hidden');
      const intv = setInterval(() => {
        seconds--;
        const tel = document.getElementById('rl-timer');
        if(tel) tel.textContent = seconds;
        if(seconds <= 0) {
          clearInterval(intv);
          if(tel) tel.parentElement.textContent = "Rate limit cleared. You can try again.";
        }
      }, 1000);
    } else if (e.code === 'TIMEOUT' || e.code === 'GITHUB_TIMEOUT' || e.code === 'GEMINI_TIMEOUT') {
      errorEl.textContent = 'The analysis took too long and timed out. Try a smaller repo or retry.';
      errorEl.classList.remove('hidden');
    } else if (e.code === 'GEMINI_ERROR') {
      errorEl.textContent = "Gemini API timeout. This repo may be too large. Try psf/requests or pallets/flask.";
      errorEl.classList.remove('hidden');
    } else if (e.code === 'PARSE_ERROR') {
      errorEl.textContent = "Response parsing failed.";
      if (e.raw) localStorage.setItem('gitspire_debug_last_raw', JSON.stringify(e.raw));
      errorEl.classList.remove('hidden');
    } else if (e.code === 'REPO_NOT_FOUND') {
      errorEl.textContent = "Repository not found. Check the URL and try again.";
      errorEl.classList.remove('hidden');
    } else {
      errorEl.textContent = e.message || "An unknown error occurred.";
      errorEl.classList.remove('hidden');
    }
  }
});

// Demo pills
document.querySelectorAll('.demo-pill').forEach(pill => {
  pill.addEventListener('click', () => {
    document.getElementById('repo-url').value = pill.dataset.url;
    document.getElementById('analyze-btn').click();
  });
});

// Enter key on input
document.getElementById('repo-url').addEventListener('keydown', e => {
  if (e.key === 'Enter') document.getElementById('analyze-btn').click();
});