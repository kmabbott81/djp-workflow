/**
 * AI Orchestrator v0.1 - Premium Web UI
 * State management with Alpine.js
 */

document.addEventListener('alpine:init', () => {
  Alpine.store('app', {
    // State
    prompt: '',
    plan: null,
    isPlanning: false,
    planError: null,
    isExecuting: false,
    executeError: null,
    jobIds: [],
    jobs: [],
    selectedJob: null,
    isLoadingJobs: false,
    jobsError: null,
    pollingIntervals: {},
    toasts: [],

    // Settings
    settings: {
      apiKey: localStorage.getItem('api_key') || '',
      autoRefresh: true
    },

    // Initialize
    init() {
      this.loadPromptFromStorage();
      this.loadJobs();

      // Auto-refresh jobs every 5 seconds if enabled
      setInterval(() => {
        if (this.settings.autoRefresh && this.jobs.length > 0) {
          this.loadJobs(true); // Silent refresh
        }
      }, 5000);
    },

    // === Planning ===
    async planPrompt() {
      if (!this.prompt.trim()) {
        this.showToast('Please enter a prompt', 'error');
        return;
      }

      this.isPlanning = true;
      this.planError = null;
      this.plan = null;

      // Debounce - prevent double-click
      await new Promise(resolve => setTimeout(resolve, 100));

      try {
        const response = await fetch('/ai/plan2', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(this.settings.apiKey && { 'Authorization': `Bearer ${this.settings.apiKey}` })
          },
          body: JSON.stringify({ prompt: this.prompt })
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();
        this.plan = data.plan;
        this.savePromptToStorage();
        this.showToast('Plan generated successfully', 'success');

        // Focus execute button after planning
        setTimeout(() => {
          const executeBtn = document.querySelector('#execute-btn');
          if (executeBtn) executeBtn.focus();
        }, 100);
      } catch (error) {
        this.planError = error.message;
        this.showToast(`Planning failed: ${error.message}`, 'error');
      } finally {
        this.isPlanning = false;
      }
    },

    // === Execution ===
    async executePlan() {
      if (!this.plan || !this.plan.actions || this.plan.actions.length === 0) {
        this.showToast('No plan to execute', 'error');
        return;
      }

      this.isExecuting = true;
      this.executeError = null;
      this.jobIds = [];

      try {
        const response = await fetch('/ai/execute', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(this.settings.apiKey && { 'Authorization': `Bearer ${this.settings.apiKey}` })
          },
          body: JSON.stringify({
            actions: this.plan.actions
          })
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();
        this.jobIds = data.job_ids || [];

        if (this.jobIds.length === 0) {
          this.showToast('No jobs created (possibly duplicate request)', 'info');
        } else {
          this.showToast(`${this.jobIds.length} job(s) queued`, 'success');

          // Start polling for each job
          this.jobIds.forEach(jobId => this.startPolling(jobId));

          // Refresh jobs list
          await this.loadJobs();
        }
      } catch (error) {
        this.executeError = error.message;
        this.showToast(`Execution failed: ${error.message}`, 'error');
      } finally {
        this.isExecuting = false;
      }
    },

    // === Job Polling ===
    startPolling(jobId) {
      // Don't poll if already polling
      if (this.pollingIntervals[jobId]) return;

      const poll = async () => {
        try {
          const response = await fetch(`/ai/jobs/${jobId}`, {
            headers: {
              ...(this.settings.apiKey && { 'Authorization': `Bearer ${this.settings.apiKey}` })
            }
          });

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
          }

          const job = await response.json();

          // Update job in list
          const index = this.jobs.findIndex(j => j.job_id === jobId);
          if (index >= 0) {
            this.jobs[index] = job;
          } else {
            this.jobs.unshift(job);
          }

          // Update selected job if viewing
          if (this.selectedJob && this.selectedJob.job_id === jobId) {
            this.selectedJob = job;
          }

          // Stop polling if terminal state
          if (job.status === 'completed' || job.status === 'error') {
            this.stopPolling(jobId);

            if (job.status === 'completed') {
              this.showToast(`Job ${jobId.slice(0, 8)} completed`, 'success');
            } else {
              this.showToast(`Job ${jobId.slice(0, 8)} failed`, 'error');
            }
          }
        } catch (error) {
          console.error(`Polling error for job ${jobId}:`, error);
          // Don't stop polling on error - might be transient
        }
      };

      // Poll immediately, then every 2 seconds
      poll();
      this.pollingIntervals[jobId] = setInterval(poll, 2000);
    },

    stopPolling(jobId) {
      if (this.pollingIntervals[jobId]) {
        clearInterval(this.pollingIntervals[jobId]);
        delete this.pollingIntervals[jobId];
      }
    },

    // === Jobs List ===
    async loadJobs(silent = false) {
      if (!silent) {
        this.isLoadingJobs = true;
        this.jobsError = null;
      }

      try {
        const response = await fetch('/ai/jobs?limit=50', {
          headers: {
            ...(this.settings.apiKey && { 'Authorization': `Bearer ${this.settings.apiKey}` })
          }
        });

        if (!response.ok) {
          // If endpoint doesn't exist yet, silently fail
          if (response.status === 404) {
            if (!silent) {
              this.jobsError = 'Jobs list endpoint not yet available';
            }
            return;
          }
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        this.jobs = data.jobs || data.items || [];
      } catch (error) {
        if (!silent) {
          this.jobsError = error.message;
          console.error('Failed to load jobs:', error);
        }
      } finally {
        this.isLoadingJobs = false;
      }
    },

    selectJob(job) {
      this.selectedJob = job;

      // Start polling if not terminal
      if (job.status !== 'completed' && job.status !== 'error') {
        this.startPolling(job.job_id);
      }
    },

    closeJobDrawer() {
      this.selectedJob = null;
    },

    // === Utilities ===
    copyToClipboard(text) {
      navigator.clipboard.writeText(text).then(() => {
        this.showToast('Copied to clipboard', 'success');
      }).catch(() => {
        this.showToast('Failed to copy', 'error');
      });
    },

    downloadJSON(obj, filename) {
      const blob = new Blob([JSON.stringify(obj, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      this.showToast('Download started', 'success');
    },

    formatDate(isoString) {
      if (!isoString) return 'N/A';
      const date = new Date(isoString);
      return new Intl.DateTimeFormat('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }).format(date);
    },

    formatDuration(ms) {
      if (!ms) return 'N/A';
      if (ms < 1000) return `${ms}ms`;
      if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
      return `${(ms / 60000).toFixed(1)}m`;
    },

    getStatusBadgeClass(status) {
      const map = {
        'pending': 'badge-pending',
        'running': 'badge-running',
        'completed': 'badge-completed',
        'error': 'badge-error'
      };
      return map[status] || 'badge-pending';
    },

    // === Toast Notifications ===
    showToast(message, type = 'info') {
      const id = Date.now();
      const toast = { id, message, type };
      this.toasts.push(toast);

      // Auto-dismiss after 5 seconds
      setTimeout(() => {
        this.dismissToast(id);
      }, 5000);
    },

    dismissToast(id) {
      const index = this.toasts.findIndex(t => t.id === id);
      if (index >= 0) {
        this.toasts.splice(index, 1);
      }
    },

    // === Storage ===
    savePromptToStorage() {
      try {
        localStorage.setItem('last_prompt', this.prompt);
        localStorage.setItem('last_plan', JSON.stringify(this.plan));
      } catch (error) {
        console.warn('Failed to save to localStorage:', error);
      }
    },

    loadPromptFromStorage() {
      try {
        this.prompt = localStorage.getItem('last_prompt') || '';
        const savedPlan = localStorage.getItem('last_plan');
        if (savedPlan) {
          this.plan = JSON.parse(savedPlan);
        }
      } catch (error) {
        console.warn('Failed to load from localStorage:', error);
      }
    },

    clearHistory() {
      if (confirm('Clear all history? This cannot be undone.')) {
        localStorage.removeItem('last_prompt');
        localStorage.removeItem('last_plan');
        this.prompt = '';
        this.plan = null;
        this.showToast('History cleared', 'info');
      }
    },

    // === Keyboard Shortcuts ===
    handleKeydown(event) {
      // Cmd/Ctrl + Enter to plan
      if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
        event.preventDefault();
        if (!this.isPlanning && this.prompt.trim()) {
          this.planPrompt();
        }
      }

      // Escape to close drawer
      if (event.key === 'Escape' && this.selectedJob) {
        this.closeJobDrawer();
      }
    }
  });
});

// Register keyboard shortcuts
document.addEventListener('keydown', (e) => {
  const store = Alpine.store('app');
  if (store) {
    store.handleKeydown(e);
  }
});
