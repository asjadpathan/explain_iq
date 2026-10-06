/**
 * Explain IQ Studio — Main Application Controller
 * ===============================================
 * Orchestrates user inputs, real-time generation pipeline monitoring,
 * telemetry health checks, Vercel backend configuration, and library history.
 */

document.addEventListener('DOMContentLoaded', () => {
  const app = new ExplainIQStudio();
  app.init();
});

class ExplainIQStudio {
  constructor() {
    this.currentJobId = null;
    this.pollingTimer = null;
    this.elapsedTimer = null;
    this.generationStartTime = null;
    this.recentJobs = [];
    this.activeFilter = 'all';

    // DOM Elements - Navigation & Telemetry
    this.statusDot = document.getElementById('status-dot');
    this.statusText = document.getElementById('status-text');
    this.telemetryActiveJobs = document.getElementById('telemetry-active-jobs');
    this.telemetryVideosStored = document.getElementById('telemetry-videos-stored');
    this.libraryCountBadge = document.getElementById('library-count-badge');

    // DOM Elements - Form & Creator
    this.form = document.getElementById('video-generation-form');
    this.conceptInput = document.getElementById('concept-input');
    this.charCounter = document.getElementById('concept-char-count');
    this.audienceInput = document.getElementById('target-audience-val');
    this.voiceSelect = document.getElementById('voice-select');
    this.btnPreviewVoice = document.getElementById('btn-preview-voice');
    this.btnSubmit = document.getElementById('btn-generate-video');
    this.btnSubmitText = document.getElementById('btn-generate-text');

    // DOM Elements - Monitor HUD
    this.monitorCard = document.getElementById('generation-monitor-card');
    this.cinemaCard = document.getElementById('cinema-player-card');
    this.monitorTitle = document.getElementById('monitor-job-title');
    this.monitorJobId = document.getElementById('monitor-job-id');
    this.monitorAudience = document.getElementById('monitor-audience-tag');
    this.monitorElapsed = document.getElementById('monitor-elapsed-timer');
    this.progressBar = document.getElementById('pipeline-progress-bar');
    this.progressPct = document.getElementById('monitor-progress-pct');
    this.stageDescription = document.getElementById('monitor-stage-description');
    this.terminalContent = document.getElementById('terminal-log-content');
    this.stepSubQueued = document.getElementById('step-sub-queued');

    // Stepper Nodes
    this.nodes = {
      queued: document.getElementById('step-node-queued'),
      storyboarding: document.getElementById('step-node-storyboard'),
      generating_audio: document.getElementById('step-node-audio'),
      generating_visuals: document.getElementById('step-node-visuals'),
      assembling: document.getElementById('step-node-assembly')
    };

    // History & Library
    this.historyContainer = document.getElementById('history-list-container');
    this.historySearch = document.getElementById('history-search-input');
    this.btnRefreshHistory = document.getElementById('btn-refresh-history');

    // Settings Modal (Vercel Backend URL)
    this.settingsModal = document.getElementById('settings-modal');
    this.btnOpenSettings = document.getElementById('btn-open-settings');
    this.btnCloseSettings = document.getElementById('btn-close-settings');
    this.backendUrlInput = document.getElementById('backend-url-input');
    this.btnSaveSettings = document.getElementById('btn-save-settings');
    this.btnTestConnection = document.getElementById('btn-test-connection');
    this.testResultBox = document.getElementById('connection-test-result');
    this.testIcon = document.getElementById('test-icon');
    this.testText = document.getElementById('test-text');
    this.presetLocalBtn = document.getElementById('preset-local-url');
    this.presetOriginBtn = document.getElementById('preset-same-origin');
  }

  init() {
    this.bindNavigation();
    this.bindFormInteractions();
    this.bindSettingsModal();
    this.bindHistoryEvents();

    // Initial Telemetry & History Fetch
    this.updateTelemetry();
    this.refreshHistory();

    // Start 15s Heartbeat
    setInterval(() => this.updateTelemetry(), 15000);
  }

  /* ── 1. Telemetry & Microservice Health ────────────────────────── */

  async updateTelemetry() {
    try {
      const data = await window.api.checkHealth();
      this.statusDot.className = 'status-dot online';
      this.statusText.textContent = 'Engine Online';
      if (this.telemetryActiveJobs) {
        this.telemetryActiveJobs.textContent = data.active_jobs ?? 0;
      }
      if (this.telemetryVideosStored) {
        this.telemetryVideosStored.textContent = data.completed_videos_stored ?? 0;
      }
    } catch (err) {
      this.statusDot.className = 'status-dot offline';
      this.statusText.textContent = 'Engine Offline';
      console.warn('Telemetry check failed:', err.message);
    }
  }

  /* ── 2. Navigation & Tabs ──────────────────────────────────────── */

