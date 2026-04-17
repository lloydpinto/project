// ===================== DASHBOARD JS =====================

const API_BASE = window.location.origin + '/api';

// Brand image database - maps make names to logo URLs
const BRAND_IMAGES = {
    'edwards': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Edwards_Lifesciences_logo.svg/1200px-Edwards_Lifesciences_logo.svg.png',
    'bosch': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Bosch_symbol_logo.svg/2048px-Bosch_symbol_logo.svg.png',
    'honeywell': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Honeywell_Logo.svg/2560px-Honeywell_Logo.svg.png',
    'siemens': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Siemens-logo.svg/2560px-Siemens-logo.svg.png',
    'schneider': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Schneider_Electric_2007.svg/2560px-Schneider_Electric_2007.svg.png',
    'schneider electric': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Schneider_Electric_2007.svg/2560px-Schneider_Electric_2007.svg.png',
    'abbott': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Abbott_Laboratories_logo.svg/1200px-Abbott_Laboratories_logo.svg.png',
    'samsung': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Samsung_Logo.svg/2560px-Samsung_Logo.svg.png',
    'apple': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Apple_logo_black.svg/800px-Apple_logo_black.svg.png',
    'dell': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/48/Dell_Logo.svg/2560px-Dell_Logo.svg.png',
    'hp': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ad/HP_logo_2012.svg/800px-HP_logo_2012.svg.png',
    'sony': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Sony_logo.svg/2560px-Sony_logo.svg.png',
    'microsoft': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Microsoft_logo.svg/2048px-Microsoft_logo.svg.png',
    'cisco': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Cisco_logo_blue_2016.svg/2560px-Cisco_logo_blue_2016.svg.png',
    'panasonic': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Panasonic_logo_%28Blue%29.svg/2560px-Panasonic_logo_%28Blue%29.svg.png',
    'lg': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/LG_symbol.svg/2048px-LG_symbol.svg.png',
    'philips': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Philips_logo_new.svg/2048px-Philips_logo_new.svg.png',
    'abb': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/ABB_logo.svg/2048px-ABB_logo.svg.png',
    'eaton': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Eaton_Corporation_logo.svg/2560px-Eaton_Corporation_logo.svg.png',
    'tyco': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Tyco_International_logo.svg/1200px-Tyco_International_logo.svg.png',
    'notifier': 'https://i.pinimg.com/originals/3a/12/76/3a1276a2a856c78e0073cf5fa9f97c1a.png',
    'apollo': 'https://www.apollo-fire.co.uk/img/apollo-logo-header.png',
    'hochiki': 'https://www.hochiki.co.uk/wp-content/uploads/2021/05/Hochiki-Europe-Logo.png',
    'esser': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Esser_logo.svg/1200px-Esser_logo.svg.png',
    'ravel': 'https://via.placeholder.com/120x60/1a5cf5/ffffff?text=RAVEL',
    'generic': 'https://via.placeholder.com/120x60/1a5cf5/ffffff?text=BRAND'
};

// Product image database - maps keywords in model/description to product image URLs
const PRODUCT_IMAGES = {
    'smoke detector': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
    'smoke': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
    'heat detector': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
    'heat': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
    'detector': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
    'manual call point': 'https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400&h=300&fit=crop',
    'call point': 'https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400&h=300&fit=crop',
    'hooter': 'https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=400&h=300&fit=crop',
    'strobe': 'https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=400&h=300&fit=crop',
    'speaker': 'https://images.unsplash.com/photo-1545454675-3531b543be5d?w=400&h=300&fit=crop',
    'amplifier': 'https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=400&h=300&fit=crop',
    'module': 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=400&h=300&fit=crop',
    'monitor module': 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=400&h=300&fit=crop',
    'control module': 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=400&h=300&fit=crop',
    'relay module': 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=400&h=300&fit=crop',
    'panel': 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400&h=300&fit=crop',
    'controller': 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400&h=300&fit=crop',
    'power supply': 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=400&h=300&fit=crop',
    'router': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
    'beam': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
    'duct': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
    'telephone': 'https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400&h=300&fit=crop',
    'annunciator': 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400&h=300&fit=crop',
    'isolator': 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=400&h=300&fit=crop',
    'call station': 'https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400&h=300&fit=crop',
    'ceiling': 'https://images.unsplash.com/photo-1545454675-3531b543be5d?w=400&h=300&fit=crop',
    'wall': 'https://images.unsplash.com/photo-1545454675-3531b543be5d?w=400&h=300&fit=crop',
    'cabinet': 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400&h=300&fit=crop',
    'base': 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=400&h=300&fit=crop',
    'default': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop'
};

// Get brand image URL
function getBrandImageUrl(makeName) {
    const key = (makeName || '').toLowerCase().trim();
    return BRAND_IMAGES[key] || null;
}

// Get product image URL based on model/description keywords
function getProductImageUrl(product) {
    const combined = [
        product['Model'] || '',
        product['Description'] || '',
        product['Make'] || ''
    ].join(' ').toLowerCase();

    const keys = Object.keys(PRODUCT_IMAGES).filter(k => k !== 'default');
    for (const key of keys) {
        if (combined.includes(key)) {
            return PRODUCT_IMAGES[key];
        }
    }
    return PRODUCT_IMAGES['default'];
}

// Build image element with fallback
function buildImage(src, alt, className, fallbackHtml) {
    if (!src) return fallbackHtml;
    return `
        <img
            src="${escapeHtml(src)}"
            alt="${escapeHtml(alt)}"
            class="${className}"
            loading="lazy"
            onerror="this.parentElement.innerHTML='${fallbackHtml.replace(/'/g, "\\'").replace(/\n/g, '')}'"
        >
    `;
}

// ===================== STATE =====================

const state = {
    user: null, token: null,
    allMakes: [], currentMake: null,
    currentProducts: [], filteredProducts: [],
    viewMode: 'table', sortCol: null, sortDir: 'asc',
    debounceTimer: null, tableFilterTimer: null,
    cache: new Map(), isLoading: false
};

// ===================== INIT =====================

document.addEventListener('DOMContentLoaded', () => initDashboard());

