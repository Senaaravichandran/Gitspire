class APIError extends Error {
  constructor(message, code, raw) {
    super(message);
    this.code = code;
    this.raw = raw;
  }
}

const ApiRuntime = {
  baseUrl: null,
  resolutionPromise: null,

  normalizeBaseUrl(value) {
    if (!value) return null;
    return String(value).trim().replace(/\/+$/, '').replace(/\/api$/, '');
  },

  formatHost(host) {
    if (!host) return '127.0.0.1';
    if (host.includes(':') && !host.startsWith('[')) return `[${host}]`;
    return host;
  },

  isLocalhost() {
    const host = window.location.hostname;
    return host === 'localhost' || host === '127.0.0.1' || host === '::1';
  },

  getConfiguredBaseUrl() {
    try {
      const url = new URL(window.location.href);
      const fromQuery = url.searchParams.get('apiBase');
      if (fromQuery) return this.normalizeBaseUrl(fromQuery);
    } catch (error) {
      // Ignore malformed browser URL state.
    }

    const fromWindow = this.normalizeBaseUrl(window.GITSPIRE_API_BASE_URL);
    if (fromWindow) return fromWindow;

    try {
      return this.normalizeBaseUrl(window.localStorage.getItem('gitspire_api_base_url'));
    } catch (error) {
      return null;
    }
  },

  buildCandidateBaseUrls() {
    const candidates = [];
    const configured = this.getConfiguredBaseUrl();
    if (configured) candidates.push(configured);

    if (window.location.origin && window.location.origin !== 'null') {
      candidates.push(this.normalizeBaseUrl(window.location.origin));
    }

    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
    const hostOptions = new Set();
    if (window.location.hostname) {
      hostOptions.add(window.location.hostname);
    }

    if (this.isLocalhost() || window.location.protocol === 'file:') {
      hostOptions.add('127.0.0.1');
      hostOptions.add('localhost');
    }

    for (const host of hostOptions) {
      const formattedHost = this.formatHost(host);
      candidates.push(`${protocol}//${formattedHost}:8000`);
      candidates.push(`${protocol}//${formattedHost}:8001`);
    }

    return [...new Set(candidates.filter(Boolean))];
  },

  async probe(baseUrl) {
    try {
      const response = await fetch(new URL('/api/meta', `${baseUrl}/`).toString(), {
        method: 'GET'
      });
      if (!response.ok) return null;

      let meta = null;
      try {
        meta = await response.json();
      } catch (error) {
        meta = null;
      }

      return {
        apiBaseUrl: this.normalizeBaseUrl(meta?.api_base_url) || this.normalizeBaseUrl(baseUrl),
        frontendUrl: this.normalizeBaseUrl(meta?.frontend_url)
      };
    } catch (error) {
      return null;
    }
  },

  async resolveBaseUrl() {
    if (this.baseUrl) return this.baseUrl;
    if (this.resolutionPromise) return this.resolutionPromise;

    this.resolutionPromise = (async () => {
      const candidates = this.buildCandidateBaseUrls();
      for (const candidate of candidates) {
        const meta = await this.probe(candidate);
        if (meta?.apiBaseUrl) {
          this.baseUrl = meta.apiBaseUrl;
          if (meta.frontendUrl) {
            window.GITSPIRE_FRONTEND_URL = meta.frontendUrl;
          }
          return this.baseUrl;
        }
      }

      const configured = this.getConfiguredBaseUrl();
      const origin = this.normalizeBaseUrl(window.location.origin);
      const localFallback = (this.isLocalhost() || window.location.protocol === 'file:')
        ? 'http://127.0.0.1:8000'
        : null;
      this.baseUrl = configured || origin || localFallback;
      return this.baseUrl;
    })();

    return this.resolutionPromise;
  },

  async buildApiUrl(path) {
    const baseUrl = await this.resolveBaseUrl();
    return new URL(path, `${baseUrl}/`).toString();
  }
};

const API = {
  async _request(path, options = {}) {
    const url = await ApiRuntime.buildApiUrl(path);

    try {
      return await fetch(url, options);
    } catch (error) {
      if (error && error.name === 'AbortError') {
        throw new APIError('Request timed out. Please try again.', 'TIMEOUT', { url });
      }
      throw new APIError(
        'Unable to reach the GitSpire API. Set ?apiBase=https://your-api or define window.GITSPIRE_API_BASE_URL.',
        'NETWORK_ERROR',
        { detail: error.message, url }
      );
    }
  },

  async _fetch(url, body, options = {}) {
    const timeoutMs = options.timeoutMs ?? 240000;
    const controller = timeoutMs ? new AbortController() : null;
    const timeoutId = controller ? setTimeout(() => controller.abort(), timeoutMs) : null;

    const res = await this._request(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller ? controller.signal : undefined
    });

    if (timeoutId) clearTimeout(timeoutId);
    
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

  async getMeta() {
    const res = await this._request('/api/meta', { method: 'GET' });

    let data;
    try {
      data = await res.json();
    } catch (error) {
      data = null;
    }

    if (!res.ok) {
      throw new APIError(
        data?.error || `HTTP ${res.status}`,
        data?.error_code || 'UNKNOWN',
        data
      );
    }

    const apiBaseUrl = ApiRuntime.normalizeBaseUrl(data?.api_base_url);
    if (apiBaseUrl) {
      ApiRuntime.baseUrl = apiBaseUrl;
    }

    return data;
  },

  analyze(repoUrl, forceRefresh = false) {
    return this._fetch('/api/analyze', { repo_url: repoUrl, force_refresh: forceRefresh }, { timeoutMs: 240000 });
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