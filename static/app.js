// Global State
let leadsData = [];
let activeTab = 'tocall';
let searchQuery = '';
let tzFilter = 'ALL';
let expandedSlug = null;
let selectedIndex = 0;
let currentFilteredLeads = [];

// Web Audio API Chime for Celebrations
function playSuccessChime() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(523.25, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(659.25, ctx.currentTime + 0.1);
    osc.frequency.exponentialRampToValueAtTime(783.99, ctx.currentTime + 0.2);
    osc.frequency.exponentialRampToValueAtTime(1046.50, ctx.currentTime + 0.3);
    gain.gain.setValueAtTime(0.2, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.6);
  } catch (e) {
    // Ignore audio errors
  }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
  initEventListeners();
  initKeyboardShortcuts();
  loadLeads();
  updateLiveClocks();
  setInterval(updateLiveClocks, 1000); // 1-sec live second/minute clock tick
  setInterval(loadLeads, 30000); // 30-sec live leads sync
});

function initEventListeners() {
  // Filter Tabs
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeTab = btn.getAttribute('data-tab');
      selectedIndex = 0;
      renderTable();
    });
  });

  // Search Input
  const searchInput = document.getElementById('searchInput');
  const clearSearch = document.getElementById('clearSearch');
  searchInput.addEventListener('input', (e) => {
    searchQuery = e.target.value.toLowerCase().trim();
    clearSearch.style.display = searchQuery ? 'block' : 'none';
    selectedIndex = 0;
    renderTable();
  });

  clearSearch.addEventListener('click', () => {
    searchInput.value = '';
    searchQuery = '';
    clearSearch.style.display = 'none';
    renderTable();
  });

  // Timezone Filter Dropdown
  document.getElementById('tzFilter').addEventListener('change', (e) => {
    tzFilter = e.target.value;
    selectedIndex = 0;
    updateLiveClocks();
    renderTable();
  });

  // Timezone Clock Cards Click-to-Filter
  document.querySelectorAll('.tz-card').forEach(card => {
    card.addEventListener('click', () => {
      const selectedTz = card.getAttribute('data-tz');
      const tzSelect = document.getElementById('tzFilter');
      if (tzFilter === selectedTz) {
        tzFilter = 'ALL';
        tzSelect.value = 'ALL';
        showToast('Showing leads from ALL timezones');
      } else {
        tzFilter = selectedTz;
        tzSelect.value = selectedTz;
        showToast(`Filtered calling list to ${selectedTz} leads`);
      }
      selectedIndex = 0;
      updateLiveClocks();
      renderTable();
    });
  });

  // Refresh Button
  document.getElementById('btnRefresh').addEventListener('click', () => {
    showToast('Refreshing lead data & live clocks...');
    loadLeads();
  });

  // Sync Emails Button
  const btnSync = document.getElementById('btnSyncGmail');
  if (btnSync) {
    btnSync.addEventListener('click', () => {
      showToast('⚡ Syncing sent emails from Gmail...');
      btnSync.disabled = true;
      btnSync.textContent = 'Syncing...';
      fetch('/api/sync_emails', { method: 'POST' })
        .then(r => r.json())
        .then(res => {
          btnSync.disabled = false;
          btnSync.textContent = '⚡ Sync Emails';
          showToast(`Synced with Gmail! Added ${res.added || 0} updates.`);
          loadLeads();
        })
        .catch(err => {
          btnSync.disabled = false;
          btnSync.textContent = '⚡ Sync Emails';
          showToast('Error syncing with Gmail', true);
        });
    });
  }

  // Add Lead Button
  const btnAdd = document.getElementById('btnAddLead');
  if (btnAdd) {
    btnAdd.addEventListener('click', openAddLeadModal);
  }

  // Daily Report Button
  document.getElementById('btnDailyReport').addEventListener('click', openReportModal);

  // Reset Day Button
  document.getElementById('btnResetDay').addEventListener('click', () => {
    if (confirm('Start a new calling day? This resets daily checkmarks to Uncalled, while keeping all call notes and history.')) {
      fetch('/api/reset_today', { method: 'POST' })
        .then(r => r.json())
        .then(() => {
          showToast('Daily calling queue refreshed for new day!');
          loadLeads();
        });
    }
  });
}


function initKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    // If typing in input or textarea, ignore single-key shortcuts unless Escape
    const tag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
    if (tag === 'input' || tag === 'textarea') {
      if (e.key === 'Escape') {
        document.activeElement.blur();
      }
      return;
    }

    if (e.key === '/') {
      e.preventDefault();
      document.getElementById('searchInput').focus();
      return;
    }

    if (e.key === 'Escape') {
      if (document.getElementById('reportModal').style.display !== 'none') {
        closeReportModal();
      } else if (document.getElementById('imageModal').style.display !== 'none') {
        closeImageModal();
      } else if (expandedSlug) {
        expandedSlug = null;
        renderTable();
      }
      return;
    }

    if (currentFilteredLeads.length === 0) return;

    // J or ArrowDown -> Next Lead
    if (e.key === 'j' || e.key === 'J' || e.key === 'ArrowDown') {
      e.preventDefault();
      if (selectedIndex < currentFilteredLeads.length - 1) {
        selectedIndex++;
        updateSelectionHighlight();
      }
      return;
    }

    // K or ArrowUp -> Prev Lead
    if (e.key === 'k' || e.key === 'K' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (selectedIndex > 0) {
        selectedIndex--;
        updateSelectionHighlight();
      }
      return;
    }

    // Space or Enter -> Toggle Expand Active Lead
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      const activeLead = currentFilteredLeads[selectedIndex];
      if (activeLead) {
        toggleExpand(activeLead.slug);
      }
      return;
    }

    // C -> Copy Phone
    if (e.key === 'c' || e.key === 'C') {
      e.preventDefault();
      const activeLead = currentFilteredLeads[selectedIndex];
      if (activeLead && activeLead.clean_phone) {
        copyText(activeLead.clean_phone, `Phone for ${activeLead.name}`);
      }
      return;
    }

    // E -> Copy Email
    if (e.key === 'e' || e.key === 'E') {
      e.preventDefault();
      const activeLead = currentFilteredLeads[selectedIndex];
      if (activeLead && activeLead.email) {
        copyText(activeLead.email, `Email for ${activeLead.name}`);
      } else {
        showToast('No email found for this lead', true);
      }
      return;
    }

    // W -> Copy Website
    if (e.key === 'w' || e.key === 'W') {
      e.preventDefault();
      const activeLead = currentFilteredLeads[selectedIndex];
      if (activeLead && activeLead.website) {
        copyText(activeLead.website, `Website for ${activeLead.name}`);
      } else {
        showToast('No website found for this lead', true);
      }
      return;
    }

    // Quick Outcome Hotkeys (1-5)
    const activeLead = currentFilteredLeads[selectedIndex];
    if (!activeLead) return;

    if (e.key === '1') {
      e.preventDefault();
      logCallOutcome(activeLead.slug, 'meeting_booked');
    } else if (e.key === '2') {
      e.preventDefault();
      logCallOutcome(activeLead.slug, 'spoke_followup');
    } else if (e.key === '3') {
      e.preventDefault();
      logCallOutcome(activeLead.slug, 'left_voicemail');
    } else if (e.key === '4') {
      e.preventDefault();
      logCallOutcome(activeLead.slug, 'no_answer');
    } else if (e.key === '5') {
      e.preventDefault();
      logCallOutcome(activeLead.slug, 'not_interested');
    }
  });
}

function loadLeads() {
  fetch('/api/leads')
    .then(r => r.json())
    .then(data => {
      leadsData = data.leads || [];
      updateTopBar(data);
      renderTable();
    })
    .catch(err => {
      console.error('Failed to load leads:', err);
      showToast('Error loading leads', true);
    });
}

function updateTopBar(data) {
  const stats = data.stats || {};
  
  const dials = stats.dials_today || 0;
  const goal = stats.daily_goal || 25;
  const meetings = stats.meetings_booked || 0;
  const callbacks = stats.callbacks_count || 0;
  const safeCount = stats.safe_to_call || 0;
  const total = leadsData.length;

  document.getElementById('statDialsToday').textContent = dials;
  document.getElementById('statDailyGoal').textContent = goal;
  document.getElementById('statMeetingsBooked').textContent = meetings;
  document.getElementById('statCallbacksScheduled').textContent = callbacks;
  document.getElementById('statSafeToCall').textContent = safeCount;

  const pct = Math.min(100, Math.round((dials / goal) * 100));
  document.getElementById('statProgressBar').style.width = pct + '%';
  const rem = Math.max(0, goal - dials);
  document.getElementById('statDialsRemaining').textContent = rem === 0 ? '🎉 Daily dial goal completed!' : `${rem} dials to hit daily goal`;

  // Timezone Clocks
  updateLiveClocks(data.timezone_clocks);

  // Tab counts
  const todayIso = new Date().toISOString().split('T')[0];
  const toCallCount = leadsData.filter(l => {
    if (l.called_today) return false;
    if (l.on_hold) return false;
    if (l.callback_datetime && l.callback_datetime > todayIso) return false;
    return true;
  }).length;
  const calledCount = leadsData.filter(l => l.called_today).length;
  const callbackCount = leadsData.filter(l => l.last_outcome === 'spoke_followup' || l.callback_datetime).length;
  const meetingCount = leadsData.filter(l => l.last_outcome === 'meeting_booked').length;

  document.getElementById('countToCall').textContent = toCallCount;
  document.getElementById('countCalled').textContent = calledCount;
  document.getElementById('countCallbacks').textContent = callbackCount;
  document.getElementById('countMeetings').textContent = meetingCount;
  document.getElementById('countAll').textContent = total;
}

