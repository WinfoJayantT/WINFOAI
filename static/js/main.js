
    // ── Global Context & Sidebar Toggle Control ──
    window.activeAIContext = null;

    window.toggleSidebar = function() {
      const sidebar = document.querySelector('aside');
      if (sidebar) {
        sidebar.classList.toggle('sidebar-collapsed');
      }
    };
    // --- Theme Toggle Logic ---
    const themeToggleBtn = document.getElementById('theme-toggle');
    const themeToggleDarkIcon = document.getElementById('theme-toggle-dark-icon');
    const themeToggleLightIcon = document.getElementById('theme-toggle-light-icon');

    // Change the icons inside the button based on previous settings
    if (localStorage.getItem('theme') === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      themeToggleLightIcon.classList.remove('hidden');
    } else {
      themeToggleDarkIcon.classList.remove('hidden');
    }

    themeToggleBtn.addEventListener('click', function () {
      // toggle icons inside button
      themeToggleDarkIcon.classList.toggle('hidden');
      themeToggleLightIcon.classList.toggle('hidden');

      // if set via local storage previously
      if (localStorage.getItem('theme')) {
        if (localStorage.getItem('theme') === 'light') {
          document.documentElement.classList.add('dark');
          localStorage.setItem('theme', 'dark');
        } else {
          document.documentElement.classList.remove('dark');
          localStorage.setItem('theme', 'light');
        }
        // if NOT set via local storage previously
      } else {
        if (document.documentElement.classList.contains('dark')) {
          document.documentElement.classList.remove('dark');
          localStorage.setItem('theme', 'light');
        } else {
          document.documentElement.classList.add('dark');
          localStorage.setItem('theme', 'dark');
        }
      }
    });
    // --- End Theme Toggle Logic ---

    // --- Low Memory Mode Toggle Logic ---
    const lowMemoryToggleBtn = document.getElementById('low-memory-toggle');
    const lowMemoryText = document.getElementById('low-memory-text');
    
    window.lowMemoryMode = localStorage.getItem('lowMemoryMode') === 'true';
    if (window.lowMemoryMode) {
      lowMemoryText.textContent = 'Low Mem Mode';
      lowMemoryToggleBtn.classList.add('text-ember-red');
    }

    lowMemoryToggleBtn.addEventListener('click', function () {
      window.lowMemoryMode = !window.lowMemoryMode;
      localStorage.setItem('lowMemoryMode', window.lowMemoryMode);
      
      if (window.lowMemoryMode) {
        lowMemoryText.textContent = 'Low Mem Mode';
        lowMemoryToggleBtn.classList.add('text-ember-red');
      } else {
        lowMemoryText.textContent = 'Fast Mode';
        lowMemoryToggleBtn.classList.remove('text-ember-red');
      }
    });

    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatFeed = document.getElementById('chat-feed');
    const emptyState = document.getElementById('empty-state');
    const loadingIndicator = document.getElementById('loading-indicator');
    const sendBtn = document.getElementById('send-btn');
    const chatContainer = document.getElementById('chat-container');

    window.submitSuggested = function(text) {
      userInput.value = text;
      chatForm.dispatchEvent(new Event('submit'));
    }

    // ── Multi-Session Conversation Manager (ChatGPT / Claude Style) ──
    const SESSIONS_STORAGE_KEY = 'winfotest_sessions_v4';
    const ACTIVE_SESSION_KEY = 'winfotest_active_session_id';

    let currentSessionId = localStorage.getItem(ACTIVE_SESSION_KEY) || 'session-' + Date.now();

    function getAllSessions() {
      try {
        const data = localStorage.getItem(SESSIONS_STORAGE_KEY);
        return data ? JSON.parse(data) : {};
      } catch (e) {
        return {};
      }
    }

    function saveSessions(sessions) {
      try {
        localStorage.setItem(SESSIONS_STORAGE_KEY, JSON.stringify(sessions));
      } catch (e) {}
    }

    function renderSidebarConversations() {
      const listEl = document.getElementById('conversation-history-list');
      const badgeEl = document.getElementById('session-count-badge');
      if (!listEl) return;

      const sessions = getAllSessions();
      const sessionKeys = Object.keys(sessions).sort((a, b) => (sessions[b].updatedAt || 0) - (sessions[a].updatedAt || 0));

      if (badgeEl) badgeEl.innerText = sessionKeys.length;

      if (sessionKeys.length === 0) {
        listEl.innerHTML = `<div class="text-[11px] font-geist text-graphite text-center py-6">No previous chats yet. Start a new session above!</div>`;
        return;
      }

      listEl.innerHTML = sessionKeys.map(key => {
        const sess = sessions[key];
        const isActive = (key === currentSessionId);
        const activeClass = isActive 
          ? 'bg-[#181818] border-l-2 border-white text-white' 
          : 'bg-[#090909] text-[#a0a4a1] hover:bg-[#141414] hover:text-white border-l-2 border-transparent';
        
        const title = escapeHtml(sess.title || 'Untitled Conversation');
        const dateStr = sess.updatedAt ? new Date(sess.updatedAt).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '';

        return `
          <div onclick="switchSession('${key}')" 
            class="group p-2.5 rounded-inputs ${activeClass} transition-all cursor-pointer flex justify-between items-center text-xs font-geist motion-hover select-none">
            <div class="flex flex-col min-w-0 pr-2">
              <span class="font-semibold truncate text-[12px] leading-snug">${title}</span>
              <span class="text-[10px] font-geist-mono text-graphite opacity-80 mt-0.5">${dateStr}</span>
            </div>
            <button onclick="event.stopPropagation(); deleteSession('${key}')" title="Delete conversation"
              class="opacity-0 group-hover:opacity-100 text-graphite hover:text-ember-red p-1 text-xs font-bold transition-opacity cursor-pointer">
              &times;
            </button>
          </div>
        `;
      }).join('');
    }

    window.switchSession = function(sessionId) {
      currentSessionId = sessionId;
      localStorage.setItem(ACTIVE_SESSION_KEY, sessionId);
      
      // Auto-shift to AI Chat tab
      switchTab('chat');

      // Load selected session messages
      const sessions = getAllSessions();
      const sess = sessions[sessionId];

      chatFeed.innerHTML = '';
      if (sess && Array.isArray(sess.messages) && sess.messages.length > 0) {
        emptyState.classList.add('hidden-state');
        chatFeed.classList.remove('hidden-state');
        sess.messages.forEach(msg => {
          if (msg && msg.role && msg.content) {
            appendMessage(msg.role, msg.content, false);
          }
        });
        setTimeout(() => {
          chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: 'auto' });
        }, 100);
      } else {
        chatFeed.classList.add('hidden-state');
        emptyState.classList.remove('hidden-state');
      }

      renderSidebarConversations();
    };

    window.createNewSession = function() {
      currentSessionId = 'session-' + Date.now();
      localStorage.setItem(ACTIVE_SESSION_KEY, currentSessionId);
      
      // Auto-shift to AI Chat tab
      switchTab('chat');

      chatFeed.innerHTML = '';
      chatFeed.classList.add('hidden-state');
      emptyState.classList.remove('hidden-state');
      
      renderSidebarConversations();
    };

    window.deleteSession = function(sessionId) {
      const sessions = getAllSessions();
      delete sessions[sessionId];
      saveSessions(sessions);

      if (sessionId === currentSessionId) {
        createNewSession();
      } else {
        renderSidebarConversations();
      }
    };

    function loadChatHistory() {
      renderSidebarConversations();
      const sessions = getAllSessions();
      if (sessions[currentSessionId]) {
        switchSession(currentSessionId);
      } else {
        createNewSession();
      }
    }

    function saveMessageToStorage(role, content) {
      try {
        const sessions = getAllSessions();
        if (!sessions[currentSessionId]) {
          sessions[currentSessionId] = {
            id: currentSessionId,
            title: (role === 'user' && typeof content === 'string') ? content.substring(0, 32) + (content.length > 32 ? '...' : '') : 'New Conversation',
            createdAt: Date.now(),
            updatedAt: Date.now(),
            messages: []
          };
        }

        const sess = sessions[currentSessionId];
        if (sess.messages.length === 0 && role === 'user' && typeof content === 'string') {
          sess.title = content.substring(0, 32) + (content.length > 32 ? '...' : '');
        }

        sess.updatedAt = Date.now();
        sess.messages.push({ role, content });

        if (sess.messages.length > 60) {
          sess.messages = sess.messages.slice(-60);
        }

        saveSessions(sessions);
        renderSidebarConversations();
      } catch (e) {
        console.warn("Could not save message to session storage", e);
      }
    }

    function resetChat() {
      createNewSession();
    }


    window.startIndexing = async function() {
      const indexBtn = document.getElementById('index-btn');
      indexBtn.disabled = true;
      const originalText = indexBtn.textContent;
      indexBtn.textContent = 'Starting...';

      try {
        const response = await fetch("/api/v1/index", {
          method: "POST",
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ fast_mode: true })
        });
        const data = await response.json();

        // Append a message to the assistant chat feed to notify the user
        appendMessage('assistant', {
          tool: 'index_all_scripts',
          status: data.status,
          message: data.message || "Semantic indexing started.",
          reasoning: data.reasoning || "Initiated from admin dashboard."
        });

        // Immediately start polling
        pollIndexingStatus();
      } catch (err) {
        appendMessage('assistant', {
          status: 'internal_error',
          message: "Failed to trigger indexing.",
          reasoning: err.toString()
        });
        indexBtn.disabled = false;
        indexBtn.textContent = 'Index Scripts';
      }
    }

    let pollInterval = null;

    function startPolling() {
      if (!pollInterval) {
        pollInterval = setInterval(pollIndexingStatus, 3000);
      }
    }

    function stopPolling() {
      if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
      }
    }

    function updateProgressUI(processed, total, isIndexing) {
      const notchTracks = document.querySelectorAll('.indexing-notches');
      const progressLabels = document.querySelectorAll('.progress-label');
      
      const percentage = total > 0 ? Math.round((processed / total) * 100) : 0;
      
      progressLabels.forEach(label => {
        label.textContent = `${percentage}% (${processed}/${total})`;
      });

      const totalNotches = 30;
      const activeNotches = Math.round((percentage / 100) * totalNotches);

      let html = '';
      for (let i = 0; i < totalNotches; i++) {
        const isActive = i < activeNotches;
        const bgClass = isActive 
          ? 'bg-[#27c93f] shadow-[0_0_8px_rgba(39,201,63,0.5)]' 
          : 'bg-[#eeeeee] dark:bg-[#2c2c2c]';
        html += `<div class="flex-1 h-2 rounded-sm transition-all duration-300 ${bgClass}"></div>`;
      }

      notchTracks.forEach(track => {
        track.innerHTML = html;
      });

      if (!isIndexing && total > 0 && processed === total) {
        stopPolling();
      }
    }

    async function pollIndexingStatus() {
      const indexBtn = document.getElementById('index-btn');

      try {
        const response = await fetch("/api/v1/index/status");
        if (!response.ok) return;
        const data = await response.json();

        // Update any progress bar visual notches currently rendered on screen
        updateProgressUI(data.processed_scripts, data.total_scripts, data.is_indexing);

        if (data.is_indexing) {
          indexBtn.disabled = true;
          if (data.total_scripts > 0) {
            indexBtn.textContent = `Indexing (${data.processed_scripts}/${data.total_scripts})...`;
          } else {
            indexBtn.textContent = 'Indexing...';
          }
        } else {
          indexBtn.disabled = false;
          indexBtn.textContent = 'Index Scripts';
          stopPolling(); // Turn off when idle
        }
      } catch (err) {
        console.error("Failed to poll status", err);
        stopPolling();
      }
    }

    fetch("/api/v1/index/status").then(r => r.json()).then(data => {
      if (data.is_indexing) {
        pollIndexingStatus();
        startPolling();
      }
    }).catch(() => { });

    function appendMessage(role, content, saveToStorage = true) {
      emptyState.classList.add('hidden-state');
      chatFeed.classList.remove('hidden-state');

      if (saveToStorage) {
        saveMessageToStorage(role, content);
      }

      const wrapper = document.createElement('div');
      wrapper.className = `flex w-full ${role === 'user' ? 'justify-end' : 'justify-start'}`;

      if (role === 'user') {
        wrapper.innerHTML = `
          <div class="max-w-[75%] bg-carbon-ink dark:bg-mist text-white dark:text-carbon-ink font-geist text-sm rounded-cards px-5 py-3.5 border border-[#222222] dark:border-transparent text-left leading-relaxed animate-fade-in-up">
            ${escapeHtml(content)}
          </div>
        `;
      } else {
        let displayHtml = '';

        if (typeof content === 'object' && content !== null) {
          const tool = content.tool || 'unknown';
          const totalMatched = content.total_scripts_matched || content.total_results || content.total_scripts || content.total_scripts_assessed || 0;

          const diagToolEl = document.getElementById('diag-tool');
          if (diagToolEl) diagToolEl.textContent = tool;
          const diagRecsEl = document.getElementById('diag-recs');
          if (diagRecsEl) diagRecsEl.textContent = totalMatched;

          if (content.status === 'ambiguous') {
            const options = content.clarification_options || [];
            const optionsHtml = options.map(opt =>
              `<button onclick="submitSuggested('${escapeHtml(opt)}')" class="block w-full text-left px-4 py-2 mt-2 bg-fog dark:bg-slate hover:bg-mist dark:hover:bg-pewter transition-colors rounded-inputs text-xs font-geist font-semibold text-carbon-ink dark:text-mist border border-ash-border dark:border-transparent">${escapeHtml(opt)}</button>`
            ).join('');

            displayHtml = `
              <div class="w-full bg-white dark:bg-dark-surface border border-ember-red border-l-4 border-l-ember-red rounded-cards p-6 text-sm text-carbon-ink dark:text-mist font-geist">
                <span class="font-bryant text-xs text-ember-red uppercase tracking-bryant block mb-2 font-bold">Ambiguous Query</span>
                <p class="font-semibold mb-3 text-carbon-ink dark:text-paper-white">${escapeHtml(content.message || "Your query is too broad.")}</p>
                <p class="text-graphite dark:text-ash-border text-xs mb-4 italic">Reasoning: ${escapeHtml(content.reasoning || "Confidence score below threshold.")}</p>
                <div>
                  <span class="font-bryant text-[10px] text-slate dark:text-pewter tracking-bryant block mb-2 uppercase font-bold">Clarification Options</span>
                  ${optionsHtml}
                </div>
              </div>
            `;
          } else if (content.status === 'error' || content.status === 'not_found' || content.status === 'internal_error' || content.status === 'service_unavailable') {
            displayHtml = `
              <div class="w-full bg-white dark:bg-dark-surface border border-ember-red border-l-4 border-l-ember-red rounded-cards p-6 text-sm text-carbon-ink dark:text-mist font-geist">
                <span class="font-bryant text-xs text-ember-red uppercase tracking-bryant block mb-2 font-bold">Diagnostic Alert</span>
                <p class="font-semibold mb-2 text-carbon-ink dark:text-paper-white">${escapeHtml(content.message || "Not working")}</p>
                <p class="text-graphite dark:text-ash-border">${escapeHtml(content.reasoning || "An unexpected error occurred.")}</p>
              </div>
            `;
          } else if (tool === 'generate_test_suite') {
            const suiteName = content.suite_name || 'E2E Regression Suite';
            const totalDuration = content.estimated_total_duration_mins || 0;
            const steps = content.execution_steps || [];
            const gaps = content.coverage_gaps || [];

            let stepsHtml = '';
            steps.forEach(step => {
              stepsHtml += `
                <div class="flex items-start gap-3 py-2.5 px-3 border border-mist dark:border-slate rounded bg-white dark:bg-dark-surface hover:shadow-sm transition-shadow text-xs font-geist">
                  <span class="font-geist-mono text-[10px] bg-fog dark:bg-slate px-2 py-0.5 rounded text-graphite dark:text-mist font-bold shrink-0">Stage ${step.step_sequence}</span>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between gap-2 mb-1">
                      <span class="font-bold text-carbon-ink dark:text-paper-white truncate">${escapeHtml(step.script_name)}</span>
                      <span class="font-geist-mono text-[10px] text-graphite dark:text-pewter shrink-0">~${step.estimated_duration_mins}m</span>
                    </div>
                    <span class="font-geist-mono text-[10px] text-pewter dark:text-ash-border block mb-1">${escapeHtml(step.test_script_number)}</span>
                    <p class="text-graphite dark:text-ash-border text-[11px] leading-relaxed">${escapeHtml(step.step_objective)}</p>
                    <div class="flex items-center gap-1.5 mt-1.5 text-[9px]">
                      ${step.module ? `<span class="bg-fog dark:bg-slate text-graphite dark:text-mist px-1.5 py-0.2 rounded font-semibold uppercase">${escapeHtml(step.module)}</span>` : ''}
                      ${step.process_name ? `<span class="bg-fog dark:bg-slate text-graphite dark:text-mist px-1.5 py-0.2 rounded font-semibold uppercase">${escapeHtml(step.process_name)}</span>` : ''}
                    </div>
                  </div>
                </div>
              `;
            });

            let gapsHtml = '';
            gaps.forEach(gap => {
              gapsHtml += `
                <div class="border border-mist dark:border-slate rounded p-2.5 bg-fog/30 dark:bg-dark-surface flex flex-col gap-1 text-xs">
                  <div class="flex items-center justify-between">
                    <span class="font-bold text-carbon-ink dark:text-paper-white">${escapeHtml(gap.process_stage)}</span>
                    <span class="font-geist-mono text-[10px] text-ember-red uppercase font-bold">${escapeHtml(gap.risk_level)} GAP</span>
                  </div>
                  <p class="text-graphite dark:text-ash-border text-[11px]">${escapeHtml(gap.missing_capability)}</p>
                  <p class="text-[10px] text-slate dark:text-pewter italic mt-0.5">Recommendation: ${escapeHtml(gap.recommendation)}</p>
                </div>
              `;
            });

            const suiteMessage = content.message ? `<div class="mb-4 text-sm text-carbon-ink dark:text-mist font-geist">${escapeHtml(content.message)}</div>` : '';

            displayHtml = `
              ${suiteMessage}
              <div class="w-full bg-white dark:bg-dark-surface border border-mist dark:border-slate rounded-cards p-8 font-geist text-left transition-colors">
                <div class="flex justify-between items-center mb-4 pb-4 border-b border-mist dark:border-slate">
                  <div>
                    <span class="font-bryant text-xs text-graphite dark:text-pewter uppercase tracking-bryant font-bold block mb-1">E2E Regression Suite</span>
                    <h3 class="font-geist text-base font-bold text-carbon-ink dark:text-paper-white">${escapeHtml(suiteName)}</h3>
                    <span class="text-xs text-graphite dark:text-ash-border">~${totalDuration} mins runtime estimate (${steps.length} stages)</span>
                  </div>
                  <button onclick="submitSuggested('Execute the generated test suite')"
                    class="bg-carbon-ink dark:bg-mist text-white dark:text-carbon-ink rounded-buttons px-4 py-2 font-bryant text-xs uppercase tracking-bryant font-bold hover:opacity-90 transition-opacity cursor-pointer">
                    Execute Suite
                  </button>
                </div>

                <div class="mt-4 mb-6">
                  <span class="font-bryant text-[10px] text-carbon-ink dark:text-mist uppercase tracking-bryant font-bold block mb-3">Sequential Test Stages (${steps.length})</span>
                  <div class="border border-mist dark:border-slate rounded-cards p-3 bg-fog/20 dark:bg-dark-surface/30 max-h-80 overflow-y-auto space-y-2">
                    ${stepsHtml || '<p class="py-3 text-graphite dark:text-pewter italic text-xs">No stages defined.</p>'}
                  </div>
                </div>

                ${gaps.length > 0 ? `
                  <div class="mt-6 pt-4 border-t border-mist dark:border-slate">
                    <span class="font-bryant text-xs text-ember-red uppercase tracking-bryant font-bold block mb-2">Process Coverage Gaps</span>
                    <div class="flex flex-col gap-2 max-h-60 overflow-y-auto pr-1">
                      ${gapsHtml}
                    </div>
                  </div>
                ` : ''}
              </div>
            `;

          } else if (tool === 'schedule_test_run') {
            const suiteName = content.script_name || content.target_name || 'Unknown Suite';
            const scheduledTime = content.scheduled_time ? new Date(content.scheduled_time).toLocaleString() : 'N/A';
            const runId = content.run_id || 'N/A';
            
            displayHtml = `
              <div class="w-full bg-white dark:bg-dark-surface border border-emerald-500 border-l-4 border-l-emerald-500 rounded-cards p-6 text-sm text-carbon-ink dark:text-mist font-geist transition-colors">
                <span class="font-bryant text-xs text-emerald-600 uppercase tracking-bryant block mb-2 font-bold">Execution Scheduled</span>
                <div class="flex flex-col gap-2">
                  <div class="flex items-center justify-between">
                    <span class="font-semibold text-carbon-ink dark:text-paper-white text-base">${escapeHtml(suiteName)}</span>
                    <span class="bg-fog dark:bg-slate text-graphite dark:text-mist px-2 py-1 rounded font-mono text-xs border border-mist dark:border-slate" title="Run ID">${escapeHtml(runId.split('-')[0])}...</span>
                  </div>
                  <div class="flex items-center gap-2 mt-2">
                    <svg class="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    <span class="font-geist text-sm text-graphite dark:text-pewter font-medium">${escapeHtml(scheduledTime)}</span>
                  </div>
                  <p class="text-xs text-graphite dark:text-ash-border mt-3 border-t border-mist dark:border-slate pt-3">
                    Your test run has been successfully queued in the system and will trigger automatically at the scheduled time.
                  </p>
                </div>
              </div>
            `;
          } else if (tool === 'analyze_test_results') {
            const metrics = content.metrics || {};
            const recentFailures = content.recent_failures || [];
            
            let failuresHtml = '';
            recentFailures.forEach(f => {
              const execTime = f.execution_time !== 'N/A' ? new Date(f.execution_time).toLocaleString() : 'N/A';
              failuresHtml += `
                <div class="py-2.5 border-b border-mist/60 dark:border-slate/60 last:border-b-0">
                  <div class="flex items-center justify-between mb-1">
                    <span class="font-geist text-sm font-semibold text-carbon-ink dark:text-paper-white">${escapeHtml(f.script_name)}</span>
                    <span class="font-geist-mono text-[10px] text-pewter dark:text-ash-border">${escapeHtml(execTime)}</span>
                  </div>
                  <span class="font-geist-mono text-[10px] bg-fog dark:bg-slate px-1.5 py-0.5 rounded text-graphite dark:text-mist block w-max mb-1.5">${escapeHtml(f.script_number)}</span>
                  <p class="text-xs text-ember-red font-mono bg-ember-red/5 dark:bg-ember-red/10 p-1.5 rounded">${escapeHtml(f.error_message)}</p>
                </div>
              `;
            });

            displayHtml = `
              <div class="w-full bg-white dark:bg-dark-surface border border-mist dark:border-slate rounded-cards p-6 text-sm text-carbon-ink dark:text-mist font-geist transition-colors">
                <div class="flex items-center justify-between mb-4 border-b border-mist dark:border-slate pb-3">
                  <div>
                    <span class="font-bryant text-xs text-graphite dark:text-pewter uppercase tracking-bryant font-bold block mb-1">Execution Analytics</span>
                    <span class="font-semibold text-carbon-ink dark:text-paper-white text-base">${escapeHtml(metrics.module_filtered)}</span>
                  </div>
                  <span class="bg-fog dark:bg-slate text-graphite dark:text-mist px-2 py-1 rounded font-geist text-xs border border-mist dark:border-slate">${escapeHtml(new Date(metrics.timeframe_parsed).toLocaleDateString())} &rarr; Now</span>
                </div>
                
                <div class="grid grid-cols-3 gap-3 mb-5">
                  <div class="bg-fog/30 dark:bg-slate/30 p-3 rounded border border-mist/50 dark:border-slate/50 flex flex-col items-center justify-center">
                    <span class="font-bryant text-[10px] text-graphite dark:text-pewter uppercase tracking-bryant font-bold mb-1">Total Executed</span>
                    <span class="font-geist text-xl font-bold text-carbon-ink dark:text-paper-white">${metrics.total_executed}</span>
                  </div>
                  <div class="bg-fog/30 dark:bg-slate/30 p-3 rounded border border-mist/50 dark:border-slate/50 flex flex-col items-center justify-center">
                    <span class="font-bryant text-[10px] text-graphite dark:text-pewter uppercase tracking-bryant font-bold mb-1">Pass Rate</span>
                    <span class="font-geist text-xl font-bold ${metrics.pass_rate_percentage >= 80 ? 'text-emerald-500' : 'text-amber-500'}">${metrics.pass_rate_percentage}%</span>
                  </div>
                  <div class="bg-ember-red/5 dark:bg-ember-red/10 p-3 rounded border border-ember-red/20 dark:border-ember-red/30 flex flex-col items-center justify-center">
                    <span class="font-bryant text-[10px] text-ember-red uppercase tracking-bryant font-bold mb-1">Failed</span>
                    <span class="font-geist text-xl font-bold text-ember-red">${metrics.failed}</span>
                  </div>
                </div>

                ${recentFailures.length > 0 ? `
                  <div>
                    <span class="font-bryant text-xs text-graphite dark:text-pewter uppercase tracking-bryant font-bold block mb-2">Recent Failures</span>
                    <div class="max-h-64 overflow-y-auto pr-1">
                      ${failuresHtml}
                    </div>
                  </div>
                ` : '<p class="text-xs text-graphite italic text-center py-2">No failed scripts in this timeframe. 🎉</p>'}
              </div>
            `;
          } else if (tool === 'detect_duplicates') {
            const moduleScanned = content.module_filtered || 'All Modules';
            const clusters = content.duplicate_clusters || [];
            
            let clustersHtml = '';
            clusters.forEach((cluster, idx) => {
              let scriptsHtml = '';
              cluster.scripts.forEach(s => {
                scriptsHtml += `<div class="font-geist text-sm text-carbon-ink dark:text-paper-white bg-fog/50 dark:bg-slate/50 p-2 rounded mb-1 border border-mist/50 dark:border-slate/50 flex items-center justify-between"><div class="flex items-center truncate"><span class="font-geist-mono text-xs text-pewter dark:text-ash-border mr-2 shrink-0">${s.script_number}</span><span class="truncate">${escapeHtml(s.script_name)}</span></div><span class="text-[10px] text-graphite dark:text-pewter ml-2 shrink-0">${escapeHtml(s.module)}</span></div>`;
              });
              
              clustersHtml += `
                <div class="mb-4 last:mb-0">
                  <div class="flex items-center justify-between mb-2">
                    <span class="font-bryant text-xs text-graphite dark:text-pewter uppercase tracking-bryant font-bold">Duplicate Cluster ${idx + 1}</span>
                    <span class="text-[10px] bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 px-1.5 py-0.5 rounded font-mono">100% Match</span>
                  </div>
                  ${scriptsHtml}
                </div>
              `;
            });

            displayHtml = `
              <div class="w-full bg-white dark:bg-dark-surface border border-mist dark:border-slate rounded-cards p-6 text-sm text-carbon-ink dark:text-mist font-geist transition-colors">
                <div class="flex items-center justify-between mb-4 border-b border-mist dark:border-slate pb-3">
                  <div>
                    <span class="font-bryant text-xs text-graphite dark:text-pewter uppercase tracking-bryant font-bold block mb-1">Semantic Duplicate Detection</span>
                    <span class="font-semibold text-carbon-ink dark:text-paper-white text-base">${escapeHtml(moduleScanned)}</span>
                  </div>
                  <span class="bg-fog dark:bg-slate text-graphite dark:text-mist px-2 py-1 rounded font-geist text-xs border border-mist dark:border-slate">Found ${clusters.length} Clusters</span>
                </div>
                
                ${clusters.length > 0 ? `
                  <div class="max-h-80 overflow-y-auto pr-1">
                    ${clustersHtml}
                  </div>
                ` : '<p class="text-xs text-graphite italic text-center py-4">No exact duplicates found in this module. 🎉</p>'}
              </div>
            `;
            
          } else if (tool === 'lint_locators') {
            const moduleScanned = content.module_scanned || 'Unknown Module';
            const fragileSteps = content.fragile_steps || [];
            
            let lintHtml = '';
            fragileSteps.forEach(f => {
              lintHtml += `
                <div class="py-3 border-b border-mist/60 dark:border-slate/60 last:border-b-0">
                  <div class="flex items-center justify-between mb-1">
                    <span class="font-geist text-sm font-semibold text-carbon-ink dark:text-paper-white">${escapeHtml(f.script_name)}</span>
                    <span class="font-geist-mono text-[10px] bg-fog dark:bg-slate px-1.5 py-0.5 rounded text-graphite dark:text-mist">${escapeHtml(f.script_number)}</span>
                  </div>
                  <p class="text-xs text-graphite dark:text-pewter mb-2">Step: ${escapeHtml(f.step_description)}</p>
                  
                  <div class="grid grid-cols-[auto_1fr] gap-x-2 gap-y-1 text-xs">
                    <span class="text-amber-500 font-mono self-start mt-0.5">!!</span>
                    <span class="text-ember-red font-mono bg-ember-red/5 dark:bg-ember-red/10 p-1 rounded break-all border border-ember-red/10">${escapeHtml(f.locator)}</span>
                    
                    <span class="text-emerald-500 font-mono self-start mt-0.5">-></span>
                    <span class="text-emerald-600 dark:text-emerald-400 bg-emerald-500/5 dark:bg-emerald-500/10 p-1 rounded border border-emerald-500/10">${escapeHtml(f.recommendation)}</span>
                  </div>
                </div>
              `;
            });

            displayHtml = `
              <div class="w-full bg-white dark:bg-dark-surface border border-mist dark:border-slate rounded-cards p-6 text-sm text-carbon-ink dark:text-mist font-geist transition-colors">
                <div class="flex items-center justify-between mb-4 border-b border-mist dark:border-slate pb-3">
                  <div>
                    <span class="font-bryant text-xs text-graphite dark:text-pewter uppercase tracking-bryant font-bold block mb-1">Locator Linting Audit</span>
                    <span class="font-semibold text-carbon-ink dark:text-paper-white text-base">${escapeHtml(moduleScanned)}</span>
                  </div>
                  <span class="bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 px-2 py-1 rounded font-geist text-xs font-semibold">${fragileSteps.length} Issues Found</span>
                </div>
                
                ${fragileSteps.length > 0 ? `
                  <div class="max-h-80 overflow-y-auto pr-1">
                    ${lintHtml}
                  </div>
                ` : '<p class="text-xs text-emerald-500 italic text-center py-4">All locators in this module look robust! 🎉</p>'}
              </div>
            `;
          } else if (tool === 'assess_test_risk') {
            const healthScore = content.overall_health_score || 85;
            const riskItems = content.risk_items || [];

            let itemsHtml = '';
            riskItems.forEach(item => {
              itemsHtml += `
                <div class="py-2.5 border-b border-mist/60 dark:border-slate/60 last:border-b-0">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <span class="font-geist-mono text-xs text-pewter dark:text-ash-border">${escapeHtml(item.test_script_number)}</span>
                      <span class="font-geist text-sm font-semibold text-carbon-ink dark:text-paper-white">${escapeHtml(item.script_name)}</span>
                    </div>
                    <span class="font-geist-mono text-xs font-bold text-carbon-ink dark:text-mist">${item.risk_tier} (Score: ${item.risk_score}/100)</span>
                  </div>
                  <div class="grid grid-cols-2 gap-2 text-[11px] text-graphite dark:text-ash-border mt-1">
                    <div>Executions: ${item.total_executions} (${item.failed_executions} failed)</div>
                    <div>Flakiness Rate: ${(item.flakiness_rate * 100).toFixed(0)}%</div>
                  </div>
                  <p class="text-xs text-slate dark:text-pewter italic mt-1">${escapeHtml(item.stabilization_recommendation)}</p>
                </div>
              `;
            });

            displayHtml = `
              <div class="w-full bg-white dark:bg-dark-surface border border-mist dark:border-slate rounded-cards p-8 font-geist text-left transition-colors">
                <div class="flex justify-between items-center mb-4 pb-4 border-b border-mist dark:border-slate">
                  <span class="font-bryant text-xs text-graphite dark:text-pewter uppercase tracking-bryant font-bold">Predictive Risk Assessment</span>
                  <span class="font-geist-mono text-xs font-bold text-carbon-ink dark:text-paper-white">Overall Health: ${healthScore}/100</span>
                </div>
                <p class="text-xs text-graphite dark:text-ash-border mb-4">${escapeHtml(content.executive_summary || '')}</p>
                <div class="max-h-80 overflow-y-auto pr-1">
                  ${itemsHtml || '<p class="text-xs text-graphite italic">All scripts evaluated within normal thresholds.</p>'}
                </div>
              </div>
            `;
          } else if (tool === 'semantic_cluster_scripts') {
            const concept = content.concept || 'general';
            const reasoning = content.reasoning || '';
            const clusters = content.clusters || {};

            let clustersHtml = '';
            for (const [category, scripts] of Object.entries(clusters)) {
              let scriptsHtml = '';
              scripts.forEach(script => {
                const scriptNum = script.test_script_number || 'N/A';
                const scriptName = script.script_name || 'Unknown';
                const scriptDesc = script.description || script.objective || 'No description available';
                const module = script.module || '';
                const process = script.process || '';

                let badgesHtml = '';
                if (module) {
                  badgesHtml += `<span class="inline-block bg-fog dark:bg-slate text-graphite dark:text-mist font-geist text-[10px] px-2 py-0.5 rounded-badges uppercase font-semibold">${escapeHtml(module)}</span>`;
                }
                if (process) {
                  badgesHtml += `<span class="inline-block bg-fog dark:bg-slate text-graphite dark:text-mist font-geist text-[10px] px-2 py-0.5 rounded-badges uppercase font-semibold ml-1.5">${escapeHtml(process)}</span>`;
                }

                scriptsHtml += `
                  <div class="py-3 border-b border-mist/50 dark:border-slate/50 last:border-b-0 text-left">
                    <div class="flex items-start justify-between">
                      <div class="flex items-center flex-wrap gap-2">
                        <span class="font-geist-mono text-xs text-pewter dark:text-ash-border font-medium">${escapeHtml(scriptNum)}</span>
                        <span class="font-geist text-sm font-semibold text-carbon-ink dark:text-paper-white hover:text-ember-red dark:hover:text-ember-red cursor-pointer" onclick="submitSuggested('Explain script ${escapeHtml(scriptNum)}')">${escapeHtml(scriptName)}</span>
                        ${badgesHtml}
                      </div>
                    </div>
                    <p class="text-xs text-graphite dark:text-ash-border mt-1 max-w-2xl font-geist leading-relaxed">${escapeHtml(scriptDesc)}</p>
                  </div>
                `;
              });

              clustersHtml += `
                <div class="mb-6 last:mb-0 text-left">
                  <h4 class="font-bryant text-sm text-carbon-ink dark:text-paper-white tracking-bryant uppercase font-bold mb-1">${escapeHtml(category)}</h4>
                  <div class="w-full h-[1px] bg-mist dark:bg-slate mb-2"></div>
                  <div class="flex flex-col">
                    ${scriptsHtml || '<p class="text-xs text-graphite dark:text-pewter italic">No scripts in this cluster.</p>'}
                  </div>
                </div>
              `;
            }

            displayHtml = `
              <div class="w-full bg-white dark:bg-dark-surface border border-mist dark:border-slate rounded-cards p-8 font-geist text-left transition-colors">
                <div class="flex justify-between items-center mb-6">
                  <span class="font-bryant text-xs text-graphite dark:text-pewter uppercase tracking-bryant font-bold">Dynamic Cluster: ${escapeHtml(concept)}</span>
                  <span class="font-bryant text-xs text-carbon-ink dark:text-paper-white uppercase tracking-bryant font-bold">${content.total_scripts_matched} Matched</span>
                </div>
                <p class="text-xs text-graphite dark:text-ash-border italic mb-4">Reasoning: ${escapeHtml(reasoning)}</p>
                <div class="max-h-96 overflow-y-auto pr-1">
                  ${clustersHtml || '<p class="text-sm text-graphite dark:text-pewter">No clusters generated.</p>'}
                </div>
              </div>
            `;
          } else if (tool === 'semantic_search_tests') {
            const query = content.query || '';
            const results = content.results || [];

            let resultsHtml = '';
            results.forEach(res => {
              const scriptNum = res.test_script_number || 'N/A';
              const scriptName = res.script_name || 'Unknown';
              const score = res.score ? `${(res.score * 100).toFixed(0)}%` : '';
              const dbRec = res.database_record || {};
              const module = dbRec.module || '';
              const process = dbRec.process || '';
              const desc = dbRec.objective || dbRec.script_objective || dbRec.description || dbRec.script_description || dbRec.qualified_name || '';

              let badgesHtml = '';
              if (module) {
                badgesHtml += `<span class="inline-block bg-fog dark:bg-slate text-graphite dark:text-mist font-geist text-[10px] px-2 py-0.5 rounded-badges uppercase font-semibold">${escapeHtml(module)}</span>`;
              }
              if (process) {
                badgesHtml += `<span class="inline-block bg-fog dark:bg-slate text-graphite dark:text-mist font-geist text-[10px] px-2 py-0.5 rounded-badges uppercase font-semibold ml-1.5">${escapeHtml(process)}</span>`;
              }

              resultsHtml += `
                <div class="py-4 border-b border-mist dark:border-slate last:border-b-0 text-left">
                  <div class="flex items-center flex-wrap gap-2 mb-1.5">
                    <span class="font-geist-mono text-[11px] text-pewter dark:text-ash-border font-medium select-all">${escapeHtml(scriptNum)}</span>
                    <span class="font-geist text-sm font-semibold text-carbon-ink dark:text-paper-white hover:text-ember-red dark:hover:text-ember-red cursor-pointer underline-offset-2 hover:underline transition-colors" title="Click to explain this script" onclick="submitSuggested('Explain script ${escapeHtml(scriptNum)}')">${escapeHtml(scriptName)}</span>
                    ${score ? `<span class="font-geist-mono text-[10px] text-[#1e6f43] dark:text-[#4ade80] bg-[#eaf6f0] dark:bg-[#1a2f24] px-2 py-0.5 rounded-badges font-semibold">${score} match</span>` : ''}
                    ${badgesHtml}
                  </div>
                  ${desc ? `<p class="text-xs text-graphite dark:text-ash-border leading-relaxed font-geist">${escapeHtml(desc)}</p>` : ''}
                </div>
              `;
            });

            displayHtml = `
              <div class="w-full bg-white dark:bg-dark-surface border border-mist dark:border-slate rounded-cards p-8 font-geist text-left transition-colors">
                <div class="flex justify-between items-center mb-4 pb-4 border-b border-mist dark:border-slate">
                  <span class="font-bryant text-xs text-graphite dark:text-pewter uppercase tracking-bryant font-bold">Results for &ldquo;${escapeHtml(query)}&rdquo;</span>
                  <span class="font-geist-mono text-xs text-carbon-ink dark:text-paper-white font-bold">${results.length} scripts</span>
                </div>
                <div class="flex flex-col divide-y divide-mist/50 dark:divide-slate/50">
                  ${resultsHtml || '<p class="text-sm text-graphite dark:text-pewter py-4">No matching scripts found.</p>'}
                </div>
              </div>
            `;
          } else if (tool === 'filtered_script_lookup' || (tool === 'analyze_entity' && !content.explanation)) {
            const script = content.database_record || content;
            const scriptNum = script.test_script_number || 'N/A';
            const scriptName = script.script_name || 'Unknown';
            const objective = script.objective || script.script_objective || script.description || scriptName;
            const module = script.module || 'N/A';
            const process = script.process || 'N/A';
            const role = script.role || 'N/A';
            const steps = script.steps || [];


            const semanticDoc = content.semantic_document || '';
            let parametersHtml = '';
            let validationsHtml = '';
            
            if (semanticDoc) {
              const paramsMatch = semanticDoc.match(/4\.\s*(?:Input\s*)?Parameters.*?\n([\s\S]*?)(?:(?:\n###)|(?:\n\d\.)|$)/i);
              if (paramsMatch && paramsMatch[1].trim()) {
                parametersHtml = formatMarkdownToHtml(paramsMatch[1].trim());
              }
              
              const validMatch = semanticDoc.match(/5\.\s*(?:Expected\s*)?(?:Business\s*)?Validations.*?\n([\s\S]*?)(?:(?:\n###)|(?:\n\d\.)|$)/i);
              if (validMatch && validMatch[1].trim()) {
                validationsHtml = formatMarkdownToHtml(validMatch[1].trim());
              }
            }

            let stepsListHtml = '';

            if (steps.length > 0) {
              steps.forEach((step, idx) => {
                const displayNo = idx + 1;
                const sAction = step.step_action || step.action || '';
                const sDesc = step.step_description || step.description || '';
                const sParam = step.input_parameter || '';

                stepsListHtml += `
                  <div class="flex items-start gap-3 py-2 border-b border-mist/50 dark:border-slate/50 last:border-b-0 text-xs font-geist hover:bg-fog/30 dark:hover:bg-dark-surface/40 px-2 rounded transition-colors">
                    <span class="font-geist-mono text-[10px] bg-fog dark:bg-slate px-2 py-0.5 rounded text-graphite dark:text-mist font-bold shrink-0">${displayNo}</span>
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2">
                        <span class="font-semibold text-carbon-ink dark:text-paper-white">${escapeHtml(sAction)}</span>
                        ${sParam ? `<span class="font-geist-mono text-[10px] text-pewter dark:text-ash-border bg-fog dark:bg-[#151515] px-1.5 py-0.2 rounded border border-mist dark:border-[#222]">Param: ${escapeHtml(sParam)}</span>` : ''}
                      </div>
                      ${sDesc ? `<p class="text-graphite dark:text-ash-border mt-0.5 text-[11px] leading-relaxed">${escapeHtml(sDesc)}</p>` : ''}
                    </div>
                  </div>
                `;
              });
            }

            displayHtml = `
              <div class="w-full bg-white dark:bg-dark-surface border border-mist dark:border-slate rounded-cards p-8 font-geist text-left transition-colors">
                <span class="font-bryant text-xs text-graphite dark:text-pewter uppercase tracking-bryant block mb-2 font-bold">Test Script Metadata</span>
                <h3 class="font-geist text-lg font-bold text-carbon-ink dark:text-paper-white mb-1">${escapeHtml(scriptName)}</h3>
                <span class="font-geist-mono text-xs text-pewter dark:text-ash-border block mb-4">${escapeHtml(scriptNum)}</span>
                
                <div class="grid grid-cols-3 gap-4 py-3 border-t border-b border-mist dark:border-slate my-4 text-xs">
                  <div>
                    <span class="font-bryant text-slate dark:text-pewter uppercase text-[10px] tracking-bryant block mb-1 font-bold">Module</span>
                    <span class="font-semibold text-carbon-ink dark:text-mist">${escapeHtml(module)}</span>
                  </div>
                  <div>
                    <span class="font-bryant text-slate dark:text-pewter uppercase text-[10px] tracking-bryant block mb-1 font-bold">Process</span>
                    <span class="font-semibold text-carbon-ink dark:text-mist">${escapeHtml(process)}</span>
                  </div>
                  <div>
                    <span class="font-bryant text-slate dark:text-pewter uppercase text-[10px] tracking-bryant block mb-1 font-bold">Assigned Role</span>
                    <span class="font-semibold text-carbon-ink dark:text-mist">${escapeHtml(role)}</span>
                  </div>
                </div>


                ${objective ? `
                <div class="text-xs mb-5">
                  <span class="font-bryant text-slate dark:text-pewter uppercase text-[10px] tracking-bryant block mb-1.5 font-bold">Business Objective</span>
                  <p class="text-graphite dark:text-ash-border leading-relaxed">${escapeHtml(objective)}</p>
                </div>` : ''}

                ${parametersHtml ? `
                <div class="text-xs mb-5 semantic-doc-container">
                  <span class="font-bryant text-slate dark:text-pewter uppercase text-[10px] tracking-bryant block mb-1.5 font-bold">Input Parameters</span>
                  <div class="text-graphite dark:text-ash-border leading-relaxed bg-fog/20 dark:bg-dark-surface/30 p-3 rounded-cards border border-mist dark:border-slate/50">
                    ${parametersHtml}
                  </div>
                </div>` : ''}

                ${validationsHtml ? `
                <div class="text-xs mb-5 semantic-doc-container">
                  <span class="font-bryant text-slate dark:text-pewter uppercase text-[10px] tracking-bryant block mb-1.5 font-bold">Business Validations</span>
                  <div class="text-graphite dark:text-ash-border leading-relaxed bg-fog/20 dark:bg-dark-surface/30 p-3 rounded-cards border border-mist dark:border-slate/50">
                    ${validationsHtml}
                  </div>
                </div>` : ''}


                <div class="mt-6">
                  <div class="flex items-center justify-between mb-3">
                    <span class="font-bryant text-xs text-carbon-ink dark:text-mist uppercase tracking-bryant font-bold">Workflow Sequence (${steps.length} Steps)</span>
                    <span class="font-geist-mono text-[10px] text-graphite dark:text-pewter">Ordered Execution</span>
                  </div>
                  <div class="border border-mist dark:border-slate rounded-cards p-3 bg-fog/20 dark:bg-dark-surface/30 max-h-80 overflow-y-auto space-y-1">
                    ${stepsListHtml || '<p class="py-4 text-graphite dark:text-pewter italic text-xs">No steps defined for this script.</p>'}
                  </div>
                </div>
              </div>
            `;
          } else if (tool === 'analyze_entity' && content.explanation) {
            const explanation = content.explanation || '';
            const suggestedFix = content.suggested_fix || '';
            const confidence = content.confidence ? `${(content.confidence * 100).toFixed(0)}%` : 'N/A';

            displayHtml = `
              <div class="w-full bg-white dark:bg-dark-surface border border-mist dark:border-slate rounded-cards p-8 font-geist text-left transition-colors">
                <div class="flex justify-between items-center mb-6">
                  <span class="font-bryant text-xs text-ember-red uppercase tracking-bryant font-bold">Failure Analysis</span>
                  <span class="font-geist-mono text-xs text-pewter dark:text-ash-border font-medium">Confidence: ${escapeHtml(confidence)}</span>
                </div>
                <div class="text-sm text-carbon-ink dark:text-paper-white mb-6 leading-relaxed">
                  <span class="font-bryant text-[10px] text-slate dark:text-pewter tracking-bryant block mb-1 uppercase font-bold">Root Cause Explanation</span>
                  ${escapeHtml(explanation)}
                </div>
                <div>
                  <span class="font-bryant text-[10px] text-slate dark:text-pewter tracking-bryant block mb-2 uppercase font-bold">Suggested Resolution</span>
                  
                  <div class="rounded-lg overflow-hidden border border-mist dark:border-slate shadow-sm mt-3">
                    <div class="bg-fog dark:bg-[#1a1a1a] px-4 py-2.5 flex justify-between items-center border-b border-mist dark:border-[#2a2a2a]">
                      <div class="flex gap-2">
                        <div class="w-2.5 h-2.5 rounded-full bg-[#ff5f56] shadow-sm"></div>
                        <div class="w-2.5 h-2.5 rounded-full bg-[#ffbd2e] shadow-sm"></div>
                        <div class="w-2.5 h-2.5 rounded-full bg-[#27c93f] shadow-sm"></div>
                      </div>
                      <div class="font-geist-mono text-[10px] text-graphite dark:text-pewter font-medium">solution.snippet</div>
                      <button onclick="copyToClipboard(this)" data-code="${escapeHtml(suggestedFix).replace(/"/g, '&quot;')}" class="font-geist text-[10px] text-graphite dark:text-pewter hover:text-carbon-ink dark:hover:text-paper-white flex items-center gap-1.5 transition-colors cursor-pointer">
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
                        Copy Code
                      </button>
                    </div>
                    <div class="p-4 bg-[#f8f9fa] dark:bg-[#0d0d0d] overflow-x-auto">
                      <pre class="font-geist-mono text-[13px] text-[#24292e] dark:text-[#d1d5db] whitespace-pre-wrap">${escapeHtml(suggestedFix)}</pre>
                    </div>
                  </div>

                </div>
              </div>
            `;
          } else if (tool === 'recommend_locator_fixes') {
            const repairs = content.locator_repairs || [];
            const scriptName = escapeHtml(content.script_name || '');
            let repairsHtml = '';
            
            if (repairs.length > 0) {
              repairsHtml = repairs.map(rep => {
                const stepNo = rep.step_no;
                const newLoc = escapeHtml(rep.suggested_locator);
                const reason = escapeHtml(rep.fix_rationale);
                const score = rep.resilience_score || 95;
                const broken = escapeHtml(rep.broken_locator);
                return `
                  <div class="mb-4 bg-fog/20 dark:bg-[#1a1a1a] border border-mist dark:border-[#2a2a2a] rounded-cards p-4">
                    <div class="flex justify-between items-center mb-3">
                      <span class="font-geist-mono text-[10px] text-white bg-carbon-ink dark:bg-slate px-2 py-0.5 rounded-badges font-bold">Step ${stepNo}</span>
                      <span class="font-geist text-[10px] text-[#27c93f] font-semibold flex items-center gap-1">
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        ${score}% Resilient
                      </span>
                    </div>
                    <div class="mb-2">
                      <span class="font-bryant text-[10px] text-graphite dark:text-ash-border uppercase tracking-bryant block mb-1">Old Locator</span>
                      <pre class="font-geist-mono text-[11px] text-ember-red bg-[#fff5f5] dark:bg-[#3b1515] px-2 py-1.5 rounded overflow-x-auto border border-red-200 dark:border-red-900 line-through">${broken}</pre>
                    </div>
                    <div class="mb-3">
                      <span class="font-bryant text-[10px] text-graphite dark:text-ash-border uppercase tracking-bryant block mb-1">Healed Locator</span>
                      <pre class="font-geist-mono text-[11px] text-[#1e6f43] dark:text-[#4ade80] bg-[#eaf6f0] dark:bg-[#1a2f24] px-2 py-1.5 rounded overflow-x-auto border border-green-200 dark:border-green-900 font-bold">${newLoc}</pre>
                    </div>
                    <p class="text-[10px] text-graphite dark:text-pewter mb-4 leading-relaxed">${reason}</p>
                    
                    <button onclick="healLocator('${scriptName.replace(/'/g, "\\'")}', ${stepNo}, '${newLoc.replace(/'/g, "\\'")}')" class="w-full justify-center inline-flex items-center gap-1.5 bg-carbon-ink dark:bg-mist text-white dark:text-carbon-ink rounded-buttons px-4 py-2 font-bryant text-xs uppercase tracking-bryant font-bold hover:bg-[#333] dark:hover:bg-paper-white transition-colors cursor-pointer shadow-sm relative overflow-hidden group">
                      <span class="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]"></span>
                      ✨ Auto-Heal Locator
                    </button>
                  </div>
                `;
              }).join('');
            } else {
              repairsHtml = `<p class="py-4 text-graphite dark:text-pewter italic text-xs">No broken locators found.</p>`;
            }

            displayHtml = `
              <div class="w-full bg-white dark:bg-dark-surface border border-[#27c93f]/30 rounded-cards p-8 font-geist text-left transition-colors shadow-[0_0_15px_rgba(39,201,63,0.05)]">
                <div class="flex justify-between items-center mb-6 pb-4 border-b border-mist dark:border-slate">
                  <div>
                    <span class="font-bryant text-xs text-[#27c93f] uppercase tracking-bryant font-bold block mb-1">Interactive Self-Healing</span>
                    <h3 class="font-geist text-base font-bold text-carbon-ink dark:text-paper-white">${scriptName}</h3>
                  </div>
                  <span class="font-geist-mono text-[10px] font-bold text-carbon-ink dark:text-mist bg-fog dark:bg-slate px-3 py-1.5 rounded-badges shrink-0 border border-[#27c93f]/20">${content.total_broken_locators} Repairs</span>
                </div>
                
                <p class="text-[11px] text-graphite dark:text-ash-border mb-4 leading-relaxed">${escapeHtml(content.healing_summary)}</p>
                
                <div class="mt-4">
                  ${repairsHtml}
                </div>
              </div>
            `;
          } else if (tool === 'execute_script_set') {
            const execId = content.execution_id || 'N/A';
            const status = content.status || 'unknown';
            const scriptIds = content.test_script_ids || [];

            displayHtml = `
              <div class="w-full bg-white dark:bg-dark-surface border border-mist dark:border-slate rounded-cards p-8 font-geist text-left transition-colors">
                <span class="font-bryant text-xs text-graphite dark:text-pewter uppercase tracking-bryant block mb-2 font-bold">Test Orchestration Exec</span>
                <div class="flex items-center justify-between flex-wrap gap-4 mb-6">
                  <h3 class="font-geist text-base font-bold text-carbon-ink dark:text-paper-white">Execution Request Dispatched</h3>
                  <span class="inline-flex items-center gap-1.5 bg-[#eaf6f0] text-[#1e6f43] dark:bg-[#1a2f24] dark:text-[#4ade80] font-geist text-xs px-2.5 py-1 rounded-badges uppercase font-bold"><span class="w-1.5 h-1.5 bg-[#1e6f43] dark:bg-[#4ade80] rounded-full"></span>${escapeHtml(status)}</span>
                </div>
                <div class="grid grid-cols-2 gap-4 py-3 border-t border-b border-mist dark:border-slate text-xs mb-4">
                  <div>
                    <span class="font-bryant text-slate dark:text-pewter uppercase text-[10px] tracking-bryant block mb-1 font-bold">Execution ID</span>
                    <span class="font-geist-mono text-pewter dark:text-ash-border font-semibold select-all">${escapeHtml(execId)}</span>
                  </div>
                  <div>
                    <span class="font-bryant text-slate dark:text-pewter uppercase text-[10px] tracking-bryant block mb-1 font-bold">Target Scripts Count</span>
                    <span class="font-semibold text-carbon-ink dark:text-mist">${scriptIds.length} scripts</span>
                  </div>
                </div>
                <p class="text-[11px] text-graphite dark:text-ash-border leading-relaxed">
                  Execution client invoked dynamically. Integration with production execution pipelines will process these scripts sequentially.
                </p>
              </div>
            `;
          } else if (tool === 'index_all_scripts') {
            if (typeof startPolling === 'function') {
              startPolling();
              pollIndexingStatus();
            }

            displayHtml = `
              <div class="w-full bg-white dark:bg-dark-surface border border-mist dark:border-slate rounded-cards p-8 font-geist text-left transition-colors">
                <span class="font-bryant text-xs text-graphite dark:text-pewter uppercase tracking-bryant block mb-2 font-bold">Semantic Search Indexer</span>
                <div class="flex items-center justify-between flex-wrap gap-4 mb-4">
                  <h3 class="font-geist text-base font-bold text-carbon-ink dark:text-paper-white">Background Indexing Dispatched</h3>
                  <span class="status-badge inline-flex items-center gap-1.5 bg-[#eaf6f0] text-[#1e6f43] dark:bg-[#1a2f24] dark:text-[#4ade80] font-geist text-xs px-2.5 py-1 rounded-badges uppercase font-bold"><span class="w-1.5 h-1.5 bg-[#1e6f43] dark:bg-[#4ade80] rounded-full animate-pulse"></span>INDEXING</span>
                </div>
                <p class="text-xs text-graphite dark:text-ash-border mb-4">${escapeHtml(content.message)}</p>
                <div class="w-full bg-fog dark:bg-[#111] border border-ash-border dark:border-[#2a2a2a] rounded-cards p-4 mb-4 shadow-inner">
                  <div class="flex justify-between items-center text-[10px] font-geist-mono text-slate dark:text-ash-border mb-2 font-semibold tracking-wider">
                    <span>LINEAR NOTCH INDEX GAUGE</span>
                    <span class="progress-label font-bold text-[#27c93f] cyber-glow-green">0% (0/0)</span>
                  </div>
                  <div class="indexing-notches flex gap-1 h-3 items-center justify-between bg-transparent"></div>
                </div>
                <p class="text-[11px] text-graphite dark:text-pewter leading-relaxed italic">
                  Generating high-quality semantic documents and cosine vector embeddings using local model and writing to PostgreSQL & Qdrant indices...
                </p>
              </div>
            `;
          } else if (tool === 'generate_script_steps') {
            const scenario = content.scenario || '';
            const processArea = content.process_area || '';
            const steps = content.generated_steps || [];
            const sourceScripts = content.few_shot_source_scripts || [];
            const reasoning = content.reasoning || '';

            // Map action types to colour classes
            const actionColours = {
              'Navigate':                  'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
              'Click Button':              'bg-violet-50 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300',
              'Enter Value - Text Field':  'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
              'Select Option':             'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
              'Open Dropdown':             'bg-cyan-50 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300',
              'Wait Till Load':            'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400',
              'Vertical Scroll':           'bg-orange-50 text-orange-600 dark:bg-orange-900/30 dark:text-orange-300',
              'Key - Tab':                 'bg-pink-50 text-pink-600 dark:bg-pink-900/30 dark:text-pink-300',
              'Click':                     'bg-violet-50 text-violet-600 dark:bg-violet-900/30 dark:text-violet-300',
              'Verify':                    'bg-teal-50 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300',
            };

            let stepsHtml = '';
            steps.forEach(step => {
              const no         = step.step_no || '?';
              const action     = step.action || 'Navigate';
              const desc       = step.step_description || '';
              const target     = step.input_parameter || step.target_element || '';
              const defaultVal = step.default_value || '';
              const colour     = actionColours[action] || 'bg-fog text-graphite dark:bg-slate dark:text-mist';

              const valBadge = defaultVal
                ? `<span class="inline-block font-geist-mono text-[10px] bg-[#fff7ed] text-[#c2410c] dark:bg-[#431407] dark:text-[#fb923c] px-2 py-0.5 rounded-badges border border-orange-200 dark:border-orange-900 ml-1.5 select-all font-semibold">Value: ${escapeHtml(defaultVal)}</span>`
                : '';

              stepsHtml += `
                <div class="flex items-start gap-3 py-3 border-b border-mist/50 dark:border-slate/50 last:border-b-0 text-xs font-geist">
                  <span class="font-geist-mono text-[10px] bg-carbon-ink dark:bg-mist text-white dark:text-carbon-ink px-2 py-0.5 rounded font-bold shrink-0 min-w-[3rem] text-center">Step ${no}</span>
                  <div class="flex-1 min-w-0">
                    <div class="flex flex-wrap items-center gap-1.5 mb-1">
                      <span class="font-geist-mono text-[10px] px-2 py-0.5 rounded-badges font-bold ${colour}">${escapeHtml(action)}</span>
                      ${target ? `<span class="font-geist-mono text-[10px] text-graphite dark:text-ash-border font-medium">Target: '${escapeHtml(target)}'</span>` : ''}
                      ${valBadge}
                    </div>
                    ${desc ? `<p class="text-graphite dark:text-ash-border leading-relaxed text-[11px]">${escapeHtml(desc)}</p>` : ''}
                  </div>
                </div>
              `;
            });

            // Source scripts badges
            let sourceBadges = '';
            sourceScripts.forEach(s => {
              sourceBadges += `<span class="inline-block bg-fog dark:bg-slate text-graphite dark:text-mist font-geist-mono text-[10px] px-2 py-0.5 rounded-badges mr-1.5">${escapeHtml(s)}</span>`;
            });

            // Export JSON button
            const exportPayload = JSON.stringify(steps, null, 2);
            const escapedExport = escapeHtml(exportPayload).replace(/"/g, '&quot;');

            displayHtml = `
              <div class="w-full bg-white dark:bg-dark-surface border border-mist dark:border-slate rounded-cards p-8 font-geist text-left transition-colors">
                <div class="flex justify-between items-start mb-4 pb-4 border-b border-mist dark:border-slate">
                  <div>
                    <span class="font-bryant text-xs text-graphite dark:text-pewter uppercase tracking-bryant font-bold block mb-1">AI-Generated Test Steps</span>
                    <h3 class="font-geist text-base font-bold text-carbon-ink dark:text-paper-white">${escapeHtml(scenario)}</h3>
                    ${processArea ? `<span class="font-geist text-xs text-graphite dark:text-ash-border">${escapeHtml(processArea)}</span>` : ''}
                  </div>
                  <span class="font-geist-mono text-xs font-bold text-carbon-ink dark:text-mist bg-fog dark:bg-slate px-3 py-1.5 rounded-badges shrink-0">${steps.length} Steps</span>
                </div>

                <p class="text-[11px] text-graphite dark:text-ash-border italic mb-4">${escapeHtml(reasoning)}</p>

                ${sourceScripts.length > 0 ? `
                  <div class="mb-4">
                    <span class="font-bryant text-[10px] text-slate dark:text-pewter uppercase tracking-bryant font-bold block mb-1.5">Few-Shot Sources</span>
                    <div class="flex flex-wrap gap-1">${sourceBadges}</div>
                  </div>
                ` : ''}

                <div class="mb-2">
                  <span class="font-bryant text-[10px] text-carbon-ink dark:text-mist uppercase tracking-bryant font-bold block mb-2">Automation Step Sequence</span>
                  <div class="border border-mist dark:border-slate rounded-cards p-3 bg-fog/20 dark:bg-dark-surface/30 max-h-80 overflow-y-auto space-y-0">
                    ${stepsHtml || '<p class="py-4 text-graphite dark:text-pewter italic text-xs text-center">No steps generated.</p>'}
                  </div>
                </div>

                <div class="flex flex-wrap items-center gap-3 mt-5 pt-4 border-t border-mist dark:border-slate">
                  <button onclick="downloadWinfoTestCSV(this)" data-steps="${escapeHtml(JSON.stringify(steps)).replace(/"/g, '&quot;')}" data-scenario="${escapeHtml(scenario).replace(/"/g, '&quot;')}"
                    class="inline-flex items-center gap-1.5 bg-[#1e6f43] dark:bg-[#27c93f] text-white dark:text-carbon-ink rounded-buttons px-4 py-2 font-bryant text-xs uppercase tracking-bryant font-bold hover:opacity-90 transition-opacity cursor-pointer shadow-sm">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                    Download WinfoTest CSV
                  </button>
                  <button onclick="copyToClipboard(this)" data-code="${escapedExport}"
                    class="inline-flex items-center gap-1.5 bg-carbon-ink dark:bg-mist text-white dark:text-carbon-ink rounded-buttons px-4 py-2 font-bryant text-xs uppercase tracking-bryant font-bold hover:opacity-90 transition-opacity cursor-pointer">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
                    Copy JSON
                  </button>
                  <span class="text-[10px] text-graphite dark:text-pewter font-geist">WinfoTest CSV includes action verbs, locators, and {{Variable}} binds.</span>
                </div>
              </div>
            `;
          } else {

            displayHtml = `
              <div class="w-full bg-white dark:bg-dark-surface border border-mist dark:border-slate rounded-cards p-8 font-geist text-left transition-colors">
                <span class="font-bryant text-xs text-graphite dark:text-pewter uppercase tracking-bryant block mb-4 font-bold">${escapeHtml(tool)}</span>
                <pre class="font-geist-mono text-xs p-4 bg-fog dark:bg-[#151515] border border-ash-border dark:border-slate rounded-inputs overflow-x-auto text-[#24292e] dark:text-[#d1d5db] whitespace-pre">${escapeHtml(JSON.stringify(content, null, 2))}</pre>
              </div>
            `;
          }
        } else {
          displayHtml = `
            <div class="w-full bg-white dark:bg-dark-surface border border-mist dark:border-slate rounded-cards p-8 font-geist text-left transition-colors">
              <p class="text-sm text-carbon-ink dark:text-paper-white leading-relaxed">${escapeHtml(String(content))}</p>
            </div>
          `;
        }

        wrapper.innerHTML = `
          <div class="w-full animate-fade-in-up">
            ${displayHtml}
          </div>
        `;
      }

      chatFeed.appendChild(wrapper);
      chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: 'smooth' });
    }

    function escapeHtml(str) {
      if (!str) return '';
      return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    function formatMarkdownToHtml(text) {
      if (!text) return '';
      let cleanText = text.replace(/^```markdown\s*/gm, '').replace(/^```\s*/gm, '');
      let html = escapeHtml(cleanText);

      html = html.replace(/^### (.*?)$/gm, '<strong class="block mt-5 mb-1 text-carbon-ink dark:text-paper-white font-bryant tracking-bryant uppercase text-[10px]">$1</strong>');
      html = html.replace(/^## (.*?)$/gm, '<strong class="block mt-5 mb-1 text-carbon-ink dark:text-paper-white font-bryant tracking-bryant uppercase text-[11px]">$1</strong>');
      html = html.replace(/^# (.*?)$/gm, '<strong class="block mt-5 mb-2 text-carbon-ink dark:text-paper-white font-bryant tracking-bryant uppercase text-xs">$1</strong>');

      html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-carbon-ink dark:text-paper-white">$1</strong>');
      html = html.replace(/^- (.*?)$/gm, '<div class="ml-2 flex items-start gap-2 text-carbon-ink dark:text-mist"><span class="text-[10px] text-graphite dark:text-ash-border mt-0.5">•</span> <span>$1</span></div>');
      html = html.replace(/^• (.*?)$/gm, '<div class="ml-2 flex items-start gap-2 text-carbon-ink dark:text-mist"><span class="text-[10px] text-graphite dark:text-ash-border mt-0.5">•</span> <span>$1</span></div>');

      html = html.replace(/\n/g, '<br/>');
      return html;
    }

    function autoResizeInput() {
      userInput.style.height = 'auto';
      const newHeight = Math.min(userInput.scrollHeight, 180);
      userInput.style.height = newHeight + 'px';
      if (newHeight >= 180) {
        userInput.style.overflowY = 'auto';
      } else {
        userInput.style.overflowY = 'hidden';
      }
    }

    userInput.addEventListener('input', autoResizeInput);

    userInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
      }
    });

    chatForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const message = userInput.value.trim();
      if (!message) return;

      // Extract test data if present
      let testDataPayload = null;
      const testDataInput = document.getElementById('test-data-input');
      const testDataRaw = testDataInput ? testDataInput.value.trim() : '';
      if (testDataRaw) {
        try {
          testDataPayload = JSON.parse(testDataRaw);
        } catch (e) {
          testDataPayload = {};
          testDataRaw.split('\n').forEach(line => {
            const sep = line.includes(':') ? ':' : (line.includes('=') ? '=' : (line.includes(',') ? ',' : null));
            if (sep) {
              const [k, ...v] = line.split(sep);
              if (k && v.length) testDataPayload[k.trim()] = v.join(sep).trim();
            }
          });
        }
      }

      appendMessage('user', message, true);
      userInput.value = '';
      autoResizeInput();
      sendBtn.disabled = true;

      // Show the visible querying database indicator banner
      loadingIndicator.classList.remove('hidden-state');
      chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: 'smooth' });

      try {
        const payload = { 
            message: message,
            test_data: testDataPayload
        };
        if (window.activeAIContext) {
            payload.active_context = window.activeAIContext;
        }

        const response = await fetch("/api/v1/chat/stream", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        if (!response.ok) {
          loadingIndicator.classList.add('hidden-state');
          appendMessage('assistant', "Not working (Server returned error)", true);
          sendBtn.disabled = false;
          userInput.focus();
          return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        let streamingWrapper = null;
        let textBubble = null;
        let streamingText = '';
        let hasTextResponse = false;
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          
          // Process SSE lines
          let lines = buffer.split('\n');
          buffer = lines.pop(); // keep the last incomplete line in the buffer
          
          for (let line of lines) {
            line = line.trim();
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.substring(6));
                
                if (data.type === 'token') {
                  // Only create container once actual token text arrives!
                  if (!streamingWrapper) {
                    loadingIndicator.classList.add('hidden-state');
                    streamingWrapper = document.createElement('div');
                    streamingWrapper.className = 'flex w-full justify-start';
                    
                    const contentDiv = document.createElement('div');
                    contentDiv.className = 'w-full animate-fade-in-up';
                    
                    textBubble = document.createElement('div');
                    textBubble.className = 'w-full bg-white dark:bg-dark-surface border border-mist dark:border-slate rounded-cards p-6 mb-4 font-geist text-left transition-colors text-sm text-carbon-ink dark:text-paper-white leading-relaxed';
                    
                    contentDiv.appendChild(textBubble);
                    streamingWrapper.appendChild(contentDiv);
                    chatFeed.appendChild(streamingWrapper);
                  }

                  hasTextResponse = true;
                  streamingText += data.content;
                  textBubble.innerHTML = formatMarkdownToHtml(streamingText);
                  chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: 'smooth' });

                } else if (data.type === 'done') {
                  loadingIndicator.classList.add('hidden-state');

                  if (hasTextResponse && streamingText) {
                    saveMessageToStorage('assistant', streamingText);
                  }
                  
                  // Render the UI cards
                  if (data.results && Array.isArray(data.results)) {
                    for (const result of data.results) {
                      appendMessage('assistant', result, true);
                    }
                  }
                }
              } catch (e) {
                console.error("Failed to parse SSE JSON:", e, line);
              }
            }
          }
        }

      } catch (error) {
        loadingIndicator.classList.add('hidden-state');
        appendMessage('assistant', "Not working (Network or connection failure)", true);
      } finally {
        loadingIndicator.classList.add('hidden-state');
        sendBtn.disabled = false;
        userInput.focus();
      }
    });

    window.toggleTestDataDrawer = function () {
      const drawer = document.getElementById('test-data-drawer');
      const btn = document.getElementById('test-data-btn');
      if (drawer) {
        drawer.classList.toggle('hidden-state');
        if (!drawer.classList.contains('hidden-state')) {
          document.getElementById('test-data-input').focus();
          btn.classList.add('text-ember-red', 'dark:text-ember-red');
        } else {
          btn.classList.remove('text-ember-red', 'dark:text-ember-red');
        }
      }
    };

    window.handleTestDataFileUpload = function (input) {
      if (!input.files || !input.files[0]) return;
      const file = input.files[0];
      const reader = new FileReader();
      reader.onload = function (e) {
        const content = e.target.result;
        document.getElementById('test-data-input').value = content;
        const drawer = document.getElementById('test-data-drawer');
        if (drawer.classList.contains('hidden-state')) {
          drawer.classList.remove('hidden-state');
        }
        document.getElementById('test-data-btn').classList.add('text-ember-red', 'dark:text-ember-red');
      };
      reader.readAsText(file);
    };

    window.downloadWinfoTestCSV = async function (btn) {
      try {
        const rawSteps = btn.getAttribute('data-steps');
        const scenario = btn.getAttribute('data-scenario') || 'winfotest_steps';
        const steps = JSON.parse(rawSteps);
        
        const response = await fetch('/api/v1/export/steps-csv', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ steps: steps })
        });
        
        if (!response.ok) throw new Error('Failed to generate CSV');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const cleanName = scenario.replace(/[^a-zA-Z0-9_\-]/g, '_').substring(0, 35);
        a.download = `${cleanName || 'winfotest_steps'}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      } catch (err) {
        console.error('Failed to export CSV:', err);
        alert('Could not export CSV file.');
      }
    };

    window.copyToClipboard = function (button) {
      const code = button.getAttribute('data-code');
      const textarea = document.createElement('textarea');
      textarea.innerHTML = code;
      const decodedCode = textarea.value;

      navigator.clipboard.writeText(decodedCode).then(() => {
        const originalHtml = button.innerHTML;
        button.innerHTML = `<svg class="w-3.5 h-3.5 text-[#27c93f]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg> <span class="text-[#27c93f]">Copied!</span>`;

        setTimeout(() => {
          button.innerHTML = originalHtml;
        }, 2000);
      });
    };


    // ── Tab Switching & Analytics JS ──
    let activeTab = 'chat';
    let cachedRiskData = [];
    let cachedScripts = [];

    window.switchTab = function(tabName) {
      activeTab = tabName;
      try {
        localStorage.setItem('winfotest_active_tab', tabName);
        if (history.replaceState) {
          history.replaceState(null, null, '#' + tabName);
        }
      } catch(e) {}
      
      const sidebar = document.querySelector('aside');
      const chatView = document.getElementById('chat-container');
      const emptyState = document.getElementById('empty-state');
      const chatFeed = document.getElementById('chat-feed');
      const analyticsView = document.getElementById('bento-analytics-view');
      const workbenchView = document.getElementById('script-workbench-view');
      const inputFooter = document.querySelector('footer');

      const btnChat = document.getElementById('tab-btn-chat');
      const btnAnalytics = document.getElementById('tab-btn-analytics');
      const btnWorkbench = document.getElementById('tab-btn-workbench');

      // User has manual control of sidebar across all tabs

      // Reset button styles
      [btnChat, btnAnalytics, btnWorkbench].forEach(btn => {
        if (btn) {
          btn.className = "px-3 py-1 rounded-[3px] font-bryant text-xs uppercase tracking-bryant font-bold transition-all duration-200 cursor-pointer text-graphite dark:text-pewter hover:text-carbon-ink dark:hover:text-mist";
        }
      });

      // Hide all views first
      if (chatView) chatView.classList.add('hidden-state');
      if (analyticsView) analyticsView.classList.add('hidden-state');
      if (workbenchView) workbenchView.classList.add('hidden-state');
      if (inputFooter) inputFooter.classList.add('hidden-state');

      if (tabName === 'chat') {
        if (chatView) chatView.classList.remove('hidden-state');
        if (inputFooter) inputFooter.classList.remove('hidden-state');
        if (btnChat) btnChat.className = "px-3 py-1 rounded-[3px] font-bryant text-xs uppercase tracking-bryant font-bold transition-all duration-200 cursor-pointer bg-white dark:bg-dark-surface text-carbon-ink dark:text-paper-white shadow-sm";
        const miniChatContainer = document.getElementById('mini-chat-container');
        if (miniChatContainer) miniChatContainer.classList.add('hidden');
      } else if (tabName === 'analytics') {
        if (analyticsView) analyticsView.classList.remove('hidden-state');
        if (btnAnalytics) btnAnalytics.className = "px-3 py-1 rounded-[3px] font-bryant text-xs uppercase tracking-bryant font-bold transition-all duration-200 cursor-pointer bg-white dark:bg-dark-surface text-carbon-ink dark:text-paper-white shadow-sm";
        const miniChatContainer = document.getElementById('mini-chat-container');
        if (miniChatContainer) miniChatContainer.classList.remove('hidden');
        fetchBentoData();
      } else if (tabName === 'workbench') {
        if (workbenchView) workbenchView.classList.remove('hidden-state');
        if (btnWorkbench) btnWorkbench.className = "px-3 py-1 rounded-[3px] font-bryant text-xs uppercase tracking-bryant font-bold transition-all duration-200 cursor-pointer bg-white dark:bg-dark-surface text-carbon-ink dark:text-paper-white shadow-sm";
        const miniChatContainer = document.getElementById('mini-chat-container');
        if (miniChatContainer) miniChatContainer.classList.remove('hidden');
        loadWorkbenchScripts();
      }
    };

    let passRateChartInstance = null;
    let toolUsageChartInstance = null;

    window.fetchBentoData = async function() {
      try {
        const res = await fetch('/api/v1/analytics/overview');
        if (!res.ok) return;
        const data = await res.json();
        
        if (data.status === 'success') {
          // KPI Row 1
          document.getElementById('kpi-total-calls').innerText = data.telemetry?.total_calls || 0;
          document.getElementById('kpi-avg-latency').innerText = (data.telemetry?.avg_duration_ms || 320) + 'ms';
          document.getElementById('kpi-success-rate').innerText = (data.telemetry?.success_rate || 98.6) + '%';
          document.getElementById('kpi-health-score').innerText = data.health?.overall_score || 92;

          // Vector Store
          if (document.getElementById('bento-total-chunks')) document.getElementById('bento-total-chunks').innerText = (data.vector_store?.total_chunks || 0).toLocaleString();
          if (document.getElementById('bento-dim')) document.getElementById('bento-dim').innerText = (data.vector_store?.dimension || 768) + '-d';
          if (document.getElementById('bento-model')) document.getElementById('bento-model').innerText = data.vector_store?.embedding_model || 'all-mpnet-base-v2';
          if (document.getElementById('bento-collection')) document.getElementById('bento-collection').innerText = data.vector_store?.collection_name || 'winfotest_semantic_scripts';
          if (document.getElementById('bento-qdrant-status')) document.getElementById('bento-qdrant-status').innerText = 'QDRANT ' + (data.vector_store?.status || 'ONLINE');
          
          // Indexation
          if (document.getElementById('bento-sync-pct')) document.getElementById('bento-sync-pct').innerText = (data.indexation?.sync_percentage || 100) + '%';
          if (document.getElementById('bento-synced-count')) document.getElementById('bento-synced-count').innerText = (data.indexation?.indexed_scripts || 0) + ' / ' + (data.indexation?.total_scripts || 0);
          if (document.getElementById('bento-stale-chunks')) document.getElementById('bento-stale-chunks').innerText = data.indexation?.stale_chunks || 0;
          if (document.getElementById('bento-sync-bar')) document.getElementById('bento-sync-bar').style.width = (data.indexation?.sync_percentage || 100) + '%';
          
          // Server
          if (document.getElementById('server-fastapi')) document.getElementById('server-fastapi').innerText = data.server?.fastapi + ' (8000)';
          if (document.getElementById('server-postgres')) document.getElementById('server-postgres').innerText = data.server?.postgres;
          if (document.getElementById('server-qdrant')) document.getElementById('server-qdrant').innerText = data.server?.qdrant + ' (6333)';
          if (document.getElementById('bento-llm-name')) document.getElementById('bento-llm-name').innerText = data.server?.llm_engine || 'Qwen 2.5 Coder';

          // Old Telemetry fallback (if they exist)
          if (document.getElementById('bento-total-calls')) document.getElementById('bento-total-calls').innerText = (data.telemetry?.total_calls || 0) + ' Invocations';
          if (document.getElementById('bento-avg-latency')) document.getElementById('bento-avg-latency').innerText = (data.telemetry?.avg_duration_ms || 320) + 'ms';
          if (document.getElementById('bento-success-rate')) document.getElementById('bento-success-rate').innerText = (data.telemetry?.success_rate || 98.6) + '%';
          if (document.getElementById('bento-error-count')) document.getElementById('bento-error-count').innerText = data.telemetry?.error_count || 0;

          // Render Tool Usage Donut
          if (data.telemetry && data.telemetry.tool_distribution) {
            const toolCtx = document.getElementById('tool-usage-chart');
            if (toolCtx) {
              const toolLabels = Object.keys(data.telemetry.tool_distribution);
              const toolData = Object.values(data.telemetry.tool_distribution);
              
              if (toolUsageChartInstance) toolUsageChartInstance.destroy();
              toolUsageChartInstance = new Chart(toolCtx, {
                type: 'doughnut',
                data: {
                  labels: toolLabels,
                  datasets: [{
                    data: toolData,
                    backgroundColor: ['#27c93f', '#cc2e39', '#eef1f0', '#606562', '#363537', '#1a211e'],
                    borderWidth: 0
                  }]
                },
                options: {
                  responsive: true,
                  maintainAspectRatio: false,
                  cutout: '75%',
                  plugins: {
                    legend: { position: 'right', labels: { color: '#cccfcd', font: { family: 'Geist' }, boxWidth: 10 } }
                  }
                }
              });
            }
          }
        }
        
        // Fetch Trend Data
        const trendRes = await fetch('/api/v1/analytics/test-health');
        if (trendRes.ok) {
           const trendData = await trendRes.json();
           if (trendData.status === 'success') {
             const trendCtx = document.getElementById('pass-rate-chart');
             if (trendCtx) {
               if (passRateChartInstance) passRateChartInstance.destroy();
               
               if (document.getElementById('trend-total-runs')) document.getElementById('trend-total-runs').innerText = trendData.total_runs + ' total runs';
               
               passRateChartInstance = new Chart(trendCtx, {
                 type: 'bar',
                 data: {
                   labels: trendData.labels,
                   datasets: [
                     { label: 'Passed', data: trendData.passed, backgroundColor: '#27c93f' },
                     { label: 'Failed', data: trendData.failed, backgroundColor: '#cc2e39' }
                   ]
                 },
                 options: {
                   responsive: true,
                   maintainAspectRatio: false,
                   scales: {
                     x: { stacked: true, grid: { display: false } },
                     y: { stacked: true, grid: { color: '#333' } }
                   },
                   plugins: {
                     legend: { display: false }
                   }
                 }
               });
             }
           }
        }

        // Fetch Oracle Bot Status
        const botRes = await fetch('/api/v1/oracle-bot/status');
        if (botRes.ok) {
           const botData = await botRes.json();
           if (botData.status === 'success') {
             if (document.getElementById('bot-status-badge')) {
               document.getElementById('bot-status-badge').innerText = botData.bot_running ? 'ACTIVE' : 'IDLE';
             }
             if (document.getElementById('bot-last-run')) {
               document.getElementById('bot-last-run').innerText = botData.last_run ? new Date(botData.last_run).toLocaleString() : 'Never';
             }
             if (document.getElementById('bot-scripts-scanned')) {
               document.getElementById('bot-scripts-scanned').innerText = botData.scripts_scanned || 0;
             }
             if (document.getElementById('bot-patches-applied')) {
               document.getElementById('bot-patches-applied').innerText = botData.patches_applied || 0;
             }
           }
        }

        // Fetch Risk Matrix
        const riskRes = await fetch('/api/v1/analytics/risk');
        if (riskRes.ok) {
          const riskData = await riskRes.json();
          cachedRiskData = riskData.risk_items || [];
          renderRiskMatrix(cachedRiskData);
        }
      } catch (e) {
        console.error('Error fetching bento data:', e);
      }
    };

    function renderRiskMatrix(items) {
      const tbody = document.getElementById('risk-matrix-body');
      if (!tbody) return;
      if (!items || items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="py-6 text-center text-graphite font-geist-mono">No scripts match current filter criteria.</td></tr>`;
        return;
      }

      tbody.innerHTML = items.map(item => {
        let tierBadgeClass = 'bg-fog dark:bg-slate text-carbon-ink dark:text-mist';
        if (item.risk_tier === 'CRITICAL') tierBadgeClass = 'bg-ember-red text-white';
        else if (item.risk_tier === 'HIGH') tierBadgeClass = 'bg-amber-600 text-white';
        else if (item.risk_tier === 'MEDIUM') tierBadgeClass = 'bg-blue-600 text-white';

        return `
          <tr class="hover:bg-fog/50 dark:hover:bg-[#151515] transition-colors">
            <td class="py-2.5 px-3 font-geist-mono font-bold text-carbon-ink dark:text-paper-white select-all">${escapeHtml(item.test_script_number)}</td>
            <td class="py-2.5 px-3 font-semibold">${escapeHtml(item.script_name)}</td>
            <td class="py-2.5 px-3 text-graphite dark:text-ash-border">${escapeHtml(item.module || 'N/A')}</td>
            <td class="py-2.5 px-3 text-center font-geist-mono font-bold">${item.risk_score}</td>
            <td class="py-2.5 px-3 text-center">
              <span class="px-2 py-0.5 rounded-[3px] text-[10px] font-bryant font-bold uppercase ${tierBadgeClass}">${item.risk_tier}</span>
            </td>
            <td class="py-2.5 px-3 font-geist-mono text-[11px] text-graphite dark:text-pewter">${escapeHtml(item.most_fragile_step || 'N/A')}</td>
            <td class="py-2.5 px-3 text-graphite dark:text-ash-border leading-tight">${escapeHtml(item.stabilization_recommendation || 'Stable execution.')}</td>
          </tr>
        `;
      }).join('');
    }

    window.filterRiskMatrix = function() {
      const q = (document.getElementById('risk-search-input').value || '').toLowerCase();
      if (!q) {
        renderRiskMatrix(cachedRiskData);
        return;
      }
      const filtered = cachedRiskData.filter(i => 
        (i.test_script_number || '').toLowerCase().includes(q) ||
        (i.script_name || '').toLowerCase().includes(q) ||
        (i.module || '').toLowerCase().includes(q)
      );
      renderRiskMatrix(filtered);
    };

    // ── Pagination State ──
    let wbCurrentPage = 1;
    let wbPageSize = 10;
    let wbFilteredScripts = [];

    window.loadWorkbenchScripts = async function() {
      try {
        const res = await fetch('/api/v1/scripts');
        if (!res.ok) return;
        const data = await res.json();
        cachedScripts = data.scripts || [];
        wbFilteredScripts = [...cachedScripts];
        wbCurrentPage = 1;
        renderWorkbenchScripts();
      } catch (e) {
        console.error('Error loading scripts:', e);
      }
    };

    function renderWorkbenchScripts() {
      const tbody = document.getElementById('workbench-script-body');
      if (!tbody) return;
      
      const total = wbFilteredScripts.length;
      if (total === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="py-6 text-center text-graphite font-geist-mono">No scripts found.</td></tr>`;
        updatePaginationInfo(0, 0, 0, 1, 1);
        return;
      }

      const totalPages = Math.ceil(total / wbPageSize);
      if (wbCurrentPage > totalPages) wbCurrentPage = totalPages;
      if (wbCurrentPage < 1) wbCurrentPage = 1;

      const startIdx = (wbCurrentPage - 1) * wbPageSize;
      const endIdx = Math.min(startIdx + wbPageSize, total);
      const pageItems = wbFilteredScripts.slice(startIdx, endIdx);

      tbody.innerHTML = pageItems.map(s => `
        <tr class="hover:bg-[#121212] transition-colors">
          <td class="py-2.5 px-3 font-geist-mono font-bold text-white select-all">${escapeHtml(s.test_script_number || 'N/A')}</td>
          <td class="py-2.5 px-3 font-semibold text-white">${escapeHtml(s.script_name || s.name || 'Unnamed')}</td>
          <td class="py-2.5 px-3 text-[#a0a4a1]">${escapeHtml(s.module || 'N/A')}</td>
          <td class="py-2.5 px-3 text-[#a0a4a1]">${escapeHtml(s.process || s.process_area || 'General')}</td>
          <td class="py-2.5 px-3 text-right">
            <button onclick="viewScriptSteps('${s.id}')" class="px-3 py-1 border border-[#333] text-white hover:bg-white hover:text-obsidian rounded-[3px] font-bryant text-xs uppercase tracking-bryant font-bold transition-all cursor-pointer">
              Inspect Steps
            </button>
          </td>
        </tr>
      `).join('');

      updatePaginationInfo(startIdx + 1, endIdx, total, wbCurrentPage, totalPages);
    }

    function updatePaginationInfo(start, end, total, page, totalPages) {
      const infoEl = document.getElementById('workbench-total-info');
      const numEl = document.getElementById('workbench-page-num');
      const prevBtn = document.getElementById('workbench-prev-btn');
      const nextBtn = document.getElementById('workbench-next-btn');

      if (infoEl) infoEl.innerText = `Showing ${start}-${end} of ${total} scripts`;
      if (numEl) numEl.innerText = `Page ${page} of ${totalPages || 1}`;
      if (prevBtn) prevBtn.disabled = (page <= 1);
      if (nextBtn) nextBtn.disabled = (page >= totalPages);
    }

    window.changePageSize = function(val) {
      wbPageSize = parseInt(val, 10) || 10;
      wbCurrentPage = 1;
      renderWorkbenchScripts();
    };

    window.prevPage = function() {
      if (wbCurrentPage > 1) {
        wbCurrentPage--;
        renderWorkbenchScripts();
      }
    };

    window.nextPage = function() {
      const totalPages = Math.ceil(wbFilteredScripts.length / wbPageSize);
      if (wbCurrentPage < totalPages) {
        wbCurrentPage++;
        renderWorkbenchScripts();
      }
    };

    window.filterWorkbenchScripts = function() {
      const q = (document.getElementById('workbench-search').value || '').toLowerCase();
      if (!q) {
        wbFilteredScripts = [...cachedScripts];
      } else {
        wbFilteredScripts = cachedScripts.filter(s => 
          (s.test_script_number || '').toLowerCase().includes(q) ||
          (s.script_name || s.name || '').toLowerCase().includes(q) ||
          (s.module || '').toLowerCase().includes(q)
        );
      }
      wbCurrentPage = 1;
      renderWorkbenchScripts();
    };

    // Direct Database Query for Exact Script Steps (No LLM, Instant PostgreSQL Lookup)
    window.viewScriptSteps = async function(scriptId) {
      const script = cachedScripts.find(s => String(s.id) === String(scriptId));
      
      const modal = document.getElementById('step-modal');
      const content = document.getElementById('modal-step-content');
      
      if (script) {
        document.getElementById('modal-script-num').innerText = script.test_script_number || 'TS-001';
        document.getElementById('modal-script-title').innerText = script.script_name || script.name || 'Step Inspection';
        
        // Update AI Context
        window.activeAIContext = { type: 'script', id: script.id, name: script.script_name || script.name };
        console.log("Active AI Context set to:", window.activeAIContext);
      }

      modal.classList.remove('hidden-state');

      content.innerHTML = `
        <div class="p-4 bg-[#121212] border border-[#222] rounded-cards space-y-2 mb-4">
          <div class="flex justify-between text-xs text-white">
            <span>Module: <strong class="text-white">${escapeHtml(script ? (script.module || 'N/A') : 'N/A')}</strong></span>
            <span>Process Area: <strong class="text-white">${escapeHtml(script ? (script.process || script.process_area || 'General') : 'N/A')}</strong></span>
          </div>
          <p class="text-xs text-[#888c89] leading-relaxed">${escapeHtml(script ? (script.description || 'Direct PostgreSQL script definition.') : '')}</p>
        </div>
        <div class="text-center py-6 font-geist-mono text-graphite">Querying PostgreSQL for exact step sequence...</div>
      `;

      try {
        const res = await fetch(`/api/v1/scripts/${encodeURIComponent(scriptId)}/steps`);
        if (!res.ok) throw new Error('Direct DB query failed');
        const data = await res.json();

        const stepsArr = data.steps || [];
        if (window.activeAIContext && window.activeAIContext.id === scriptId) {
          // Send a simplified version of the steps to the AI so it doesn't hallucinate
          window.activeAIContext.steps = stepsArr.map(s => ({
             step_num: s.step_sequence || s.step_number,
             action: s.action || s.keyword,
             target: s.target || s.object_name,
             value: s.value || s.input_value
          }));
        }
        
        if (stepsArr.length === 0) {
          content.innerHTML = `<div class="p-6 text-center text-graphite font-geist-mono">No steps found in PostgreSQL master_steps or test_run_script_steps for this script.</div>`;
          return;
        }

        content.innerHTML = stepsArr.map((st, i) => `
          <div class="step-item p-3 bg-[#0d0d0d] border border-[#222] rounded-cards flex flex-col gap-1.5 font-geist opacity-0" style="transform: translateY(16px);">
            <div class="flex justify-between items-center">
              <span class="font-geist-mono font-bold text-white text-xs">Step ${st.step_no || i+1}: <span class="uppercase text-[#27c93f]">${escapeHtml(st.step_action || st.action || 'ACTION')}</span></span>
              <span class="font-geist-mono text-[10px] text-[#a0a4a1] bg-[#1a1a1a] px-2 py-0.5 rounded-badges border border-[#333]">${escapeHtml(st.input_parameter || 'No Input Value')}</span>
            </div>
            <p class="text-xs text-[#d1d5db] leading-relaxed">${escapeHtml(st.step_description || 'Step execution.')}</p>
          </div>
        `).join('');

        if (typeof anime !== 'undefined') {
          anime({
            targets: '.step-item',
            translateY: [16, 0],
            opacity: [0, 1],
            delay: anime.stagger(40),
            duration: 600,
            easing: 'easeOutQuart'
          });
        }


        document.getElementById('modal-csv-btn').onclick = function() {
          downloadWinfoTestCSV({
            getAttribute: (attr) => attr === 'data-steps' ? JSON.stringify(stepsArr) : (script ? script.test_script_number : 'steps')
          });
        };
      } catch (err) {
        console.error('Error fetching steps:', err);
        content.innerHTML = `<div class="p-6 text-center text-ember-red font-geist-mono">Failed to retrieve exact steps from PostgreSQL database.</div>`;
      }
    };

    window.healLocator = async function(scriptName, stepNo, newLocator) {
      try {
        const res = await fetch('/api/v1/heal-locator', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            script_name: scriptName,
            step_no: stepNo,
            new_locator: newLocator
          })
        });
        
        const data = await res.json();
        
        if (data.status === 'success') {
          // Toast notification or visual change
          alert(`Success: ${data.message}`);
          // You could also visually disable the heal button here to show it was applied
        } else {
          alert(`Error: ${data.message}`);
        }
      } catch (err) {
        console.error('Failed to heal locator:', err);
        alert('Network error while attempting to heal locator.');
      }
    };

    window.closeStepModal = function() {
      document.getElementById('step-modal').classList.add('hidden-state');
      // Clear AI context when modal closes (optional, depending on desired UX)
      // window.activeAIContext = null; 
    };

    // Restore persistent chat history & saved active tab on page load
    document.addEventListener('DOMContentLoaded', () => {
      loadChatHistory();
      
      const hashTab = (window.location.hash || '').replace('#', '').trim();
      const savedTab = hashTab || localStorage.getItem('winfotest_active_tab') || 'chat';
      if (['chat', 'analytics', 'workbench'].includes(savedTab)) {
        switchTab(savedTab);
      }
    });

    // ── Mini Chat Feature ──
    window.miniChatSessionId = null;

    let expandClickTimer = null;
    let isHalfScreen = false;

    window.handleExpandClick = function() {
      if (expandClickTimer) {
        clearTimeout(expandClickTimer);
        expandClickTimer = null;
        expandMiniChatFull();
      } else {
        expandClickTimer = setTimeout(() => {
          expandClickTimer = null;
          toggleHalfScreen();
        }, 250);
      }
    };

    window.toggleHalfScreen = function() {
      const panel = document.getElementById('mini-chat-panel');
      const fab = document.getElementById('mini-chat-fab');
      isHalfScreen = !isHalfScreen;
      
      if (typeof anime !== 'undefined') {
        anime({
          targets: panel,
          width: isHalfScreen ? '45vw' : '20rem',
          height: isHalfScreen ? '85vh' : '24rem',
          bottom: isHalfScreen ? '7.5vh' : '6rem',
          duration: 600,
          easing: 'spring(1, 80, 10, 0)'
        });
        
        if (fab) {
          anime({
            targets: fab,
            opacity: isHalfScreen ? 0 : 1,
            scale: isHalfScreen ? 0 : 1,
            duration: 300,
            easing: 'easeOutQuad',
            complete: () => {
              if (isHalfScreen) {
                fab.style.pointerEvents = 'none';
              } else {
                fab.style.pointerEvents = 'auto';
              }
            }
          });
        }
        
        // Find step-modal's wrapper and adjust padding so flexbox centers it naturally without overflowing left
        const stepModal = document.getElementById('step-modal');
        if (stepModal && !stepModal.classList.contains('hidden-state')) {
          anime({
            targets: stepModal,
            paddingRight: isHalfScreen ? '45vw' : '1rem',
            duration: 600,
            easing: 'spring(1, 80, 10, 0)'
          });
        }
      }
    };

    window.expandMiniChatFull = function() {
      toggleMiniChat();
      if (isHalfScreen) toggleHalfScreen(); // reset it back
      
      // Close the step inspector modal if it is open
      const stepModal = document.getElementById('step-modal');
      if (stepModal) stepModal.classList.add('hidden-state');

      switchTab('chat');
      
      if (window.miniChatSessionId) {
        // Set the active session to the one we just started in the mini chat
        currentSessionId = window.miniChatSessionId;
        localStorage.setItem(ACTIVE_SESSION_KEY, currentSessionId);
        window.miniChatSessionId = null; // Reset for next mini chat usage
      }

      const miniInput = document.getElementById('mini-user-input');
      const mainInput = document.getElementById('user-input');
      if (miniInput && mainInput && miniInput.value.trim() !== '') {
        mainInput.value = miniInput.value;
        miniInput.value = '';
        mainInput.focus();
      }
      if (typeof loadChatHistory === 'function') {
        loadChatHistory();
        renderSidebarConversations();
      }
    };

    window.toggleMiniChat = function() {
      const panel = document.getElementById('mini-chat-panel');
      if (panel.classList.contains('hidden-state')) {
        panel.classList.remove('hidden-state');
        // HeroUI-inspired bouncy spring animation
        if (typeof anime !== 'undefined') {
          anime({
            targets: panel,
            scale: [0.5, 1],
            opacity: [0, 1],
            duration: 800,
            easing: 'spring(1, 80, 10, 0)'
          });
        } else {
          panel.style.opacity = '1';
          panel.style.transform = 'scale(1)';
        }
        document.getElementById('mini-user-input').focus();
      } else {
        if (isHalfScreen) toggleHalfScreen();
        if (typeof anime !== 'undefined') {
          anime({
            targets: panel,
            scale: [1, 0.5],
            opacity: [1, 0],
            duration: 250,
            easing: 'easeInQuad',
            complete: () => {
              panel.classList.add('hidden-state');
            }
          });
        } else {
          panel.style.opacity = '0';
          panel.style.transform = 'scale(0.5)';
          panel.classList.add('hidden-state');
        }
      }
    };

    const miniChatForm = document.getElementById('mini-chat-form');
    if (miniChatForm) {
      miniChatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const miniInput = document.getElementById('mini-user-input');
        const query = miniInput.value.trim();
        if (!query) return;

        const feed = document.getElementById('mini-chat-feed');
        miniInput.value = '';

        // Render user message
        const userHtml = `<div class="bg-carbon-ink dark:bg-mist text-white dark:text-carbon-ink p-3 rounded-lg text-xs leading-relaxed self-end max-w-[85%] font-semibold">${escapeHtml(query)}</div>`;
        feed.insertAdjacentHTML('beforeend', userHtml);
        feed.scrollTop = feed.scrollHeight;

        // Render loading animation
        const loadingId = 'loading-' + Date.now();
        const loadingHtml = `<div id="${loadingId}" class="bg-fog dark:bg-[#151515] border border-mist dark:border-slate p-3 rounded-lg text-xs self-start text-graphite dark:text-pewter flex items-center gap-2">
                               <div class="w-1.5 h-1.5 bg-graphite dark:bg-pewter rounded-full animate-bounce"></div>
                               <div class="w-1.5 h-1.5 bg-graphite dark:bg-pewter rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                               <div class="w-1.5 h-1.5 bg-graphite dark:bg-pewter rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                             </div>`;
        feed.insertAdjacentHTML('beforeend', loadingHtml);
        feed.scrollTop = feed.scrollHeight;

        try {
          // Save user query instantly to active session
          let currentSessions = getAllSessions();
          if (window.currentSessionId && currentSessions[window.currentSessionId]) {
            currentSessions[window.currentSessionId].messages.push({ role: 'user', content: query });
            saveSessions(currentSessions);
          }
          
          const reqBody = { message: query, session_id: window.currentSessionId || 'default', low_memory_mode: window.lowMemoryMode };
          if (window.activeAIContext) {
            reqBody.active_context = window.activeAIContext;
          }

          const response = await fetch('/api/v1/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(reqBody)
          });

          const loadingEl = document.getElementById(loadingId);
          if (loadingEl) loadingEl.remove();

          if (!response.ok) throw new Error('API Error');

          const reader = response.body.getReader();
          const decoder = new TextDecoder("utf-8");
          let botMessageHtml = '';
          const msgId = 'bot-' + Date.now();
          
          feed.insertAdjacentHTML('beforeend', `<div id="${msgId}" class="bg-fog dark:bg-[#151515] border border-mist dark:border-slate p-3 rounded-lg text-xs leading-relaxed self-start max-w-[85%]"></div>`);
          const msgEl = document.getElementById(msgId);
          feed.scrollTop = feed.scrollHeight;
          let buffer = '';

          let toolResults = [];

          while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            let lines = buffer.split('\n');
            buffer = lines.pop(); // keep incomplete line
            
            for (let line of lines) {
              line = line.trim();
              if (line.startsWith('data: ')) {
                const dataStr = line.replace('data: ', '');
                try {
                  const data = JSON.parse(dataStr);
                  if (data.type === 'thinking_step') {
                     // Ensure thinking timeline exists
                     let thinkingTimeline = document.getElementById('thinking-timeline');
                     if (!thinkingTimeline) {
                        thinkingTimeline = document.createElement('div');
                        thinkingTimeline.id = 'thinking-timeline';
                        thinkingTimeline.className = 'flex flex-col gap-2 mb-3 px-2 border-l-2 border-carbon-ink dark:border-mist ml-2 opacity-80';
                        msgEl.before(thinkingTimeline);
                     }
                     // Add animated step
                     const stepId = 'step-' + Date.now();
                     const stepHtml = \<div id="" class="text-[10px] font-geist-mono text-graphite dark:text-pewter flex items-center gap-2">
                        <span class="w-1.5 h-1.5 rounded-full bg-ember-red animate-pulse"></span>
                        <span>\</span>
                     </div>\;
                     thinkingTimeline.insertAdjacentHTML('beforeend', stepHtml);
                     
                     // If complete, fade out the whole timeline after a short delay
                     if (data.stage === 'complete') {
                        setTimeout(() => {
                           if (thinkingTimeline) {
                              thinkingTimeline.style.transition = "opacity 0.5s ease-out, height 0.5s ease-out";
                              thinkingTimeline.style.opacity = '0';
                              setTimeout(() => thinkingTimeline.remove(), 500);
                           }
                        }, 2000);
                     }
                     feed.scrollTop = feed.scrollHeight;
                  } else if (data.type === 'token') {
                    botMessageHtml += data.content;
                    // Format markdown if available, else escape
                    if (typeof formatMarkdownToHtml === 'function') {
                      msgEl.innerHTML = formatMarkdownToHtml(botMessageHtml);
                    } else {
                      msgEl.innerHTML = escapeHtml(botMessageHtml).replace(/\n/g, '<br>');
                    }
                    feed.scrollTop = feed.scrollHeight;
                  } else if (data.type === 'done') {
                    if (data.results && data.results.length > 0) {
                       toolResults = data.results;
                       let resHtml = `<div class="mt-2 text-[10px] text-graphite dark:text-pewter italic">Executed tool: ${escapeHtml(data.results[0].tool)}</div>`;
                       
                       // Try to format explanations or text results directly if available
                       if (data.results[0].explanation) {
                           resHtml += `<div class="mt-2 text-carbon-ink dark:text-paper-white text-xs leading-relaxed">${formatMarkdownToHtml ? formatMarkdownToHtml(data.results[0].explanation) : escapeHtml(data.results[0].explanation)}</div>`;
                       } else if (data.results[0].generated_steps) {
                           resHtml += `<div class="mt-2 text-carbon-ink dark:text-paper-white text-xs leading-relaxed">Generated ${data.results[0].generated_steps.length} steps. Open in main chat for full view.</div>`;
                       } else {
                           resHtml += `<div class="mt-2 bg-[#151515] p-2 rounded max-h-40 overflow-y-auto"><pre class="text-[10px] text-ash-border whitespace-pre-wrap">${escapeHtml(JSON.stringify(data.results[0], null, 2))}</pre></div>`;
                       }
                       
                       msgEl.insertAdjacentHTML('beforeend', resHtml);
                       feed.scrollTop = feed.scrollHeight;
                    }
                  }
                } catch (e) {}
              }
            }
          }
          
          // Save to local storage for persistence when expanded
          const finalSessions = getAllSessions();
          if (window.currentSessionId && finalSessions[window.currentSessionId]) {
            // Check if explanation exists
            if (toolResults.length > 0) {
                finalSessions[window.currentSessionId].messages.push({ role: 'assistant', content: toolResults[0] });
            } else {
                finalSessions[window.currentSessionId].messages.push({ role: 'assistant', content: botMessageHtml });
            }
            saveSessions(finalSessions);
          }
        } catch (error) {
          const loadingEl = document.getElementById(loadingId);
          if (loadingEl) loadingEl.remove();
          feed.insertAdjacentHTML('beforeend', `<div class="bg-fog dark:bg-[#151515] border border-mist dark:border-slate p-3 rounded-lg text-xs leading-relaxed self-start text-ember-red">Error: Could not connect to AI service.</div>`);
        }
      });
    }
    window.runOracleBot = async function() {
      const btn = document.getElementById('oracle-bot-btn');
      if (btn) {
         btn.innerText = 'Running...';
         btn.disabled = true;
         btn.classList.add('opacity-50');
      }
      try {
        const res = await fetch('/api/v1/oracle-bot/run', {method: 'POST'});
        if (res.ok) {
           window.fetchBentoData(); // Refresh UI
        }
      } catch (e) {
        console.error('Error running bot', e);
      } finally {
        if (btn) {
           btn.innerText = 'Run Now';
           btn.disabled = false;
           btn.classList.remove('opacity-50');
        }
      }
    };
