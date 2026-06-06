// ============================================================
// API BASE URL — tự động phát hiện môi trường
// ============================================================
const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? `${window.location.protocol}//${window.location.hostname}:8000`
    : '';

// ============================================================
// CONFIG
// ============================================================
const CONFIG = {
    map: {
        center: [21.028511, 105.804817],
        zoom: 13,
    },
    simulation: {
        intervalMs: 5000,
    }
};

// ============================================================
// KHỞI TẠO BẢN ĐỒ
// ============================================================
const googleMaps = L.tileLayer('https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}&hl=vi', {
    maxZoom: 20,
    subdomains: ['mt0','mt1','mt2','mt3'],
    attribution: 'Map data &copy; Google'
});

const map = L.map('map', {
    center: CONFIG.map.center,
    zoom: CONFIG.map.zoom,
    layers: [googleMaps],
    zoomControl: false
});
map.attributionControl.setPrefix(
    '<span style="margin-right:3px;">🇻🇳</span><a href="https://utc.edu.vn" target="_blank" style="color:#0284c7;font-weight:bold;text-decoration:none;">AI Traffic UTC</a>'
);

const markersLayer = L.layerGroup().addTo(map);
const markerRegistry = new Map();

// ============================================================
// SEARCH MARKER — giống Google Maps (pin đỏ + popup tên)
// ============================================================
let searchMarker = null;

// Icon pin đỏ giống Google Maps
const searchIcon = L.divIcon({
    className: '',
    html: `
        <div style="position:relative;width:32px;height:42px;">
            <svg viewBox="0 0 32 42" xmlns="http://www.w3.org/2000/svg" style="width:32px;height:42px;filter:drop-shadow(0 3px 6px rgba(0,0,0,0.35));">
                <path d="M16 0C7.163 0 0 7.163 0 16c0 10.5 14 26 16 26S32 26.5 32 16C32 7.163 24.837 0 16 0z" fill="#ea4335"/>
                <circle cx="16" cy="16" r="7" fill="white"/>
                <circle cx="16" cy="16" r="4" fill="#ea4335"/>
            </svg>
        </div>`,
    iconSize: [32, 42],
    iconAnchor: [16, 42],
    popupAnchor: [0, -44],
});

function placeSearchMarker(lat, lon, name) {
    // Xóa marker cũ nếu có
    if (searchMarker) {
        map.removeLayer(searchMarker);
        searchMarker = null;
    }

    searchMarker = L.marker([lat, lon], { icon: searchIcon })
        .addTo(map)
        .bindPopup(`
            <div style="font-family:'Inter',sans-serif;min-width:180px;padding:2px;">
                <div style="font-weight:700;font-size:13px;color:#1e293b;margin-bottom:4px;">📍 ${name}</div>
                <div style="font-size:11px;color:#94a3b8;font-family:monospace;">${parseFloat(lat).toFixed(5)}, ${parseFloat(lon).toFixed(5)}</div>
                <div style="margin-top:8px;">
                    <button onclick="if(window.searchMarker){map.removeLayer(window.searchMarker);window.searchMarker=null;}" 
                        style="font-size:11px;padding:3px 8px;border:1px solid #e2e8f0;border-radius:6px;cursor:pointer;background:#f8fafc;color:#64748b;">
                        ✕ Xóa điểm đánh dấu
                    </button>
                </div>
            </div>`, { maxWidth: 240 })
        .openPopup();

    // Expose ra window để nút xóa trong popup có thể dùng
    window.searchMarker = searchMarker;
}

// ============================================================
// TRẠNG THÁI HỆ THỐNG
// ============================================================
let rawIssuesList = [];
let currentFilterType = 'all';

// ============================================================
// ĐỒNG HỒ
// ============================================================
function updateClock() {
    document.getElementById('current-time').innerText =
        new Date().toLocaleTimeString('vi-VN', { hour12: false });
}
setInterval(updateClock, 1000);
updateClock();

// ============================================================
// TAB SWITCHING
// ============================================================
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
    });
});

// ============================================================
// SIDEBAR TOGGLE
// ============================================================
const sidebar = document.querySelector('.main-sidebar');
const toggleBtn = document.getElementById('toggleSidebar');

