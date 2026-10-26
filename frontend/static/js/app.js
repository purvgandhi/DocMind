/**
 * DocMind Studio 2.0 - Core Frontend Controller
 * Arctic Glass & Midnight Arctic Design System
 */

// Global State
const state = {
  documents: [],
  selectedDocId: null, // null = Global Scope
  activeTab: 'chat',
  chatHistory: [],
  radarNodes: [],
  topSimilarityRecorded: 0.894,
  isSidebarCollapsed: false,
  theme: 'light',
};

// Initialize Application on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initIcons();
  initSidebar();
  initTabs();
  initRadarCanvas();
  initChat();
  initSearch();
  initChunks();
  initUploadModal();
  initReaderModal();
  fetchInitialData();
});

function initIcons() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

// ============================================================================
// 1. THEME SWITCHER (ARCTIC GLASS & MIDNIGHT ARCTIC)
// ============================================================================
function initTheme() {
  const savedTheme = localStorage.getItem('docmind_theme');
  if (savedTheme) {
    state.theme = savedTheme;
  } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    state.theme = 'dark';
  } else {
    state.theme = 'light';
  }

  applyTheme(state.theme);

  const appThemeBtn = document.getElementById('app-theme-toggle-btn');
  if (appThemeBtn) {
    appThemeBtn.addEventListener('click', () => {
      state.theme = state.theme === 'light' ? 'dark' : 'light';
      applyTheme(state.theme);
    });
  }
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('docmind_theme', theme);

  const sunIcon = document.getElementById('app-theme-sun');
  const moonIcon = document.getElementById('app-theme-moon');

  if (theme === 'dark') {
    if (sunIcon) sunIcon.classList.remove('hidden');
    if (moonIcon) moonIcon.classList.add('hidden');
  } else {
    if (sunIcon) sunIcon.classList.add('hidden');
    if (moonIcon) moonIcon.classList.remove('hidden');
  }

  initIcons();
}

// ============================================================================
// 2. SIDEBAR COLLAPSE / EXPAND
// ============================================================================
function initSidebar() {
  const toggleBtn = document.getElementById('btn-toggle-sidebar');
  const sidebar = document.getElementById('app-sidebar');
  const toggleIcon = document.getElementById('sidebar-toggle-icon');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      state.isSidebarCollapsed = !state.isSidebarCollapsed;
      if (state.isSidebarCollapsed) {
        sidebar.classList.remove('lg:w-64');
        sidebar.classList.add('lg:w-16');
        document.querySelectorAll('.sidebar-label').forEach(el => el.classList.add('hidden'));
        if (toggleIcon) toggleIcon.style.transform = 'rotate(180deg)';
      } else {
        sidebar.classList.remove('lg:w-16');
        sidebar.classList.add('lg:w-64');
        document.querySelectorAll('.sidebar-label').forEach(el => el.classList.remove('hidden'));
        if (toggleIcon) toggleIcon.style.transform = 'rotate(0deg)';
      }
    });
  }

  // Active Scope Dropdown
  const scopeSelect = document.getElementById('select-active-scope');
  if (scopeSelect) {
    scopeSelect.addEventListener('change', (e) => {
      setActiveScope(e.target.value);
    });
  }
}

function setActiveScope(docId) {
  state.selectedDocId = docId || null;
  const badge = document.getElementById('scope-status-badge');
  const chatLabel = document.getElementById('chat-active-doc-label');

  if (!state.selectedDocId) {
    if (badge) badge.textContent = 'Global (All)';
    if (chatLabel) chatLabel.textContent = 'Scope: All Indexed Documents';
  } else {
    const doc = state.documents.find(d => d.id === state.selectedDocId);
    const name = doc ? doc.filename : 'Document Scoped';
    if (badge) badge.textContent = name.length > 15 ? name.substring(0, 15) + '...' : name;
    if (chatLabel) chatLabel.textContent = `Scope: ${name}`;
  }

  const scopeSelect = document.getElementById('select-active-scope');
  if (scopeSelect && scopeSelect.value !== (state.selectedDocId || '')) {
    scopeSelect.value = state.selectedDocId || '';
  }
}

// ============================================================================
// 3. TAB NAVIGATION
// ============================================================================
function initTabs() {
  const tabs = [
    { id: 'chat', btn: 'tab-btn-chat', side: 'side-nav-chat', view: 'view-chat' },
    { id: 'docs', btn: 'tab-btn-docs', side: 'side-nav-docs', view: 'view-docs' },
    { id: 'search', btn: 'tab-btn-search', side: 'side-nav-search', view: 'view-search' },
    { id: 'chunks', btn: 'tab-btn-chunks', side: 'side-nav-chunks', view: 'view-chunks' },
  ];

  tabs.forEach(tab => {
    const topBtn = document.getElementById(tab.btn);
    const sideBtn = document.getElementById(tab.side);

    if (topBtn) topBtn.addEventListener('click', () => switchTab(tab.id));
    if (sideBtn) sideBtn.addEventListener('click', () => switchTab(tab.id));
  });

  const radarSideBtn = document.getElementById('side-nav-radar');
  if (radarSideBtn) {
    radarSideBtn.addEventListener('click', () => {
      const radar = document.getElementById('vector-radar-canvas');
      if (radar) {
        radar.scrollIntoView({ behavior: 'smooth' });
        radar.classList.add('ring-2', 'ring-[#B83A42]');
        setTimeout(() => radar.classList.remove('ring-2', 'ring-[#B83A42]'), 1500);
      }
    });
  }

  // Global Refresh
  const refreshBtn = document.getElementById('btn-global-refresh');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      refreshBtn.classList.add('animate-spin');
      fetchInitialData().finally(() => {
        setTimeout(() => refreshBtn.classList.remove('animate-spin'), 600);
      });
    });
  }
}

