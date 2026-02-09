// ============================================
// SUPABASE RAG APPLICATION
// ============================================

// Check if config is valid BEFORE trying to create Supabase client
function isConfigValid() {
    if (typeof SUPABASE_CONFIG === 'undefined') return false;

    const isPlaceholderUrl = !SUPABASE_CONFIG.url ||
        SUPABASE_CONFIG.url.includes('YOUR_SUPABASE') ||
        SUPABASE_CONFIG.url.includes('YOUR-PROJECT') ||
        SUPABASE_CONFIG.url === 'https://your-project-ref.supabase.co';

    const isPlaceholderKey = !SUPABASE_CONFIG.anonKey ||
        SUPABASE_CONFIG.anonKey.includes('YOUR_SUPABASE') ||
        SUPABASE_CONFIG.anonKey.includes('your-anon-key') ||
        SUPABASE_CONFIG.anonKey.length < 20;

    return !isPlaceholderUrl && !isPlaceholderKey;
}

// Initialize Supabase client only if config is valid
let supabaseClient = null;
const configIsValid = isConfigValid();

if (configIsValid) {
    try {
        supabaseClient = window.supabase.createClient(
            SUPABASE_CONFIG.url,
            SUPABASE_CONFIG.anonKey
        );
    } catch (err) {
        console.error('Failed to initialize Supabase client:', err);
    }
}

// DOM Elements
const loginScreen = document.getElementById('login-screen');
const appScreen = document.getElementById('app-screen');
const emailInput = document.getElementById('email-input');
const loginBtn = document.getElementById('login-btn');
const loginMessage = document.getElementById('login-message');
const logoutBtn = document.getElementById('logout-btn');
const userEmailSpan = document.getElementById('user-email');
const loading = document.getElementById('loading');

// Setup Banner Elements
const setupBanner = document.getElementById('setup-banner');
const githubPagesUrl = document.getElementById('github-pages-url');
const copyUrlBtn = document.getElementById('copy-url-btn');
const closeSetupBannerBtn = document.getElementById('close-setup-banner');
const checkConfig = document.getElementById('check-config');
const checkConnection = document.getElementById('check-connection');
const checkRedirect = document.getElementById('check-redirect');

// Search Panel Elements
const keywordInput = document.getElementById('keyword-input');
const keywordBtn = document.getElementById('keyword-btn');
const keywordResults = document.getElementById('keyword-results');
const keywordStatus = document.getElementById('keyword-status');

const semanticInput = document.getElementById('semantic-input');
const semanticBtn = document.getElementById('semantic-btn');
const semanticResults = document.getElementById('semantic-results');
const semanticStatus = document.getElementById('semantic-status');

const ragInput = document.getElementById('rag-input');
const ragBtn = document.getElementById('rag-btn');
const ragResults = document.getElementById('rag-results');
const ragStatus = document.getElementById('rag-status');

// ============================================
// SETUP BANNER DETECTION
// ============================================

