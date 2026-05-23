class APIError extends Error {
  constructor(message, code, raw) {
    super(message);
    this.code = code;
    this.raw = raw;
  }
}

const API = {
  async _fetch(url, body) {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    
    let data;
    try {
      data = await res.json();
    } catch (e) {
      data = null;
    }
    
    if (!res.ok || (data && data.success === false)) {
      throw new APIError(
        data?.error || `HTTP ${res.status}`, 
        data?.error_code || 'UNKNOWN',
        data
      );
    }
    return data;
  },

  analyze(repoUrl, forceRefresh = false) {
    return this._fetch('/api/analyze', { repo_url: repoUrl, force_refresh: forceRefresh });
  },

  query(repoUrl, question) {
    return this._fetch('/api/query', { repo_url: repoUrl, question: question });
  },

  checkAlarm(repoUrl, codeSnippet) {
    return this._fetch('/api/alarm', { repo_url: repoUrl, code_snippet: codeSnippet });
  },

  onboard(repoUrl, featureDescription) {
    return this._fetch('/api/onboard', { repo_url: repoUrl, feature_description: featureDescription });
  }
};