function switchTab(tabId) {
  state.activeTab = tabId;
  const tabDefs = [
    { id: 'chat', btn: 'tab-btn-chat', side: 'side-nav-chat', view: 'view-chat' },
    { id: 'docs', btn: 'tab-btn-docs', side: 'side-nav-docs', view: 'view-docs' },
    { id: 'search', btn: 'tab-btn-search', side: 'side-nav-search', view: 'view-search' },
    { id: 'chunks', btn: 'tab-btn-chunks', side: 'side-nav-chunks', view: 'view-chunks' },
  ];

  tabDefs.forEach(t => {
    const viewEl = document.getElementById(t.view);
    const topBtn = document.getElementById(t.btn);
    const sideBtn = document.getElementById(t.side);

    if (t.id === tabId) {
      if (viewEl) viewEl.classList.remove('hidden');
      if (topBtn) {
        topBtn.classList.add('tab-active');
        topBtn.classList.remove('text-[var(--text-secondary)]');
      }
      if (sideBtn) {
        sideBtn.classList.add('bg-gradient-to-r', 'from-[#B83A42]', 'to-[#87252C]', 'text-white', 'shadow-xs', 'border', 'border-white/10');
        sideBtn.classList.remove('text-[var(--text-secondary)]', 'border-transparent');
      }
    } else {
      if (viewEl) viewEl.classList.add('hidden');
      if (topBtn) {
        topBtn.classList.remove('tab-active');
        topBtn.classList.add('text-[var(--text-secondary)]');
      }
      if (sideBtn) {
        sideBtn.classList.remove('bg-gradient-to-r', 'from-[#B83A42]', 'to-[#87252C]', 'text-white', 'shadow-xs', 'border', 'border-white/10');
        sideBtn.classList.add('text-[var(--text-secondary)]', 'border-transparent');
      }
    }
  });

  initIcons();
}

// ============================================================================
// 4. INTERACTIVE ARCTIC GLASS VECTOR TOPOLOGY RADAR
// ============================================================================
function initRadarCanvas() {
  const canvas = document.getElementById('vector-radar-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const tooltip = document.getElementById('radar-tooltip');
  let animationFrameId;

  function resize() {
    canvas.width = canvas.parentElement.clientWidth;
    canvas.height = canvas.parentElement.clientHeight || 112;
  }
  resize();
  window.addEventListener('resize', resize);

  // Seed initial semantic vector nodes
  const nodeCount = 22;
  state.radarNodes = [];

  for (let i = 0; i < nodeCount; i++) {
    state.radarNodes.push({
      id: i + 1,
      x: 30 + Math.random() * (canvas.width - 60),
      y: 15 + Math.random() * (canvas.height - 30),
      vx: (Math.random() - 0.5) * 0.45,
      vy: (Math.random() - 0.5) * 0.35,
      radius: 3 + Math.random() * 2.5,
      pulse: Math.random() * Math.PI,
      page: (i % 2) + 1,
      similarity: (0.72 + Math.random() * 0.26).toFixed(3),
      label: `Chunk #${i + 1}`,
      sampleQuery: i % 2 === 0 ? "What is Dense Passage Retrieval (DPR)?" : "Explain RAG-Sequence vs RAG-Token models."
    });
  }

  let radarAngle = 0;

  function render() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;

    // Clean subtle background grid (minimal dots, no fake rotating radar or concentric circles)
    ctx.save();
    const dotSpacing = 30;
    ctx.fillStyle = isDark ? 'rgba(65, 70, 77, 0.25)' : 'rgba(209, 213, 219, 0.35)';
    for (let x = 15; x < canvas.width; x += dotSpacing) {
      for (let y = 10; y < canvas.height; y += dotSpacing) {
        ctx.fillRect(x, y, 1, 1);
      }
    }
    ctx.restore();

    // Distance lines between nearby nodes
    for (let i = 0; i < state.radarNodes.length; i++) {
      for (let j = i + 1; j < state.radarNodes.length; j++) {
        const dx = state.radarNodes[i].x - state.radarNodes[j].x;
        const dy = state.radarNodes[i].y - state.radarNodes[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 60) {
          ctx.strokeStyle = isDark
            ? `rgba(184, 58, 66, ${0.30 * (1 - dist / 60)})`
            : `rgba(184, 58, 66, ${0.22 * (1 - dist / 60)})`;
          ctx.lineWidth = 0.8;
          ctx.beginPath();
          ctx.moveTo(state.radarNodes[i].x, state.radarNodes[i].y);
          ctx.lineTo(state.radarNodes[j].x, state.radarNodes[j].y);
          ctx.stroke();
        }
      }
    }

    // Palette per theme (Black, Charcoal, Graphite & Muted Red)
    const nodePalette = isDark
      ? ['#B83A42', '#D6535B', '#862B32', '#A8ADB3']
      : ['#B83A42', '#A02D35', '#862B32', '#5F6368'];

    // Draw & Update nodes
    state.radarNodes.forEach((node, idx) => {
      node.x += node.vx;
      node.y += node.vy;

      if (node.x < 15 || node.x > canvas.width - 15) node.vx *= -1;
      if (node.y < 10 || node.y > canvas.height - 10) node.vy *= -1;

      node.pulse += 0.05;
      const pulseSize = Math.sin(node.pulse) * 1.5;
      const nodeColor = nodePalette[idx % nodePalette.length];

      // Glow halo
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius + 3 + pulseSize, 0, Math.PI * 2);
      ctx.fillStyle = isDark ? 'rgba(184, 58, 66, 0.20)' : 'rgba(184, 58, 66, 0.15)';
      ctx.fill();

      // Core
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
      ctx.fillStyle = nodeColor;
      ctx.fill();
    });

    animationFrameId = requestAnimationFrame(render);
  }

  render();

  // Mouse hover tooltip
  canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    let hoveredNode = null;
    let minDist = 18;

    state.radarNodes.forEach(node => {
      const d = Math.hypot(node.x - mouseX, node.y - mouseY);
      if (d < minDist) {
        minDist = d;
        hoveredNode = node;
      }
    });

    if (hoveredNode && tooltip) {
      tooltip.classList.remove('hidden');
      tooltip.style.left = `${Math.min(hoveredNode.x + 10, canvas.width - 190)}px`;
      tooltip.style.top = `${Math.max(hoveredNode.y - 45, 5)}px`;
      tooltip.innerHTML = `
        <div class="font-bold text-[var(--text-primary)]">${hoveredNode.label} &bull; Page ${hoveredNode.page}</div>
        <div class="text-[var(--primary-accent)] font-semibold">Cosine: ${hoveredNode.similarity} (${(hoveredNode.similarity * 100).toFixed(1)}%)</div>
        <div class="text-[9px] text-[var(--text-muted)] mt-0.5">Click to query in chat</div>
      `;
    } else if (tooltip) {
      tooltip.classList.add('hidden');
    }
  });

  canvas.addEventListener('mouseleave', () => {
    if (tooltip) tooltip.classList.add('hidden');
  });

  // Click node to query concept in chat
  canvas.addEventListener('click', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    state.radarNodes.forEach(node => {
      if (Math.hypot(node.x - mouseX, node.y - mouseY) < 18) {
        switchTab('chat');
        setChatInput(node.sampleQuery);
        const chatForm = document.getElementById('chat-form');
        if (chatForm) chatForm.dispatchEvent(new Event('submit'));
      }
    });
  });
}