async function initDashboard() {
    state.token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
    if (!state.token || !userStr) { window.location.href = '/'; return; }
    try { state.user = JSON.parse(userStr); } catch { window.location.href = '/'; return; }

    try {
        const res = await apiCall('/auth/profile');
        if (res.user) state.user = res.user;
    } catch (err) {
        if (err.code === 'TOKEN_EXPIRED' || err.code === 'INVALID_TOKEN') {
            showToast('Session expired', 'Please sign in again.', 'warning');
            setTimeout(() => handleLogout(), 1500);
            return;
        }
    }

    setupUserInfo();
    await loadAllData();
    setupListeners();
}

function setupUserInfo() {
    if (!state.user) return;
    const initials = (
        (state.user.first_name || 'U')[0] +
        (state.user.last_name || 'S')[0]
    ).toUpperCase();
    el('userAvatar').textContent = initials;
    el('userName').textContent = `${state.user.first_name} ${state.user.last_name}`;
    el('userRole').textContent = state.user.role || 'user';
}

// ===================== API =====================

async function apiCall(endpoint, options = {}) {
    const controller = new AbortController();
    const tid = setTimeout(() => controller.abort(), 30000);
    try {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            signal: controller.signal,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`,
                ...options.headers
            }
        });
        clearTimeout(tid);
        const data = await res.json();
        if (!res.ok) {
            if (res.status === 401) throw { code: data.code || 'UNAUTHORIZED', message: data.error };
            throw new Error(data.error || `Request failed ${res.status}`);
        }
        return data;
    } catch (err) {
        clearTimeout(tid);
        if (err.name === 'AbortError') throw new Error('Request timed out.');
        throw err;
    }
}

// ===================== LOAD DATA =====================

async function loadAllData() {
    showLoading(true, 'Loading catalog...');
    try {
        const [statsData, makesData] = await Promise.all([
            apiCall('/products/stats'),
            apiCall('/products/makes')
        ]);

        state.allMakes = makesData.makes || [];
        animateCounter('statMakes', state.allMakes.length);
        animateCounter('statProducts', statsData.total_items || 0);
        el('statValue').textContent = '—';
        el('statShowing').textContent = '0';

        populateMakeDropdown(state.allMakes);

        const now = new Date();
        el('lastUpdated').textContent = `${now.toLocaleTimeString()}`;

        if (statsData.total_items > 0) {
            showToast('Ready', `${statsData.total_items} models across ${state.allMakes.length} brands.`, 'success');
        }
    } catch (e) {
        console.error(e);
        showToast('Error', e.message || 'Failed to load data.', 'error');
        showCanvasError(e.message || 'Failed to load. Please refresh.');
    } finally {
        showLoading(false);
    }
}

// ===================== DROPDOWN =====================

function populateMakeDropdown(makes) {
    const sel = el('makeSelect');
    sel.innerHTML = '<option value="">— Select a brand —</option>';
    makes.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m.name;
        opt.textContent = `${m.name}  (${m.count} model${m.count !== 1 ? 's' : ''})`;
        sel.appendChild(opt);
    });
}

// ===================== SELECTED MAKE CARD =====================

function showSelectedMakeCard(makeName, makeInfo) {
    const card = el('selectedMakeCard');
    const imageWrap = el('makeCardImageWrap');
    const fallback = el('makeCardFallback');
    const nameEl = el('makeCardName');
    const metaEl = el('makeCardMeta');

    nameEl.textContent = makeName;

    const totalVal = makeInfo ? makeInfo.total_value || 0 : 0;
    const count = makeInfo ? makeInfo.count || 0 : 0;
    metaEl.innerHTML = `
        <div class="make-card-chip">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/>
            </svg>
            ${count} models
        </div>
        <div class="make-card-chip">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
            </svg>
            ${formatCurrency(totalVal)}
        </div>
    `;

    // Load brand image
    const imgUrl = getBrandImageUrl(makeName);
    if (imgUrl) {
        imageWrap.innerHTML = `
            <img
                src="${imgUrl}"
                alt="${escapeHtml(makeName)} logo"
                class="make-card-image"
                loading="lazy"
                onerror="this.parentElement.innerHTML='<div class=\\'make-card-image-fallback\\'>${escapeHtml(makeName.charAt(0).toUpperCase())}</div>'"
            >
        `;
    } else {
        imageWrap.innerHTML = `<div class="make-card-image-fallback">${escapeHtml(makeName.charAt(0).toUpperCase())}</div>`;
    }

    card.classList.add('visible');
}

function hideSelectedMakeCard() {
    el('selectedMakeCard').classList.remove('visible');
    el('makeCardImageWrap').innerHTML = '<div class="make-card-image-fallback" id="makeCardFallback"></div>';
}

// ===================== MAKE CHANGE =====================

async function handleMakeChange(makeName) {
    if (!makeName) { resetView(); return; }
    if (state.isLoading) return;

    state.isLoading = true;
    showLoading(true, `Loading ${makeName}...`);
    el('clearMakeBtn').style.display = 'flex';
    el('tableSearch').value = '';
    el('globalSearch').value = '';
    el('searchBar').classList.remove('visible');
    el('searchClearBtn').classList.remove('visible');
    state.pagination && (state.pagination.page = 1);
    state.sortCol = null;
    state.sortDir = 'asc';

    try {
        let products;
        const cached = state.cache.get(makeName);

        if (cached) {
            products = cached.products;
        } else {
            const res = await apiCall(`/products/by-make/${encodeURIComponent(makeName)}`);
            if (res.error) throw new Error(res.error);
            products = res.products || [];
            state.cache.set(makeName, {
                products,
                total_value: res.total_value || 0,
                count: res.count || products.length,
                ts: Date.now()
            });
        }

        const cacheData = state.cache.get(makeName);
        state.currentMake = makeName;
        state.currentProducts = products;
        state.filteredProducts = [...products];

        el('statValue').textContent = formatCurrency(cacheData.total_value || 0);
        animateCounter('statShowing', products.length);

        // Find make info for card
        const makeInfo = state.allMakes.find(m => m.name === makeName);
        showSelectedMakeCard(makeName, makeInfo || cacheData);
        showMakeBanner(makeName, products, cacheData.total_value || 0);
        renderContent();

    } catch (e) {
        console.error(e);
        showToast('Error', `Failed to load ${makeName}: ${e.message}`, 'error');
        showCanvasError(`Failed to load products for "${makeName}". ${e.message}`);
    } finally {
        state.isLoading = false;
        showLoading(false);
    }
}

function showMakeBanner(makeName, products, totalVal) {
    el('makeBanner').style.display = 'flex';
    el('canvasToolbar').style.display = 'flex';
    el('canvasEmpty').style.display = 'none';
    el('canvasError').style.display = 'none';

    // Banner icon — try to show brand image
    const bannerIcon = el('makeBannerIcon');
    const imgUrl = getBrandImageUrl(makeName);
    if (imgUrl) {
        bannerIcon.innerHTML = `
            <img src="${imgUrl}" alt="${escapeHtml(makeName)}"
                 loading="lazy"
                 onerror="this.parentElement.textContent='${escapeHtml(makeName.charAt(0).toUpperCase())}'">
        `;
    } else {
        bannerIcon.textContent = makeName.charAt(0).toUpperCase();
    }

    el('makeBannerName').textContent = makeName;
    el('makeBannerMeta').innerHTML = `
        <span>${products.length} models</span>
        <span>·</span>
        <span>${formatCurrency(totalVal)}</span>
    `;

    el('makeSummaryChips').innerHTML = `
        <div class="summary-chip">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/>
            </svg>
            ${products.length} Models
        </div>
        <div class="summary-chip">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
            </svg>
            ${formatCurrency(totalVal)}
        </div>
    `;

    el('recordCount').textContent = `${products.length} records`;
}

// ===================== RENDER =====================

function renderContent() {
    const products = state.filteredProducts;
    el('recordCount').textContent = `${products.length} record${products.length !== 1 ? 's' : ''}`;
    el('statShowing').textContent = products.length;

    if (state.viewMode === 'table') {
        el('tableContainer').style.display = 'block';
        el('cardContainer').style.display = 'none';
        renderTable(products);
    } else {
        el('tableContainer').style.display = 'none';
        el('cardContainer').style.display = 'grid';
        renderCards(products);
    }
}

// ===================== TABLE =====================

function renderTable(products) {
    const tbody = el('tableBody');
    const tfoot = el('tableFoot');

    if (!products || !products.length) {
        tbody.innerHTML = `<tr><td colspan="6" class="table-no-data"><div class="no-data-inner"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg><span>No records found</span></div></td></tr>`;
        tfoot.innerHTML = '';
        return;
    }

    const frag = document.createDocumentFragment();
    products.forEach((p, idx) => {
        const tr = document.createElement('tr');
        tr.dataset.idx = idx;
        tr.onclick = () => openProductModal(idx);
        const slNo = (p['Sl.No'] !== null && p['Sl.No'] !== undefined) ? p['Sl.No'] : '—';
        tr.innerHTML = `
            <td class="td-slno">${escapeHtml(String(slNo))}</td>
            <td class="td-make"><span class="make-chip">${escapeHtml(p['Make'] || '—')}</span></td>
            <td class="td-model">${escapeHtml(p['Model'] || '—')}</td>
            <td class="td-desc">${p['Description'] ? escapeHtml(p['Description']) : '<span class="null-badge">—</span>'}</td>
            <td class="td-qty">${escapeHtml(String(p['Quantity'] ?? 1))}</td>
            <td class="td-price">
                <div class="price-display">
                    <span class="price-currency">₹</span>
                    <span>${formatNumber(p['Net Price'])}</span>
                </div>
            </td>
        `;
        frag.appendChild(tr);
    });

    tbody.innerHTML = '';
    tbody.appendChild(frag);

    const totalQty = products.reduce((s, p) => s + _safeNum(p['Quantity'], 1), 0);
    const totalVal = products.reduce((s, p) => s + (_safeNum(p['Net Price'], 0) * _safeNum(p['Quantity'], 1)), 0);
    tfoot.innerHTML = `
        <tr>
            <td colspan="4" class="total-label">Total · ${products.length} records</td>
            <td class="td-qty" style="font-weight:700;text-align:center;">${totalQty}</td>
            <td class="total-value">₹ ${formatNumber(totalVal)}</td>
        </tr>`;
}

// ===================== CARDS =====================

function renderCards(products) {
    const container = el('cardContainer');
    if (!products || !products.length) {
        container.innerHTML = `<div class="card-no-data"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg><span>No records found</span></div>`;
        return;
    }

    const frag = document.createDocumentFragment();
    products.forEach((p, idx) => {
        const div = document.createElement('div');
        div.className = 'product-mini-card';
        div.onclick = () => openProductModal(idx);
        const slNo = (p['Sl.No'] !== null && p['Sl.No'] !== undefined) ? p['Sl.No'] : '—';
        div.innerHTML = `
            <div class="mini-card-header">
                <span class="mini-card-slno">#${escapeHtml(String(slNo))}</span>
                <span class="mini-card-make">${escapeHtml(p['Make'] || '—')}</span>
            </div>
            <div class="mini-card-body">
                <div class="mini-card-model">${escapeHtml(p['Model'] || '—')}</div>
                <div class="mini-card-desc">${p['Description']
                    ? escapeHtml(p['Description'])
                    : '<em style="color:var(--text-tertiary);font-size:0.75rem;">No description</em>'}</div>
            </div>
            <div class="mini-card-footer">
                <div class="mini-qty-badge">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/></svg>
                    Qty: ${escapeHtml(String(p['Quantity'] ?? 1))}
                </div>
                <div class="mini-card-price">₹ ${formatNumber(p['Net Price'])}</div>
            </div>
        `;
        frag.appendChild(div);
    });

    container.innerHTML = '';
    container.appendChild(frag);
}

// ===================== PRODUCT MODAL =====================

function openProductModal(idx) {
    const p = state.filteredProducts[idx];
    if (!p) return;

    el('modalTitle').textContent = p['Model'] || 'Product Details';

    const slNo = (p['Sl.No'] !== null && p['Sl.No'] !== undefined) ? p['Sl.No'] : '—';
    const price = _safeNum(p['Net Price'], 0);
    const qty = _safeNum(p['Quantity'], 1);
    const lineTotal = price * qty;

    // Get product image
    const productImgUrl = getProductImageUrl(p);
    const brandImgUrl = getBrandImageUrl(p['Make']);

    // Product image section
    const productImageHtml = `
        <div class="product-modal-image-wrap">
            <img
                src="${productImgUrl}"
                alt="${escapeHtml(p['Model'] || 'Product')}"
                class="product-modal-image"
                loading="lazy"
                onerror="this.parentElement.innerHTML='<div class=\\'product-modal-image-fallback\\'><svg width=\\'48\\' height=\\'48\\' viewBox=\\'0 0 24 24\\' fill=\\'none\\' stroke=\\'currentColor\\' stroke-width=\\'1\\'><path d=\\'m7.5 4.27 9 5.15\\'/><path d=\\'M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z\\'/></svg><span>No image</span></div>'"
            >
            <div class="product-image-source">via Unsplash</div>
        </div>
    `;

    // Brand logo in header
    const brandBadgeHtml = brandImgUrl ? `
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
            <img
                src="${brandImgUrl}"
                alt="${escapeHtml(p['Make'] || '')}"
                style="height:20px;width:auto;filter:brightness(10);object-fit:contain;"
                loading="lazy"
                onerror="this.style.display='none'"
            >
            <span class="detail-make-badge">${escapeHtml(p['Make'] || '—')}</span>
        </div>
    ` : `<div class="detail-make-badge" style="margin-bottom:10px;">${escapeHtml(p['Make'] || '—')}</div>`;

    el('modalBody').innerHTML = `
        ${productImageHtml}
        <div class="detail-product-header">
            ${brandBadgeHtml}
            <h2>${escapeHtml(p['Model'] || '—')}</h2>
            <div class="detail-desc">${p['Description']
                ? escapeHtml(p['Description'])
                : '<em style="opacity:0.5;">No description provided</em>'}</div>
        </div>
        <div class="detail-fields">
            <div class="detail-field">
                <div class="field-label">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14"/></svg>
                    Serial No.
                </div>
                <div class="field-value">${escapeHtml(String(slNo))}</div>
            </div>
            <div class="detail-field">
                <div class="field-label">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>
                    Brand / Make
                </div>
                <div class="field-value">${escapeHtml(p['Make'] || '—')}</div>
            </div>
            <div class="detail-field full-width">
                <div class="field-label">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/></svg>
                    Model
                </div>
                <div class="field-value font-mono" style="font-size:0.875rem;">${escapeHtml(p['Model'] || '—')}</div>
            </div>
            <div class="detail-field">
                <div class="field-label">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 12V22H4V12"/><path d="M22 7H2v5h20V7z"/><path d="M12 22V7"/></svg>
                    Quantity
                </div>
                <div class="field-value">${escapeHtml(String(qty))}</div>
            </div>
            <div class="detail-field price-field">
                <div class="field-label">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                    Unit Price
                </div>
                <div class="field-value">₹ ${formatNumber(price)}</div>
            </div>
            <div class="detail-field highlight full-width">
                <div class="field-label" style="color:var(--primary-600);">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                    Total Line Value (Qty × Price)
                </div>
                <div class="field-value" style="font-family:'JetBrains Mono',monospace;font-size:1.125rem;color:var(--primary-700);">
                    ₹ ${formatNumber(lineTotal)}
                </div>
            </div>
        </div>
    `;

    el('productModal').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeProductModal() {
    el('productModal').classList.remove('active');
    document.body.style.overflow = '';
}

// ===================== FILTER / SORT / SEARCH =====================

function filterTable(query) {
    clearTimeout(state.tableFilterTimer);
    state.tableFilterTimer = setTimeout(() => {
        if (!query || !query.trim()) {
            state.filteredProducts = [...state.currentProducts];
        } else {
            const q = query.toLowerCase().trim();
            state.filteredProducts = state.currentProducts.filter(p =>
                [String(p['Sl.No'] ?? ''), p['Make'] || '', p['Model'] || '',
                 p['Description'] || '', String(p['Net Price'] ?? ''), String(p['Quantity'] ?? '')]
                .join(' ').toLowerCase().includes(q)
            );
        }
        renderContent();
    }, 200);
}

function sortTable(col) {
    if (state.sortCol === col) {
        state.sortDir = state.sortDir === 'asc' ? 'desc' : 'asc';
    } else {
        state.sortCol = col;
        state.sortDir = 'asc';
    }
    const colMap = { slno:'Sl.No', make:'Make', model:'Model', desc:'Description', qty:'Quantity', price:'Net Price' };
    const key = colMap[col];
    state.filteredProducts.sort((a, b) => {
        let av = a[key] ?? '';
        let bv = b[key] ?? '';
        if (typeof av === 'number' && typeof bv === 'number') return state.sortDir === 'asc' ? av - bv : bv - av;
        av = String(av).toLowerCase();
        bv = String(bv).toLowerCase();
        if (av < bv) return state.sortDir === 'asc' ? -1 : 1;
        if (av > bv) return state.sortDir === 'asc' ? 1 : -1;
        return 0;
    });
    document.querySelectorAll('.products-table th[data-sort]').forEach(th => {
        th.classList.remove('sorted-asc','sorted-desc');
        if (th.dataset.sort === col) th.classList.add(state.sortDir === 'asc' ? 'sorted-asc' : 'sorted-desc');
    });
    renderContent();
}

function onSearchInput(val) {
    const clearBtn = el('searchClearBtn');
    clearBtn && clearBtn.classList.toggle('visible', val.length > 0);
    clearTimeout(state.debounceTimer);
    if (!val.trim()) { clearSearch(); return; }
    state.debounceTimer = setTimeout(() => {
        if (val.trim().length >= 2) performSearch(val.trim());
    }, 350);
}

async function performSearch(query) {
    if (!query || query.trim().length < 2 || state.isLoading) return;
    state.isLoading = true;
    showLoading(true, 'Searching...');
    try {
        const makeFilter = state.currentMake || '';
        const res = await apiCall(`/products/search?q=${encodeURIComponent(query)}&make=${encodeURIComponent(makeFilter)}&limit=1000`);
        const results = res.results || [];
        el('searchBar').classList.add('visible');
        el('searchCount').textContent = results.length;
        el('searchQueryDisplay').textContent = query;
        state.filteredProducts = results;
        if (!state.currentMake) {
            el('makeBanner').style.display = 'none';
            el('canvasToolbar').style.display = 'flex';
            el('canvasEmpty').style.display = 'none';
            el('canvasError').style.display = 'none';
        }
        renderContent();
    } catch (e) {
        showToast('Search failed', e.message || 'Please try again.', 'error');
    } finally {
        state.isLoading = false;
        showLoading(false);
    }
}

function clearSearch() {
    el('globalSearch').value = '';
    el('searchBar').classList.remove('visible');
    el('searchClearBtn').classList.remove('visible');
    if (state.currentMake) {
        state.filteredProducts = [...state.currentProducts];
        el('tableSearch').value = '';
        renderContent();
    } else {
        resetView();
    }
}

function setViewMode(mode) {
    state.viewMode = mode;
    el('tableViewBtn').classList.toggle('active', mode === 'table');
    el('cardViewBtn').classList.toggle('active', mode === 'cards');
    if (state.currentMake || state.filteredProducts.length) renderContent();
}

function resetView() {
    state.currentMake = null;
    state.currentProducts = [];
    state.filteredProducts = [];
    state.sortCol = null;
    state.sortDir = 'asc';
    el('makeSelect').value = '';
    el('clearMakeBtn').style.display = 'none';
    el('tableSearch').value = '';
    el('globalSearch').value = '';
    el('searchBar').classList.remove('visible');
    el('searchClearBtn').classList.remove('visible');
    hideSelectedMakeCard();
    el('makeBanner').style.display = 'none';
    el('canvasToolbar').style.display = 'none';
    el('tableContainer').style.display = 'none';
    el('cardContainer').style.display = 'none';
    el('canvasError').style.display = 'none';
    el('canvasEmpty').style.display = 'flex';
    el('emptyTitle').textContent = 'Select a brand to view products';
    el('emptySubtitle').textContent = 'Use the dropdown above to load the product catalog for that brand.';
    el('statValue').textContent = '—';
    el('statShowing').textContent = '0';
}

function showCanvasError(msg) {
    el('makeBanner').style.display = 'none';
    el('canvasToolbar').style.display = 'none';
    el('tableContainer').style.display = 'none';
    el('cardContainer').style.display = 'none';
    el('canvasEmpty').style.display = 'none';
    el('canvasError').style.display = 'flex';
    el('canvasErrorMsg').textContent = msg;
}

// ===================== EXPORT =====================

function exportToCSV() {
    const products = state.filteredProducts;
    if (!products.length) { showToast('No data', 'Nothing to export.', 'warning'); return; }
    const headers = ['Sl.No','Make','Model','Description','Quantity','Net Price'];
    const rows = products.map(p => [
        p['Sl.No'] ?? '',
        `"${String(p['Make'] || '').replace(/"/g,'""')}"`,
        `"${String(p['Model'] || '').replace(/"/g,'""')}"`,
        `"${String(p['Description'] || '').replace(/"/g,'""')}"`,
        p['Quantity'] ?? 1,
        p['Net Price'] ?? ''
    ]);
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob(['\uFEFF' + csv], { type:'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${state.currentMake || 'products'}_${new Date().toISOString().slice(0,10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Exported', `${products.length} records saved.`, 'success');
}