function updateLiveClocks(backendClocks) {
  const zones = {
    'est': { name: 'EST', timeZone: 'America/New_York' },
    'cst': { name: 'CST', timeZone: 'America/Chicago' },
    'mst': { name: 'MST', timeZone: 'America/Denver' },
    'pst': { name: 'PST', timeZone: 'America/Los_Angeles' }
  };

  const now = new Date();

  for (const [code, meta] of Object.entries(zones)) {
    const el = document.getElementById(`tz-${code}`);
    if (!el) continue;

    let h = '--', m = '--', p = '--', isOpen = true;

    try {
      const formatter = new Intl.DateTimeFormat('en-US', {
        timeZone: meta.timeZone,
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
      const parts = formatter.formatToParts(now);
      h = parts.find(part => part.type === 'hour')?.value || '12';
      m = parts.find(part => part.type === 'minute')?.value || '00';
      p = (parts.find(part => part.type === 'dayPeriod')?.value || 'PM').toUpperCase();

      const hour24Formatter = new Intl.DateTimeFormat('en-US', {
        timeZone: meta.timeZone,
        hour: 'numeric',
        hour12: false
      });
      const h24 = parseInt(hour24Formatter.format(now), 10);

      const dayFormatter = new Intl.DateTimeFormat('en-US', {
        timeZone: meta.timeZone,
        weekday: 'short'
      });
      const day = dayFormatter.format(now);
      const isWeekday = !['Sat', 'Sun'].includes(day);
      isOpen = isWeekday && h24 >= 9 && h24 < 17;
    } catch (e) {
      if (backendClocks && backendClocks[meta.name]) {
        const info = backendClocks[meta.name];
        const rawParts = (info.time_str || '').split(' ');
        if (rawParts.length >= 2) {
          const hm = rawParts[0].split(':');
          h = hm[0] || '--';
          m = hm[1] || '--';
          p = rawParts[1] || '';
        }
        isOpen = info.is_safe;
      }
    }

    const timeValEl = el.querySelector('.tz-time-val');
    const ampmEl = el.querySelector('.tz-ampm');
    const statusInd = el.querySelector('.tz-status-indicator');
    const statusLabel = el.querySelector('.tz-label');

    if (timeValEl) timeValEl.textContent = `${h}:${m}`;
    if (ampmEl) ampmEl.textContent = p;

    if (statusInd && statusLabel) {
      statusInd.className = 'tz-status-indicator ' + (isOpen ? 'safe' : 'closed');
      statusLabel.textContent = isOpen ? 'OPEN' : 'CLOSED';
    }

    if (tzFilter === meta.name) {
      el.classList.add('active-filter');
    } else {
      el.classList.remove('active-filter');
    }
  }
}

function renderTable() {
  const tbody = document.getElementById('leadsTableBody');
  const emptyState = document.getElementById('emptyState');
  const todayIso = new Date().toISOString().split('T')[0];
  
  // 1. Filter by Active Tab
  let filtered = leadsData.filter(lead => {
    const isPaused = lead.on_hold || (lead.callback_datetime && lead.callback_datetime > todayIso);
    if (activeTab === 'tocall') {
      if (lead.called_today) return false;
      if (isPaused) return false; // Exclude on-hold and future callback leads from Needs Call Today
      return true;
    }
    if (activeTab === 'called') return lead.called_today;
    if (activeTab === 'callbacks') return (lead.last_outcome === 'spoke_followup' || lead.callback_datetime);
    if (activeTab === 'meetings') return lead.last_outcome === 'meeting_booked';
    return true;
  });

  // 2. Filter by Timezone
  if (tzFilter !== 'ALL') {
    filtered = filtered.filter(lead => lead.timezone === tzFilter);
  }

  // 3. Filter by Search Query
  if (searchQuery) {
    filtered = filtered.filter(lead => {
      const corpus = `${lead.name} ${lead.business} ${lead.phone} ${lead.clean_phone} ${lead.email} ${lead.website} ${lead.location} ${lead.colleague} ${lead.competitors} ${lead.quick_notes}`.toLowerCase();
      return corpus.includes(searchQuery);
    });
  }

  // 4. Sort Leads
  filtered.sort((a, b) => {
    if (a.called_today !== b.called_today) {
      return a.called_today ? 1 : -1;
    }
    return (a.priority_score || 500) - (b.priority_score || 500);
  });

  currentFilteredLeads = filtered;
  if (selectedIndex >= currentFilteredLeads.length) {
    selectedIndex = Math.max(0, currentFilteredLeads.length - 1);
  }

  if (filtered.length === 0) {
    tbody.innerHTML = '';
    emptyState.style.display = 'block';
    updateSelectionHint(null);
    return;
  }
  emptyState.style.display = 'none';

  let html = '';
  filtered.forEach((lead, index) => {
    const isExpanded = (lead.slug === expandedSlug);
    const isSelected = (index === selectedIndex);
    const calledClass = lead.called_today ? 'called-today' : '';
    const expandedClass = isExpanded ? 'expanded' : '';
    const selectedClass = isSelected ? 'keyboard-selected' : '';

    // Status pill
    let statusPill = '';
    const isPaused = lead.on_hold || (lead.callback_datetime && lead.callback_datetime > todayIso);
    if (lead.last_outcome === 'meeting_booked') {
      statusPill = `<span class="status-pill meeting">🎯 Booked</span>`;
    } else if (isPaused) {
      const pauseLabel = lead.snooze_until || lead.callback_datetime || 'Paused';
      statusPill = `<span class="status-pill on-hold" style="background:#fee2e2; color:#b91c1c; border:1px solid #f87171; font-weight:700;" title="On hold until ${escapeHtml(pauseLabel)}">⛔ Hold: ${escapeHtml(pauseLabel)}</span>`;
    } else if (lead.callback_datetime) {
      statusPill = `<span class="status-pill callback">📅 ${escapeHtml(lead.callback_datetime)}</span>`;
    } else if (lead.called_today) {
      statusPill = `<span class="status-pill called">🟢 Dialed</span>`;
    } else {
      statusPill = `<span class="status-pill pending">🔴 Pending</span>`;
    }

    // Local Time
    const timeInfo = lead.local_time || {};
    const timeSafeClass = timeInfo.is_safe ? 'safe' : 'closed';
    const timeSafeText = timeInfo.is_safe ? '● Safe (9am-5pm)' : '○ Closed';

    // Phone display
    const phoneDisplay = lead.phone || 'No Phone';
    const cleanDigits = lead.clean_phone || '';

    // SEO Hook
    const as = lead.authority_score ? `AS: ${lead.authority_score.split('/')[0].trim()}` : '';
    const usShare = lead.us_traffic_share ? `<span class="traffic-alert">${lead.us_traffic_share} US</span>` : '';
    const refDom = lead.referring_domains ? `${lead.referring_domains.split(' ')[0]} Ref` : '';

    const webUrl = lead.website ? (lead.website.startsWith('http') ? lead.website : 'https://' + lead.website) : '';

    const emailHist = lead.email_history || {};
    let emailDatesHtml = '';
    if (emailHist.has_history) {
      const followPill = emailHist.followup_due 
        ? `<span class="email-followup-pill" title="More than 48 hours since last email sent">⚠️ 48h Follow-up Due</span>` 
        : '';
      const countPill = emailHist.sent_count > 1 
        ? `<span class="email-count-pill">${emailHist.sent_count} emails</span>` 
        : '';
      emailDatesHtml = `
        <div class="lead-email-dates" title="First email: ${escapeHtml(emailHist.first_sent_date)} | Most recent: ${escapeHtml(emailHist.last_sent_date)}">
          <span class="email-date-item"><strong>1st:</strong> ${escapeHtml(emailHist.first_sent_date)}</span>
          <span class="email-date-sep">•</span>
          <span class="email-date-item"><strong>Last:</strong> ${escapeHtml(emailHist.last_sent_date_short)} <small>(${escapeHtml(emailHist.last_sent_relative)})</small></span>
          ${countPill}
          ${followPill}
        </div>
      `;
    } else {
      emailDatesHtml = `
        <div class="lead-email-dates" style="opacity:0.6;">
          <span class="email-date-item"><small style="color:#64748b;">No email sent yet</small></span>
        </div>
      `;
    }

    const leadInitials = (lead.name || lead.business || 'LP')
      .trim()
      .split(/\s+/)
      .map(w => w[0])
      .filter(Boolean)
      .slice(0, 2)
      .join('')
      .toUpperCase();

    const avatarColors = [
      'avatar-cyan', 'avatar-purple', 'avatar-emerald', 'avatar-amber', 'avatar-rose', 'avatar-indigo'
    ];
    const colorIdx = Math.abs((lead.slug || '').split('').reduce((acc, c) => acc + c.charCodeAt(0), 0)) % avatarColors.length;
    const avatarClass = avatarColors[colorIdx];

    html += `
      <tr class="lead-row ${calledClass} ${expandedClass} ${selectedClass}" onclick="selectAndExpand(${index}, '${lead.slug}')" id="row-${lead.slug}" data-index="${index}">
        <td class="col-status" onclick="event.stopPropagation()">
          <label style="cursor:pointer; display:inline-flex; align-items:center; gap:6px;">
            <input type="checkbox" ${lead.called_today ? 'checked' : ''} onchange="toggleCalledToday('${lead.slug}', this.checked)" />
            ${statusPill}
          </label>
        </td>
        <td class="col-lead">
          <div class="lead-identity-group">
            <div class="lead-avatar ${avatarClass}" title="${escapeHtml(lead.business)}">${escapeHtml(leadInitials)}</div>
            <div class="lead-title-box">
              <span class="lead-name">${escapeHtml(lead.name)}</span>
              <span class="lead-biz">${escapeHtml(lead.business)}</span>
              <div class="lead-quick-chips" onclick="event.stopPropagation()">
                ${lead.email ? `<button class="chip-btn chip-email" onclick="copyText('${escapeHtml(lead.email)}', 'Email')">✉️ ${escapeHtml(lead.email)}</button>` : ''}
                ${lead.website ? `
                  <button class="chip-btn chip-web" onclick="copyText('${escapeHtml(lead.website)}', 'Website')">🌐 ${escapeHtml(lead.website)}</button>
                  <a class="chip-link" href="${webUrl}" target="_blank" title="Visit website">↗</a>
                ` : ''}
              </div>
              ${emailDatesHtml}
            </div>
          </div>
        </td>

        <td class="col-phone" onclick="event.stopPropagation()">
          <div class="phone-cell">
            <span class="phone-digits">${escapeHtml(phoneDisplay)}</span>
            <div class="phone-actions">
              ${cleanDigits ? `
                <button class="btn-phone-copy" onclick="copyText('${cleanDigits}', 'Phone for ${escapeHtml(lead.name)}')">📋 Copy</button>
                <a class="btn-phone-dial" href="tel:${cleanDigits}">📞 Call</a>
              ` : '<span style="color:#64748b; font-size:0.75rem;">No direct #</span>'}
            </div>
          </div>
        </td>
        <td class="col-clock">
          <div class="clock-cell">
            <span class="local-time">${timeInfo.time_str || '--:--'} <small style="color:#64748b">${lead.timezone}</small></span>
            <span class="time-badge ${timeSafeClass}">${timeSafeText}</span>
          </div>
        </td>
        <td class="col-colleague" onclick="event.stopPropagation()">
          <div class="colleague-box">
            <div class="outreach-header-row">
              <span class="colleague-persona-badge" title="Outreach Persona">👤 ${escapeHtml(lead.colleague || 'Direct')}</span>
            </div>
            ${lead.colleague_email ? `
              <button class="chip-btn chip-outreach-email" onclick="copyText('${escapeHtml(lead.colleague_email)}', 'Outreach Email')" title="Click to copy outreach email account (${escapeHtml(lead.colleague_email)})">
                ✉️ ${escapeHtml(lead.colleague_email)}
              </button>
            ` : '<span class="outreach-no-email">(Direct outreach)</span>'}
            <div class="colleague-reply" title="${escapeHtml(lead.lead_reply || 'Replied to outreach')}">
              <span>💬</span> "${escapeHtml(lead.lead_reply || 'Replied to outreach')}"
            </div>
          </div>
        </td>
        <td class="col-seo">
          <div class="seo-cell">
            <span class="seo-metrics">${as} ${usShare ? '• ' + usShare : ''}</span>
            <span class="seo-sub">${refDom} • ${escapeHtml(lead.organic_traffic || '0 visits')}</span>
          </div>
        </td>
        <td class="col-action">
          <span class="expand-icon">▾</span>
        </td>
      </tr>
    `;

    if (isExpanded) {
      html += renderExpandedTray(lead);
    }
  });

  tbody.innerHTML = html;
  updateSelectionHint(currentFilteredLeads[selectedIndex]);
}

function renderExpandedTray(lead) {
  const screenshotThumb = lead.has_screenshot
    ? `<div class="scorecard-thumb-container" onclick="openImageModal('/screenshots/${lead.screenshot_file}')">
         <img src="/screenshots/${lead.screenshot_file}" alt="Semrush Scorecard">
         <div class="thumb-overlay">🔍 Click to Enlarge Scorecard</div>
       </div>`
    : `<div style="font-size:0.75rem; color:#64748b; padding:8px; border:1px dashed #334155; border-radius:4px; text-align:center;">Scorecard image not generated yet</div>`;

  const historyHtml = (lead.call_history && lead.call_history.length > 0)
    ? lead.call_history.slice(-3).reverse().map(h => `
        <div class="history-item">
          <span>${escapeHtml(h.outcome)}</span>
          <span>${escapeHtml(h.timestamp)}</span>
        </div>
      `).join('')
    : '<div style="color:#64748b;">No previous calls logged yet.</div>';

  // Objections chips
  const objectionsHtml = (lead.objections && lead.objections.length > 0)
    ? lead.objections.map((obj, i) => `
        <div class="objection-item">
          <button class="objection-btn" onclick="toggleObjection('${lead.slug}', ${i})">
            <span>💬 ${escapeHtml(obj.objection)}</span>
            <span style="font-size:0.7rem; color:#38bdf8;">▾</span>
          </button>
          <div class="objection-reframe" id="obj-${lead.slug}-${i}">
            <strong>Verbal Reframe:</strong> "${escapeHtml(obj.reframe)}"
          </div>
        </div>
      `).join('')
    : '';

  const emailHist = lead.email_history || {};
  const timelineHtml = emailHist.has_history ? `
    <div class="email-timeline-box">
      <div class="timeline-header">
        <span>📬 Outreach Email History</span>
        <span class="timeline-count-badge">${emailHist.sent_count} sent</span>
      </div>
      <div class="timeline-row">
        <div class="timeline-col">
          <span class="t-label">First Email Sent:</span>
          <span class="t-val">${escapeHtml(emailHist.first_sent_date)} ${emailHist.first_sent_relative ? `<small style="color:#94a3b8">(${escapeHtml(emailHist.first_sent_relative)})</small>` : ''}</span>
        </div>
        <div class="timeline-col">
          <span class="t-label">Most Recent Email:</span>
          <span class="t-val text-info">${escapeHtml(emailHist.last_sent_date)} ${emailHist.last_sent_relative ? `<small style="color:#94a3b8">(${escapeHtml(emailHist.last_sent_relative)})</small>` : ''}</span>
        </div>
      </div>
      ${emailHist.last_subject ? `
        <div class="timeline-subject">
          <span class="t-label">Last Subject:</span>
          <span class="t-subj">"${escapeHtml(emailHist.last_subject)}"</span>
        </div>
      ` : ''}
      ${emailHist.followup_due ? `
        <div class="timeline-alert">
          ⚠️ <strong>48-Hour Follow-up Window:</strong> Last email was sent ${emailHist.days_since_last_sent} days ago. Great time to follow up on the phone or send an in-thread bump!
        </div>
      ` : ''}
    </div>
  ` : `
    <div class="email-timeline-box" style="opacity: 0.7;">
      <div class="timeline-header">
        <span>📬 Outreach Email History</span>
        <span class="timeline-count-badge" style="background:rgba(255,255,255,0.08); color:#94a3b8;">0 sent</span>
      </div>
      <div style="font-size:0.75rem; color:#64748b; padding:4px 0;">No outreach emails logged for this recipient yet.</div>
    </div>
  `;

  const gmailSearchUrl = `https://mail.google.com/mail/u/0/#search/${encodeURIComponent(lead.email || lead.name)}`;
  const webUrl = lead.website ? (lead.website.startsWith('http') ? lead.website : 'https://' + lead.website) : '';

  return `
    <tr class="tray-row" id="tray-${lead.slug}">
      <td colspan="7">
        <div class="cockpit-tray">
          ${(lead.on_hold || (lead.callback_datetime && lead.callback_datetime > todayIso)) ? `
            <div style="grid-column: 1 / -1; background: #450a0a; border: 1px solid #ef4444; border-radius: 8px; padding: 12px 18px; margin-bottom: 8px; color: #fee2e2; font-size: 13px; font-weight: 600; display: flex; align-items: center; justify-content: space-between;">
              <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.4rem;">⛔</span>
                <div>
                  <div style="color: #fca5a5; font-size: 14px; font-weight: 700; letter-spacing: 0.5px;">DO NOT CALL OR EMAIL — ON HOLD UNTIL ${escapeHtml(lead.snooze_until || lead.callback_datetime || 'SCHEDULED DATE')}</div>
                  <div style="color: #fecaca; font-weight: 400; font-size: 12px; margin-top: 2px;">Note: ${escapeHtml(lead.quick_notes || 'Client requested 1-month pause for internal website updates.')}</div>
                </div>
              </div>
              <span style="background: #b91c1c; color: white; padding: 4px 10px; border-radius: 4px; font-size: 11px; text-transform: uppercase; font-weight: 700; letter-spacing: 1px;">Snoozed</span>
            </div>
          ` : ''}
          <!-- Card 1: Live Call Script & Objections -->
          <div class="tray-card">
            <div class="card-title">
              <span>📞 LIVE CALL SCRIPT</span>
              <span style="font-size:0.7rem; color:#94a3b8;">Hotkeys: 1=Booked, 2=Callback, 3=VM</span>
            </div>
            
            <div class="script-box">
              <div class="script-label">Word-for-Word Opener:</div>
              <div>"${escapeHtml(lead.live_opener)}"</div>
            </div>

            <div class="script-box rebound">
              <div class="script-label">If asked "What is it about?":</div>
              <div>"${escapeHtml(lead.what_is_it_about)}"</div>
            </div>

            <div class="script-box">
              <div class="script-label">Voicemail (&lt; 15s):</div>
              <div>"${escapeHtml(lead.voicemail)}"</div>
            </div>

            <div class="objections-box">
              <div class="objections-title">Instant Objection Reframes:</div>
              ${objectionsHtml}
            </div>
          </div>

          <!-- Card 2: Email Conversation & Complete Data Copy -->
          <div class="tray-card">
            <div class="card-title">
              <span>✉️ CONTACT DATA &amp; EMAIL CONVERSATION</span>
              <a href="${gmailSearchUrl}" target="_blank" class="btn-open-gmail">↗ Open in Gmail</a>
            </div>
            
            <div class="contact-details-grid">
              <div class="contact-data-row">
                <span class="data-label">Prospect Email:</span>
                <span class="data-val text-blue">${escapeHtml(lead.email || 'N/A')}</span>
                ${lead.email ? `<button class="btn-copy-mini" onclick="copyText('${escapeHtml(lead.email)}', 'Email')">📋 Copy</button>` : ''}
              </div>

              <div class="contact-data-row">
                <span class="data-label">Website:</span>
                <span class="data-val text-muted">${escapeHtml(lead.website || 'N/A')}</span>
                ${lead.website ? `
                  <button class="btn-copy-mini" onclick="copyText('${escapeHtml(lead.website)}', 'Website')">📋 Copy</button>
                  <a class="btn-copy-mini" href="${webUrl}" target="_blank">↗ Visit</a>
                ` : ''}
              </div>

              <div class="contact-data-row">
                <span class="data-label">Phone:</span>
                <span class="data-val text-green">${escapeHtml(lead.phone || 'N/A')}</span>
                ${lead.clean_phone ? `<button class="btn-copy-mini" onclick="copyText('${escapeHtml(lead.clean_phone)}', 'Phone')">📋 Copy</button>` : ''}
              </div>

              <div class="contact-data-row">
                <span class="data-label">Location:</span>
                <span class="data-val">${escapeHtml(lead.location || 'N/A')}</span>
                ${lead.location ? `<button class="btn-copy-mini" onclick="copyText('${escapeHtml(lead.location)}', 'Location')">📋 Copy</button>` : ''}
              </div>

              <div class="contact-data-row">
                <span class="data-label">Outreach Account (Sent From):</span>
                <span class="data-val text-blue font-mono">${escapeHtml(lead.colleague_email || 'Direct Outreach')}</span>
                ${lead.colleague_email ? `<button class="btn-copy-mini" onclick="copyText('${escapeHtml(lead.colleague_email)}', 'Outreach Email')">📋 Copy</button>` : ''}
              </div>

              <div class="contact-data-row">
                <span class="data-label">Outreach Persona:</span>
                <span class="data-val text-purple font-bold">👤 ${escapeHtml(lead.colleague || 'Direct')}</span>
              </div>
            </div>

            ${timelineHtml}

            <div class="quoted-box-preview">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; flex-wrap:wrap; gap:6px;">
                <strong style="color:#f8fafc;">Client's Exact Reply:</strong>
                ${lead.colleague_email ? `<span style="font-size:0.75rem; color:#93c5fd; background:rgba(30,58,138,0.4); padding:2px 8px; border-radius:4px; font-family:'JetBrains Mono',monospace;">To: ${escapeHtml(lead.colleague)} &lt;${escapeHtml(lead.colleague_email)}&gt;</span>` : ''}
              </div>
              <div style="font-size:0.86rem; color:#f1f5f9; line-height:1.45; font-style:italic;">
                "${escapeHtml(lead.lead_reply || 'Interested in report')}"
              </div>
            </div>

            <div class="master-copy-bar">
              <button class="btn-copy-master" onclick="copyContactCard('${lead.slug}')">
                📋 Copy All Contact Info (Card)
              </button>
              <button class="btn-copy-master" onclick="copyEmailDraft('${lead.slug}')">
                📋 Copy Audit Email Text
              </button>
            </div>
          </div>

          <!-- Card 3: Technical SEO & Competitors -->
          <div class="tray-card">
            <div class="card-title">
              <span>📊 SEO SCORECARD &amp; COMPETITORS</span>
              ${lead.website ? `<button class="btn-copy-mini" onclick="copyText('${escapeHtml(lead.website)}', 'Website')">📋 Copy Web</button>` : ''}
            </div>
            
            ${lead.core_trap ? `
              <div class="core-trap-card">
                <div class="core-trap-title">⚠️ Core Diagnostic Wedge:</div>
                ${escapeHtml(lead.core_trap)}
              </div>
            ` : ''}

            ${screenshotThumb}

            <div style="font-size:0.8rem; line-height:1.6; color:#cbd5e1;">
              • <strong>Authority Score:</strong> ${escapeHtml(lead.authority_score || 'N/A')}<br>
              • <strong>Organic Traffic:</strong> ${escapeHtml(lead.organic_traffic || 'N/A')} (${escapeHtml(lead.us_traffic_share || '100%')} US)<br>
              • <strong>Ref Domains &amp; Links:</strong> ${escapeHtml(lead.referring_domains || '0')} domains / ${escapeHtml(lead.backlinks || '0')} links<br>
              • <strong>Local Competitors:</strong> <span style="color:#f59e0b;">${escapeHtml(lead.competitors || 'Local competitors')}</span>
            </div>
          </div>

          <!-- Card 4: Live Call Logger & Notes -->
          <div class="tray-card">
            <div class="card-title">📝 CALL LOGGER &amp; NOTES</div>
            
            <div class="outcome-buttons">
              <button class="btn-outcome btn-meeting" onclick="logCallOutcome('${lead.slug}', 'meeting_booked')">
                🎯 Meeting Booked (10-min Zoom) [1]
              </button>
              <button class="btn-outcome btn-callback" onclick="logCallOutcome('${lead.slug}', 'spoke_followup')">
                🗣️ Callback / Follow-up [2]
              </button>
              <button class="btn-outcome btn-vm" onclick="logCallOutcome('${lead.slug}', 'left_voicemail')">
                📼 Left Voicemail [3]
              </button>
              <button class="btn-outcome" onclick="logCallOutcome('${lead.slug}', 'no_answer')">
                ❌ No Answer [4]
              </button>
              <button class="btn-outcome" onclick="logCallOutcome('${lead.slug}', 'not_interested')">
                🚫 Not Interested [5]
              </button>
            </div>

            <textarea class="notes-area" id="notes-${lead.slug}" placeholder="Type notes while speaking... Auto-saves on outcome">${escapeHtml(lead.quick_notes || '')}</textarea>
            
            <div style="display:flex; justify-content:space-between; align-items:center;">
              ${lead.callback_datetime ? `<span style="font-size:0.72rem; color:#c084fc;">📅 Callback: ${escapeHtml(lead.callback_datetime)}</span>` : '<span></span>'}
              <button class="btn-save-note" onclick="saveNote('${lead.slug}')">💾 Save Note</button>
            </div>

            <div class="call-history-mini">
              <div style="font-weight:700; margin-bottom:4px; color:#94a3b8;">Call History:</div>
              ${historyHtml}
            </div>
          </div>
        </div>
      </td>
    </tr>
  `;
}

// User Actions
function selectAndExpand(index, slug) {
  selectedIndex = index;
  toggleExpand(slug);
  updateSelectionHighlight();
}

function updateSelectionHighlight() {
  document.querySelectorAll('.lead-row').forEach(row => row.classList.remove('keyboard-selected'));
  const activeLead = currentFilteredLeads[selectedIndex];
  if (activeLead) {
    const row = document.getElementById(`row-${activeLead.slug}`);
    if (row) {
      row.classList.add('keyboard-selected');
      row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    updateSelectionHint(activeLead);
  }
}

function updateSelectionHint(lead) {
  const el = document.getElementById('activeSelectionHint');
  if (!el) return;
  if (!lead) {
    el.textContent = 'No leads in view';
    return;
  }
  el.innerHTML = `Active: <strong>${escapeHtml(lead.name)}</strong> • <em>[Hotkeys: <kbd>C</kbd> Phone | <kbd>E</kbd> Email | <kbd>W</kbd> Website]</em>`;
}

function toggleExpand(slug) {
  expandedSlug = (expandedSlug === slug) ? null : slug;
  renderTable();
  if (expandedSlug) {
    const row = document.getElementById(`row-${slug}`);
    if (row) row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}

function toggleObjection(slug, index) {
  const reframeEl = document.getElementById(`obj-${slug}-${index}`);
  if (reframeEl) {
    reframeEl.classList.toggle('show');
  }
}

// Universal Copy Function with Toast
function copyText(text, label = 'Text') {
  if (!text) {
    showToast(`No ${label} available to copy`, true);
    return;
  }
  navigator.clipboard.writeText(text).then(() => {
    showToast(`Copied ${label} to clipboard!`);
  }).catch(() => {
    const input = document.createElement('input');
    input.value = text;
    document.body.appendChild(input);
    input.select();
    document.execCommand('copy');
    document.body.removeChild(input);
    showToast(`Copied ${label} to clipboard!`);
  });
}

// Copy Complete Contact Card
function copyContactCard(slug) {
  const lead = leadsData.find(l => l.slug === slug);
  if (!lead) return;
  const card = [
    `Prospect: ${lead.name}`,
    `Company: ${lead.business}`,
    `Phone: ${lead.phone || lead.clean_phone || 'N/A'}`,
    `Email: ${lead.email || 'N/A'}`,
    `Website: ${lead.website || 'N/A'}`,
    `Location: ${lead.location || 'N/A'}`,
    `Outreach Sender Email: ${lead.colleague_email || 'N/A'}`,
    `Outreach Persona: ${lead.colleague || 'Direct'}`,
    `Client Reply: ${lead.lead_reply || 'Replied to outreach'}`,
    `Authority Score: ${lead.authority_score || 'N/A'}`,
    `Competitors: ${lead.competitors || 'N/A'}`
  ].join('\n');
  
  copyText(card, `Full Contact Card for ${lead.name}`);
}

function copyEmailDraft(slug) {
  const lead = leadsData.find(l => l.slug === slug);
  if (!lead) return;
  const colleagueRef = lead.colleague ? lead.colleague : 'our outreach team';
  const text = `Hi ${lead.name},\n\nMy colleague ${colleagueRef} forwarded me your reply asking about the website report for ${lead.website || lead.business}.\n\nI pulled your live Google search diagnostic data today:\n• Authority Score: ${lead.authority_score || 'N/A'}\n• Monthly Traffic: ${lead.organic_traffic || 'N/A'} (${lead.us_traffic_share || '100%'} US)\n• Referring Domains: ${lead.referring_domains || '0'}\n\nCan we do a quick 5-minute Zoom call tomorrow to look at it together?\n\nBest,\nShiv\nInnovate Marketers LLC`;
  copyText(text, 'Email Body Text');
}

function toggleCalledToday(slug, isChecked) {
  fetch('/api/lead/toggle_called', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slug: slug, called_today: isChecked })
  })
  .then(r => r.json())
  .then(() => {
    showToast(isChecked ? 'Marked as dialed today!' : 'Marked as uncalled');
    loadLeads();
  });
}

function logCallOutcome(slug, outcome) {
  let meetingTime = '';
  let callbackTime = '';

  if (outcome === 'meeting_booked') {
    meetingTime = prompt('🎯 Meeting Booked! Enter Zoom date/time (e.g. Thursday 2:30 PM PST):');
    if (meetingTime === null) return;
    if (!meetingTime) meetingTime = 'Time TBD';
    playSuccessChime();
  } else if (outcome === 'spoke_followup') {
    callbackTime = prompt('🗣️ Agreed Callback! Enter callback day/time (e.g. Friday 11:00 AM PST):');
    if (callbackTime === null) return;
    if (!callbackTime) callbackTime = 'Follow up soon';
  }

  const noteInput = document.getElementById(`notes-${slug}`);
  const note = noteInput ? noteInput.value.trim() : '';

  fetch('/api/lead/log_call', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      slug: slug,
      outcome: outcome,
      note: note,
      meeting_datetime: meetingTime,
      callback_datetime: callbackTime
    })
  })
  .then(r => r.json())
  .then(() => {
    showToast(`Outcome logged: ${outcome.replace('_', ' ').toUpperCase()}`);
    expandedSlug = null;
    loadLeads();
  });
}