toggleBtn.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
    setTimeout(() => map.invalidateSize(), 320);
});

// ============================================================
// SEARCH — Google Maps style autocomplete (Nominatim)
// ============================================================
const searchInput = document.getElementById('map-search');
const searchBox  = searchInput.closest('.search-box');

const dropdown = document.createElement('div');
dropdown.id = 'search-suggestions';
dropdown.style.cssText = `
    position: absolute;
    top: calc(100% + 6px);
    left: 0;
    right: 0;
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(15,23,42,0.12);
    z-index: 9999;
    overflow: hidden;
    display: none;
    max-height: 280px;
    overflow-y: auto;
`;
searchBox.style.position = 'relative';
searchBox.appendChild(dropdown);

let debounceTimer = null;
let activeSuggestionIdx = -1;
let suggestions = [];

function clearDropdown() {
    dropdown.innerHTML = '';
    dropdown.style.display = 'none';
    activeSuggestionIdx = -1;
    suggestions = [];
}

function renderSuggestions(results) {
    dropdown.innerHTML = '';
    if (!results.length) { dropdown.style.display = 'none'; return; }

    suggestions = results;
    results.forEach((item, idx) => {
        const parts = item.display_name.split(',');
        const main  = parts[0].trim();
        const sub   = parts.slice(1, 3).join(',').trim();

        const row = document.createElement('div');
        row.style.cssText = `
            display: flex; align-items: center; gap: 10px;
            padding: 10px 14px; cursor: pointer; transition: background 0.12s;
            border-bottom: 1px solid #f1f5f9;
        `;
        row.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#ea4335" stroke-width="2.5" style="flex-shrink:0">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
            </svg>
            <div style="overflow:hidden;">
                <div style="font-size:0.84rem;font-weight:600;color:#1e293b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${main}</div>
                <div style="font-size:0.72rem;color:#94a3b8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${sub}</div>
            </div>`;
        row.addEventListener('mouseenter', () => { row.style.background = '#f8fafc'; });
        row.addEventListener('mouseleave', () => { row.style.background = idx === activeSuggestionIdx ? '#f0f9ff' : ''; });
        row.addEventListener('mousedown', (e) => {
            e.preventDefault();
            selectSuggestion(idx);
        });
        dropdown.appendChild(row);
    });
    dropdown.style.display = 'block';
}

function selectSuggestion(idx) {
    const item = suggestions[idx];
    if (!item) return;

    const lat = parseFloat(item.lat);
    const lon = parseFloat(item.lon);
    const name = item.display_name.split(',').slice(0, 2).join(',').trim();

    searchInput.value = name;

    // Bay đến địa điểm
    map.flyTo([lat, lon], 16, { animate: true, duration: 1.2 });

    // Đặt marker sau khi animation xong
    setTimeout(() => placeSearchMarker(lat, lon, name), 1000);

    clearDropdown();
}

function highlightRow(idx) {
    const rows = dropdown.querySelectorAll('div[style*="cursor: pointer"]');
    rows.forEach((r, i) => { r.style.background = i === idx ? '#f0f9ff' : ''; });
}

searchInput.addEventListener('input', () => {
    const q = searchInput.value.trim();
    clearTimeout(debounceTimer);
    if (q.length < 2) { clearDropdown(); return; }

    debounceTimer = setTimeout(() => {
        fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}&limit=6&accept-language=vi&countrycodes=vn`)
            .then(r => r.json())
            .then(renderSuggestions)
            .catch(() => clearDropdown());
    }, 250);
});

searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') {
        e.preventDefault();
        activeSuggestionIdx = Math.min(activeSuggestionIdx + 1, suggestions.length - 1);
        highlightRow(activeSuggestionIdx);
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        activeSuggestionIdx = Math.max(activeSuggestionIdx - 1, -1);
        highlightRow(activeSuggestionIdx);
    } else if (e.key === 'Enter') {
        e.preventDefault();
        if (activeSuggestionIdx >= 0) {
            selectSuggestion(activeSuggestionIdx);
        } else if (suggestions.length > 0) {
            selectSuggestion(0);
        }
    } else if (e.key === 'Escape') {
        clearDropdown();
    }
});

searchInput.addEventListener('blur', () => {
    setTimeout(clearDropdown, 150);
});

