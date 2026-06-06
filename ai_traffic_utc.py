"""
╔══════════════════════════════════════════════════════════════════╗
║        AI TRAFFIC UTC  —  ALL-IN-ONE SERVER (FE + BE)           ║
║   Chạy: python3 ai_traffic_utc.py                               ║
║   Mở:   http://localhost:8000                                    ║
╚══════════════════════════════════════════════════════════════════╝

Phụ thuộc:
    pip install fastapi uvicorn pydantic

Không cần file ngoài — FE được nhúng trực tiếp vào đây.
"""

from __future__ import annotations
import asyncio, hashlib, math, os, random, time, uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

# ════════════════════════════════════════════════
# TOÀN BỘ HTML / CSS / JS NHÚNG SẴN
# ════════════════════════════════════════════════

_CSS = ":root {\n    --bg-main: #0f172a;\n    --bg-sidebar: #ffffff;\n    --bg-surface: #f8fafc;\n    --bg-surface-hover: #f1f5f9;\n    --border-color: #e2e8f0;\n    --border-strong: #cbd5e1;\n    --text-primary: #1e293b;\n    --text-secondary: #64748b;\n    --text-light: #94a3b8;\n    --brand-blue: #0284c7;\n    --brand-orange: #f97316;\n    --brand-green: #10b981;\n    --brand-red: #ef4444;\n    --brand-purple: #6366f1;\n    --brand-yellow: #f59e0b;\n    --sidebar-width: 380px;\n    --sidebar-offset: 396px; /* sidebar-width + 16px gap */\n    --transition-sidebar: 0.3s cubic-bezier(0.4, 0, 0.2, 1);\n}\n\n* { margin: 0; padding: 0; box-sizing: border-box; }\n\nbody, html {\n    height: 100%;\n    width: 100%;\n    overflow: hidden;\n    color: var(--text-primary);\n    font-family: 'Inter', system-ui, -apple-system, sans-serif;\n    -webkit-font-smoothing: antialiased;\n}\n\n/* \u2500\u2500 B\u1ea2N \u0110\u1ed2 \u2500\u2500 */\n#map {\n    position: absolute;\n    inset: 0;\n    width: 100%;\n    height: 100%;\n    z-index: 1;\n}\n\n/* \u2500\u2500 CONTROLS PH\u00cdA TR\u00caN B\u1ea2N \u0110\u1ed2 \u2500\u2500 */\n.map-top-controls {\n    position: absolute;\n    top: 16px;\n    left: calc(var(--sidebar-offset) + 16px);\n    right: 16px;\n    z-index: 100;\n    display: flex;\n    flex-wrap: wrap;\n    gap: 10px;\n    pointer-events: none;\n    transition: left var(--transition-sidebar);\n}\n\n.main-sidebar.collapsed ~ .map-top-controls {\n    left: 24px;\n}\n\n.map-top-controls > * { pointer-events: auto; }\n\n.search-box {\n    background: #ffffff;\n    border: 1px solid var(--border-strong);\n    border-radius: 12px;\n    display: flex;\n    align-items: center;\n    padding: 0 14px;\n    gap: 10px;\n    flex: 1;\n    min-width: 200px;\n    max-width: 340px;\n    height: 44px;\n    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);\n}\n\n.search-box input {\n    border: none;\n    outline: none;\n    width: 100%;\n    font-size: 0.875rem;\n    color: var(--text-primary);\n    font-family: inherit;\n    background: transparent;\n}\n\n.search-box input:disabled { opacity: 0.5; cursor: wait; }\n.search-box svg { color: var(--text-secondary); flex-shrink: 0; }\n\n\n.filter-tags {\n    display: flex;\n    gap: 8px;\n    overflow-x: auto;\n    scroll-behavior: smooth;\n    -ms-overflow-style: none;\n    scrollbar-width: none;\n    flex-wrap: wrap;\n}\n\n.filter-tags::-webkit-scrollbar { display: none; }\n\n.filter-tag {\n    background: #ffffff;\n    border: 1px solid var(--border-strong);\n    padding: 0 14px;\n    height: 44px;\n    border-radius: 12px;\n    font-size: 0.82rem;\n    font-weight: 600;\n    cursor: pointer;\n    white-space: nowrap;\n    display: flex;\n    align-items: center;\n    gap: 6px;\n    transition: all 0.18s ease;\n    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);\n}\n\n.filter-tag:hover { background: var(--bg-surface-hover); border-color: var(--text-light); }\n.filter-tag.active { background: var(--text-primary); color: #ffffff; border-color: var(--text-primary); }\n\n/* \u2500\u2500 SIDEBAR \u2500\u2500 */\n.main-sidebar {\n    position: absolute;\n    top: 16px;\n    left: 16px;\n    bottom: 16px;\n    width: var(--sidebar-width);\n    z-index: 200;\n    background: var(--bg-sidebar);\n    border: 1px solid var(--border-strong);\n    border-radius: 20px;\n    box-shadow: 0 8px 24px rgba(0,0,0,0.08);\n    display: flex;\n    flex-direction: column;\n    overflow: hidden;\n    transition: transform var(--transition-sidebar);\n}\n\n.main-sidebar.collapsed { transform: translateX(calc(-1 * var(--sidebar-width) - 20px)); }\n\n/* \u2500\u2500 HEADER \u2500\u2500 */\n.sidebar-header {\n    padding: 18px 20px 14px;\n    display: flex;\n    align-items: center;\n    justify-content: space-between;\n    border-bottom: 1px solid var(--border-color);\n    flex-shrink: 0;\n}\n\n.brand-container { display: flex; align-items: center; gap: 12px; }\n\n.app-logo { width: 36px; height: 36px; object-fit: contain; }\n\n.brand-text h1 {\n    font-size: 1.1rem;\n    font-weight: 800;\n    letter-spacing: -0.5px;\n    color: var(--text-primary);\n    line-height: 1.15;\n}\n\n.brand-text h1 .highlight { color: var(--brand-orange); }\n\n.brand-text p {\n    font-size: 0.68rem;\n    font-weight: 600;\n    color: var(--text-secondary);\n    text-transform: uppercase;\n    letter-spacing: 0.5px;\n    margin-top: 2px;\n}\n\n.system-status {\n    display: flex;\n    align-items: center;\n    gap: 6px;\n    background: rgba(16,185,129,0.1);\n    padding: 5px 10px;\n    border-radius: 30px;\n    border: 1px solid rgba(16,185,129,0.2);\n    flex-shrink: 0;\n}\n\n.status-indicator { width: 8px; height: 8px; border-radius: 50%; background: var(--brand-green); }\n.status-text { font-size: 0.68rem; font-weight: 700; color: var(--brand-green); letter-spacing: 0.5px; }\n\n.blinking { animation: statusPulse 1.8s infinite ease-in-out; }\n\n@keyframes statusPulse {\n    0%, 100% { opacity: 0.4; transform: scale(0.9); }\n    50% { opacity: 1; transform: scale(1.1); box-shadow: 0 0 8px var(--brand-green); }\n}\n\n/* \u2500\u2500 NETWORK BANNER \u2500\u2500 */\n.network-banner {\n    background: #f8fafc;\n    padding: 8px 20px;\n    border-bottom: 1px solid var(--border-color);\n    display: flex;\n    align-items: center;\n    justify-content: space-between;\n    flex-shrink: 0;\n}\n\n.net-info { display: flex; align-items: center; gap: 6px; font-size: 0.73rem; color: var(--text-secondary); }\n.net-info svg { color: var(--brand-purple); flex-shrink: 0; }\n\n.gateway-tag {\n    font-size: 0.63rem;\n    font-family: 'JetBrains Mono', monospace;\n    background: rgba(99,102,241,0.1);\n    color: var(--brand-purple);\n    padding: 2px 7px;\n    border-radius: 4px;\n    font-weight: 600;\n}\n\n/* \u2500\u2500 STATISTICS \u2500\u2500 */\n.statistics-grid {\n    display: grid;\n    grid-template-columns: 1fr 1fr;\n    gap: 10px;\n    padding: 14px 16px;\n    background: #ffffff;\n    border-bottom: 1px solid var(--border-color);\n    flex-shrink: 0;\n}\n\n.stat-box {\n    border-radius: 12px;\n    padding: 10px 12px;\n    display: flex;\n    flex-direction: column;\n    gap: 3px;\n    border: 1px solid var(--border-color);\n    transition: transform 0.2s;\n}\n\n.stat-box:hover { transform: translateY(-2px); }\n\n.stat-box.red   { background: #fff5f5; border-color: rgba(239,68,68,0.15); }\n.stat-box.green { background: #f0fdf4; border-color: rgba(16,185,129,0.15); }\n.stat-box.purple{ background: #f5f3ff; border-color: rgba(99,102,241,0.15); }\n.stat-box.orange{ background: #fff7ed; border-color: rgba(249,115,22,0.15); }\n\n.stat-label {\n    font-size: 0.65rem;\n    font-weight: 600;\n    color: var(--text-secondary);\n    text-transform: uppercase;\n    letter-spacing: 0.2px;\n    line-height: 1.3;\n}\n\n.stat-value {\n    font-size: 1.35rem;\n    font-weight: 800;\n    font-family: 'JetBrains Mono', monospace;\n    line-height: 1.1;\n}\n\n.stat-box.red    .stat-value { color: var(--brand-red); }\n.stat-box.green  .stat-value { color: var(--brand-green); }\n.stat-box.purple .stat-value { color: var(--brand-purple); }\n.stat-box.orange .stat-value { color: var(--brand-orange); }\n\n/* \u2500\u2500 TABS \u2500\u2500 */\n.content-tabs {\n    display: flex;\n    border-bottom: 1px solid var(--border-color);\n    background: var(--bg-surface);\n    padding: 4px 4px 0;\n    flex-shrink: 0;\n}\n\n.tab-btn {\n    flex: 1;\n    border: none;\n    background: none;\n    padding: 10px 8px;\n    font-size: 0.75rem;\n    font-weight: 700;\n    color: var(--text-secondary);\n    cursor: pointer;\n    border-radius: 10px 10px 0 0;\n    transition: all 0.15s ease;\n    text-align: center;\n}\n\n.tab-btn:hover { color: var(--text-primary); background: rgba(0,0,0,0.02); }\n\n.tab-btn.active {\n    color: var(--brand-blue);\n    background: #ffffff;\n    border: 1px solid var(--border-color);\n    border-bottom-color: #ffffff;\n}\n\n/* \u2500\u2500 TAB PANELS \u2500\u2500 */\n.tab-panel { display: none; flex: 1; flex-direction: column; overflow: hidden; min-height: 0; }\n.tab-panel.active { display: flex; }\n\n.panel-meta {\n    padding: 8px 16px;\n    font-size: 0.7rem;\n    color: var(--text-secondary);\n    background: var(--bg-surface);\n    border-bottom: 1px solid var(--border-color);\n    font-style: italic;\n    flex-shrink: 0;\n}\n\n/* \u2500\u2500 SCROLL CONTAINERS \u2500\u2500 */\n.feed-container, .blockchain-container {\n    flex: 1;\n    overflow-y: auto;\n    padding: 10px 14px;\n    display: flex;\n    flex-direction: column;\n    gap: 8px;\n    min-height: 0;\n}\n\n/* \u2500\u2500 LOADING / EMPTY STATES \u2500\u2500 */\n.loading-state {\n    display: flex;\n    align-items: center;\n    gap: 10px;\n    padding: 24px 16px;\n    color: var(--text-secondary);\n    font-size: 0.82rem;\n}\n\n.loading-spinner {\n    width: 16px;\n    height: 16px;\n    border: 2px solid var(--border-color);\n    border-top-color: var(--brand-blue);\n    border-radius: 50%;\n    animation: spin 0.8s linear infinite;\n    flex-shrink: 0;\n}\n\n@keyframes spin { to { transform: rotate(360deg); } }\n\n.empty-state {\n    display: flex;\n    align-items: center;\n    justify-content: center;\n    padding: 32px 16px;\n    color: var(--text-light);\n    font-size: 0.82rem;\n    text-align: center;\n}\n\n/* \u2500\u2500 FEED CARDS \u2500\u2500 */\n.feed-card {\n    background: #ffffff;\n    border: 1px solid var(--border-color);\n    border-radius: 12px;\n    padding: 11px 12px 11px 16px;\n    display: flex;\n    flex-direction: column;\n    gap: 7px;\n    cursor: pointer;\n    transition: all 0.18s ease;\n    position: relative;\n    overflow: hidden;\n    flex-shrink: 0;\n}\n\n.feed-card::before {\n    content: '';\n    position: absolute;\n    top: 0; left: 0; bottom: 0;\n    width: 4px;\n    background: var(--brand-red);\n    border-radius: 0;\n}\n\n.feed-card.verified::before { background: var(--brand-green); }\n\n.feed-card:hover {\n    background: var(--bg-surface);\n    border-color: var(--text-light);\n    transform: translateX(2px);\n    box-shadow: 0 2px 8px rgba(0,0,0,0.06);\n}\n\n.feed-card.selected {\n    border-color: var(--brand-blue);\n    background: #f0f9ff;\n}\n\n.card-top { display: flex; justify-content: space-between; align-items: flex-start; }\n\n.issue-badge {\n    background: rgba(239,68,68,0.08);\n    color: var(--brand-red);\n    font-size: 0.73rem;\n    font-weight: 700;\n    padding: 3px 9px;\n    border-radius: 6px;\n    border: 1px solid rgba(239,68,68,0.15);\n    display: inline-flex;\n    align-items: center;\n    line-height: 1.3;\n    white-space: nowrap;\n}\n\n.issue-badge.map-jump-btn {\n    cursor: pointer;\n    transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;\n    user-select: none;\n}\n\n.issue-badge.map-jump-btn:hover {\n    transform: scale(1.07);\n    background: rgba(239,68,68,0.16);\n    box-shadow: 0 2px 8px rgba(239,68,68,0.25);\n}\n\n.issue-badge.map-jump-btn:active {\n    transform: scale(0.95);\n}\n\n.feed-card.verified .issue-badge.map-jump-btn:hover {\n    background: rgba(16,185,129,0.16);\n    box-shadow: 0 2px 8px rgba(16,185,129,0.25);\n}\n\n.feed-card.verified .issue-badge {\n    background: rgba(16,185,129,0.08);\n    color: var(--brand-green);\n    border-color: rgba(16,185,129,0.15);\n}\n\n.time-stamp { font-size: 0.68rem; font-family: 'JetBrains Mono', monospace; color: var(--text-light); font-weight: 500; }\n\n.card-mid { display: flex; flex-direction: column; gap: 2px; }\n.coord-lbl { font-size: 0.76rem; font-family: 'JetBrains Mono', monospace; color: var(--text-primary); font-weight: 600; }\n.node-lbl { font-size: 0.7rem; color: var(--text-secondary); }\n.node-name { color: var(--brand-purple); font-weight: 600; }\n\n.card-bottom {\n    display: flex;\n    justify-content: space-between;\n    align-items: center;\n    border-top: 1px dashed var(--border-color);\n    padding-top: 5px;\n}\n\n.confidence-rate { font-size: 0.7rem; font-weight: 600; color: var(--text-secondary); }\n.confidence-rate span { color: var(--brand-red); font-weight: 700; }\n.feed-card.verified .confidence-rate span { color: var(--brand-green); }\n\n.verification-status { font-size: 0.68rem; font-weight: 600; padding: 2px 8px; border-radius: 4px; }\n.status-pending  { background: #fef3c7; color: #d97706; }\n.status-approved { background: #dcfce7; color: #15803d; }\n\n/* \u2500\u2500 BLOCKCHAIN CARDS \u2500\u2500 */\n.block-card {\n    background: var(--bg-surface);\n    border: 1px solid var(--border-color);\n    border-radius: 10px;\n    padding: 10px 12px;\n    display: flex;\n    flex-direction: column;\n    gap: 5px;\n    font-family: 'JetBrains Mono', monospace;\n    flex-shrink: 0;\n    animation: slideIn 0.25s ease;\n}\n\n@keyframes slideIn {\n    from { opacity: 0; transform: translateY(-6px); }\n    to   { opacity: 1; transform: translateY(0); }\n}\n\n.block-header {\n    display: flex;\n    justify-content: space-between;\n    font-size: 0.72rem;\n    font-weight: 600;\n    color: var(--brand-purple);\n}\n\n.block-payload { font-size: 0.7rem; color: var(--text-primary); }\n\n.tx-hash-row { display: flex; align-items: center; gap: 6px; }\n\n.tx-hash {\n    font-size: 0.65rem;\n    color: var(--text-secondary);\n    word-break: break-all;\n    background: #ffffff;\n    padding: 4px 6px;\n    border-radius: 4px;\n    border: 1px solid var(--border-color);\n    flex: 1;\n    line-height: 1.4;\n}\n\n.tx-link {\n    display: flex;\n    align-items: center;\n    justify-content: center;\n    width: 26px;\n    height: 26px;\n    border-radius: 6px;\n    border: 1px solid var(--border-color);\n    background: #ffffff;\n    color: var(--brand-blue);\n    text-decoration: none;\n    flex-shrink: 0;\n    transition: background 0.15s;\n}\n\n.tx-link:hover { background: #eff6ff; border-color: var(--brand-blue); }\n\n/* \u2500\u2500 FOOTER \u2500\u2500 */\n.sidebar-footer {\n    padding: 10px 20px;\n    border-top: 1px solid var(--border-color);\n    background: var(--bg-surface);\n    display: flex;\n    align-items: center;\n    justify-content: space-between;\n    flex-shrink: 0;\n}\n\n.clock { font-size: 0.76rem; font-family: 'JetBrains Mono', monospace; font-weight: 600; color: var(--text-primary); }\n.copyright { font-size: 0.63rem; color: var(--text-light); font-weight: 500; }\n\n/* \u2500\u2500 TOGGLE BUTTON \u2500\u2500 */\n.toggle-sidebar-btn {\n    position: absolute;\n    top: 50%;\n    left: calc(var(--sidebar-offset) + 4px);\n    transform: translateY(-50%);\n    z-index: 200;\n    width: 28px;\n    height: 52px;\n    background: #ffffff;\n    border: 1px solid var(--border-strong);\n    border-radius: 8px;\n    cursor: pointer;\n    display: flex;\n    align-items: center;\n    justify-content: center;\n    box-shadow: 3px 0 8px rgba(0,0,0,0.06);\n    color: var(--text-secondary);\n    transition: left var(--transition-sidebar), color 0.15s;\n}\n\n.toggle-sidebar-btn:hover { color: var(--text-primary); background: var(--bg-surface-hover); }\n\n.main-sidebar.collapsed ~ .toggle-sidebar-btn { left: 20px; }\n.main-sidebar.collapsed ~ .toggle-sidebar-btn svg { transform: rotate(180deg); }\n.toggle-sidebar-btn svg { transition: transform var(--transition-sidebar); }\n\n\n/* \u2500\u2500 MARKER ANIMATION \u2500\u2500 */\n.blinking-marker { animation: markerGlow 2s infinite ease-out; }\n\n@keyframes markerGlow {\n    0%   { fill-opacity: 0.9; stroke-width: 2;  stroke-opacity: 0.4; }\n    50%  { fill-opacity: 0.6; stroke-width: 10; stroke-opacity: 0.12; }\n    100% { fill-opacity: 0.9; stroke-width: 2;  stroke-opacity: 0.4; }\n}\n\n/* \u2500\u2500 SCROLLBAR \u2500\u2500 */\n::-webkit-scrollbar { width: 5px; }\n::-webkit-scrollbar-track { background: transparent; }\n::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }\n::-webkit-scrollbar-thumb:hover { background: #94a3b8; }\n\n/* \u2500\u2500 RESPONSIVE \u2014 TABLET (\u2264 768px) \u2500\u2500 */\n@media (max-width: 768px) {\n    :root {\n        --sidebar-width: 320px;\n        --sidebar-offset: 336px;\n    }\n}\n\n/* \u2500\u2500 RESPONSIVE \u2014 MOBILE (\u2264 500px) \u2500\u2500 */\n@media (max-width: 500px) {\n    :root {\n        --sidebar-width: calc(100vw - 32px);\n        --sidebar-offset: 0px;\n    }\n\n    .main-sidebar {\n        top: auto;\n        bottom: 0;\n        left: 0;\n        right: 0;\n        width: 100%;\n        height: 55vh;\n        border-radius: 20px 20px 0 0;\n        border-bottom: none;\n        transform: translateY(0);\n    }\n\n    .main-sidebar.collapsed {\n        transform: translateY(calc(55vh - 56px));\n    }\n\n    .map-top-controls {\n        top: 12px;\n        left: 12px;\n        right: 12px;\n    }\n\n    .main-sidebar.collapsed ~ .map-top-controls { left: 12px; }\n\n    .toggle-sidebar-btn {\n        bottom: 56px;\n        top: auto;\n        left: 50%;\n        transform: translateX(-50%);\n        width: 52px;\n        height: 28px;\n        border-radius: 8px;\n    }\n\n    .main-sidebar.collapsed ~ .toggle-sidebar-btn {\n        bottom: calc(56px - 55vh + 56px);\n        left: 50%;\n        transform: translateX(-50%);\n    }\n\n    .toggle-sidebar-btn svg { transform: rotate(-90deg); }\n    .main-sidebar.collapsed ~ .toggle-sidebar-btn svg { transform: rotate(90deg); }\n\n    .search-box { max-width: 100%; }\n    .search-hint { display: none; }\n    .filter-tags { flex-wrap: nowrap; overflow-x: auto; }\n\n    .leaflet-top.leaflet-left {\n        top: 80px !important;\n        left: 12px !important;\n    }\n\n    .statistics-grid { grid-template-columns: 1fr 1fr; gap: 8px; padding: 12px; }\n    .stat-value { font-size: 1.2rem; }\n}"