// ===================== USER MENU & AUTH =====================

function toggleUserMenu() { el('userDropdown').classList.toggle('open'); }

function showChangePasswordModal() {
    el('userDropdown').classList.remove('open');
    el('changePasswordModal').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeChangePasswordModal() {
    el('changePasswordModal').classList.remove('active');
    document.body.style.overflow = '';
    el('changePasswordForm').reset();
    el('changePasswordAlert').innerHTML = '';
}

async function handleChangePassword(event) {
    event.preventDefault();
    const cur = el('currentPassword').value;
    const np = el('newPwd').value;
    const cp = el('confirmNewPwd').value;
    if (np !== cp) { showModalAlert('changePasswordAlert','Passwords do not match.','error'); return; }
    if (np.length < 8) { showModalAlert('changePasswordAlert','Min. 8 characters.','error'); return; }
    try {
        await apiCall('/auth/change-password', { method:'POST', body:JSON.stringify({ current_password:cur, new_password:np }) });
        showToast('Success','Password updated.','success');
        closeChangePasswordModal();
    } catch (e) {
        showModalAlert('changePasswordAlert', e.message || 'Failed.', 'error');
    }
}

async function clearAllCache() {
    el('userDropdown').classList.remove('open');
    try { await apiCall('/cache/clear', { method:'DELETE' }); } catch {}
    state.cache.clear();
    showToast('Cache cleared','All cached data removed.','info');
}

async function refreshData() {
    el('userDropdown').classList.remove('open');
    const prevMake = state.currentMake;
    state.cache.clear();
    resetView();
    await loadAllData();
    if (prevMake) {
        el('makeSelect').value = prevMake;
        await handleMakeChange(prevMake);
    }
    showToast('Refreshed','Data reloaded.','success');
}

function handleLogout() {
    ['access_token','refresh_token','user','machine_id'].forEach(k => {
        localStorage.removeItem(k); sessionStorage.removeItem(k);
    });
    window.location.href = '/';
}

// ===================== LISTENERS =====================

function setupListeners() {
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') { closeProductModal(); closeChangePasswordModal(); }
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') { e.preventDefault(); el('globalSearch').focus(); }
    });

    document.addEventListener('click', e => {
        const btn = el('userMenuBtn');
        if (btn && !btn.contains(e.target)) el('userDropdown').classList.remove('open');
    });

    ['productModal','changePasswordModal'].forEach(id => {
        el(id).addEventListener('click', e => {
            if (e.target.id === id) {
                if (id === 'productModal') closeProductModal();
                else closeChangePasswordModal();
            }
        });
    });

    // Swipe down to close modal on mobile
    let touchStartY = 0;
    document.querySelectorAll('.modal-container').forEach(modal => {
        modal.addEventListener('touchstart', e => { touchStartY = e.touches[0].clientY; }, { passive:true });
        modal.addEventListener('touchmove', e => {
            const diff = e.touches[0].clientY - touchStartY;
            if (diff > 80) { closeProductModal(); closeChangePasswordModal(); }
        }, { passive:true });
    });
}

