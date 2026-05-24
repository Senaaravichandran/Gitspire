const AppState = { 
  IDLE: 'idle', ANALYZING: 'analyzing', READY: 'ready',
  QUERYING: 'querying', ALARMING: 'alarming', ONBOARDING: 'onboarding'
};

const state = { current: AppState.IDLE, repo: null, core: null };
window._currentRepo = null;

let geminiLottieInitialized = false;
async function initGeminiLottie() {
  if (geminiLottieInitialized) return;
  if (!window.lottie) return;
  const container = document.getElementById('gemini-lottie');
  if (!container) return;

  const candidates = [
    '/gemini.json',
    '/static/gemini.json',
    'gemini.json'
  ];

  for (const url of candidates) {
    try {
      const res = await fetch(url);
      if (!res.ok) continue;
      const animationData = await res.json();
      window.lottie.loadAnimation({
        container,
        renderer: 'svg',
        loop: true,
        autoplay: true,
        animationData
      });
      geminiLottieInitialized = true;
      break;
    } catch (error) {
      continue;
    }
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
  initGeminiLottie();
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
  
  // Repo bar
  document.getElementById('repo-bar').innerHTML = `
    <strong>${core.repo_url.replace('https://github.com/','')}</strong>
    <span class="text-label">Analyzed ${new Date(core.analyzed_at).toLocaleString()}</span>
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