async function runSetupChecks() {
    const setupStatus = {
        configValid: false,
        connectionOk: false,
        allGood: false
    };

    // Calculate and display GitHub Pages URL (full URL with path)
    const currentUrl = window.location.origin + window.location.pathname;
    if (githubPagesUrl) {
        githubPagesUrl.textContent = currentUrl;
    }

    // Set setup guide link to GitHub repo (for better preview)
    const setupGuideLink = document.getElementById('setup-guide-link');
    if (setupGuideLink && currentUrl.includes('github.io')) {
        const pathParts = window.location.pathname.split('/').filter(p => p);
        const repoName = pathParts[0] || 'conference-rag';
        const username = currentUrl.split('.github.io')[0].split('//')[1];
        setupGuideLink.href = `https://github.com/${username}/${repoName}/blob/main/README.md`;
    } else if (setupGuideLink) {
        setupGuideLink.href = 'README.md';
    }

    // Set Supabase URL configuration link
    const supabaseConfigLink = document.getElementById('supabase-config-link');
    if (supabaseConfigLink && typeof SUPABASE_CONFIG !== 'undefined' && SUPABASE_CONFIG.url) {
        try {
            const supabaseUrl = new URL(SUPABASE_CONFIG.url);
            const projectId = supabaseUrl.hostname.split('.')[0];
            supabaseConfigLink.href = `https://supabase.com/dashboard/project/${projectId}/auth/url-configuration`;
        } catch (err) {
            supabaseConfigLink.style.display = 'none';
        }
    } else if (supabaseConfigLink) {
        supabaseConfigLink.style.display = 'none';
    }

    // Check 1: Config has real values
    if (!configIsValid) {
        updateCheckItem(checkConfig, 'error', '❌', 'Configure Supabase credentials in config.js');
        updateCheckItem(checkConnection, 'warning', '⏳', 'Waiting for config...');
    } else {
        updateCheckItem(checkConfig, 'success', '✅', 'Supabase credentials configured');
        setupStatus.configValid = true;

        // Check 2: Supabase connection
        if (supabaseClient) {
            try {
                const { data, error } = await supabaseClient.auth.getSession();
                if (error) {
                    updateCheckItem(checkConnection, 'error', '❌', `Connection failed: ${error.message}`);
                } else {
                    updateCheckItem(checkConnection, 'success', '✅', 'Supabase connection OK');
                    setupStatus.connectionOk = true;
                }
            } catch (err) {
                updateCheckItem(checkConnection, 'error', '❌', 'Connection failed - check config');
            }
        } else {
            updateCheckItem(checkConnection, 'error', '❌', 'Failed to create Supabase client');
        }
    }

    // Check 3: Redirect URL reminder
    updateCheckItem(checkRedirect, 'warning', '⚠️', `Add ${currentUrl} to Supabase redirect URLs`);

    // Show/hide banner
    setupStatus.allGood = setupStatus.configValid && setupStatus.connectionOk;
    const bannerDismissed = sessionStorage.getItem('setup_banner_dismissed');
    if (setupBanner) {
        if (!setupStatus.allGood && !bannerDismissed) {
            setupBanner.classList.remove('hidden');
        } else {
            setupBanner.classList.add('hidden');
        }
    }

    return setupStatus;
}

function updateCheckItem(element, status, icon, text) {
    if (!element) return;
    element.className = `setup-item ${status}`;
    const iconSpan = element.querySelector('.check-icon');
    const textSpan = element.querySelector('span:last-child');
    if (iconSpan) iconSpan.textContent = icon;
    if (textSpan) textSpan.textContent = text;
}

// Copy URL to clipboard
if (copyUrlBtn) {
    copyUrlBtn.addEventListener('click', async () => {
        const url = githubPagesUrl ? githubPagesUrl.textContent : (window.location.origin + window.location.pathname);
        try {
            await navigator.clipboard.writeText(url);
            copyUrlBtn.textContent = '✅';
            copyUrlBtn.classList.add('copied');
            setTimeout(() => {
                copyUrlBtn.textContent = '📋';
                copyUrlBtn.classList.remove('copied');
            }, 2000);
        } catch (err) {
            console.error('Failed to copy URL:', err);
        }
    });
}

// Dismiss setup banner
if (closeSetupBannerBtn) {
    closeSetupBannerBtn.addEventListener('click', () => {
        if (setupBanner) {
            setupBanner.classList.add('hidden');
        }
        sessionStorage.setItem('setup_banner_dismissed', 'true');
    });
}

// ============================================
// AUTHENTICATION
// ============================================

async function checkSession() {
    if (!supabaseClient) {
        showLogin();
        return;
    }

    const { data: { session } } = await supabaseClient.auth.getSession();

    if (session) {
        showApp(session.user);
    } else {
        showLogin();
    }
}