// ===================== UTILITIES =====================

function el(id) { return document.getElementById(id); }

function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const d = document.createElement('div');
    d.textContent = String(text);
    return d.innerHTML;
}

function _safeNum(val, def = 0) {
    if (val === null || val === undefined) return def;
    const n = Number(val);
    return isNaN(n) ? def : n;
}

function formatNumber(val) {
    if (val === null || val === undefined) return '—';
    return _safeNum(val).toLocaleString('en-IN', { minimumFractionDigits:2, maximumFractionDigits:2 });
}

function formatCurrency(val) {
    const n = _safeNum(val);
    if (n === 0) return '₹0';
    if (n >= 10000000) return `₹${(n/10000000).toFixed(2)} Cr`;
    if (n >= 100000) return `₹${(n/100000).toFixed(2)} L`;
    if (n >= 1000) return `₹${(n/1000).toFixed(1)} K`;
    return `₹${formatNumber(n)}`;
}

function animateCounter(id, target) {
    const element = el(id);
    if (!element) return;
    const start = parseInt(element.textContent) || 0;
    const diff = target - start;
    if (diff === 0) { element.textContent = target; return; }
    const steps = 20;
    const inc = diff / steps;
    let cur = start, step = 0;
    const timer = setInterval(() => {
        step++;
        cur += inc;
        element.textContent = Math.round(cur);
        if (step >= steps) { element.textContent = target; clearInterval(timer); }
    }, 30);
}

