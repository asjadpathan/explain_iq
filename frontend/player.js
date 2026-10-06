/**
 * Explain IQ Studio — Cinema Player & Subtitle Controller
 * =======================================================
 * Manages 1080p video streaming, synchronized subtitle cues,
 * and click-to-seek transcript interaction.
 */

class StudioPlayer {
  constructor() {
    this.videoEl = document.getElementById('main-video-player');
    this.placeholderEl = document.getElementById('player-placeholder');
    this.conceptTitleEl = document.getElementById('player-concept-title');
    this.metaInfoEl = document.getElementById('player-meta-info');
    this.downloadVideoBtn = document.getElementById('btn-download-video');
    this.downloadSubtitlesBtn = document.getElementById('btn-download-subtitles');
    this.transcriptContainer = document.getElementById('transcript-body-container');

    this.currentCues = [];
    this.activeCueIndex = -1;

    this.bindEvents();
  }

  bindEvents() {
    if (!this.videoEl) return;

    // Track playback time to sync subtitle cues
    this.videoEl.addEventListener('timeupdate', () => {
      this.syncActiveSubtitle(this.videoEl.currentTime);
    });

    // Remove placeholder on video load
    this.videoEl.addEventListener('loadeddata', () => {
      if (this.placeholderEl) {
        this.placeholderEl.style.display = 'none';
      }
    });

    // Keyboard shortcuts for convenience
    window.addEventListener('keydown', (e) => {
      // Ignore if user is typing in form inputs
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
        return;
      }

      if (e.code === 'Space' && this.videoEl && this.videoEl.src) {
        e.preventDefault();
        if (this.videoEl.paused) {
          this.videoEl.play();
        } else {
          this.videoEl.pause();
        }
      }
    });
  }

  /**
   * Parse SRT format into structured timed cue objects.
   */
  parseSRT(srtContent) {
    if (!srtContent || !srtContent.trim()) return [];

    const lines = srtContent.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n');
    const cues = [];
    let currentCue = null;

    const timeRegex = /(\d{2}):(\d{2}):(\d{2})[,\.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,\.](\d{3})/;

    const toSeconds = (h, m, s, ms) => {
      return parseInt(h, 10) * 3600 + parseInt(m, 10) * 60 + parseInt(s, 10) + parseInt(ms, 10) / 1000;
    };

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) {
        if (currentCue && currentCue.text) {
          cues.push(currentCue);
          currentCue = null;
        }
        continue;
      }

      const match = timeRegex.exec(line);
      if (match) {
        const start = toSeconds(match[1], match[2], match[3], match[4]);
        const end = toSeconds(match[5], match[6], match[7], match[8]);
        currentCue = {
          id: cues.length + 1,
          start,
          end,
          text: ''
        };
      } else if (currentCue) {
        if (currentCue.text) {
          currentCue.text += ' ' + line;
        } else {
          currentCue.text = line;
        }
      }
    }

    if (currentCue && currentCue.text) {
      cues.push(currentCue);
    }

    return cues;
  }

  /**
   * Format seconds to mm:ss for display.
   */
  formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  /**
   * Render cue cards into the transcript DOM.
   */
  renderTranscript(cues) {
    this.currentCues = cues;
    this.activeCueIndex = -1;

    if (!this.transcriptContainer) return;
    this.transcriptContainer.innerHTML = '';

    if (!cues || cues.length === 0) {
      this.transcriptContainer.innerHTML = `
        <div class="transcript-empty">
          <span>No subtitle timestamps available for this video.</span>
        </div>
      `;
      return;
    }

    const fragment = document.createDocumentFragment();

    cues.forEach((cue, index) => {
      const cueEl = document.createElement('div');
      cueEl.className = 'transcript-cue';
      cueEl.id = `cue-${index}`;
      cueEl.dataset.index = index;

      cueEl.innerHTML = `
        <span class="cue-time">[${this.formatTime(cue.start)}]</span>
        <span class="cue-text">${this.escapeHTML(cue.text)}</span>
      `;

      // Click to seek video to start of cue
      cueEl.addEventListener('click', () => {
        if (this.videoEl) {
          this.videoEl.currentTime = cue.start;
          this.videoEl.play();
        }
      });

      fragment.appendChild(cueEl);
    });

    this.transcriptContainer.appendChild(fragment);
  }

  /**
   * Highlight current spoken cue and scroll smoothly into view.
   */
  syncActiveSubtitle(currentTime) {
    if (!this.currentCues || this.currentCues.length === 0) return;

    let foundIndex = -1;
    for (let i = 0; i < this.currentCues.length; i++) {
      const cue = this.currentCues[i];
      if (currentTime >= cue.start && currentTime <= cue.end) {
        foundIndex = i;
        break;
      }
    }

    if (foundIndex !== this.activeCueIndex) {
      // Remove old active
      if (this.activeCueIndex !== -1) {
        const oldEl = document.getElementById(`cue-${this.activeCueIndex}`);
        if (oldEl) oldEl.classList.remove('active');
      }

      // Set new active
      this.activeCueIndex = foundIndex;
      if (foundIndex !== -1) {
        const newEl = document.getElementById(`cue-${foundIndex}`);
        if (newEl) {
          newEl.classList.add('active');
          // Smooth scroll within transcript container
          newEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      }
    }
  }

  /**
   * Load and play a completed video job into the studio player.
   */
  async loadVideo(job) {
    if (!job || !this.videoEl) return;

    const videoUrl = window.api.getVideoDownloadUrl(job.job_id);
    const srtUrl = window.api.getSubtitlesDownloadUrl(job.job_id);

    // Update UI headers
    if (this.conceptTitleEl) {
      this.conceptTitleEl.textContent = job.concept || 'Educational Video';
    }

    if (this.metaInfoEl) {
      const dur = job.duration_seconds ? `${job.duration_seconds}s` : 'Full Length';
      const audience = job.target_audience || 'General Audience';
      this.metaInfoEl.textContent = `Duration: ${dur} • Audience: ${audience}`;
    }

    // Update download buttons
    if (this.downloadVideoBtn) {
      this.downloadVideoBtn.href = videoUrl;
      this.downloadVideoBtn.setAttribute('download', `explain_iq_${job.job_id.slice(0, 8)}.mp4`);
      this.downloadVideoBtn.style.display = 'inline-flex';
    }

    if (this.downloadSubtitlesBtn) {
      this.downloadSubtitlesBtn.href = srtUrl;
      this.downloadSubtitlesBtn.setAttribute('download', `explain_iq_${job.job_id.slice(0, 8)}.srt`);
      this.downloadSubtitlesBtn.style.display = 'inline-flex';
    }

    // Hide placeholder and load video source
    if (this.placeholderEl) {
      this.placeholderEl.style.display = 'none';
    }

    this.videoEl.src = videoUrl;
    this.videoEl.load();

    // Fetch and parse subtitles
    try {
      const srtText = await window.api.fetchSubtitlesText(job.job_id);
      if (srtText) {
        const cues = this.parseSRT(srtText);
        this.renderTranscript(cues);
      } else {
        this.renderTranscript([]);
      }
    } catch (err) {
      console.warn('Could not load subtitles:', err);
      this.renderTranscript([]);
    }
  }

  escapeHTML(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
}

// Global player instance
window.player = new StudioPlayer();