function saveNote(slug) {
  const noteInput = document.getElementById(`notes-${slug}`);
  const note = noteInput ? noteInput.value.trim() : '';
  fetch('/api/lead/save_note', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slug: slug, note: note })
  })
  .then(r => r.json())
  .then(() => {
    showToast('Note saved!');
  });
}

// Daily Report Modal
let dailyReportData = null;
function openReportModal() {
  fetch('/api/daily_report')
    .then(r => r.json())
    .then(report => {
      dailyReportData = report;
      const body = document.getElementById('reportBody');
      
      const dials = report.total_dials || 0;
      const meetings = report.meetings_booked_count || 0;
      const callbacks = report.callbacks_count || 0;
      const voicemails = report.voicemails_count || 0;
      const noAns = report.no_answers_count || 0;

      let historyRows = '';
      (report.all_dialed || []).forEach(item => {
        historyRows += `
          <div style="display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid #1e293b;">
            <span><strong>${escapeHtml(item.slug)}</strong> <small style="color:#94a3b8">(${escapeHtml(item.outcome)})</small></span>
            <span style="color:#38bdf8;">${escapeHtml(item.meeting || item.callback || item.called_at)}</span>
          </div>
          ${item.note ? `<div style="font-size:0.75rem; color:#cbd5e1; padding-left:10px; font-style:italic;">"${escapeHtml(item.note)}"</div>` : ''}
        `;
      });

      body.innerHTML = `
        <div style="background:#0f172a; padding:14px; border-radius:8px; margin-bottom:16px;">
          <div style="font-size:1.1rem; font-weight:700; color:#fff; margin-bottom:8px;">Date: ${report.date}</div>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
            <div>📞 <strong>Total Dials:</strong> ${dials} / ${report.daily_goal}</div>
            <div>🎯 <strong>Meetings Booked:</strong> <span style="color:#34d399">${meetings}</span></div>
            <div>📅 <strong>Callbacks Set:</strong> <span style="color:#c084fc">${callbacks}</span></div>
            <div>📼 <strong>Voicemails:</strong> ${voicemails}</div>
            <div>❌ <strong>No Answers:</strong> ${noAns}</div>
          </div>
        </div>

        <div style="font-weight:700; color:#cbd5e1; margin-bottom:8px;">Activity Log for Today:</div>
        <div style="max-height:220px; overflow-y:auto;">
          ${historyRows || '<div style="color:#64748b;">No dials logged yet today.</div>'}
        </div>
      `;

      document.getElementById('reportModal').style.display = 'flex';
    });
}