_JS  = "// ============================================================\n// API BASE URL \u2014 t\u1ef1 \u0111\u1ed9ng ph\u00e1t hi\u1ec7n m\u00f4i tr\u01b0\u1eddng\n// N\u1ebfu m\u1edf qua Live Server (port 5500, 3000, ...) \u2192 g\u1ecdi backend port 8000\n// N\u1ebfu m\u1edf qua Python backend (port 8000) \u2192 d\u00f9ng URL t\u01b0\u01a1ng \u0111\u1ed1i\n// ============================================================\nconst BACKEND_PORT = 8000;\nconst _currentPort = parseInt(window.location.port) || 80;\nconst API_BASE = (_currentPort !== BACKEND_PORT)\n    ? `${window.location.protocol}//${window.location.hostname}:${BACKEND_PORT}`\n    : '';\n\n// ============================================================\n// CONFIG \u2014 C\u1ea5u h\u00ecnh b\u1ea3n \u0111\u1ed3 v\u00e0 chu k\u1ef3 \u0111\u1ed3ng b\u1ed9\n// ============================================================\nconst CONFIG = {\n    map: {\n        center: [21.028511, 105.804817],\n        zoom: 13,\n    },\n    simulation: {\n        intervalMs: 5000, // C\u1ee9 5 gi\u00e2y g\u1ecdi API l\u1ea5y d\u1eef li\u1ec7u m\u1edbi 1 l\u1ea7n\n    }\n};\n\n// ============================================================\n// KH\u1edeI T\u1ea0O B\u1ea2N \u0110\u1ed2\n// ============================================================\nconst googleMaps = L.tileLayer('https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}&hl=vi', {\n    maxZoom: 20,\n    subdomains: ['mt0','mt1','mt2','mt3'],\n    attribution: 'Map data &copy; Google'\n});\n\nconst map = L.map('map', {\n    center: CONFIG.map.center,\n    zoom: CONFIG.map.zoom,\n    layers: [googleMaps],\n    zoomControl: false\n});\nmap.attributionControl.setPrefix(\n    '<span style=\"margin-right:3px;\">\ud83c\uddfb\ud83c\uddf3</span><a href=\"https://utc.edu.vn\" target=\"_blank\" style=\"color:#0284c7;font-weight:bold;text-decoration:none;\">AI Traffic UTC</a>'\n);\n\nconst markersLayer = L.layerGroup().addTo(map);\n\n// Map t\u1eeb issue id -> leaflet marker (\u0111\u1ec3 click card m\u1edf \u0111\u00fang popup)\nconst markerRegistry = new Map();\n\n// ============================================================\n// TR\u1ea0NG TH\u00c1I H\u1ec6 TH\u1ed0NG HI\u1ec6N T\u1ea0I\n// ============================================================\nlet rawIssuesList = [];\nlet currentFilterType = 'all';\n\n// ============================================================\n// \u0110\u1ed2NG H\u1ed2\n// ============================================================\nfunction updateClock() {\n    document.getElementById('current-time').innerText =\n        new Date().toLocaleTimeString('vi-VN', { hour12: false });\n}\nsetInterval(updateClock, 1000);\nupdateClock();\n\n// ============================================================\n// TAB SWITCHING\n// ============================================================\ndocument.querySelectorAll('.tab-btn').forEach(btn => {\n    btn.addEventListener('click', () => {\n        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));\n        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));\n        btn.classList.add('active');\n        document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');\n    });\n});\n\n// ============================================================\n// SIDEBAR TOGGLE \u2014 c\u1eadp nh\u1eadt v\u1ecb tr\u00ed zoom control theo sidebar\n// ============================================================\nconst sidebar = document.querySelector('.main-sidebar');\nconst toggleBtn = document.getElementById('toggleSidebar');\n\ntoggleBtn.addEventListener('click', () => {\n    sidebar.classList.toggle('collapsed');\n    // \u0110\u1ea9y l\u1ea1i viewport b\u1ea3n \u0111\u1ed3 sau khi animation xong\n    setTimeout(() => map.invalidateSize(), 320);\n});\n\n// ============================================================\n// SEARCH \u2014 Google Maps style autocomplete (Nominatim)\n// ============================================================\nconst searchInput = document.getElementById('map-search');\nconst searchBox  = searchInput.closest('.search-box');\n\n// T\u1ea1o dropdown suggestions\nconst dropdown = document.createElement('div');\ndropdown.id = 'search-suggestions';\ndropdown.style.cssText = `\n    position: absolute;\n    top: calc(100% + 6px);\n    left: 0;\n    right: 0;\n    background: #fff;\n    border: 1px solid #e2e8f0;\n    border-radius: 12px;\n    box-shadow: 0 8px 24px rgba(15,23,42,0.12);\n    z-index: 9999;\n    overflow: hidden;\n    display: none;\n    max-height: 280px;\n    overflow-y: auto;\n`;\nsearchBox.style.position = 'relative';\nsearchBox.appendChild(dropdown);\n\nlet debounceTimer = null;\nlet activeSuggestionIdx = -1;\nlet suggestions = [];\n\nfunction clearDropdown() {\n    dropdown.innerHTML = '';\n    dropdown.style.display = 'none';\n    activeSuggestionIdx = -1;\n    suggestions = [];\n}\n\nfunction renderSuggestions(results) {\n    dropdown.innerHTML = '';\n    if (!results.length) { dropdown.style.display = 'none'; return; }\n\n    suggestions = results;\n    results.forEach((item, idx) => {\n        const parts = item.display_name.split(',');\n        const main  = parts[0].trim();\n        const sub   = parts.slice(1, 3).join(',').trim();\n\n        const row = document.createElement('div');\n        row.style.cssText = `\n            display: flex; align-items: center; gap: 10px;\n            padding: 10px 14px; cursor: pointer; transition: background 0.12s;\n            border-bottom: 1px solid #f1f5f9;\n        `;\n        row.innerHTML = `\n            <svg width=\"14\" height=\"14\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"#94a3b8\" stroke-width=\"2.5\" flex-shrink=\"0\" style=\"flex-shrink:0\">\n                <path d=\"M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z\"/><circle cx=\"12\" cy=\"10\" r=\"3\"/>\n            </svg>\n            <div style=\"overflow:hidden;\">\n                <div style=\"font-size:0.84rem;font-weight:600;color:#1e293b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;\">${main}</div>\n                <div style=\"font-size:0.72rem;color:#94a3b8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;\">${sub}</div>\n            </div>`;\n        row.addEventListener('mouseenter', () => { row.style.background = '#f8fafc'; });\n        row.addEventListener('mouseleave', () => { row.style.background = idx === activeSuggestionIdx ? '#f0f9ff' : ''; });\n        row.addEventListener('mousedown', (e) => {\n            e.preventDefault(); // ng\u0103n blur tr\u01b0\u1edbc khi click x\u1eed l\u00fd\n            selectSuggestion(idx);\n        });\n        dropdown.appendChild(row);\n    });\n    dropdown.style.display = 'block';\n}\n\nfunction selectSuggestion(idx) {\n    const item = suggestions[idx];\n    if (!item) return;\n    searchInput.value = item.display_name.split(',').slice(0, 2).join(',').trim();\n    map.setView([parseFloat(item.lat), parseFloat(item.lon)], 16, { animate: true });\n    clearDropdown();\n}\n\nfunction highlightRow(idx) {\n    const rows = dropdown.querySelectorAll('div[style*=\"cursor: pointer\"]');\n    rows.forEach((r, i) => { r.style.background = i === idx ? '#f0f9ff' : ''; });\n}\n\nsearchInput.addEventListener('input', () => {\n    const q = searchInput.value.trim();\n    clearTimeout(debounceTimer);\n    if (q.length < 2) { clearDropdown(); return; }\n\n    debounceTimer = setTimeout(() => {\n        fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}&limit=6&accept-language=vi&countrycodes=vn`)\n            .then(r => r.json())\n            .then(renderSuggestions)\n            .catch(() => clearDropdown());\n    }, 250);\n});\n\nsearchInput.addEventListener('keydown', (e) => {\n    const rows = dropdown.querySelectorAll('div[style*=\"cursor: pointer\"]');\n    if (e.key === 'ArrowDown') {\n        e.preventDefault();\n        activeSuggestionIdx = Math.min(activeSuggestionIdx + 1, suggestions.length - 1);\n        highlightRow(activeSuggestionIdx);\n    } else if (e.key === 'ArrowUp') {\n        e.preventDefault();\n        activeSuggestionIdx = Math.max(activeSuggestionIdx - 1, -1);\n        highlightRow(activeSuggestionIdx);\n    } else if (e.key === 'Enter') {\n        e.preventDefault();\n        if (activeSuggestionIdx >= 0) {\n            selectSuggestion(activeSuggestionIdx);\n        } else if (suggestions.length > 0) {\n            selectSuggestion(0);\n        }\n    } else if (e.key === 'Escape') {\n        clearDropdown();\n    }\n});\n\nsearchInput.addEventListener('blur', () => {\n    setTimeout(clearDropdown, 150);\n});\n\n// ============================================================\n// POPUP TEMPLATE\n// ============================================================\nfunction createPopupContent(issue) {\n    const verifiedLabel = issue.isVerified\n        ? `<span style=\"color:#10b981;font-weight:700;\">\u2713 \u0110\u00e3 x\u00e1c th\u1ef1c \u2014 \u0110\u1ed3ng thu\u1eadn m\u1ea1ng l\u01b0\u1edbi (${issue.consensusCount || 0})</span>`\n        : `<span style=\"color:#f59e0b;font-weight:700;\">\u23f3 Ch\u1edd x\u00e1c th\u1ef1c \u2014 Thi\u1ebfu b\u1ea3n tin bi\u00ean (${issue.consensusCount || 0})</span>`;\n\n    return `\n        <div style=\"font-family:'Inter',sans-serif;min-width:240px;padding:2px;\">\n            <div style=\"color:#1e293b;font-weight:800;font-size:13px;margin-bottom:6px;display:flex;align-items:center;gap:6px;\">\n                \ud83d\udea8 ${issue.type}\n            </div>\n            <div style=\"margin-bottom:8px;border-radius:8px;overflow:hidden;border:1px solid #e2e8f0;\">\n                <img src=\"${issue.imageUrl}\" style=\"width:100%;height:auto;display:block;\" loading=\"lazy\" />\n            </div>\n            <div style=\"font-size:11px;color:#64748b;margin-bottom:4px;\">\n                <b>C\u1ef1c bi\u00ean x\u1eed l\u00fd:</b>\n                <span style=\"color:#6366f1;font-weight:600;\">${issue.nodeId}</span>\n            </div>\n            <div style=\"font-size:11px;color:#64748b;margin-bottom:4px;\">\n                <b>\u0110\u1ed9 ch\u00ednh x\u00e1c AI:</b>\n                <span style=\"color:#ef4444;font-weight:600;\">${(issue.confidence * 100).toFixed(0)}%</span>\n            </div>\n            <div style=\"font-size:11px;color:#94a3b8;font-family:'JetBrains Mono',monospace;margin-bottom:8px;\">\n                \ud83d\udccd ${issue.lat.toFixed(5)}, ${issue.lng.toFixed(5)}\n            </div>\n            <div style=\"font-size:11px;background:#f8fafc;padding:6px;border-radius:6px;border:1px solid #e2e8f0;\">\n                ${verifiedLabel}\n            </div>\n        </div>`;\n}\n\n// ============================================================\n// RENDER D\u1eee LI\u1ec6U S\u1ef0 C\u1ed0 (LIVE FEED & MARKERS)\n// ============================================================\nfunction renderFeed() {\n    markersLayer.clearLayers();\n    markerRegistry.clear();\n\n    const logContainer = document.getElementById('log-container');\n    logContainer.innerHTML = '';\n\n    const filtered = currentFilterType === 'all'\n        ? rawIssuesList\n        : rawIssuesList.filter(i => i.type === currentFilterType);\n\n    if (filtered.length === 0) {\n        logContainer.innerHTML = `\n            <div class=\"empty-state\">\n                <span>Kh\u00f4ng c\u00f3 s\u1ef1 c\u1ed1 n\u00e0o cho b\u1ed9 l\u1ecdc n\u00e0y</span>\n            </div>`;\n        return;\n    }\n\n    filtered.forEach((issue) => {\n        const isVerified = issue.isVerified;\n        const markerColor = isVerified ? '#10b981' : '#ef4444';\n        const fillColor   = isVerified ? '#34d399' : '#f87171';\n\n        const marker = L.circleMarker([issue.lat, issue.lng], {\n            color: markerColor,\n            fillColor,\n            fillOpacity: isVerified ? 0.95 : 0.7,\n            radius: isVerified ? 10 : 7,\n            weight: 2,\n            className: 'blinking-marker'\n        }).addTo(markersLayer);\n\n        marker.bindPopup(createPopupContent(issue));\n        markerRegistry.set(issue.id, marker);\n\n        const timeStr = issue.timestamp.toLocaleTimeString('vi-VN', { hour12: false });\n        const card = document.createElement('div');\n        card.className = `feed-card ${isVerified ? 'verified' : ''}`;\n        card.dataset.issueId = issue.id;\n        card.innerHTML = `\n            <div class=\"card-top\">\n                <span class=\"issue-badge map-jump-btn\" title=\"Nh\u1ea5n \u0111\u1ec3 xem tr\u00ean b\u1ea3n \u0111\u1ed3 \ud83d\udccd\">\n                    ${issue.type}\n                    <svg width=\"10\" height=\"10\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2.5\" style=\"margin-left:4px;flex-shrink:0;\">\n                        <path d=\"M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z\"/><circle cx=\"12\" cy=\"10\" r=\"3\"/>\n                    </svg>\n                </span>\n                <span class=\"time-stamp\">${timeStr}</span>\n            </div>\n            <div class=\"card-mid\">\n                <span class=\"coord-lbl\">[${issue.lat.toFixed(5)}, ${issue.lng.toFixed(5)}]</span>\n                <span class=\"node-lbl\">Ngu\u1ed3n ph\u00e1t hi\u1ec7n: <span class=\"node-name\">${issue.nodeId}</span></span>\n            </div>\n            <div class=\"card-bottom\">\n                <span class=\"confidence-rate\">\u0110\u1ed9 tin c\u1eady: <span>${(issue.confidence * 100).toFixed(0)}%</span></span>\n                <span class=\"verification-status ${isVerified ? 'status-approved' : 'status-pending'}\">\n                    ${isVerified ? '\u0110\u00e3 x\u00e1c th\u1ef1c' : '\u0110ang x\u00e1c minh'}\n                </span>\n            </div>`;\n\n        // Click v\u00e0o BADGE \u2192 flyTo m\u01b0\u1ee3t + m\u1edf popup\n        card.querySelector('.map-jump-btn').addEventListener('click', (e) => {\n            e.stopPropagation();\n            document.querySelectorAll('.feed-card').forEach(c => c.classList.remove('selected'));\n            card.classList.add('selected');\n            map.flyTo([issue.lat, issue.lng], 17, { animate: true, duration: 1.2 });\n            setTimeout(() => marker.openPopup(), 1100);\n        });\n\n        // Click v\u00e0o ph\u1ea7n c\u00f2n l\u1ea1i c\u1ee7a card \u2192 setView nhanh + m\u1edf popup\n        card.addEventListener('click', () => {\n            map.setView([issue.lat, issue.lng], 16, { animate: true, duration: 0.6 });\n            marker.openPopup();\n            document.querySelectorAll('.feed-card').forEach(c => c.classList.remove('selected'));\n            card.classList.add('selected');\n        });\n\n        logContainer.appendChild(card);\n    });\n}\n\n// ============================================================\n// RENDER BLOCKCHAIN LEDGER\n// ============================================================\nfunction renderBlockchainLedger(blocks) {\n    const container = document.getElementById('blockchain-container');\n    container.innerHTML = '';\n\n    blocks.forEach(block => {\n        const bCard = document.createElement('div');\n        bCard.className = 'block-card';\n        bCard.innerHTML = `\n            <div class=\"block-header\">\n                <span>Slot: ${block.slot.toLocaleString('en-US')}</span>\n                <span>Metadata: ${block.metadataLabel}</span>\n            </div>\n            <div class=\"block-payload\">\n                <b>Payload:</b> GPS [${block.lat.toFixed(4)}, ${block.lng.toFixed(4)}] | ${block.issueType}\n            </div>\n            <div class=\"tx-hash-row\">\n                <div class=\"tx-hash\">${block.txHash}</div>\n                <a class=\"tx-link\" href=\"${block.explorerUrl}\" target=\"_blank\" title=\"Xem tr\u00ean Cardanoscan\">\n                    <svg width=\"12\" height=\"12\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2.5\">\n                        <path d=\"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6\"/>\n                        <polyline points=\"15 3 21 3 21 9\"/>\n                        <line x1=\"10\" y1=\"14\" x2=\"21\" y2=\"3\"/>\n                    </svg>\n                </a>\n            </div>`;\n        container.appendChild(bCard);\n    });\n}\n\n// ============================================================\n// \u0110\u1ed2NG B\u1ed8 D\u1eee LI\u1ec6U T\u1eea BACKEND\n// ============================================================\nasync function syncDataFromServer() {\n    try {\n        // 1. L\u1ea5y Dashboard Stats\n        const statsRes = await fetch(`${API_BASE}/api/stats`);\n        if (statsRes.ok) {\n            const stats = await statsRes.json();\n            // \u0110\u1ecdc an to\u00e0n c\u1ea3 2 chu\u1ea9n snake_case v\u00e0 camelCase \u0111\u1ec3 tr\u00e1nh l\u1ed7i undefined\n            const totalAlerts = stats.total_alerts ?? stats.totalAlerts ?? 0;\n            const verifiedCount = stats.verified_count ?? stats.verifiedCount ?? 0;\n            const nodeCount = stats.node_count ?? stats.nodeCount ?? 0;\n            const avgConfidence = stats.avg_confidence_pct ?? stats.avgConfidencePct ?? 0;\n\n            document.getElementById('total-alerts').innerText = totalAlerts.toLocaleString('vi-VN');\n            document.getElementById('verified-count').innerText = verifiedCount.toLocaleString('vi-VN');\n            document.getElementById('node-count').innerText = nodeCount.toLocaleString('vi-VN');\n            document.getElementById('avg-confidence').innerText = avgConfidence + '%';\n        }\n\n        // 2. L\u1ea5y Live Feed (Issues)\n        const issuesRes = await fetch(`${API_BASE}/api/issues`);\n        if (issuesRes.ok) {\n            const rawData = await issuesRes.json();\n            rawIssuesList = rawData.map(item => ({\n                ...item,\n                timestamp: new Date(item.timestamp)\n            }));\n            renderFeed();\n        }\n\n        // 3. L\u1ea5y Blockchain Ledger\n        const ledgerRes = await fetch(`${API_BASE}/api/blockchain`);\n        if (ledgerRes.ok) {\n            const blocks = await ledgerRes.json();\n            renderBlockchainLedger(blocks);\n        }\n    } catch (error) {\n        console.error('L\u1ed7i k\u1ebft n\u1ed1i API v\u1edbi Backend:', error);\n    }\n}\n\n// ============================================================\n// B\u1ed8 L\u1eccC T\u00ccM KI\u1ebeM THEO TH\u1eba TAG\n// ============================================================\ndocument.querySelectorAll('.filter-tag').forEach(tag => {\n    tag.addEventListener('click', (e) => {\n        document.querySelectorAll('.filter-tag').forEach(t => t.classList.remove('active'));\n        e.target.classList.add('active');\n        currentFilterType = e.target.dataset.type;\n        renderFeed();\n    });\n});\n\n// ============================================================\n// KH\u1edeI \u0110\u1ed8NG H\u1ec6 TH\u1ed0NG\n// ============================================================\n// Hi\u1ec3n th\u1ecb loading state ng\u1eafn tr\u01b0\u1edbc khi d\u1eef li\u1ec7u \u0111\u1ea7u ti\u00ean \u0111\u01b0\u1ee3c t\u1ea3i\ndocument.getElementById('log-container').innerHTML = `\n    <div class=\"loading-state\">\n        <div class=\"loading-spinner\"></div>\n        <span>\u0110ang k\u1ebft n\u1ed1i API h\u1ec7 th\u1ed1ng Backend...</span>\n    </div>`;\n\nsetTimeout(() => {\n    syncDataFromServer(); // Ch\u1ea1y ngay l\u1ea7n \u0111\u1ea7u ti\u00ean\n    setInterval(syncDataFromServer, CONFIG.simulation.intervalMs); // L\u1eb7p l\u1ea1i sau m\u1ed7i 5s\n}, 800);"

_HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI TRAFFIC UTC — Hệ Thống Giám Sát Hạ Tầng Giao Thông Phi Tập Trung</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>{CSS_PLACEHOLDER}</style>
</head>
<body>
    <div id="map"></div>
    <div class="map-top-controls">
        <div class="search-box">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input type="text" id="map-search" placeholder="Tìm kiếm vị trí, tuyến đường tại Hà Nội..." aria-label="Tìm kiếm địa điểm" />
        </div>
        <div class="filter-tags">
            <button class="filter-tag active" data-type="all">Tất cả</button>
            <button class="filter-tag" data-type="Ổ gà">⚠️ Ổ gà</button>
            <button class="filter-tag" data-type="Mặt đường lún">📉 Vết lún</button>
            <button class="filter-tag" data-type="Ngập nước nhẹ">🌊 Ngập nước</button>
            <button class="filter-tag" data-type="Nắp cống hỏng">🚫 Nắp cống</button>
        </div>
    </div>
    <div class="main-sidebar">
        <div class="sidebar-header">
            <div class="brand-container">
                <div style="width:36px;height:36px;background:linear-gradient(135deg,#6366f1,#0284c7);border-radius:10px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:900;font-size:14px;flex-shrink:0;">UTC</div>
                <div class="brand-text">
                    <h1>AI TRAFFIC <span class="highlight">UTC</span></h1>
                    <p>Decentralized Edge-AI Grid</p>
                </div>
            </div>
            <div class="system-status" aria-label="Trạng thái: đang hoạt động">
                <span class="status-indicator blinking"></span>
                <span class="status-text">LIVE</span>
            </div>
        </div>
        <div class="network-banner">
            <div class="net-info">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
                <span>Mạng đồng thuận: <b>Cardano Preprod Testnet</b></span>
            </div>
            <div class="gateway-tag">Blockfrost API</div>
        </div>
        <div class="statistics-grid">
            <div class="stat-box red"><span class="stat-label">Tổng sự cố phát hiện</span><span class="stat-value" id="total-alerts">0</span></div>
            <div class="stat-box green"><span class="stat-label">Đã đồng thuận đám đông</span><span class="stat-value" id="verified-count">0</span></div>
            <div class="stat-box purple"><span class="stat-label">Edge Node active</span><span class="stat-value" id="node-count">0</span></div>
            <div class="stat-box orange"><span class="stat-label">Độ tin cậy TB mạng</span><span class="stat-value" id="avg-confidence">0%</span></div>
        </div>
        <div class="content-tabs" role="tablist">
            <button class="tab-btn active" data-tab="live-feed" role="tab" aria-selected="true">DỮ LIỆU SỰ CỐ (LIVE FEED)</button>
            <button class="tab-btn" data-tab="blockchain-log" role="tab" aria-selected="false">SỔ CÁI MINH BẠCH (LEDGER)</button>
        </div>
        <div id="tab-live-feed" class="tab-panel active" role="tabpanel">
            <div class="panel-meta">Cập nhật tự động từ các mắt thần di động (Camera/Smartphone)</div>
            <div class="feed-container" id="log-container"></div>
        </div>
        <div id="tab-blockchain-log" class="tab-panel" role="tabpanel">
            <div class="panel-meta">TxHash 64-ký-tự ghi nhận tọa độ GPS bất biến lên Cardano Blockchain</div>
            <div class="blockchain-container" id="blockchain-container"></div>
        </div>
        <div class="sidebar-footer">
            <div class="clock" id="current-time" aria-live="polite">--:--:--</div>
            <div class="copyright">&copy; 2026 Nhóm Nghiên Cứu AI &amp; Blockchain UTC</div>
        </div>
    </div>
    <button class="toggle-sidebar-btn" id="toggleSidebar" aria-label="Đóng/Mở bảng điều khiển">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
    </button>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>{JS_PLACEHOLDER}</script>