// ============================================================================
// 5. DOCUMENT REPOSITORY & LIBRARY
// ============================================================================
async function fetchInitialData() {
  try {
    const res = await fetch('/api/v1/documents');
    if (!res.ok) throw new Error('Failed to load documents');
    const json = await res.json();

    if (json.success && json.data) {
      state.documents = json.data;
      renderDocumentLibrary(state.documents);
      updateSummaryMetrics();
      populateScopeDropdowns();
    }
  } catch (err) {
    console.error('Initial data fetch failed:', err);
  }
}

function updateSummaryMetrics() {
  const statDocs = document.getElementById('stat-total-docs');
  const statChunks = document.getElementById('stat-total-chunks');
  const sideStat = document.getElementById('side-stat-chunks');

  const totalChunks = state.documents.reduce((acc, d) => acc + (d.totalChunks || 0), 0);

  if (statDocs) statDocs.textContent = state.documents.length;
  if (statChunks) statChunks.textContent = totalChunks;
  if (sideStat) sideStat.textContent = `${totalChunks} Chunks`;
}

function populateScopeDropdowns() {
  const scopeSelect = document.getElementById('select-active-scope');
  const chunksSelect = document.getElementById('chunks-doc-select');

  if (scopeSelect) {
    scopeSelect.innerHTML = '<option value="">All Indexed Documents (Global Scope)</option>';
    state.documents.forEach(d => {
      const opt = document.createElement('option');
      opt.value = d.id;
      opt.textContent = `${d.filename} (${d.totalPages}p, ${d.totalChunks}c)`;
      scopeSelect.appendChild(opt);
    });
  }

  if (chunksSelect) {
    chunksSelect.innerHTML = '<option value="">Select Document to Inspect...</option>';
    state.documents.forEach(d => {
      const opt = document.createElement('option');
      opt.value = d.id;
      opt.textContent = `${d.filename} (${d.totalChunks} chunks)`;
      chunksSelect.appendChild(opt);
    });
    if (state.documents.length > 0 && !chunksSelect.value) {
      chunksSelect.value = state.documents[0].id;
      fetchDocumentChunks(state.documents[0].id);
    }
  }
}