function showLoading(show, text = 'Loading...') {
    const overlay = el('loadingOverlay');
    const txt = el('loadingText');
    if (txt) txt.textContent = text;
    if (show) overlay.classList.add('active'); else overlay.classList.remove('active');
}

function showToast(title, message, type) {
    const c = el('toastContainer');
    if (!c) return;
    const t = document.createElement('div');
    t.className = `toast toast-${type}`;
    const icons = { success:'✓', error:'✕', warning:'⚠', info:'ℹ' };
    t.innerHTML = `<span class="toast-icon">${icons[type]||'ℹ'}</span><div class="toast-body"><div class="toast-title">${escapeHtml(title)}</div><div class="toast-message">${escapeHtml(message)}</div></div><button class="toast-close" onclick="this.parentElement.remove()">✕</button><div class="toast-progress"></div>`;
    c.appendChild(t);
    setTimeout(() => { if (t.parentElement) t.remove(); }, 4500);
}

function showModalAlert(cid, msg, type) {
    el(cid).innerHTML = `<div class="alert alert-${type}"><span class="alert-icon">${type==='error'?'⚠':'✓'}</span><span class="alert-content">${escapeHtml(msg)}</span></div>`;
}

// ════════════════════════════════════════════════════
//  ADD PRODUCT
// ════════════════════════════════════════════════════

