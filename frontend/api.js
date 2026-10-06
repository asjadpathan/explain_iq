/**
 * Explain IQ Studio — Microservice API Client
 * ===========================================
 * Connects to the FastAPI backend with flexible base URL resolution.
 * Supports running natively from FastAPI (same origin) or Vercel static deployments.
 */

class ExplainIQApi {
  constructor() {
    this.STORAGE_KEY = 'explain_iq_backend_url';
    this.defaultLocalUrl = 'http://localhost:8000';
    this.baseUrl = this.resolveInitialBaseUrl();
  }

  /**
   * Determine starting backend URL based on host environment & localStorage.
   */
  resolveInitialBaseUrl() {
    const saved = localStorage.getItem(this.STORAGE_KEY);
    if (saved) {
      return this.cleanUrl(saved);
    }

    // If served on port 8000 or same host as backend, default to current origin
    if (window.location.port === '8000') {
      return window.location.origin;
    }

    // Default to local FastAPI address (can be changed via UI for Vercel)
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
