// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => {
      b.classList.remove('active');
      b.setAttribute('aria-selected', 'false');
      b.tabIndex = -1;
    });
    document.querySelectorAll('.tab-panel').forEach(p => {
      p.classList.add('hidden');
      p.classList.remove('active');
    });
    btn.classList.add('active');
    btn.setAttribute('aria-selected', 'true');
    btn.tabIndex = 0;
    const panel = document.getElementById('tab-' + btn.dataset.tab);
    panel.classList.remove('hidden');
    panel.classList.add('active');
  });

  btn.addEventListener('keydown', event => {
    const tabs = Array.from(document.querySelectorAll('.tab-btn'));
    const currentIndex = tabs.indexOf(btn);
    let nextIndex = null;
    if (event.key === 'ArrowRight') nextIndex = (currentIndex + 1) % tabs.length;
    if (event.key === 'ArrowLeft') nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
    if (event.key === 'Home') nextIndex = 0;
    if (event.key === 'End') nextIndex = tabs.length - 1;
    if (nextIndex !== null) {
      event.preventDefault();
      tabs[nextIndex].click();
      tabs[nextIndex].focus();
    }
  });
});

function handleError(responseEl, e) {
  responseEl.textContent = e.code === 'NOT_ANALYZED'
    ? 'Analyze this repository first before querying.'
    : e.message || 'An error occurred';
  responseEl.style.color = 'var(--accent-danger)';
  responseEl.classList.remove('hidden');
}

// Wire query button
document.getElementById('query-btn').addEventListener('click', async () => {
  const question = document.getElementById('query-input').value.trim();
  if (!question || !window._currentRepo) return;
  const btn = document.getElementById('query-btn');
  const responseEl = document.getElementById('query-response');
  btn.disabled = true; btn.textContent = 'Asking...';
  responseEl.className = 'tool-response'; 
  responseEl.innerHTML = '';
  
  try {
    const data = await API.query(window._currentRepo, question);
    responseEl.innerHTML = renderQueryResponse(data);
    responseEl.classList.remove('hidden');
  } catch (e) {
    handleError(responseEl, e);
  } finally {
    btn.disabled = false; btn.textContent = 'Ask Gitspire';
  }
});

// Wire alarm button
document.getElementById('alarm-btn').addEventListener('click', async () => {
  const snippet = document.getElementById('alarm-input').value.trim();
  if (!snippet || !window._currentRepo) return;
  const btn = document.getElementById('alarm-btn');
  const responseEl = document.getElementById('alarm-response');
  btn.disabled = true; btn.textContent = 'Checking...';
  responseEl.className = 'tool-response';
  responseEl.innerHTML = '';
  
  try {
    const data = await API.checkAlarm(window._currentRepo, snippet);
    responseEl.innerHTML = renderAlarmResponse(data);
    if (data.violation_detected) {
      responseEl.classList.add('violation');
      document.getElementById('alarm-panel').classList.add('alarm-active');
      setTimeout(() => document.getElementById('alarm-panel').classList.remove('alarm-active'), 2000);
    } else {
      responseEl.classList.add('clear');
    }
    responseEl.classList.remove('hidden');
  } catch (e) {
    handleError(responseEl, e);
  } finally {
    btn.disabled = false; btn.textContent = 'Check Assumptions';
  }
});

// Wire onboard button
document.getElementById('onboard-btn').addEventListener('click', async () => {
  const feature = document.getElementById('onboard-input').value.trim();
  if (!feature || !window._currentRepo) return;
  const btn = document.getElementById('onboard-btn');
  const responseEl = document.getElementById('onboard-response');
  btn.disabled = true; btn.textContent = 'Generating...';
  responseEl.className = 'tool-response';
  responseEl.innerHTML = '';
  
  try {
    const data = await API.onboard(window._currentRepo, feature);
    responseEl.innerHTML = renderOnboardingChecklist(data);
    responseEl.classList.remove('hidden');
  } catch (e) {
    handleError(responseEl, e);
  } finally {
    btn.disabled = false; btn.textContent = 'Generate Path';
  }
});

// Evidence chip click handler (delegated)
document.body.addEventListener('click', e => {
  const chip = e.target.closest('.evidence-chip[data-href]');
  if (chip) window.open(chip.dataset.href, '_blank', 'noopener,noreferrer');
});