// ============================================================
// POPUP TEMPLATE (issue)
// ============================================================
function createPopupContent(issue) {
    const verifiedLabel = issue.isVerified
        ? `<span style="color:#10b981;font-weight:700;">✓ Đã xác thực — Đồng thuận mạng lưới (${issue.consensusCount || 0})</span>`
        : `<span style="color:#f59e0b;font-weight:700;">⏳ Chờ xác thực — Thiếu bản tin biên (${issue.consensusCount || 0})</span>`;

    return `
        <div style="font-family:'Inter',sans-serif;min-width:240px;padding:2px;">
            <div style="color:#1e293b;font-weight:800;font-size:13px;margin-bottom:6px;display:flex;align-items:center;gap:6px;">
                🚨 ${issue.type}
            </div>
            <div style="margin-bottom:8px;border-radius:8px;overflow:hidden;border:1px solid #e2e8f0;">
                <img src="${issue.imageUrl}" style="width:100%;height:auto;display:block;" loading="lazy" />
            </div>
            <div style="font-size:11px;color:#64748b;margin-bottom:4px;">
                <b>Cực biên xử lý:</b>
                <span style="color:#6366f1;font-weight:600;">${issue.nodeId}</span>
            </div>
            <div style="font-size:11px;color:#64748b;margin-bottom:4px;">
                <b>Độ chính xác AI:</b>
                <span style="color:#ef4444;font-weight:600;">${(issue.confidence * 100).toFixed(0)}%</span>
            </div>
            <div style="font-size:11px;color:#94a3b8;font-family:'JetBrains Mono',monospace;margin-bottom:8px;">
                📍 ${issue.lat.toFixed(5)}, ${issue.lng.toFixed(5)}
            </div>
            <div style="font-size:11px;background:#f8fafc;padding:6px;border-radius:6px;border:1px solid #e2e8f0;">
                ${verifiedLabel}
            </div>
        </div>`;
}

// ============================================================
// RENDER LIVE FEED & MARKERS
// ============================================================
function renderFeed() {
    markersLayer.clearLayers();
    markerRegistry.clear();

    const logContainer = document.getElementById('log-container');
    logContainer.innerHTML = '';

    const filtered = currentFilterType === 'all'
        ? rawIssuesList
        : rawIssuesList.filter(i => i.type === currentFilterType);

    if (filtered.length === 0) {
        logContainer.innerHTML = `
            <div class="empty-state">
                <span>Không có sự cố nào cho bộ lọc này</span>
            </div>`;
        return;
    }

    filtered.forEach((issue) => {
        const isVerified  = issue.isVerified;
        const markerColor = isVerified ? '#10b981' : '#ef4444';
        const fillColor   = isVerified ? '#34d399' : '#f87171';

        const marker = L.circleMarker([issue.lat, issue.lng], {
            color: markerColor,
            fillColor,
            fillOpacity: isVerified ? 0.95 : 0.7,
            radius: isVerified ? 10 : 7,
            weight: 2,
            className: 'blinking-marker'
        }).addTo(markersLayer);

        marker.bindPopup(createPopupContent(issue));
        markerRegistry.set(issue.id, marker);

        const timeStr = issue.timestamp.toLocaleTimeString('vi-VN', { hour12: false });
        const card = document.createElement('div');
        card.className = `feed-card ${isVerified ? 'verified' : ''}`;
        card.dataset.issueId = issue.id;
        card.innerHTML = `
            <div class="card-top">
                <span class="issue-badge map-jump-btn" title="Nhấn để xem trên bản đồ 📍">
                    ${issue.type}
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-left:4px;flex-shrink:0;">
                        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
                    </svg>
                </span>
                <span class="time-stamp">${timeStr}</span>
            </div>
            <div class="card-mid">
                <span class="coord-lbl">[${issue.lat.toFixed(5)}, ${issue.lng.toFixed(5)}]</span>
                <span class="node-lbl">Nguồn phát hiện: <span class="node-name">${issue.nodeId}</span></span>
            </div>
            <div class="card-bottom">
                <span class="confidence-rate">Độ tin cậy: <span>${(issue.confidence * 100).toFixed(0)}%</span></span>
                <span class="verification-status ${isVerified ? 'status-approved' : 'status-pending'}">
                    ${isVerified ? 'Đã xác thực' : 'Đang xác minh'}
                </span>
            </div>`;

        card.querySelector('.map-jump-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            document.querySelectorAll('.feed-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            map.flyTo([issue.lat, issue.lng], 17, { animate: true, duration: 1.2 });
            setTimeout(() => marker.openPopup(), 1100);
        });

        card.addEventListener('click', () => {
            map.setView([issue.lat, issue.lng], 16, { animate: true, duration: 0.6 });
            marker.openPopup();
            document.querySelectorAll('.feed-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
        });

        logContainer.appendChild(card);
    });
}