function renderDocumentLibrary(docs) {
  const container = document.getElementById('docs-table-container');
  if (!container) return;

  if (docs.length === 0) {
    container.innerHTML = `
      <div class="p-12 text-center text-[var(--text-muted)] font-mono space-y-3">
        <i data-lucide="folder-open" class="w-10 h-10 mx-auto text-[var(--text-muted)]"></i>
        <p class="text-xs">No documents indexed in knowledge base.</p>
        <button onclick="document.getElementById('btn-open-upload').click()" class="btn-primary px-4 py-2 rounded-xl text-xs font-bold">
          Upload PDF
        </button>
      </div>
    `;
    initIcons();
    return;
  }

  let html = '';
  docs.forEach(doc => {
    const sizeKB = (doc.fileSize / 1024).toFixed(1);
    const dateFormatted = doc.createdAt ? new Date(doc.createdAt).toLocaleDateString() : 'Active';
    const isSelected = state.selectedDocId === doc.id;

    html += `
      <div class="p-4 rounded-xl arctic-card ${isSelected ? 'border-[var(--primary-accent)] ring-1 ring-[var(--primary-accent)]/30' : ''} flex flex-col md:flex-row md:items-center justify-between gap-4">
        
        <div class="flex items-center space-x-3.5">
          <div class="w-10 h-10 rounded-xl bg-[var(--surface-secondary)] text-[#B83A42] flex items-center justify-center shrink-0">
            <i data-lucide="file-text" class="w-5 h-5"></i>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <span class="text-sm font-bold text-[var(--text-primary)]">${doc.filename}</span>
              ${isSelected ? '<span class="px-2 py-0.2 rounded-full text-[9px] font-bold bg-[#B83A42]/15 text-[#B83A42] border border-[#B83A42]/30">Active Scope</span>' : ''}
            </div>
            <div class="text-[11px] text-[var(--text-secondary)] font-mono mt-0.5 flex flex-wrap items-center gap-3">
              <span>${doc.totalPages} Pages</span>
              <span>&bull;</span>
              <span>${doc.totalChunks} Vector Chunks</span>
              <span>&bull;</span>
              <span>${sizeKB} KB</span>
              <span>&bull;</span>
              <span>${dateFormatted}</span>
            </div>
          </div>
        </div>

        <div class="flex items-center space-x-2">
          <button onclick="handleScopeDoc('${doc.id}')" class="${isSelected ? 'btn-primary' : 'btn-secondary'} px-3 py-1.5 rounded-lg text-xs font-semibold">
            ${isSelected ? 'Scoped' : 'Scope Chat'}
          </button>

          <button onclick="openDocumentReader('${doc.id}', '${doc.filename}', ${doc.totalPages}, ${doc.totalChunks})" class="btn-secondary px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5" title="View Document in Reader">
            <i data-lucide="book-open" class="w-3.5 h-3.5 text-[#B83A42]"></i>
            <span>Read PDF</span>
          </button>

          <button onclick="handleViewChunks('${doc.id}')" class="btn-secondary px-3 py-1.5 rounded-lg text-xs font-semibold" title="Inspect Chunks">
            Chunks
          </button>

          <button onclick="handleDeleteDoc('${doc.id}', '${doc.filename}')" class="w-8 h-8 rounded-lg bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 text-red-500 flex items-center justify-center transition-all" title="Delete Document">
            <i data-lucide="trash-2" class="w-4 h-4"></i>
          </button>
        </div>

      </div>
    `;
  });

  container.innerHTML = html;
  initIcons();

  const filterInput = document.getElementById('doc-filter-input');
  if (filterInput) {
    filterInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase();
      const filtered = state.documents.filter(d => d.filename.toLowerCase().includes(q));
      renderDocumentLibrary(filtered);
    });
  }
}

function handleScopeDoc(docId) {
  if (state.selectedDocId === docId) {
    setActiveScope(null);
  } else {
    setActiveScope(docId);
  }
  renderDocumentLibrary(state.documents);
}

function handleViewChunks(docId) {
  switchTab('chunks');
  const chunksSelect = document.getElementById('chunks-doc-select');
  if (chunksSelect) {
    chunksSelect.value = docId;
    fetchDocumentChunks(docId);
  }
}

async function handleDeleteDoc(docId, filename) {
  if (!confirm(`Are you sure you want to delete "${filename}" and its vector index embeddings?`)) return;

  try {
    const res = await fetch(`/api/v1/documents/${docId}`, { method: 'DELETE' });
    const json = await res.json();
    if (json.success) {
      if (state.selectedDocId === docId) setActiveScope(null);
      await fetchInitialData();
    } else {
      alert(`Delete failed: ${json.message || 'Unknown error'}`);
    }
  } catch (err) {
    alert(`Failed to delete document: ${err.message}`);
  }
}

// ============================================================================
// 6. FIRST-CLASS AI CHAT STUDIO
// ============================================================================
function initChat() {
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const clearBtn = document.getElementById('btn-clear-chat');

  if (form && input) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const query = input.value.trim();
      if (!query) return;

      input.value = '';
      await sendChatMessage(query);
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      state.chatHistory = [];
      const messagesContainer = document.getElementById('chat-messages');
      if (messagesContainer) {
        messagesContainer.innerHTML = `
          <div id="chat-hero-state" class="my-auto py-8 text-center max-w-lg mx-auto space-y-4">
            <div class="w-14 h-14 mx-auto rounded-2xl bg-[var(--surface-secondary)] border border-[var(--border-color)] flex items-center justify-center text-[var(--primary-accent)] shadow-sm">
              <i data-lucide="sparkles" class="w-7 h-7"></i>
            </div>
            <div>
              <h3 class="text-base font-bold text-[var(--text-primary)]">Ask anything about your indexed documents</h3>
              <p class="text-xs text-[var(--text-secondary)] mt-1">
                DocMind performs dense vector retrieval across indexed PDF chunks to synthesize evidence-grounded answers with exact citations.
              </p>
            </div>
            <div class="pt-2 flex flex-col gap-2 text-left">
              <button onclick="setChatInput('What is Dense Passage Retrieval (DPR) and how does it function?')" class="p-2.5 rounded-xl bg-[var(--surface-secondary)] hover:border-[var(--primary-accent)] border border-[var(--border-color)] text-xs text-[var(--text-primary)] transition-all flex items-center justify-between group">
                <span>What is Dense Passage Retrieval (DPR) and how does it function?</span>
                <i data-lucide="arrow-right" class="w-3.5 h-3.5 text-[var(--text-muted)] group-hover:text-[var(--primary-accent)] transition-colors"></i>
              </button>
              <button onclick="setChatInput('Explain the difference between RAG-Sequence and RAG-Token models.')" class="p-2.5 rounded-xl bg-[var(--surface-secondary)] hover:border-[var(--primary-accent)] border border-[var(--border-color)] text-xs text-[var(--text-primary)] transition-all flex items-center justify-between group">
                <span>Explain the difference between RAG-Sequence and RAG-Token models.</span>
                <i data-lucide="arrow-right" class="w-3.5 h-3.5 text-[var(--text-muted)] group-hover:text-[var(--primary-accent)] transition-colors"></i>
              </button>
            </div>
          </div>
        `;
        initIcons();
      }
    });
  }
}