function closeReportModal() {
  document.getElementById('reportModal').style.display = 'none';
}

function copyReportText() {
  if (!dailyReportData) return;
  const r = dailyReportData;
  const lines = [
    `=== CALL COPILOT DAILY REPORT (${r.date}) ===`,
    `Total Dials: ${r.total_dials} / ${r.daily_goal}`,
    `Meetings Booked: ${r.meetings_booked_count}`,
    `Callbacks Scheduled: ${r.callbacks_count}`,
    `Voicemails Left: ${r.voicemails_count}`,
    `No Answers: ${r.no_answers_count}`,
    ``,
    `Detailed Activity:`
  ];
  (r.all_dialed || []).forEach(item => {
    lines.push(`• ${item.slug}: [${item.outcome}] ${item.meeting || item.callback || ''} ${item.note ? ' - Note: ' + item.note : ''}`);
  });

  navigator.clipboard.writeText(lines.join('\n')).then(() => {
    showToast('Report copied to clipboard!');
  });
}

// Modal Images
function openImageModal(imgSrc) {
  document.getElementById('modalImage').src = imgSrc;
  document.getElementById('imageModal').style.display = 'flex';
}

function closeImageModal() {
  document.getElementById('imageModal').style.display = 'none';
}

// Toast
let toastTimer = null;
function showToast(msg, isError = false) {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.style.borderColor = isError ? 'var(--accent-rose)' : 'var(--border-light)';
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.classList.remove('show');
  }, 2600);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// Add Lead Modal
