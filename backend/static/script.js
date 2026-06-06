// ============================================================
// VIETNAMESE FUZZY SEARCH — thay thế toàn bộ phần SEARCH cũ
// Tính năng:
//   ✅ Gõ có dấu hoặc không dấu đều tìm được
//   ✅ Gõ thiếu chữ / gõ tắt vẫn gợi ý đúng
//   ✅ Sai thứ tự từ vẫn khớp
//   ✅ Ưu tiên kết quả khớp chính xác nhất lên đầu
// ============================================================

// ──────────────────────────────────────────
// 1. BẢNG CHUẨN HÓA TIẾNG VIỆT
// ──────────────────────────────────────────
const VI_MAP = {
    à:'a',á:'a',ả:'a',ã:'a',ạ:'a',
    ă:'a',ằ:'a',ắ:'a',ẳ:'a',ẵ:'a',ặ:'a',
    â:'a',ầ:'a',ấ:'a',ẩ:'a',ẫ:'a',ậ:'a',
    è:'e',é:'e',ẻ:'e',ẽ:'e',ẹ:'e',
    ê:'e',ề:'e',ế:'e',ể:'e',ễ:'e',ệ:'e',
    ì:'i',í:'i',ỉ:'i',ĩ:'i',ị:'i',
    ò:'o',ó:'o',ỏ:'o',õ:'o',ọ:'o',
    ô:'o',ồ:'o',ố:'o',ổ:'o',ỗ:'o',ộ:'o',
    ơ:'o',ờ:'o',ớ:'o',ở:'o',ỡ:'o',ợ:'o',
    ù:'u',ú:'u',ủ:'u',ũ:'u',ụ:'u',
    ư:'u',ừ:'u',ứ:'u',ử:'u',ữ:'u',ự:'u',
    ỳ:'y',ý:'y',ỷ:'y',ỹ:'y',ỵ:'y',
    đ:'d',
    // Hoa → thường đã được toLowerCase() xử lý
};

/**
 * Chuẩn hóa chuỗi: lowercase + bỏ dấu tiếng Việt
 * "Hà Nội" → "ha noi"
 */
function normalize(str) {
    return str.toLowerCase().replace(/./g, c => VI_MAP[c] ?? c);
}

// ──────────────────────────────────────────
// 2. KHOẢNG CÁCH LEVENSHTEIN (edit distance)
//    Dùng để đo độ "gần đúng" giữa 2 chuỗi
// ──────────────────────────────────────────
function levenshtein(a, b) {
    const m = a.length, n = b.length;
    // Tối ưu: nếu quá dài thì bỏ qua tính toán nặng
    if (Math.abs(m - n) > 6) return 99;
    const dp = Array.from({ length: m + 1 }, (_, i) => [i, ...Array(n).fill(0)]);
    for (let j = 0; j <= n; j++) dp[0][j] = j;
    for (let i = 1; i <= m; i++)
        for (let j = 1; j <= n; j++)
            dp[i][j] = a[i-1] === b[j-1]
                ? dp[i-1][j-1]
                : 1 + Math.min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]);
    return dp[m][n];
}

// ──────────────────────────────────────────
// 3. HÀM TÍNH ĐIỂM TƯƠNG ĐỒNG
//    Trả về số càng nhỏ = càng khớp
// ──────────────────────────────────────────
function scoreMatch(queryNorm, itemNorm) {
    // Tách từng từ trong query
    const qWords = queryNorm.split(/\s+/).filter(Boolean);
    const iStr   = itemNorm;

    let score = 0;

    for (const qw of qWords) {
        if (iStr.includes(qw)) {
            // Khớp chính xác từ → điểm tốt nhất
            score += 0;
        } else {
            // Tìm từ gần nhất trong item
            const iWords = iStr.split(/\s+/);
            const minDist = Math.min(...iWords.map(iw => levenshtein(qw, iw)));
            score += minDist;
        }
    }

    // Bonus: query là tiền tố của item → ưu tiên
    if (iStr.startsWith(queryNorm)) score -= 2;
    // Bonus: item chứa chuỗi query liên tục
    if (iStr.includes(queryNorm)) score -= 1;

    return score;
}

// ──────────────────────────────────────────
// 4. NGƯỠNG LỌC — chỉ hiện kết quả đủ gần
// ──────────────────────────────────────────
const SCORE_THRESHOLD = 3; // điều chỉnh nếu muốn chặt/lỏng hơn