function setChatInput(text) {
  const input = document.getElementById('chat-input');
  if (input) {
    input.value = text;
    input.focus();
  }
}

async function sendChatMessage(question) {
  const messagesContainer = document.getElementById('chat-messages');
  if (!messagesContainer) return;

  const hero = document.getElementById('chat-hero-state');
  if (hero) hero.remove();

  // 1. User Message Bubble
  const userMsgId = 'user-' + Date.now();
  const userHtml = `
    <div id="${userMsgId}" class="flex items-start justify-end space-x-3 max-w-3xl ml-auto">
      <div class="btn-primary rounded-2xl rounded-tr-sm px-4 py-3 text-xs sm:text-sm font-medium">
        ${escapeHtml(question)}
      </div>
      <div class="w-8 h-8 rounded-lg bg-[var(--surface-secondary)] text-[var(--text-secondary)] flex items-center justify-center text-xs font-bold shrink-0 border border-[var(--border-color)]">
        <i data-lucide="user" class="w-4 h-4"></i>
      </div>
    </div>
  `;
  messagesContainer.insertAdjacentHTML('beforeend', userHtml);

  // 2. Assistant Thinking Bubble
  const botMsgId = 'bot-' + Date.now();
  const loadingHtml = `
    <div id="${botMsgId}" class="flex items-start space-x-3 max-w-3xl mr-auto">
      <div class="w-8 h-8 rounded-lg bg-gradient-to-tr from-[#862B32] to-[#B83A42] text-white flex items-center justify-center shrink-0 shadow-sm border border-white/10">
        <i data-lucide="bot" class="w-4 h-4"></i>
      </div>
      <div class="arctic-card rounded-2xl rounded-tl-sm p-4 space-y-2 text-xs sm:text-sm text-[var(--text-primary)]">
        <div class="flex items-center space-x-2 text-[#B83A42] font-mono text-xs">
          <span class="w-2 h-2 rounded-full bg-[#B83A42] animate-ping"></span>
          <span>Searching relevant passages & generating answer...</span>
        </div>
      </div>
    </div>
  `;
  messagesContainer.insertAdjacentHTML('beforeend', loadingHtml);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
  initIcons();

  // 3. Backend Query Request
  const payload = {
    question: question,
    documentId: state.selectedDocId || null,
    topK: 5,
    minSimilarity: 0.0
  };

  try {
    const res = await fetch('/api/v1/chat/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const json = await res.json();
    const botEl = document.getElementById(botMsgId);

    if (json.success && json.data) {
      const data = json.data;
      const citations = data.citations || [];
      const latency = data.responseTimeMs || 180;

      if (citations.length > 0 && citations[0].similarityScore) {
        state.topSimilarityRecorded = Math.max(state.topSimilarityRecorded, citations[0].similarityScore);
        const topStat = document.getElementById('stat-top-sim');
        if (topStat) topStat.textContent = `Max Cos: ${state.topSimilarityRecorded.toFixed(3)}`;
      }

      // Build Citations HTML
      let citationsHtml = '';
      if (citations.length > 0) {
        citationsHtml = `
          <div class="mt-3 pt-3 border-t border-[var(--border-color)] space-y-2">
            <div class="flex items-center justify-between text-[11px] font-mono text-[var(--text-secondary)]">
              <span class="flex items-center gap-1.5 text-[#B83A42] font-bold">
                <i data-lucide="bookmark" class="w-3.5 h-3.5"></i> Grounded Source Citations (${citations.length})
              </span>
              <span>${latency}ms retrieval</span>
            </div>
            <div class="space-y-1.5">
        `;

        citations.forEach(cit => {
          const docTitle = cit.fileName || cit.documentName || 'Document';
          const snippetText = cit.snippet || cit.sourceExcerpt || '';
          const score = cit.similarityScore ? (cit.similarityScore * 100).toFixed(1) : '95.0';
          const isHighMatch = cit.similarityScore && cit.similarityScore > 0.4;
          const scoreColor = isHighMatch ? 'text-emerald-400 bg-emerald-500/10' : 'text-[#B83A42] bg-[#B83A42]/10';

          citationsHtml += `
            <div class="p-2.5 rounded-lg bg-[var(--surface-secondary)] border border-[var(--border-color)] space-y-1 text-xs font-mono">
              <div class="flex items-center justify-between">
                <span class="text-[#B83A42] font-bold">${docTitle} &bull; Page ${cit.pageNumber || 1}</span>
                <span class="px-2 py-0.5 rounded text-[10px] font-bold ${scoreColor}">Cosine: ${cit.similarityScore ? cit.similarityScore.toFixed(4) : score}%</span>
              </div>
              <p class="text-[11px] text-[var(--text-secondary)] leading-relaxed font-sans line-clamp-2">
                "${escapeHtml(snippetText)}"
              </p>
            </div>
          `;
        });

        citationsHtml += `</div></div>`;
      }

      const formattedAnswer = formatMarkdown(data.answer);

      if (botEl) {
        botEl.innerHTML = `
          <div class="w-8 h-8 rounded-lg bg-gradient-to-tr from-[#862B32] to-[#B83A42] text-white flex items-center justify-center shrink-0 shadow-sm border border-white/10">
            <i data-lucide="bot" class="w-4 h-4"></i>
          </div>
          <div class="arctic-card rounded-2xl rounded-tl-sm p-4 space-y-3 text-xs sm:text-sm text-[var(--text-primary)] w-full">
            <div class="flex items-center justify-between pb-1 border-b border-[var(--border-color)] text-[10px] font-mono text-[var(--text-secondary)]">
              <span class="text-[#B83A42] font-bold">DocMind Grounded Assistant</span>
              <div class="flex items-center space-x-2">
                <button onclick="speakText('${escapeQuotes(data.answer)}')" class="hover:text-[var(--primary-accent)] flex items-center gap-1" title="Read Aloud">
                  <i data-lucide="volume-2" class="w-3.5 h-3.5"></i>
                  <span>Listen</span>
                </button>
                <button onclick="copyToClipboard('${escapeQuotes(data.answer)}', this)" class="hover:text-[var(--primary-accent)] flex items-center gap-1" title="Copy Response">
                  <i data-lucide="copy" class="w-3.5 h-3.5"></i>
                  <span>Copy</span>
                </button>
              </div>
            </div>
            
            <div class="leading-relaxed space-y-2 text-[var(--text-primary)]">
              ${formattedAnswer}
            </div>

            ${citationsHtml}
          </div>
        `;
      }
    } else {
      if (botEl) {
        botEl.innerHTML = `
          <div class="w-8 h-8 rounded-lg bg-red-600 text-white flex items-center justify-center shrink-0">
            <i data-lucide="alert-circle" class="w-4 h-4"></i>
          </div>
          <div class="arctic-card rounded-2xl rounded-tl-sm p-4 text-xs text-red-500">
            ${json.message || 'Error processing query.'}
          </div>
        `;
      }
    }
  } catch (err) {
    const botEl = document.getElementById(botMsgId);
    if (botEl) {
      botEl.innerHTML = `
        <div class="w-8 h-8 rounded-lg bg-red-600 text-white flex items-center justify-center shrink-0">
          <i data-lucide="alert-circle" class="w-4 h-4"></i>
        </div>
        <div class="arctic-card rounded-2xl rounded-tl-sm p-4 text-xs text-red-500">
          Connection error: ${err.message}. Is backend running on http://127.0.0.1:8000?
        </div>
      `;
    }
  }

  messagesContainer.scrollTop = messagesContainer.scrollHeight;
  initIcons();
}

// ============================================================================
// 7. SEMANTIC CLAUSE SEARCH
// ============================================================================
function initSearch() {
  const btn = document.getElementById('btn-exec-search');
  const input = document.getElementById('search-input');
  const topkSlider = document.getElementById('search-topk');
  const minsimSlider = document.getElementById('search-minsim');

  if (topkSlider) {
    topkSlider.addEventListener('input', (e) => {
      document.getElementById('search-topk-val').textContent = e.target.value;
    });
  }

  if (minsimSlider) {
    minsimSlider.addEventListener('input', (e) => {
      document.getElementById('search-minsim-val').textContent = parseFloat(e.target.value).toFixed(2);
    });
  }

  if (btn && input) {
    const runSearch = async () => {
      const q = input.value.trim();
      if (!q) return;

      const resultsContainer = document.getElementById('search-results-list');
      if (resultsContainer) {
        resultsContainer.innerHTML = '<div class="p-6 text-center text-xs text-[var(--primary-accent)] font-mono animate-pulse">Computing cosine dot-products across vector indices...</div>';
      }

      try {
        const payload = {
          query: q,
          documentId: state.selectedDocId || null,
          topK: parseInt(topkSlider ? topkSlider.value : 5),
          minSimilarity: parseFloat(minsimSlider ? minsimSlider.value : 0.0)
        };

        const res = await fetch('/api/v1/chat/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const json = await res.json();
        if (json.success && json.data) {
          renderSearchResults(json.data.matches || []);
        } else {
          resultsContainer.innerHTML = `<div class="p-6 text-center text-xs text-red-500 font-mono">${json.message || 'No matches found.'}</div>`;
        }
      } catch (err) {
        resultsContainer.innerHTML = `<div class="p-6 text-center text-xs text-red-500 font-mono">Search failed: ${err.message}</div>`;
      }
    };

    btn.addEventListener('click', runSearch);
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') runSearch();
    });
  }
}