// ============================================================
// RENDER BLOCKCHAIN LEDGER
// ============================================================
function renderBlockchainLedger(blocks) {
    const container = document.getElementById('blockchain-container');
    container.innerHTML = '';

    blocks.forEach(block => {
        const bCard = document.createElement('div');
        bCard.className = 'block-card';
        bCard.innerHTML = `
            <div class="block-header">
                <span>Slot: ${block.slot.toLocaleString('en-US')}</span>
                <span>Metadata: ${block.metadataLabel}</span>
            </div>
            <div class="block-payload">
                <b>Payload:</b> GPS [${block.lat.toFixed(4)}, ${block.lng.toFixed(4)}] | ${block.issueType}
            </div>
            <div class="tx-hash-row">
                <div class="tx-hash">${block.txHash}</div>
                <a class="tx-link" href="${block.explorerUrl}" target="_blank" title="Xem trên Cardanoscan">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                        <polyline points="15 3 21 3 21 9"/>
                        <line x1="10" y1="14" x2="21" y2="3"/>
                    </svg>
                </a>
            </div>`;
        container.appendChild(bCard);
    });
}

// ============================================================
// ĐỒNG BỘ DỮ LIỆU TỪ BACKEND
// ============================================================
async function syncDataFromServer() {
    try {
        const statsRes = await fetch(`${API_BASE}/api/stats`);
        if (statsRes.ok) {
            const stats = await statsRes.json();
            const totalAlerts   = stats.total_alerts       ?? stats.totalAlerts      ?? 0;
            const verifiedCount = stats.verified_count     ?? stats.verifiedCount    ?? 0;
            const nodeCount     = stats.node_count         ?? stats.nodeCount        ?? 0;
            const avgConfidence = stats.avg_confidence_pct ?? stats.avgConfidencePct ?? 0;

            document.getElementById('total-alerts').innerText   = totalAlerts.toLocaleString('vi-VN');
            document.getElementById('verified-count').innerText = verifiedCount.toLocaleString('vi-VN');
            document.getElementById('node-count').innerText     = nodeCount.toLocaleString('vi-VN');
            document.getElementById('avg-confidence').innerText = avgConfidence + '%';
        }

        const issuesRes = await fetch(`${API_BASE}/api/issues`);
        if (issuesRes.ok) {
            const rawData = await issuesRes.json();
            rawIssuesList = rawData.map(item => ({
                ...item,
                timestamp: new Date(item.timestamp)
            }));
            renderFeed();
        }

        const ledgerRes = await fetch(`${API_BASE}/api/blockchain`);
        if (ledgerRes.ok) {
            const blocks = await ledgerRes.json();
            renderBlockchainLedger(blocks);
        }
    } catch (error) {
        console.error('Lỗi kết nối API với Backend:', error);
    }
}

// ============================================================
// BỘ LỌC TAG
// ============================================================
document.querySelectorAll('.filter-tag').forEach(tag => {
    tag.addEventListener('click', (e) => {
        document.querySelectorAll('.filter-tag').forEach(t => t.classList.remove('active'));
        e.target.classList.add('active');
        currentFilterType = e.target.dataset.type;
        renderFeed();
    });
});

// ============================================================
// KHỞI ĐỘNG
// ============================================================
document.getElementById('log-container').innerHTML = `
    <div class="loading-state">
        <div class="loading-spinner"></div>
        <span>Đang kết nối API hệ thống Backend...</span>
    </div>`;

setTimeout(() => {
    syncDataFromServer();
    setInterval(syncDataFromServer, CONFIG.simulation.intervalMs);
}, 800);