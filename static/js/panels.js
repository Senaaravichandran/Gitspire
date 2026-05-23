// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.remove('hidden');
  });
});

function handleError(responseEl, e) {
  if (e.code === 'NOT_ANALYZED') {
    responseEl.innerHTML = `<p style="color:var(--accent-danger)">Analyze this repository first before querying.</p>`;
  } else {
    responseEl.innerHTML = `<p style="color:var(--accent-danger)">${e.message || 'An error occurred'}</p>`;
  }
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
  if (chip) window.open(chip.dataset.href, '_blank');
});