function openAddProductModal() {
    el('addProductModal').classList.add('active');
    document.body.style.overflow = 'hidden';
    el('addAlertContainer').innerHTML = '';

    // Pre-fill Make if one is selected
    if (state.currentMake) {
        el('addMake').value = state.currentMake;
    }

    // Live preview
    ['addMake', 'addModel', 'addDescription', 'addQuantity', 'addNetPrice'].forEach(id => {
        const inp = el(id);
        if (inp) inp.addEventListener('input', updateAddPreview);
    });
}

function closeAddProductModal() {
    el('addProductModal').classList.remove('active');
    document.body.style.overflow = '';
    _closeSuggestions();
}

function switchAddTab(tab) {
    document.querySelectorAll('.add-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-addtab="${tab}"]`).classList.add('active');
    el('addSinglePanel').classList.toggle('active', tab === 'single');
    el('addBulkPanel').classList.toggle('active', tab === 'bulk');
    el('addAlertContainer').innerHTML = '';
}

function resetAddForm() {
    el('addProductForm').reset();
    el('addPreview').style.display = 'none';
    el('addAlertContainer').innerHTML = '';
    if (state.currentMake) el('addMake').value = state.currentMake;
}

function updateAddPreview() {
    const make = el('addMake').value.trim();
    const model = el('addModel').value.trim();

    if (!make && !model) {
        el('addPreview').style.display = 'none';
        return;
    }

    const desc  = el('addDescription').value.trim();
    const qty   = el('addQuantity').value || '1';
    const price = el('addNetPrice').value || '0';

    el('addPreview').style.display = 'block';
    el('previewBody').innerHTML = `
        <div class="preview-field">
            <span class="pf-label">Make</span>
            <span class="pf-value">${escapeHtml(make || '—')}</span>
        </div>
        <div class="preview-field">
            <span class="pf-label">Model</span>
            <span class="pf-value">${escapeHtml(model || '—')}</span>
        </div>
        <div class="preview-field full">
            <span class="pf-label">Description</span>
            <span class="pf-value">${desc ? escapeHtml(desc) : '<em style="color:var(--text-tertiary)">None</em>'}</span>
        </div>
        <div class="preview-field">
            <span class="pf-label">Quantity</span>
            <span class="pf-value">${escapeHtml(qty)}</span>
        </div>
        <div class="preview-field">
            <span class="pf-label">Net Price</span>
            <span class="pf-value" style="font-family:'JetBrains Mono',monospace;">
                ₹ ${formatNumber(parseFloat(price) || 0)}
            </span>
        </div>
    `;
}

// ── Make Suggestions ──
function showMakeSuggestions(query) {
    const dropdown = el('makeSuggestDropdown');
    if (!dropdown) return;

    if (!query.trim() || !state.allMakes || state.allMakes.length === 0) {
        // Show all makes
        if (state.allMakes && state.allMakes.length > 0) {
            dropdown.innerHTML = state.allMakes.map(m =>
                `<div class="suggest-item" onclick="selectMakeSuggestion('${escapeHtml(m.name)}')">
                    <span>${escapeHtml(m.name)}</span>
                    <span class="suggest-count">${m.count} models</span>
                </div>`
            ).join('');
            dropdown.classList.add('open');
        }
        return;
    }

    const q = query.toLowerCase();
    const matches = (state.allMakes || []).filter(m =>
        m.name.toLowerCase().includes(q)
    );

    if (matches.length === 0) {
        dropdown.innerHTML = `
            <div class="suggest-item" onclick="selectMakeSuggestion('${escapeHtml(query.trim())}')">
                <span>+ Create "<strong>${escapeHtml(query.trim())}</strong>"</span>
                <span class="suggest-count">New</span>
            </div>`;
    } else {
        dropdown.innerHTML = matches.map(m =>
            `<div class="suggest-item" onclick="selectMakeSuggestion('${escapeHtml(m.name)}')">
                <span>${escapeHtml(m.name)}</span>
                <span class="suggest-count">${m.count} models</span>
            </div>`
        ).join('');
    }
    dropdown.classList.add('open');
}

function selectMakeSuggestion(name) {
    el('addMake').value = name;
    _closeSuggestions();
    updateAddPreview();
    el('addModel').focus();
}

function _closeSuggestions() {
    const dd = el('makeSuggestDropdown');
    if (dd) dd.classList.remove('open');
}

// Close suggestions when clicking outside
document.addEventListener('click', e => {
    if (!e.target.closest('.input-with-suggest')) {
        _closeSuggestions();
    }
});

// ── Submit Single Product ──
async function handleAddProduct(event) {
    event.preventDefault();

    const make  = el('addMake').value.trim();
    const model = el('addModel').value.trim();

    if (!make) { _addAlert('Make / Brand is required.', 'error'); return; }
    if (!model) { _addAlert('Model is required.', 'error'); return; }

    const slNoVal   = el('addSlNo').value.trim();
    const desc      = el('addDescription').value.trim();
    const qty       = parseFloat(el('addQuantity').value) || 1;
    const price     = parseFloat(el('addNetPrice').value) || 0;

    const product = {
        'Sl.No': slNoVal ? parseInt(slNoVal) : null,
        'Make': make,
        'Model': model,
        'Description': desc || null,
        'Quantity': qty,
        'Net Price': price,
    };

    const btn = el('addProductBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="btn-spinner"></span> Adding...';

    try {
        const res = await apiCall('/products/add', {
            method: 'POST',
            body: JSON.stringify(product),
        });

        showToast('Product Added!', res.message || `${model} added to ${make}.`, 'success');
        _addAlert(res.message || 'Product added successfully!', 'success');

        // Clear cache so data reloads fresh
        state.cache.delete(make);

        // If currently viewing this make, refresh
        if (state.currentMake && state.currentMake.toLowerCase() === make.toLowerCase()) {
            await handleMakeChange(state.currentMake);
        }

        // Refresh stats
        await _refreshStats();

        // Reset form but keep Make
        el('addModel').value = '';
        el('addDescription').value = '';
        el('addSlNo').value = '';
        el('addQuantity').value = '1';
        el('addNetPrice').value = '';
        el('addPreview').style.display = 'none';
        el('addModel').focus();

    } catch (e) {
        _addAlert(e.message || 'Failed to add product.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg> Add Product`;
    }
}

// ── Bulk Add ──
function validateBulkJson() {
    const raw = el('bulkJsonInput').value.trim();
    if (!raw) { _addAlert('Paste a JSON array first.', 'warning'); return false; }
    try {
        const arr = JSON.parse(raw);
        if (!Array.isArray(arr)) {
            _addAlert('JSON must be an array [ ... ]', 'error'); return false;
        }
        if (arr.length === 0) {
            _addAlert('Array is empty.', 'warning'); return false;
        }
        let valid = 0, invalid = 0;
        arr.forEach((item, i) => {
            if (item.Make && item.Model) valid++;
            else invalid++;
        });
        _addAlert(`Valid: ${valid} products. Invalid: ${invalid}. Total: ${arr.length}.`,
                   invalid > 0 ? 'warning' : 'success');
        return true;
    } catch (e) {
        _addAlert(`JSON parse error: ${e.message}`, 'error');
        return false;
    }
}

async function handleBulkAdd() {
    const raw = el('bulkJsonInput').value.trim();
    if (!raw) { _addAlert('Paste a JSON array first.', 'warning'); return; }

    let arr;
    try {
        arr = JSON.parse(raw);
        if (!Array.isArray(arr) || arr.length === 0) {
            _addAlert('JSON must be a non-empty array.', 'error'); return;
        }
    } catch (e) {
        _addAlert(`JSON error: ${e.message}`, 'error'); return;
    }

    const btn = el('bulkAddBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="btn-spinner"></span> Adding...';

    try {
        const res = await apiCall('/products/add-bulk', {
            method: 'POST',
            body: JSON.stringify({ products: arr }),
        });

        const msg = res.message || `Added ${res.added} products.`;
        showToast('Bulk Add Done', msg, res.skipped > 0 ? 'warning' : 'success');
        _addAlert(msg, res.skipped > 0 ? 'warning' : 'success');

        if (res.errors && res.errors.length > 0) {
            _addAlert(msg + '<br>' + res.errors.join('<br>'), 'warning');
        }

        // Clear caches
        state.cache.clear();
        if (state.currentMake) await handleMakeChange(state.currentMake);
        await _refreshStats();
        await loadAllData();

        el('bulkJsonInput').value = '';

    } catch (e) {
        _addAlert(e.message || 'Bulk add failed.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg> Add All Products`;
    }
}

function _addAlert(msg, type) {
    const c = el('addAlertContainer');
    if (!c) return;
    const icons = { error: '⚠', success: '✓', info: 'ℹ', warning: '⚠' };
    c.innerHTML = `<div class="alert alert-${type}"><span class="alert-icon">${icons[type] || 'ℹ'}</span><span class="alert-content">${msg}</span></div>`;
}

// ════════════════════════════════════════════════════
//  EDIT / DELETE PRODUCT
// ════════════════════════════════════════════════════

function openEditModal(product) {
    el('editOrigMake').value = product['Make'] || '';
    el('editOrigModel').value = product['Model'] || '';
    el('editMake').value = product['Make'] || '';
    el('editModel').value = product['Model'] || '';
    el('editSlNo').value = product['Sl.No'] ?? '';
    el('editDescription').value = product['Description'] || '';
    el('editQuantity').value = product['Quantity'] ?? 1;
    el('editNetPrice').value = product['Net Price'] ?? 0;
    el('editAlertContainer').innerHTML = '';

    el('editProductModal').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeEditModal() {
    el('editProductModal').classList.remove('active');
    document.body.style.overflow = '';
}

async function handleEditProduct(event) {
    event.preventDefault();
    const origMake  = el('editOrigMake').value;
    const origModel = el('editOrigModel').value;

    const updated = {
        original_make: origMake,
        original_model: origModel,
        'Sl.No': el('editSlNo').value ? parseInt(el('editSlNo').value) : null,
        'Make': el('editMake').value.trim(),
        'Model': el('editModel').value.trim(),
        'Description': el('editDescription').value.trim() || null,
        'Quantity': parseFloat(el('editQuantity').value) || 1,
        'Net Price': parseFloat(el('editNetPrice').value) || 0,
    };

    if (!updated.Make || !updated.Model) {
        _editAlert('Make and Model are required.', 'error'); return;
    }

    const btn = el('editSaveBtn');
    btn.disabled = true;
    btn.textContent = 'Saving...';

    try {
        const res = await apiCall('/products/edit', {
            method: 'POST',
            body: JSON.stringify(updated),
        });
        showToast('Updated', res.message || 'Product updated.', 'success');
        closeEditModal();
        state.cache.clear();
        if (state.currentMake) await handleMakeChange(state.currentMake);
        await _refreshStats();
    } catch (e) {
        _editAlert(e.message || 'Update failed.', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Save Changes';
    }
}

async function handleDeleteFromEdit() {
    const make  = el('editOrigMake').value;
    const model = el('editOrigModel').value;

    if (!confirm(`Are you sure you want to permanently delete "${model}" from "${make}"?`)) return;

    const btn = el('editDeleteBtn');
    btn.disabled = true;

    try {
        const res = await apiCall('/products/delete', {
            method: 'POST',
            body: JSON.stringify({ Make: make, Model: model }),
        });
        showToast('Deleted', res.message || 'Product deleted.', 'info');
        closeEditModal();
        state.cache.clear();
        if (state.currentMake) await handleMakeChange(state.currentMake);
        await _refreshStats();
    } catch (e) {
        _editAlert(e.message || 'Delete failed.', 'error');
    } finally {
        btn.disabled = false;
    }
}

function _editAlert(msg, type) {
    const c = el('editAlertContainer');
    if (!c) return;
    const icons = { error: '⚠', success: '✓', info: 'ℹ', warning: '⚠' };
    c.innerHTML = `<div class="alert alert-${type}"><span class="alert-icon">${icons[type] || 'ℹ'}</span><span class="alert-content">${msg}</span></div>`;
}

async function _refreshStats() {
    try {
        const [statsData, makesData] = await Promise.all([
            apiCall('/products/stats'),
            apiCall('/products/makes'),
        ]);
        state.allMakes = makesData.makes || [];
        animateCounter('statMakes', state.allMakes.length);
        animateCounter('statProducts', statsData.total_items || 0);
        populateMakeDropdown(state.allMakes);
    } catch (e) {
        console.warn('Stats refresh failed:', e);
    }
}

// ── Add Edit/Delete buttons to table rows ──
// Override the existing renderTable function's row HTML to include action buttons
// Find the line in renderTable that creates tr.innerHTML and add an actions column

// REPLACE the existing renderTable function with this:
const _originalRenderTable = renderTable;
renderTable = function(products) {
    const tbody = el('tableBody');
    const tfoot = el('tableFoot');

    if (!products || !products.length) {
        tbody.innerHTML = `<tr><td colspan="7" class="table-no-data"><div class="no-data-inner"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg><span>No records found</span></div></td></tr>`;
        tfoot.innerHTML = '';
        return;
    }

    const frag = document.createDocumentFragment();
    products.forEach((p, idx) => {
        const tr = document.createElement('tr');
        tr.dataset.idx = idx;
        const slNo = (p['Sl.No'] !== null && p['Sl.No'] !== undefined) ? p['Sl.No'] : '—';
        tr.innerHTML = `
            <td class="td-slno">${escapeHtml(String(slNo))}</td>
            <td class="td-make"><span class="make-chip">${escapeHtml(p['Make'] || '—')}</span></td>
            <td class="td-model">${escapeHtml(p['Model'] || '—')}</td>
            <td class="td-desc">${p['Description'] ? escapeHtml(p['Description']) : '<span class="null-badge">—</span>'}</td>
            <td class="td-qty">${escapeHtml(String(p['Quantity'] ?? 1))}</td>
            <td class="td-price">
                <div class="price-display">
                    <span class="price-currency">₹</span>
                    <span>${formatNumber(p['Net Price'])}</span>
                </div>
            </td>
            <td class="col-actions">
                <div class="row-actions">
                    <button class="row-action-btn" onclick="event.stopPropagation(); openProductModal(${idx})" title="View">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    </button>
                    <button class="row-action-btn" onclick="event.stopPropagation(); openEditModalByIdx(${idx})" title="Edit">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                    </button>
                    <button class="row-action-btn danger" onclick="event.stopPropagation(); quickDelete(${idx})" title="Delete">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                    </button>
                </div>
            </td>
        `;
        tr.onclick = () => openProductModal(idx);
        frag.appendChild(tr);
    });

    tbody.innerHTML = '';
    tbody.appendChild(frag);

    const totalQty = products.reduce((s, p) => s + _safeNum(p['Quantity'], 1), 0);
    const totalVal = products.reduce((s, p) => s + (_safeNum(p['Net Price'], 0) * _safeNum(p['Quantity'], 1)), 0);
    tfoot.innerHTML = `
        <tr>
            <td colspan="5" class="total-label">Total · ${products.length} records</td>
            <td class="total-value">₹ ${formatNumber(totalVal)}</td>
            <td></td>
        </tr>`;
};

function openEditModalByIdx(idx) {
    const p = state.filteredProducts[idx];
    if (p) openEditModal(p);
}

async function quickDelete(idx) {
    const p = state.filteredProducts[idx];
    if (!p) return;
    if (!confirm(`Delete "${p['Model']}" from "${p['Make']}"?\n\nThis action cannot be undone.`)) return;

    try {
        const res = await apiCall('/products/delete', {
            method: 'POST',
            body: JSON.stringify({ Make: p['Make'], Model: p['Model'] }),
        });
        showToast('Deleted', res.message || 'Product removed.', 'info');
        state.cache.clear();
        if (state.currentMake) await handleMakeChange(state.currentMake);
        await _refreshStats();
    } catch (e) {
        showToast('Error', e.message || 'Delete failed.', 'error');
    }
}

// ── Add Actions column header to table ──
// Run once on page load to add the header
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        const headerRow = document.querySelector('.products-table thead tr');
        if (headerRow && !headerRow.querySelector('.col-actions')) {
            const th = document.createElement('th');
            th.className = 'col-actions';
            th.innerHTML = '<span>Actions</span>';
            headerRow.appendChild(th);
        }
    }, 500);
});

// ── Add keyboard shortcut for Add Product ──
document.addEventListener('keydown', e => {
    // Ctrl+Shift+A to open Add Product
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'A') {
        e.preventDefault();
        openAddProductModal();
    }
});