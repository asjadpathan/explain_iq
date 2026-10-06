/**
 * Explain IQ Studio — Microservice API Client
 * ===========================================
 * Connects to the FastAPI backend.
 *
 * 🔧 PRODUCTION BACKEND URL CONFIGURATION:
 * When your Render backend is deployed, paste its URL here:
 * (e.g. const PRODUCTION_BACKEND_URL = "https://explain-iq.onrender.com";)
 */
const PRODUCTION_BACKEND_URL = "";

class ExplainIQApi {
  constructor() {
    this.STORAGE_KEY = 'explain_iq_backend_url';
    this.defaultLocalUrl = 'http://localhost:8000';
    this.baseUrl = this.resolveInitialBaseUrl();
  }

  /**
   * Determine starting backend URL silently without exposing any UI links.
   */
  resolveInitialBaseUrl() {
    // 1. Check for silent parameter: https://your-site.vercel.app?backend=https://your-render-url.onrender.com
    if (typeof window !== 'undefined' && window.location) {
      const params = new URLSearchParams(window.location.search);
      if (params.has('backend')) {
        const qUrl = this.cleanUrl(params.get('backend'));
        if (qUrl) {
          localStorage.setItem(this.STORAGE_KEY, qUrl);
          window.history.replaceState({}, document.title, window.location.pathname);
          return qUrl;
        }
      }
    }

    // 2. Check saved browser storage
    const saved = localStorage.getItem(this.STORAGE_KEY);
    if (saved) {
      return this.cleanUrl(saved);
    }

    // 3. Check Vercel environment variable (injected during build)
    const envBackendUrl = typeof window !== 'undefined' && window.__ENV && window.__ENV.BACKEND_URL;
    if (envBackendUrl && envBackendUrl.trim()) {
      return this.cleanUrl(envBackendUrl);
    }

    // 4. Check production constant if specified
    if (PRODUCTION_BACKEND_URL && PRODUCTION_BACKEND_URL.trim()) {
      return this.cleanUrl(PRODUCTION_BACKEND_URL);
    }

    // 4. Same origin (when served directly from FastAPI)
    if (window.location.port === '8000') {
      return window.location.origin;
    }

    // 5. Default local fallback
    return this.defaultLocalUrl;
  }

  cleanUrl(url) {
    if (!url) return '';
    return url.trim().replace(/\/+$/, '');
  }

  getBaseUrl() {
    return this.baseUrl;
  }

  setBaseUrl(newUrl) {
    this.baseUrl = this.cleanUrl(newUrl);
    localStorage.setItem(this.STORAGE_KEY, this.baseUrl);
  }

  /**
   * Ping /health endpoint to check server availability and queue metrics.
   */
  async checkHealth(overrideUrl = null) {
    const targetUrl = (overrideUrl ? this.cleanUrl(overrideUrl) : this.baseUrl) + '/health';
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 6000);

    try {
      const resp = await fetch(targetUrl, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
      }
      return await resp.json();
    } catch (err) {
      clearTimeout(timeoutId);
      throw err;
    }
  }

  /**
   * Submit a concept for video generation.
   * Expects: { concept, target_audience, duration_mode, voice, include_music, webhook_url }
   */
  async createJob(payload) {
    const targetUrl = `${this.baseUrl}/generate`;
    const resp = await fetch(targetUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!resp.ok) {
      let errorDetail = `HTTP ${resp.status}`;
      try {
        const errorJson = await resp.json();
        errorDetail = errorJson.detail || errorDetail;
      } catch (e) {
        // use default
      }
      throw new Error(errorDetail);
    }

    return await resp.json();
  }

  /**
   * Poll generation status of a specific job.
   */
  async getJobStatus(jobId) {
    const targetUrl = `${this.baseUrl}/status/${encodeURIComponent(jobId)}`;
    const resp = await fetch(targetUrl, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    });

    if (!resp.ok) {
      throw new Error(`Failed to fetch job status (HTTP ${resp.status})`);
    }

    return await resp.json();
  }

  /**
   * Retrieve recent video jobs from SQLite database.
   */
  async getRecentJobs(limit = 30) {
    const targetUrl = `${this.baseUrl}/jobs?limit=${limit}`;
    const resp = await fetch(targetUrl, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    });

    if (!resp.ok) {
      throw new Error(`Failed to fetch recent jobs (HTTP ${resp.status})`);
    }

    return await resp.json();
  }

  /**
   * Construct absolute URL for 1080p MP4 download/streaming.
   */
  getVideoDownloadUrl(jobId) {
    return `${this.baseUrl}/download/${encodeURIComponent(jobId)}`;
  }

  /**
   * Construct absolute URL for .srt subtitle download.
   */
  getSubtitlesDownloadUrl(jobId) {
    return `${this.baseUrl}/subtitles/${encodeURIComponent(jobId)}`;
  }

  /**
   * Fetch raw SRT text string for in-browser transcript parsing.
   */
  async fetchSubtitlesText(jobId) {
    try {
      const resp = await fetch(this.getSubtitlesDownloadUrl(jobId));
      if (!resp.ok) return null;
      return await resp.text();
    } catch (e) {
      console.warn(`Could not fetch SRT for job ${jobId}:`, e);
      return null;
    }
  }
}

// Global API instance
window.api = new ExplainIQApi();