// Handle magic link login
if (loginBtn) {
    loginBtn.addEventListener('click', async () => {
        if (!supabaseClient) {
            showMessage('Please configure Supabase first (see Setup Guide)', 'error');
            return;
        }

        const email = emailInput.value.trim();

        if (!email) {
            showMessage('Please enter your email', 'error');
            return;
        }

        showLoading(true);

        const { error } = await supabaseClient.auth.signInWithOtp({
            email: email,
            options: {
                emailRedirectTo: window.location.origin + window.location.pathname
            }
        });

        showLoading(false);

        if (error) {
            showMessage(`Error: ${error.message}`, 'error');
        } else {
            showMessage('Check your email for the magic link!', 'success');
        }
    });
}

// Handle logout
if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
        if (supabaseClient) {
            await supabaseClient.auth.signOut();
        }
        showLogin();
    });
}

// Listen for auth state changes
if (supabaseClient) {
    supabaseClient.auth.onAuthStateChange((event, session) => {
        if (event === 'SIGNED_IN' && session) {
            showApp(session.user);
        } else if (event === 'SIGNED_OUT') {
            showLogin();
        }
    });
}

// ============================================
// UI STATE MANAGEMENT
// ============================================

function showLogin() {
    if (loginScreen) loginScreen.classList.remove('hidden');
    if (appScreen) appScreen.classList.add('hidden');
}

function showApp(user) {
    if (loginScreen) loginScreen.classList.add('hidden');
    if (appScreen) appScreen.classList.remove('hidden');
    if (userEmailSpan) userEmailSpan.textContent = user.email;
    // Check search readiness when user logs in
    checkSearchReadiness();
}

function showMessage(text, type) {
    if (loginMessage) {
        loginMessage.textContent = text;
        loginMessage.className = `message ${type}`;
        loginMessage.classList.remove('hidden');
    }
}

function showLoading(show) {
    if (loading) {
        if (show) {
            loading.classList.remove('hidden');
        } else {
            loading.classList.add('hidden');
        }
    }
}

// ============================================
// SEARCH READINESS DETECTION
// ============================================