/**
 * Sắp xếp & lọc danh sách gợi ý từ Nominatim
 * @param {string} query   - Chuỗi người dùng nhập
 * @param {Array}  results - Mảng object từ Nominatim
 * @returns {Array} results đã sắp xếp theo độ phù hợp
 */
function fuzzyRankResults(query, results) {
    const qNorm = normalize(query.trim());

    const scored = results.map(item => {
        const displayNorm = normalize(item.display_name);
        const score = scoreMatch(qNorm, displayNorm);
        return { item, score };
    });

    return scored
        .filter(({ score }) => score <= SCORE_THRESHOLD)
        .sort((a, b) => a.score - b.score)
        .map(({ item }) => item);
}

// ──────────────────────────────────────────
// 5. CLIENT-SIDE PRE-FILTER
//    Gọi API với query không dấu để mở rộng kết quả,
//    sau đó rank lại bằng fuzzy
// ──────────────────────────────────────────
function buildSearchQuery(raw) {
    const withoutDiacritics = normalize(raw.trim());
    // Nếu query gốc đã không dấu thì dùng luôn,
    // ngược lại gửi cả 2 để Nominatim tìm rộng hơn
    return withoutDiacritics === raw.trim().toLowerCase()
        ? raw.trim()
        : raw.trim(); // Nominatim tự xử lý dấu tiếng Việt tốt
}

// ──────────────────────────────────────────
// 6. CẮM VÀO SEARCH INPUT (thay phần cũ)
// ──────────────────────────────────────────
const searchInput = document.getElementById('map-search');
const searchBox   = searchInput.closest('.search-box');

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

let debounceTimer       = null;
let activeSuggestionIdx = -1;
let suggestions         = [];

function clearDropdown() {
    dropdown.innerHTML        = '';
    dropdown.style.display    = 'none';
    activeSuggestionIdx       = -1;
    suggestions               = [];
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
        row.addEventListener('mousedown', e => { e.preventDefault(); selectSuggestion(idx); });
        dropdown.appendChild(row);
    });
    dropdown.style.display = 'block';
}

function selectSuggestion(idx) {
    const item = suggestions[idx];
    if (!item) return;

    const lat  = parseFloat(item.lat);
    const lon  = parseFloat(item.lon);
    const name = item.display_name.split(',').slice(0, 2).join(',').trim();

    searchInput.value = name;
    map.flyTo([lat, lon], 16, { animate: true, duration: 1.2 });
    setTimeout(() => placeSearchMarker(lat, lon, name), 1000);
    clearDropdown();
}

function highlightRow(idx) {
    dropdown.querySelectorAll('div[style*="cursor: pointer"]')
        .forEach((r, i) => { r.style.background = i === idx ? '#f0f9ff' : ''; });
}

// ── Gọi API + fuzzy rank ──
async function fetchAndRank(query) {
    const apiQuery = buildSearchQuery(query);

    // Gọi song song 2 query: có dấu & không dấu để tăng recall
    const normQuery = normalize(query.trim());
    const urls = [
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(apiQuery)}&limit=10&accept-language=vi&countrycodes=vn`,
    ];
    // Nếu query khác sau normalize thì gửi thêm bản không dấu
    if (normQuery !== apiQuery.toLowerCase()) {
        urls.push(
            `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(normQuery)}&limit=6&accept-language=vi&countrycodes=vn`
        );
    }

    const responses = await Promise.all(urls.map(u => fetch(u).then(r => r.json()).catch(() => [])));

    // Gộp, dedup theo place_id
    const seen = new Set();
    const merged = [];
    for (const list of responses) {
        for (const item of list) {
            if (!seen.has(item.place_id)) {
                seen.add(item.place_id);
                merged.push(item);
            }
        }
    }

    return fuzzyRankResults(query, merged);
}

searchInput.addEventListener('input', () => {
    const q = searchInput.value.trim();
    clearTimeout(debounceTimer);
    if (q.length < 2) { clearDropdown(); return; }

    debounceTimer = setTimeout(async () => {
        try {
            const ranked = await fetchAndRank(q);
            renderSuggestions(ranked);
        } catch {
            clearDropdown();
        }
    }, 250);
});

searchInput.addEventListener('keydown', e => {
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
        selectSuggestion(activeSuggestionIdx >= 0 ? activeSuggestionIdx : 0);
    } else if (e.key === 'Escape') {
        clearDropdown();
    }
});

searchInput.addEventListener('blur', () => setTimeout(clearDropdown, 150));