function openAddLeadModal() {
  document.getElementById('addLeadForm').reset();
  document.getElementById('addLeadModal').style.display = 'flex';
  setTimeout(() => document.getElementById('nl_company').focus(), 100);
}

function closeAddLeadModal() {
  document.getElementById('addLeadModal').style.display = 'none';
}

function submitNewLead(e) {
  e.preventDefault();
  const company = document.getElementById('nl_company').value.trim();
  const name = document.getElementById('nl_name').value.trim();
  const phone = document.getElementById('nl_phone').value.trim();
  const email = document.getElementById('nl_email').value.trim();
  const website = document.getElementById('nl_website').value.trim();
  const location = document.getElementById('nl_location').value.trim();
  const colleague = document.getElementById('nl_colleague').value.trim();
  const notes = document.getElementById('nl_notes').value.trim();

  const btn = document.getElementById('btnSubmitNewLead');
  btn.disabled = true;
  btn.textContent = 'Adding...';

  fetch('/api/lead/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      company, name, phone, email, website, location, colleague, notes
    })
  })
  .then(r => r.json())
  .then(data => {
    btn.disabled = false;
    btn.textContent = 'Add Lead to Queue';
    if (data.success) {
      showToast(`🎉 ${company} added to Cockpit!`);
      closeAddLeadModal();
      loadLeads();
    } else {
      showToast(data.error || 'Failed to add lead', true);
    }
  })
  .catch(err => {
    btn.disabled = false;
    btn.textContent = 'Add Lead to Queue';
    showToast('Network error adding lead', true);
  });
}