async function checkSearchReadiness() {
    if (!supabaseClient) return;

    // Check 1: Does the sentence_embeddings table have data? (keyword search)
    try {
        const { count, error } = await supabaseClient
            .from('sentence_embeddings')
            .select('*', { count: 'exact', head: true });

        if (!error && count > 0) {
            setSearchReady('keyword', true);
        } else {
            setSearchReady('keyword', false);
        }
    } catch (err) {
        console.log('Keyword readiness check failed:', err.message);
        setSearchReady('keyword', false);
    }

    // Check 2: Do sentence_embeddings have embeddings? (semantic search)
    try {
        const { data, error } = await supabaseClient
            .from('sentence_embeddings')
            .select('embedding')
            .not('embedding', 'is', null)
            .limit(1);

        const hasEmbeddings = !error && data && data.length > 0;

        if (hasEmbeddings) {
            // Also check if embed-question edge function responds
            try {
                const response = await fetch(`${SUPABASE_CONFIG.url}/functions/v1/embed-question`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${SUPABASE_CONFIG.anonKey}`
                    },
                    body: JSON.stringify({ question: 'test' })
                });
                setSearchReady('semantic', response.ok);
            } catch {
                // CORS error or network error means function isn't deployed
                setSearchReady('semantic', false);
            }
        } else {
            setSearchReady('semantic', false);
        }
    } catch (err) {
        console.log('Semantic readiness check failed:', err.message);
        setSearchReady('semantic', false);
    }

    // Check 3: Does generate-answer edge function respond? (RAG)
    try {
        const response = await fetch(`${SUPABASE_CONFIG.url}/functions/v1/generate-answer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${SUPABASE_CONFIG.anonKey}`
            },
            body: JSON.stringify({ question: 'test', context_talks: [] })
        });
        // Even an error response (like 400) from the function means it's deployed
        setSearchReady('rag', response.status !== 404);
    } catch {
        // CORS error or network error means function isn't deployed
        setSearchReady('rag', false);
    }
}

function setSearchReady(type, ready) {
    const statusEl = document.getElementById(`${type}-status`);
    const inputEl = document.getElementById(`${type}-input`);
    const btnEl = document.getElementById(`${type}-btn`);
    const panelEl = document.getElementById(`${type}-panel`);

    if (statusEl) {
        if (ready) {
            statusEl.textContent = '🟢 Ready';
            statusEl.className = 'status-badge ready';
        } else {
            statusEl.textContent = '🔴 Not Ready';
            statusEl.className = 'status-badge not-ready';
        }
    }

    if (inputEl) inputEl.disabled = !ready;
    if (btnEl) btnEl.disabled = !ready;

    if (panelEl) {
        if (ready) {
            panelEl.classList.add('panel-ready');
            panelEl.classList.remove('panel-not-ready');
        } else {
            panelEl.classList.add('panel-not-ready');
            panelEl.classList.remove('panel-ready');
        }
    }
}

// ============================================
// KEYWORD SEARCH
// ============================================

async function keywordSearch() {
    const query = keywordInput ? keywordInput.value.trim() : '';
    if (!query || !supabaseClient) return;

    showLoading(true);
    clearResults('keyword');

    try {
        // Search sentence_embeddings that contain the keyword (case-insensitive)
        const { data, error } = await supabaseClient
            .from('sentence_embeddings')
            .select('text, talk_id, title, speaker')
            .ilike('text', `%${query}%`)
            .limit(20);

        if (error) throw new Error(`Search failed: ${error.message}`);

        if (!data || data.length === 0) {
            showResults('keyword', '<div class="no-results">No results found. Try different keywords.</div>');
            return;
        }

        // Group by talk
        const talks = {};
        for (const row of data) {
            const talkId = row.talk_id;
            if (!talks[talkId]) {
                talks[talkId] = {
                    title: row.title || 'Unknown Talk',
                    speaker: row.speaker || 'Unknown Speaker',
                    sentences: []
                };
            }
            talks[talkId].sentences.push(highlightKeyword(row.text, query));
        }

        let html = '';
        for (const talk of Object.values(talks)) {
            html += `<div class="result-card">
                <div class="result-title">${escapeHtml(talk.title)}</div>
                <div class="result-speaker">by ${escapeHtml(talk.speaker)}</div>
                <div class="result-sentences">${talk.sentences.slice(0, 3).join('<br>')}</div>
            </div>`;
        }
        showResults('keyword', html);

    } catch (error) {
        showResults('keyword', `<div class="result-error">Error: ${escapeHtml(error.message)}</div>`);
    } finally {
        showLoading(false);
    }
}

function highlightKeyword(text, keyword) {
    const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`(${escaped})`, 'gi');
    return escapeHtml(text).replace(regex, '<mark>$1</mark>');
}

// ============================================
// SEMANTIC SEARCH
// ============================================

async function semanticSearch() {
    const query = semanticInput ? semanticInput.value.trim() : '';
    if (!query || !supabaseClient) return;

    showLoading(true);
    clearResults('semantic');

    try {
        // Step 1: Get embedding
        const embedding = await getEmbedding(query);

        // Step 2: Search for similar sentences
        const results = await searchSentences(embedding);

        if (!results || results.length === 0) {
            showResults('semantic', '<div class="no-results">No similar content found. Try a different query.</div>');
            return;
        }

        // Step 3: Group by talk
        const topTalks = groupByTalk(results);

        let html = '';
        for (const talk of topTalks) {
            html += `<div class="result-card">
                <div class="result-title">${escapeHtml(talk.title)}</div>
                <div class="result-speaker">by ${escapeHtml(talk.speaker)}</div>
                <div class="result-sentences">${escapeHtml(talk.text)}</div>
            </div>`;
        }
        showResults('semantic', html);

    } catch (error) {
        showResults('semantic', `<div class="result-error">Error: ${escapeHtml(error.message)}</div>`);
    } finally {
        showLoading(false);
    }
}

// ============================================
// RAG (ASK A QUESTION)
// ============================================

async function askQuestion() {
    const question = ragInput ? ragInput.value.trim() : '';
    if (!question || !supabaseClient) return;

    showLoading(true);
    clearResults('rag');

    try {
        // Step 1: Get embedding
        const embedding = await getEmbedding(question);

        // Step 2: Search for similar sentences
        const results = await searchSentences(embedding);

        // Step 3: Group by talk
        const topTalks = groupByTalk(results);

        // Step 4: Generate answer
        const answer = await generateAnswer(question, topTalks);

        let html = `<div class="result-card rag-answer">
            <div class="result-title">AI Answer</div>
            <div class="result-sentences">${escapeHtml(answer)}</div>
        </div>`;

        // Show source talks
        html += '<div class="result-sources"><strong>Sources:</strong></div>';
        for (const talk of topTalks) {
            html += `<div class="result-card result-source">
                <div class="result-title">${escapeHtml(talk.title)}</div>
                <div class="result-speaker">by ${escapeHtml(talk.speaker)}</div>
            </div>`;
        }
        showResults('rag', html);

    } catch (error) {
        showResults('rag', `<div class="result-error">Error: ${escapeHtml(error.message)}</div>`);
    } finally {
        showLoading(false);
    }
}

// ============================================
// SHARED SEARCH UTILITIES
// ============================================

// Get embedding via Edge Function
async function getEmbedding(text) {
    const response = await fetch(`${SUPABASE_CONFIG.url}/functions/v1/embed-question`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${SUPABASE_CONFIG.anonKey}`
        },
        body: JSON.stringify({ question: text })
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'Failed to get embedding');
    }

    const data = await response.json();
    return data.embedding;
}

// Search sentences using vector similarity
async function searchSentences(embedding) {
    if (!supabaseClient) throw new Error('Supabase not configured');

    const { data, error } = await supabaseClient.rpc('match_sentences', {
        query_embedding: embedding,
        match_threshold: 0.6,
        match_count: 20
    });

    if (error) throw new Error(`Database search failed: ${error.message}`);
    return data;
}

// Group search results by talk
function groupByTalk(sentences) {
    const talkMap = {};

    for (const sent of sentences) {
        if (!talkMap[sent.talk_id]) {
            talkMap[sent.talk_id] = {
                title: sent.title,
                speaker: sent.speaker,
                sentences: [],
                totalSimilarity: 0
            };
        }
        talkMap[sent.talk_id].sentences.push(sent.text);
        talkMap[sent.talk_id].totalSimilarity += sent.similarity;
    }

    return Object.values(talkMap)
        .sort((a, b) => b.sentences.length - a.sentences.length)
        .slice(0, 3)
        .map(talk => ({
            title: talk.title,
            speaker: talk.speaker,
            text: talk.sentences.join(' ')
        }));
}

// Generate answer via Edge Function
async function generateAnswer(question, contextTalks) {
    const response = await fetch(`${SUPABASE_CONFIG.url}/functions/v1/generate-answer`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${SUPABASE_CONFIG.anonKey}`
        },
        body: JSON.stringify({
            question: question,
            context_talks: contextTalks
        })
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'Failed to generate answer');
    }

    const data = await response.json();
    return data.answer;
}

// ============================================
// RESULTS DISPLAY HELPERS
// ============================================

function showResults(type, html) {
    const el = document.getElementById(`${type}-results`);
    if (el) el.innerHTML = html;
}

function clearResults(type) {
    const el = document.getElementById(`${type}-results`);
    if (el) el.innerHTML = '<div class="searching">Searching...</div>';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// EVENT LISTENERS
// ============================================

// Keyword search
if (keywordBtn) keywordBtn.addEventListener('click', keywordSearch);
if (keywordInput) keywordInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') keywordSearch();
});

// Semantic search
if (semanticBtn) semanticBtn.addEventListener('click', semanticSearch);
if (semanticInput) semanticInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') semanticSearch();
});

// RAG search
if (ragBtn) ragBtn.addEventListener('click', askQuestion);
if (ragInput) ragInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') askQuestion();
});

// ============================================
// INITIALIZE APP
// ============================================

// Run setup checks on page load
runSetupChecks();

// Check authentication session
checkSession();