</body>
</html>"""

_HTML = _HTML.replace("{CSS_PLACEHOLDER}", _CSS).replace("{JS_PLACEHOLDER}", _JS)

# ════════════════════════════════════════════════
# APP SETUP
# ════════════════════════════════════════════════
app = FastAPI(title="AI Traffic UTC", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

CONSENSUS_THRESHOLD = 3
COORD_EPSILON       = 0.0005
MAX_ISSUES          = 60
ISSUE_TYPES         = ["Ổ gà", "Mặt đường lún", "Ngập nước nhẹ", "Nắp cống hỏng"]
ISSUE_IMAGES = {
    "Ổ gà":           "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Pothole_on_a_road_in_India.jpg/320px-Pothole_on_a_road_in_India.jpg",
    "Mặt đường lún":  "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Road_subsidence.jpg/320px-Road_subsidence.jpg",
    "Ngập nước nhẹ":  "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Urban_flooding.jpg/320px-Urban_flooding.jpg",
    "Nắp cống hỏng":  "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Manhole_cover_broken.jpg/320px-Manhole_cover_broken.jpg",
}
DEFAULT_IMAGE = "https://placehold.co/320x180/f8fafc/94a3b8?text=Su+co+GT"
SEED_LOCS = [
    (21.0285,105.8542),(21.0442,105.8412),(21.0245,105.8412),(21.0133,105.8199),
    (21.0378,105.7834),(21.0612,105.8434),(21.0078,105.8734),(21.0512,105.8634),
    (21.0198,105.8634),(21.0334,105.8234),
]
_issues:  List[dict] = []
_ledger:  List[dict] = []
_inited = False

def _txhash(s): return hashlib.sha256(s.encode()).hexdigest() + hashlib.md5(s.encode()).hexdigest()
def _slot():    return int(time.time()) - 1_700_000_000 + random.randint(-3600, 0)

class ReportPayload(BaseModel):
    lat:        float = Field(..., ge=20.5, le=21.5)
    lng:        float = Field(..., ge=105.0, le=106.5)
    type:       str
    confidence: float = Field(..., ge=0.0, le=1.0)
    nodeId:     Optional[str] = None

def _seed():
    global _inited
    if _inited: return
    _inited = True
    pool = [f"EdgeNode-HN-{i:03d}" for i in range(1,20)]
    now  = time.time()
    for base_lat, base_lng in SEED_LOCS:
        for _ in range(random.randint(2,4)):
            t   = random.choice(ISSUE_TYPES)
            lat = base_lat + random.uniform(-0.003, 0.003)
            lng = base_lng + random.uniform(-0.003, 0.003)
            c   = round(random.uniform(0.62, 0.98), 3)
            cnt = random.randint(1, 5)
            oid = str(uuid.uuid4())[:8]
            ts  = datetime.fromtimestamp(now - random.randint(0,7200), tz=timezone.utc).isoformat()
            ok  = cnt >= CONSENSUS_THRESHOLD
            _issues.append(dict(id=oid, lat=round(lat,6), lng=round(lng,6), type=t,
                confidence=c, nodeId=random.choice(pool), timestamp=ts,
                isVerified=ok, consensusCount=cnt,
                imageUrl=ISSUE_IMAGES.get(t, DEFAULT_IMAGE)))
            if ok:
                h = _txhash(f"{oid}-{lat:.5f}-{lng:.5f}")
                _ledger.append(dict(slot=_slot()-random.randint(0,3600), metadataLabel=721,
                    lat=round(lat,6), lng=round(lng,6), issueType=t, txHash=h,
                    explorerUrl=f"https://preprod.cardanoscan.io/transaction/{h}"))
    _issues.sort(key=lambda x: x["timestamp"], reverse=True)
    _ledger.sort(key=lambda x: x["slot"], reverse=True)

async def _simulate():
    pool = [f"EdgeNode-HN-{i:03d}" for i in range(1,20)]
    while True:
        await asyncio.sleep(8)
        base_lat, base_lng = random.choice(SEED_LOCS)
        t   = random.choice(ISSUE_TYPES)
        lat = base_lat + random.uniform(-0.005, 0.005)
        lng = base_lng + random.uniform(-0.005, 0.005)
        c   = round(random.uniform(0.60, 0.99), 3)
        cnt = random.randint(1, 5)
        oid = str(uuid.uuid4())[:8]
        ts  = datetime.now(tz=timezone.utc).isoformat()
        ok  = cnt >= CONSENSUS_THRESHOLD
        _issues.insert(0, dict(id=oid, lat=round(lat,6), lng=round(lng,6), type=t,
            confidence=c, nodeId=random.choice(pool), timestamp=ts,
            isVerified=ok, consensusCount=cnt,
            imageUrl=ISSUE_IMAGES.get(t, DEFAULT_IMAGE)))
        if len(_issues) > MAX_ISSUES: _issues.pop()
        if ok:
            h = _txhash(f"{oid}-{lat:.5f}-{lng:.5f}")
            _ledger.insert(0, dict(slot=_slot(), metadataLabel=721,
                lat=round(lat,6), lng=round(lng,6), issueType=t, txHash=h,
                explorerUrl=f"https://preprod.cardanoscan.io/transaction/{h}"))
            if len(_ledger) > 30: _ledger.pop()

@app.on_event("startup")
async def startup():
    _seed()
    asyncio.create_task(_simulate())

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index(): return HTMLResponse(_HTML)

@app.get("/api/stats")
def stats():
    total = len(_issues)
    ver   = sum(1 for i in _issues if i["isVerified"])
    nodes = len(set(i["nodeId"] for i in _issues))
    avg   = round(sum(i["confidence"] for i in _issues)/total*100) if total else 0
    return dict(total_alerts=total, verified_count=ver, node_count=nodes, avg_confidence_pct=avg)

@app.get("/api/issues")
def issues(): return _issues

@app.get("/api/blockchain")
def blockchain(): return _ledger

@app.post("/api/report")
def report(p: ReportPayload):
    if p.type not in ISSUE_TYPES:
        raise HTTPException(400, detail=f"Loại không hợp lệ: {ISSUE_TYPES}")
    node = p.nodeId or f"EdgeNode-HN-{random.randint(1,99):03d}"
    oid  = str(uuid.uuid4())[:8]
    ts   = datetime.now(tz=timezone.utc).isoformat()
    near = [x for x in _issues if x["type"]==p.type and abs(x["lat"]-p.lat)<COORD_EPSILON and abs(x["lng"]-p.lng)<COORD_EPSILON]
    cnt  = len(near)+1
    ok   = cnt >= CONSENSUS_THRESHOLD
    _issues.insert(0, dict(id=oid, lat=round(p.lat,6), lng=round(p.lng,6), type=p.type,
        confidence=p.confidence, nodeId=node, timestamp=ts,
        isVerified=ok, consensusCount=cnt,
        imageUrl=ISSUE_IMAGES.get(p.type, DEFAULT_IMAGE)))
    if len(_issues)>MAX_ISSUES: _issues.pop()
    txh = None
    if ok:
        txh = _txhash(f"{oid}-{p.lat:.5f}-{p.lng:.5f}")
        _ledger.insert(0, dict(slot=_slot(), metadataLabel=721,
            lat=round(p.lat,6), lng=round(p.lng,6), issueType=p.type, txHash=txh,
            explorerUrl=f"https://preprod.cardanoscan.io/transaction/{txh}"))
        if len(_ledger)>30: _ledger.pop()
    return dict(success=True, issueId=oid, isVerified=ok, consensusCount=cnt, txHash=txh)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ai_traffic_utc:app", host="0.0.0.0", port=8000, reload=False)
