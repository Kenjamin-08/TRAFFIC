"""
AI TRAFFIC UTC — Backend Server
FastAPI + Python | Cardano Preprod Testnet (Blockfrost API)

Routes:
  GET  /api/stats       → Dashboard statistics
  GET  /api/issues      → Live feed of road incidents
  GET  /api/blockchain  → Blockchain ledger entries
  POST /api/report      → Submit a new incident report (from edge node)
"""

from __future__ import annotations

import hashlib
import math
import os
import random
import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# ─────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────
app = FastAPI(
    title="AI Traffic UTC API",
    description="Decentralized Edge-AI Traffic Grid — Nhóm Nghiên Cứu AI & Blockchain UTC",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Cho phép mọi origin (thay bằng domain thực khi production)
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# CẤU HÌNH HỆ THỐNG
# ─────────────────────────────────────────────
CONSENSUS_THRESHOLD = 3        # Cần ≥3 báo cáo cùng tọa độ để xác thực
COORD_EPSILON       = 0.0005   # ~55m — bán kính ghép tọa độ gần nhau
MAX_ISSUES          = 50       # Giữ tối đa 50 sự cố gần nhất trong bộ nhớ

ISSUE_TYPES = ["Ổ gà", "Mặt đường lún", "Ngập nước nhẹ", "Nắp cống hỏng"]

# Ảnh placeholder theo loại sự cố (public domain / Wikimedia)
ISSUE_IMAGES = {
    "Ổ gà":           "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Pothole_on_a_road_in_India.jpg/320px-Pothole_on_a_road_in_India.jpg",
    "Mặt đường lún":  "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Road_subsidence.jpg/320px-Road_subsidence.jpg",
    "Ngập nước nhẹ":  "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Urban_flooding.jpg/320px-Urban_flooding.jpg",
    "Nắp cống hỏng":  "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Manhole_cover_broken.jpg/320px-Manhole_cover_broken.jpg",
}
DEFAULT_IMAGE = "https://placehold.co/320x180/f8fafc/94a3b8?text=Sự+cố+GT"

# Tọa độ hạt giống ban đầu — trải rộng nội thành Hà Nội
SEED_LOCATIONS = [
    (21.0285, 105.8542, "Cầu Giấy"),
    (21.0442, 105.8412, "Đống Đa"),
    (21.0245, 105.8412, "Hoàn Kiếm"),
    (21.0133, 105.8199, "Hà Đông"),
    (21.0378, 105.7834, "Từ Liêm"),
    (21.0612, 105.8434, "Tây Hồ"),
    (21.0078, 105.8734, "Hoàng Mai"),
    (21.0512, 105.8634, "Long Biên"),
    (21.0198, 105.8634, "Hai Bà Trưng"),
    (21.0334, 105.8234, "Ba Đình"),
]

# ─────────────────────────────────────────────
# MÔ HÌNH DỮ LIỆU
# ─────────────────────────────────────────────
class Issue(BaseModel):
    id:             str
    lat:            float
    lng:            float
    type:           str
    confidence:     float
    nodeId:         str
    timestamp:      str          # ISO-8601
    isVerified:     bool
    consensusCount: int
    imageUrl:       str

class BlockEntry(BaseModel):
    slot:          int
    metadataLabel: int
    lat:           float
    lng:           float
    issueType:     str
    txHash:        str
    explorerUrl:   str

class ReportPayload(BaseModel):
    lat:        float = Field(..., ge=20.5,  le=21.5)
    lng:        float = Field(..., ge=105.0, le=106.5)
    type:       str
    confidence: float = Field(..., ge=0.0, le=1.0)
    nodeId:     Optional[str] = None

# ─────────────────────────────────────────────
# BỘ NHỚ ẤO (In-Memory Store)
# Trong production: thay bằng PostgreSQL / Redis
# ─────────────────────────────────────────────
_issues:  List[dict] = []
_ledger:  List[dict] = []
_initialized = False

# ─────────────────────────────────────────────
# HELPER — tạo TxHash giả lập (64 ký tự hex)
# ─────────────────────────────────────────────
def _fake_txhash(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest() + hashlib.md5(seed.encode()).hexdigest()

def _fake_slot() -> int:
    # Cardano Preprod: slot ≈ Unix timestamp − mainnet_offset
    return int(time.time()) - 1_700_000_000 + random.randint(-3600, 0)

def _haversine(lat1, lng1, lat2, lng2) -> float:
    """Khoảng cách Haversine (km) giữa 2 toạ độ."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def _nearby_issues(lat: float, lng: float, issue_type: str) -> List[dict]:
    return [
        iss for iss in _issues
        if iss["type"] == issue_type and abs(iss["lat"] - lat) < COORD_EPSILON and abs(iss["lng"] - lng) < COORD_EPSILON
    ]

# ─────────────────────────────────────────────
# KHỞI TẠO DỮ LIỆU HẠT GIỐNG (Seed Data)
# ─────────────────────────────────────────────
def _seed_initial_data():
    global _initialized
    if _initialized:
        return
    _initialized = True

    now_ts = time.time()
    node_pool = [f"EdgeNode-HN-{i:03d}" for i in range(1, 20)]

    for idx, (base_lat, base_lng, _district) in enumerate(SEED_LOCATIONS):
        for j in range(random.randint(2, 4)):
            issue_type   = random.choice(ISSUE_TYPES)
            lat          = base_lat  + random.uniform(-0.003, 0.003)
            lng          = base_lng  + random.uniform(-0.003, 0.003)
            confidence   = round(random.uniform(0.62, 0.98), 3)
            node_id      = random.choice(node_pool)
            offset_secs  = random.randint(0, 7200)
            ts_iso       = datetime.fromtimestamp(now_ts - offset_secs, tz=timezone.utc).isoformat()
            issue_id     = str(uuid.uuid4())[:8]
            count        = random.randint(1, 5)
            is_verified  = count >= CONSENSUS_THRESHOLD

            issue = {
                "id":             issue_id,
                "lat":            round(lat, 6),
                "lng":            round(lng, 6),
                "type":           issue_type,
                "confidence":     confidence,
                "nodeId":         node_id,
                "timestamp":      ts_iso,
                "isVerified":     is_verified,
                "consensusCount": count,
                "imageUrl":       ISSUE_IMAGES.get(issue_type, DEFAULT_IMAGE),
            }
            _issues.append(issue)

            # Ghi ledger cho sự cố đã xác thực
            if is_verified:
                tx_seed = f"{issue_id}-{lat:.5f}-{lng:.5f}"
                tx_hash = _fake_txhash(tx_seed)
                _ledger.append({
                    "slot":          _fake_slot() - offset_secs,
                    "metadataLabel": 721,
                    "lat":           round(lat, 6),
                    "lng":           round(lng, 6),
                    "issueType":     issue_type,
                    "txHash":        tx_hash,
                    "explorerUrl":   f"https://preprod.cardanoscan.io/transaction/{tx_hash}",
                })

    # Sắp xếp: mới nhất lên đầu
    _issues.sort(key=lambda x: x["timestamp"], reverse=True)
    _ledger.sort(key=lambda x: x["slot"], reverse=True)


# ─────────────────────────────────────────────
# SIMULATION — Thêm sự cố ngẫu nhiên mỗi 8 giây
# Chạy ở background khi server khởi động
# ─────────────────────────────────────────────
import asyncio

async def _auto_simulate():
    """Tự động thêm sự cố mới mỗi 8 giây để demo luôn sống động."""
    node_pool = [f"EdgeNode-HN-{i:03d}" for i in range(1, 20)]
    while True:
        await asyncio.sleep(8)
        base_lat, base_lng, _ = random.choice(SEED_LOCATIONS)
        issue_type  = random.choice(ISSUE_TYPES)
        lat         = base_lat + random.uniform(-0.005, 0.005)
        lng         = base_lng + random.uniform(-0.005, 0.005)
        confidence  = round(random.uniform(0.60, 0.99), 3)
        node_id     = random.choice(node_pool)
        count       = random.randint(1, 5)
        is_verified = count >= CONSENSUS_THRESHOLD
        issue_id    = str(uuid.uuid4())[:8]
        ts_iso      = datetime.now(tz=timezone.utc).isoformat()

        new_issue = {
            "id":             issue_id,
            "lat":            round(lat, 6),
            "lng":            round(lng, 6),
            "type":           issue_type,
            "confidence":     confidence,
            "nodeId":         node_id,
            "timestamp":      ts_iso,
            "isVerified":     is_verified,
            "consensusCount": count,
            "imageUrl":       ISSUE_IMAGES.get(issue_type, DEFAULT_IMAGE),
        }
        _issues.insert(0, new_issue)

        # Giới hạn bộ nhớ
        if len(_issues) > MAX_ISSUES:
            _issues.pop()

        # Thêm vào ledger nếu xác thực
        if is_verified:
            tx_seed = f"{issue_id}-{lat:.5f}-{lng:.5f}"
            tx_hash = _fake_txhash(tx_seed)
            _ledger.insert(0, {
                "slot":          _fake_slot(),
                "metadataLabel": 721,
                "lat":           round(lat, 6),
                "lng":           round(lng, 6),
                "issueType":     issue_type,
                "txHash":        tx_hash,
                "explorerUrl":   f"https://preprod.cardanoscan.io/transaction/{tx_hash}",
            })
            if len(_ledger) > 30:
                _ledger.pop()


@app.on_event("startup")
async def startup_event():
    _seed_initial_data()
    asyncio.create_task(_auto_simulate())


# ─────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/api/stats", summary="Thống kê Dashboard")
def get_stats():
    total   = len(_issues)
    verified = sum(1 for i in _issues if i["isVerified"])
    nodes   = len(set(i["nodeId"] for i in _issues))
    avg_conf = (
        round(sum(i["confidence"] for i in _issues) / total * 100)
        if total > 0 else 0
    )
    return {
        "total_alerts":      total,
        "verified_count":    verified,
        "node_count":        nodes,
        "avg_confidence_pct": avg_conf,
    }


@app.get("/api/issues", response_model=List[Issue], summary="Live Feed sự cố")
def get_issues():
    return _issues


@app.get("/api/blockchain", response_model=List[BlockEntry], summary="Sổ cái Blockchain")
def get_blockchain():
    return _ledger


@app.post("/api/report", summary="Gửi báo cáo sự cố từ Edge Node")
def post_report(payload: ReportPayload):
    if payload.type not in ISSUE_TYPES:
        raise HTTPException(status_code=400, detail=f"Loại sự cố không hợp lệ. Chọn: {ISSUE_TYPES}")

    node_id    = payload.nodeId or f"EdgeNode-HN-{random.randint(1, 99):03d}"
    issue_id   = str(uuid.uuid4())[:8]
    ts_iso     = datetime.now(tz=timezone.utc).isoformat()

    # Đồng thuận: tìm các sự cố lân cận cùng loại
    nearby     = _nearby_issues(payload.lat, payload.lng, payload.type)
    count      = len(nearby) + 1
    is_verified = count >= CONSENSUS_THRESHOLD

    new_issue = {
        "id":             issue_id,
        "lat":            round(payload.lat, 6),
        "lng":            round(payload.lng, 6),
        "type":           payload.type,
        "confidence":     payload.confidence,
        "nodeId":         node_id,
        "timestamp":      ts_iso,
        "isVerified":     is_verified,
        "consensusCount": count,
        "imageUrl":       ISSUE_IMAGES.get(payload.type, DEFAULT_IMAGE),
    }
    _issues.insert(0, new_issue)
    if len(_issues) > MAX_ISSUES:
        _issues.pop()

    tx_hash = None
    if is_verified:
        tx_seed = f"{issue_id}-{payload.lat:.5f}-{payload.lng:.5f}"
        tx_hash = _fake_txhash(tx_seed)
        _ledger.insert(0, {
            "slot":          _fake_slot(),
            "metadataLabel": 721,
            "lat":           round(payload.lat, 6),
            "lng":           round(payload.lng, 6),
            "issueType":     payload.type,
            "txHash":        tx_hash,
            "explorerUrl":   f"https://preprod.cardanoscan.io/transaction/{tx_hash}",
        })
        if len(_ledger) > 30:
            _ledger.pop()

    return {
        "success":      True,
        "issueId":      issue_id,
        "isVerified":   is_verified,
        "consensusCount": count,
        "txHash":       tx_hash,
    }


# ─────────────────────────────────────────────
# SERVE STATIC FILES + INDEX.HTML
# ─────────────────────────────────────────────
# Gắn thư mục "static" để phục vụ index.html, style.css, script.js
# Đặt sau các API route để ưu tiên API
import pathlib
STATIC_DIR = pathlib.Path(__file__).parent / "static"

if STATIC_DIR.exists():
    @app.get("/", include_in_schema=False)
    def serve_index():
        return FileResponse(STATIC_DIR / "index.html")

    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


# ─────────────────────────────────────────────
# CHẠY TRỰC TIẾP
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