  bindNavigation() {
    const tabButtons = document.querySelectorAll('.pane-tab');
    tabButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const targetId = btn.dataset.tab;
        tabButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        document.querySelectorAll('.tab-view').forEach(view => {
          view.classList.remove('active');
        });
        const targetView = document.getElementById(targetId);
        if (targetView) targetView.classList.add('active');
      });
    });
  }

  /* ── 3. Form & Creator Controls ────────────────────────────────── */

  bindFormInteractions() {
    // Character Counter
    this.conceptInput.addEventListener('input', () => {
      const len = this.conceptInput.value.length;
      this.charCounter.textContent = `${len}/500`;
    });

    // Preset Prompt Chips
    document.querySelectorAll('.preset-chip[data-concept]').forEach(chip => {
      chip.addEventListener('click', () => {
        this.conceptInput.value = chip.dataset.concept;
        this.conceptInput.dispatchEvent(new Event('input'));
        this.conceptInput.focus();
      });
    });

    // Audience Segmented Control
    const audienceButtons = document.querySelectorAll('.segment-btn');
    audienceButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        audienceButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.audienceInput.value = btn.dataset.value;
      });
    });

    // Duration Mode Cards
    const durationCards = document.querySelectorAll('.duration-card');
    durationCards.forEach(card => {
      card.addEventListener('click', () => {
        durationCards.forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
      });
    });

    // Voice Audition (Web Speech API Sample)
    this.btnPreviewVoice.addEventListener('click', () => {
      this.previewSelectedVoice();
    });

    // Form Submission
    this.form.addEventListener('submit', (e) => {
      e.preventDefault();
      this.handleFormSubmit();
    });
  }

  previewSelectedVoice() {
    const voiceVal = this.voiceSelect.value;
    const sampleText = "Welcome to Explain I Q. Here is a sample of this voice for your explainer video.";

    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(sampleText);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;

      // Find matching voice if available in browser
      const voices = window.speechSynthesis.getVoices();
      const lang = voiceVal.startsWith('en-GB') ? 'en-GB' : (voiceVal.startsWith('en-AU') ? 'en-AU' : 'en-US');
      const matched = voices.find(v => v.lang === lang);
      if (matched) utterance.voice = matched;

      window.speechSynthesis.speak(utterance);
      this.showToast(`Auditioning ${voiceVal}...`, 'info');
    } else {
      this.showToast('Speech preview not supported in this browser.', 'info');
    }
  }

  /* ── 4. Generation Pipeline Monitoring ─────────────────────────── */

  async handleFormSubmit() {
    const concept = this.conceptInput.value.trim();
    if (!concept) {
      this.showToast('Please enter an educational concept or topic.', 'error');
      return;
    }

    const durationMode = document.querySelector('input[name="duration_mode"]:checked')?.value || 'standard';
    const audience = this.audienceInput.value || 'high school students';
    const voice = this.voiceSelect.value || 'en-US-AriaNeural';
    const includeMusic = document.getElementById('include-music-toggle').checked;
    const webhookUrl = document.getElementById('webhook-url-input')?.value.trim() || null;

    const payload = {
      concept,
      target_audience: audience,
      duration_mode: durationMode,
      voice,
      include_music: includeMusic,
      webhook_url: webhookUrl || undefined
    };

    // Set UI to loading state
    this.setSubmitLoading(true);

    try {
      const response = await window.api.createJob(payload);
      this.currentJobId = response.job_id;

      this.showToast('Video job enqueued! Tracking generation...', 'success');
      this.startPipelineMonitoring(response.job_id, concept, audience, response.queue_position);

    } catch (err) {
      this.showToast(`Submission failed: ${err.message}`, 'error');
      this.setSubmitLoading(false);
    }
  }

  setSubmitLoading(isLoading) {
    if (isLoading) {
      this.btnSubmit.disabled = true;
      this.btnSubmit.classList.add('loading');
      this.btnSubmitText.textContent = 'Submitting Job...';
    } else {
      this.btnSubmit.disabled = false;
      this.btnSubmit.classList.remove('loading');
      this.btnSubmitText.textContent = 'Generate 1080p Video';
    }
  }

  startPipelineMonitoring(jobId, concept, audience, queuePos = 1) {
    // Show Monitor HUD, Hide Cinema Player while rendering
    this.monitorCard.style.display = 'flex';
    this.cinemaCard.style.display = 'none';

    // Update Header Metadata
    this.monitorTitle.textContent = concept;
    this.monitorJobId.textContent = `Job: ${jobId.slice(0, 8)}...`;
    this.monitorAudience.textContent = `Audience: ${audience}`;
    this.stepSubQueued.textContent = `Pos #${queuePos}`;

    // Reset Progress HUD
    this.progressBar.style.width = '5%';
    this.progressPct.textContent = '5%';
    this.stageDescription.textContent = 'Registered in worker queue...';

    // Reset Terminal Box
    this.terminalContent.innerHTML = '';
    this.addLog(`[00:00] Job registered (ID: ${jobId.slice(0, 8)}). Semaphore capacity check.`);

    // Reset Stepper Nodes
    Object.values(this.nodes).forEach(node => {
      node.classList.remove('active', 'completed');
    });
    this.nodes.queued.classList.add('active');

    // Start Stopwatch Timer
    this.generationStartTime = Date.now();
    this.startStopwatch();

    // Start Polling Engine
    if (this.pollingTimer) clearInterval(this.pollingTimer);
    this.pollingTimer = setInterval(() => this.pollProgress(), 2200);
  }

  startStopwatch() {
    if (this.elapsedTimer) clearInterval(this.elapsedTimer);
    this.elapsedTimer = setInterval(() => {
      const elapsedSec = Math.floor((Date.now() - this.generationStartTime) / 1000);
      const mins = Math.floor(elapsedSec / 60).toString().padStart(2, '0');
      const secs = (elapsedSec % 60).toString().padStart(2, '0');
      this.monitorElapsed.textContent = `${mins}:${secs}`;
    }, 1000);
  }

  stopStopwatch() {
    if (this.elapsedTimer) {
      clearInterval(this.elapsedTimer);
      this.elapsedTimer = null;
    }
  }

  addLog(message) {
    const elapsedSec = Math.floor((Date.now() - (this.generationStartTime || Date.now())) / 1000);
    const mins = Math.floor(elapsedSec / 60).toString().padStart(2, '0');
    const secs = (elapsedSec % 60).toString().padStart(2, '0');

    const line = document.createElement('div');
    line.className = 'log-line';
    line.innerHTML = `<span class="log-time">[${mins}:${secs}]</span> ${this.escapeHTML(message)}`;
    this.terminalContent.appendChild(line);
    this.terminalContent.scrollTop = this.terminalContent.scrollHeight;
  }

  async pollProgress() {
    if (!this.currentJobId) return;

    try {
      const job = await window.api.getJobStatus(this.currentJobId);

      // Update progress bar
      const pct = Math.max(5, Math.min(100, job.progress_pct || 0));
      this.progressBar.style.width = `${pct}%`;
      this.progressPct.textContent = `${pct}%`;
      this.stageDescription.textContent = job.current_stage || 'Processing...';

      // Update Stepper Stages
      this.updateStepper(job.status, job.queue_position);

      // Check Terminal Completion or Failure
      if (job.status === 'completed') {
        this.handleGenerationSuccess(job);
      } else if (job.status === 'failed') {
        this.handleGenerationFailure(job);
      } else {
        // Log stage update if changed
        if (this.lastStageLog !== job.current_stage) {
          this.addLog(job.current_stage);
          this.lastStageLog = job.current_stage;
        }
      }

    } catch (err) {
      console.warn('Status polling error:', err);
    }
  }

  updateStepper(status, queuePos) {
    const stages = ['queued', 'storyboarding', 'generating_audio', 'generating_visuals', 'assembling', 'completed'];
    const currentIdx = stages.indexOf(status);

    if (queuePos && queuePos > 0) {
      this.stepSubQueued.textContent = `Pos #${queuePos}`;
    }

    stages.slice(0, 5).forEach((key, idx) => {
      const node = this.nodes[key];
      if (!node) return;

      if (currentIdx > idx || status === 'completed') {
        node.classList.remove('active');
        node.classList.add('completed');
      } else if (currentIdx === idx) {
        node.classList.add('active');
        node.classList.remove('completed');
      } else {
        node.classList.remove('active', 'completed');
      }
    });
  }

  handleGenerationSuccess(job) {
    clearInterval(this.pollingTimer);
    this.pollingTimer = null;
    this.stopStopwatch();
    this.setSubmitLoading(false);

    this.addLog('✅ Pipeline completed! 1080p MP4 assembled and subtitles ready.');
    this.showToast('🎉 Explainer video generated successfully!', 'success');

    // Switch view to Cinema Player after brief animation delay
    setTimeout(() => {
      this.monitorCard.style.display = 'none';
      this.cinemaCard.style.display = 'flex';
      window.player.loadVideo(job);
      this.refreshHistory();
      this.updateTelemetry();
    }, 1200);
  }

  handleGenerationFailure(job) {
    clearInterval(this.pollingTimer);
    this.pollingTimer = null;
    this.stopStopwatch();
    this.setSubmitLoading(false);

    const errorMsg = job.error || 'Generation pipeline failed.';
    this.addLog(`❌ Error: ${errorMsg}`);
    this.showToast(`Generation failed: ${errorMsg}`, 'error');
  }

  /* ── 5. Job History Library ────────────────────────────────────── */

  bindHistoryEvents() {
    this.btnRefreshHistory.addEventListener('click', () => this.refreshHistory());

    this.historySearch.addEventListener('input', () => {
      this.renderHistoryList();
    });

    const filterPills = document.querySelectorAll('.filter-pill');
    filterPills.forEach(pill => {
      pill.addEventListener('click', () => {
        filterPills.forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        this.activeFilter = pill.dataset.filter;
        this.renderHistoryList();
      });
    });
  }

  async refreshHistory() {
    try {
      const jobs = await window.api.getRecentJobs(40);
      this.recentJobs = Array.isArray(jobs) ? jobs : [];
      if (this.libraryCountBadge) {
        this.libraryCountBadge.textContent = this.recentJobs.length;
      }
      this.renderHistoryList();
    } catch (err) {
      console.warn('Could not refresh job history:', err);
    }
  }

  renderHistoryList() {
    const searchQuery = (this.historySearch.value || '').toLowerCase().trim();
    this.historyContainer.innerHTML = '';

    const filtered = this.recentJobs.filter(job => {
      // Status filter
      if (this.activeFilter === 'completed' && job.status !== 'completed') return false;
      if (this.activeFilter === 'active' && (job.status === 'completed' || job.status === 'failed')) return false;

      // Text search
      if (searchQuery) {
        const titleMatch = (job.concept || '').toLowerCase().includes(searchQuery);
        const audienceMatch = (job.target_audience || '').toLowerCase().includes(searchQuery);
        return titleMatch || audienceMatch;
      }
      return true;
    });

    if (filtered.length === 0) {
      this.historyContainer.innerHTML = `
        <div class="empty-state">
          <p>No matching videos found</p>
          <span>Try adjusting your search query or generate a new concept</span>
        </div>
      `;
      return;
    }

    filtered.forEach(job => {
      const card = document.createElement('div');
      card.className = `history-card ${this.currentJobId === job.job_id ? 'active' : ''}`;

      const durText = job.duration_seconds ? `${job.duration_seconds}s` : '--';
      const createdTime = this.formatDate(job.created_at);

      card.innerHTML = `
        <div class="history-card-header">
          <div class="history-card-title">${this.escapeHTML(job.concept || 'Educational Video')}</div>
          <span class="history-status-badge ${job.status}">${job.status}</span>
        </div>
        <div class="history-card-meta">
          <span>${this.escapeHTML(job.target_audience || 'General')}</span>
          <span>${durText} • ${createdTime}</span>
        </div>
      `;

      // Click card to play in studio
      card.addEventListener('click', () => {
        document.querySelectorAll('.history-card').forEach(c => c.classList.remove('active'));
        card.classList.add('active');

        // Show Cinema Player
        this.monitorCard.style.display = 'none';
        this.cinemaCard.style.display = 'flex';
        window.player.loadVideo(job);
      });

      this.historyContainer.appendChild(card);
    });
  }

  formatDate(isoString) {
    if (!isoString) return '';
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  }

  /* ── 6. Settings Modal (Vercel Backend Switcher) ───────────────── */

  bindSettingsModal() {
    this.btnOpenSettings.addEventListener('click', () => {
      this.backendUrlInput.value = window.api.getBaseUrl();
      this.testResultBox.style.display = 'none';
      this.settingsModal.style.display = 'flex';
    });

    this.btnCloseSettings.addEventListener('click', () => {
      this.settingsModal.style.display = 'none';
    });

    this.presetLocalBtn.addEventListener('click', () => {
      this.backendUrlInput.value = 'http://localhost:8000';
    });

    this.presetOriginBtn.addEventListener('click', () => {
      this.backendUrlInput.value = window.location.origin;
    });

    this.btnTestConnection.addEventListener('click', async () => {
      const testUrl = this.backendUrlInput.value.trim();
      this.testResultBox.style.display = 'flex';
      this.testResultBox.className = 'connection-test-result';
      this.testText.textContent = 'Pinging /health endpoint...';

      try {
        const result = await window.api.checkHealth(testUrl);
        this.testResultBox.className = 'connection-test-result success';
        this.testText.textContent = `Connected! Engine status: ${result.status} (${result.service})`;
      } catch (err) {
        this.testResultBox.className = 'connection-test-result error';
        this.testText.textContent = `Connection error: ${err.message}`;
      }
    });

    this.btnSaveSettings.addEventListener('click', () => {
      const newUrl = this.backendUrlInput.value.trim();
      window.api.setBaseUrl(newUrl);
      this.settingsModal.style.display = 'none';
      this.showToast(`Backend updated: ${newUrl}`, 'success');
      this.updateTelemetry();
      this.refreshHistory();
    });
  }

  /* ── 7. Utilities & Toasts ─────────────────────────────────────── */

  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(15px)';
      toast.style.transition = '0.3s ease-out';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  escapeHTML(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
}