function renderSearchResults(matches) {
  const container = document.getElementById('search-results-list');
  if (!container) return;

  if (matches.length === 0) {
    container.innerHTML = '<div class="p-6 text-center text-xs text-[var(--text-muted)] font-mono">No matching passages found exceeding threshold.</div>';
    return;
  }

  let html = `
    <div class="grid grid-cols-12 text-[10px] font-mono text-[var(--text-secondary)] uppercase tracking-wider px-4 py-2 border-b border-[var(--border-color)]">
      <div class="col-span-7">Category / Passage Excerpt</div>
      <div class="col-span-1 text-center">Page</div>
      <div class="col-span-2 text-center">Cosine Similarity</div>
      <div class="col-span-2 text-right">Relevance Track</div>
    </div>
  `;

  matches.forEach(m => {
    const textSnippet = m.snippet || m.sourceExcerpt || '';
    const docName = m.fileName || m.documentName || 'Document';
    const scoreVal = m.similarityScore || 0;
    const scorePct = Math.round(scoreVal * 100);
    const scoreColor = scoreVal > 0.4 ? 'text-emerald-500' : 'text-[#B83A42]';
    const barWidth = Math.min(100, Math.max(10, scorePct * 1.5));

    html += `
      <div class="grid grid-cols-12 items-center p-3 rounded-xl arctic-card text-xs">
        <div class="col-span-7 pr-3">
          <p class="text-[var(--text-primary)] line-clamp-2 leading-relaxed font-sans">${escapeHtml(textSnippet)}</p>
          <div class="text-[10px] text-[var(--text-secondary)] font-mono mt-1">${docName}</div>
        </div>
        <div class="col-span-1 text-center font-mono">
          <span class="px-2 py-0.5 rounded bg-[var(--surface-secondary)] text-[var(--text-primary)] font-bold">P.${m.pageNumber || 1}</span>
        </div>
        <div class="col-span-2 text-center font-mono ${scoreColor} font-bold">
          ${scoreVal.toFixed(4)} <span class="text-[10px] text-[var(--text-secondary)] font-normal">(${scorePct}%)</span>
        </div>
        <div class="col-span-2 flex items-center justify-end space-x-2">
          <div class="w-20 bg-[var(--surface-secondary)] rounded-full h-1.5 overflow-hidden">
            <div class="h-full bg-gradient-to-r from-[#862B32] to-[#B83A42] rounded-full" style="width: ${barWidth}%"></div>
          </div>
          <button onclick="setChatInput('Explain this passage: ${escapeQuotes(textSnippet.substring(0, 100))}...')" class="p-1 hover:text-[#B83A42] text-[var(--text-muted)]" title="Query this passage">
            <i data-lucide="message-square" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
  initIcons();
}

// ============================================================================
// 8. CHUNK EXPLORER
// ============================================================================
function initChunks() {
  const select = document.getElementById('chunks-doc-select');
  if (select) {
    select.addEventListener('change', (e) => {
      if (e.target.value) {
        fetchDocumentChunks(e.target.value);
      }
    });
  }
}

async function fetchDocumentChunks(docId) {
  const container = document.getElementById('chunks-stream-container');
  if (!container) return;

  container.innerHTML = '<div class="p-6 text-center text-xs text-[var(--primary-accent)] font-mono animate-pulse">Loading chunks for document...</div>';

  try {
    const res = await fetch(`/api/v1/documents/${docId}/chunks`);
    const json = await res.json();

    if (json.success && json.data) {
      renderChunks(json.data);
    } else {
      container.innerHTML = `<div class="p-6 text-center text-xs text-red-500 font-mono">${json.message || 'No chunks available.'}</div>`;
    }
  } catch (err) {
    container.innerHTML = `<div class="p-6 text-center text-xs text-red-500 font-mono">Failed to load chunks: ${err.message}</div>`;
  }
}

function renderChunks(chunks) {
  const container = document.getElementById('chunks-stream-container');
  if (!container) return;

  if (chunks.length === 0) {
    container.innerHTML = '<div class="p-6 text-center text-xs text-[var(--text-muted)] font-mono">No chunks found for this document.</div>';
    return;
  }

  let html = '';
  chunks.forEach(c => {
    html += `
      <div class="p-4 rounded-xl arctic-card space-y-2">
        <div class="flex items-center justify-between text-xs font-mono pb-2 border-b border-[var(--border-color)]">
          <div class="flex items-center space-x-2">
            <span class="w-2 h-2 rounded-full bg-[var(--primary-accent)]"></span>
            <span class="text-[var(--text-primary)] font-bold">Chunk #${c.chunkIndex}</span>
            <span class="px-2 py-0.2 rounded bg-[var(--surface-secondary)] text-[var(--primary-accent)] font-bold">Page ${c.pageNumber}</span>
          </div>
          <div class="flex items-center space-x-3 text-[11px] text-[var(--text-secondary)]">
            <span>${c.charCount} characters</span>
            <button onclick="copyToClipboard('${escapeQuotes(c.text)}', this)" class="hover:text-[var(--primary-accent)] flex items-center gap-1">
              <i data-lucide="copy" class="w-3 h-3"></i> Copy
            </button>
            <button onclick="switchTab('chat'); setChatInput('What does chunk #${c.chunkIndex} on page ${c.pageNumber} state?')" class="hover:text-[var(--primary-accent)] flex items-center gap-1">
              <i data-lucide="message-square" class="w-3 h-3"></i> Ask
            </button>
          </div>
        </div>
        <p class="text-xs text-[var(--text-secondary)] leading-relaxed font-mono whitespace-pre-wrap">${escapeHtml(c.text)}</p>
      </div>
    `;
  });

  container.innerHTML = html;
  initIcons();
}

// ============================================================================
// 9. UPLOAD MODAL & FILE INGESTION
// ============================================================================
function initUploadModal() {
  const modal = document.getElementById('modal-upload');
  const openBtn = document.getElementById('btn-open-upload');
  const closeBtn = document.getElementById('btn-close-upload');
  const cancelBtn = document.getElementById('btn-cancel-upload');
  const submitBtn = document.getElementById('btn-submit-upload');
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  const uploadStatus = document.getElementById('upload-status');
  const filenameEl = document.getElementById('upload-filename');
  const progressBar = document.getElementById('upload-progress-bar');
  const percentEl = document.getElementById('upload-percent');

  let selectedFile = null;

  const showModal = () => {
    modal.classList.remove('hidden');
    selectedFile = null;
    if (uploadStatus) uploadStatus.classList.add('hidden');
    if (progressBar) progressBar.style.width = '0%';
  };

  const hideModal = () => {
    modal.classList.add('hidden');
  };

  if (openBtn) openBtn.addEventListener('click', showModal);
  if (closeBtn) closeBtn.addEventListener('click', hideModal);
  if (cancelBtn) cancelBtn.addEventListener('click', hideModal);

  if (dropZone && fileInput) {
    dropZone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        selectedFile = e.target.files[0];
        if (filenameEl) filenameEl.textContent = selectedFile.name;
        if (uploadStatus) uploadStatus.classList.remove('hidden');
        if (percentEl) percentEl.textContent = `${(selectedFile.size / 1024).toFixed(1)} KB - Ready`;
      }
    });

    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('border-[var(--primary-accent)]', 'bg-[var(--surface-tertiary)]');
    });

    dropZone.addEventListener('dragleave', () => {
      dropZone.classList.remove('border-[var(--primary-accent)]', 'bg-[var(--surface-tertiary)]');
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('border-[var(--primary-accent)]', 'bg-[var(--surface-tertiary)]');
      if (e.dataTransfer.files.length > 0) {
        selectedFile = e.dataTransfer.files[0];
        if (filenameEl) filenameEl.textContent = selectedFile.name;
        if (uploadStatus) uploadStatus.classList.remove('hidden');
        if (percentEl) percentEl.textContent = `${(selectedFile.size / 1024).toFixed(1)} KB - Ready`;
      }
    });
  }

  if (submitBtn) {
    submitBtn.addEventListener('click', async () => {
      if (!selectedFile) {
        alert('Please select a PDF document first.');
        return;
      }

      const formData = new FormData();
      formData.append('file', selectedFile);

      if (progressBar) progressBar.style.width = '40%';
      if (percentEl) percentEl.textContent = 'Parsing text & generating embeddings...';

      try {
        const res = await fetch('/api/v1/documents/upload', {
          method: 'POST',
          body: formData
        });

        const json = await res.json();
        if (json.success) {
          if (progressBar) progressBar.style.width = '100%';
          if (percentEl) percentEl.textContent = 'Completed!';
          setTimeout(async () => {
            hideModal();
            await fetchInitialData();
            switchTab('docs');
          }, 600);
        } else {
          alert(`Upload failed: ${json.message || 'Unknown error'}`);
          if (progressBar) progressBar.style.width = '0%';
        }
      } catch (err) {
        alert(`Upload error: ${err.message}`);
        if (progressBar) progressBar.style.width = '0%';
      }
    });
  }
}

// ============================================================================
// 10. DOCUMENT READER / VIEWER MODAL
// ============================================================================
function initReaderModal() {
  const modal = document.getElementById('modal-reader');
  const closeBtn = document.getElementById('btn-close-reader');

  if (closeBtn && modal) {
    closeBtn.addEventListener('click', () => {
      modal.classList.add('hidden');
      const iframe = document.getElementById('reader-iframe');
      if (iframe) iframe.src = 'about:blank';
    });
  }
}

function openDocumentReader(docId, filename, pages, chunks) {
  const modal = document.getElementById('modal-reader');
  const titleEl = document.getElementById('reader-title');
  const metaEl = document.getElementById('reader-meta');
  const dlLink = document.getElementById('reader-download-link');
  const iframe = document.getElementById('reader-iframe');

  if (modal && iframe) {
    const fileUrl = `/api/v1/documents/${docId}/file`;
    if (titleEl) titleEl.textContent = filename;
    if (metaEl) metaEl.textContent = `${pages} Pages • ${chunks} Vector Chunks • ID: ${docId.substring(0, 8)}...`;
    if (dlLink) dlLink.href = fileUrl;

    iframe.src = fileUrl;
    modal.classList.remove('hidden');
    initIcons();
  }
}

// ============================================================================
// 11. UTILITIES: SPEECH SYNTHESIS, CLIPBOARD, FORMATTING
// ============================================================================
function speakText(text) {
  if (!('speechSynthesis' in window)) {
    alert('Text-to-speech is not supported by your browser.');
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.05;
  utterance.pitch = 1.0;
  window.speechSynthesis.speak(utterance);
}

function copyToClipboard(text, btnElement) {
  navigator.clipboard.writeText(text).then(() => {
    if (btnElement) {
      const origHtml = btnElement.innerHTML;
      btnElement.innerHTML = '<span class="text-emerald-600 font-bold">Copied!</span>';
      setTimeout(() => {
        btnElement.innerHTML = origHtml;
        initIcons();
      }, 1500);
    }
  }).catch(err => {
    console.error('Copy failed:', err);
  });
}

function formatMarkdown(text) {
  if (!text) return '';
  let res = escapeHtml(text);
  res = res.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-[var(--text-primary)]">$1</strong>');
  res = res.replace(/`(.*?)`/g, '<code class="px-1.5 py-0.5 rounded bg-[var(--surface-secondary)] text-[var(--primary-accent)] font-mono text-[11px]">$1</code>');
  res = res.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');
  return res;
}

function escapeHtml(string) {
  const entityMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
    '/': '&#x2F;'
  };
  return String(string).replace(/[&<>"'\/]/g, s => entityMap[s]);
}

function escapeQuotes(string) {
  if (!string) return '';
  return string.replace(/'/g, "\\'").replace(/"/g, '&quot;').replace(/\n/g, ' ');
}
