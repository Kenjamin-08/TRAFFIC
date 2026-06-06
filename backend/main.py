"""
AI TRAFFIC UTC — Backend Server
FastAPI + Python | Cardano Preprod Testnet (Blockfrost API)

Routes:
  GET  /api/stats       → Dashboard statistics
  GET  /api/issues      → Live feed of road incidents
  GET  /api/blockchain  → Blockchain ledger entries
  POST /api/report      → Submit a new incident report (from edge node)
"""

import asyncio
import hashlib
import math
import os
import pathlib
import random
import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
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
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# CẤU HÌNH HỆ THỐNG
# ─────────────────────────────────────────────
CONSENSUS_THRESHOLD = 3
COORD_EPSILON       = 0.0005
MAX_ISSUES          = 50

ISSUE_TYPES = ["Ổ gà", "Mặt đường lún", "Ngập nước nhẹ", "Nắp cống hỏng"]

ISSUE_IMAGES = {
    "Ổ gà":           "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Pothole_on_a_road_in_India.jpg/320px-Pothole_on_a_road_in_India.jpg",
    "Mặt đường lún":  "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Road_subsidence.jpg/320px-Road_subsidence.jpg",
    "Ngập nước nhẹ":  "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Urban_flooding.jpg/320px-Urban_flooding.jpg",
    "Nắp cống hỏng":  "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Manhole_cover_broken.jpg/320px-Manhole_cover_broken.jpg",
}
DEFAULT_IMAGE = "https://placehold.co/320x180/f8fafc/94a3b8?text=Su+co+GT"

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
    id: str
    lat: float
    lng: float
    type: str
    confidence: float
    nodeId: str
    timestamp: str
    isVerified: bool
    consensusCount: int
    imageUrl: str


class BlockEntry(BaseModel):
    slot: int
    metadataLabel: int
    lat: float
    lng: float
    issueType: str
    txHash: str
    explorerUrl: str


class ReportPayload(BaseModel):
    lat: float = Field(..., ge=20.5, le=21.5)
    lng: float = Field(..., ge=105.0, le=106.5)
    type: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    nodeId: Optional[str] = None


# ─────────────────────────────────────────────
# BỘ NHỚ ẤO (In-Memory Store)
# ─────────────────────────────────────────────
_issues = []   # type: List[dict]
_ledger = []   # type: List[dict]
_initialized = False


# ─────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────
def _fake_txhash(seed):
    # type: (str) -> str
    return hashlib.sha256(seed.encode()).hexdigest() + hashlib.md5(seed.encode()).hexdigest()


def _fake_slot():
    # type: () -> int
    return int(time.time()) - 1_700_000_000 + random.randint(-3600, 0)


def _nearby_issues(lat, lng, issue_type):
    # type: (float, float, str) -> List[dict]
    return [
        iss for iss in _issues
        if iss["type"] == issue_type
        and abs(iss["lat"] - lat) < COORD_EPSILON
        and abs(iss["lng"] - lng) < COORD_EPSILON
    ]


# ─────────────────────────────────────────────
# SEED DATA
# ─────────────────────────────────────────────
def _seed_initial_data():
    global _initialized
    if _initialized:
        return
    _initialized = True

    now_ts = time.time()
    node_pool = ["EdgeNode-HN-{:03d}".format(i) for i in range(1, 20)]

    for idx, (base_lat, base_lng, _district) in enumerate(SEED_LOCATIONS):
        for j in range(random.randint(2, 4)):
            issue_type  = random.choice(ISSUE_TYPES)
            lat         = base_lat + random.uniform(-0.003, 0.003)
            lng         = base_lng + random.uniform(-0.003, 0.003)
            confidence  = round(random.uniform(0.62, 0.98), 3)
            node_id     = random.choice(node_pool)
            offset_secs = random.randint(0, 7200)
            ts_iso      = datetime.fromtimestamp(now_ts - offset_secs, tz=timezone.utc).isoformat()
            issue_id    = str(uuid.uuid4())[:8]
            count       = random.randint(1, 5)
            is_verified = count >= CONSENSUS_THRESHOLD

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

            if is_verified:
                tx_seed = "{}-{:.5f}-{:.5f}".format(issue_id, lat, lng)
                tx_hash = _fake_txhash(tx_seed)
                _ledger.append({
                    "slot":          _fake_slot() - offset_secs,
                    "metadataLabel": 721,
                    "lat":           round(lat, 6),
                    "lng":           round(lng, 6),
                    "issueType":     issue_type,
                    "txHash":        tx_hash,
                    "explorerUrl":   "https://preprod.cardanoscan.io/transaction/{}".format(tx_hash),
                })

    _issues.sort(key=lambda x: x["timestamp"], reverse=True)
    _ledger.sort(key=lambda x: x["slot"], reverse=True)


# ─────────────────────────────────────────────
# SIMULATION
# ─────────────────────────────────────────────
async def _auto_simulate():
    node_pool = ["EdgeNode-HN-{:03d}".format(i) for i in range(1, 20)]
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

        if len(_issues) > MAX_ISSUES:
            _issues.pop()

        if is_verified:
            tx_seed = "{}-{:.5f}-{:.5f}".format(issue_id, lat, lng)
            tx_hash = _fake_txhash(tx_seed)
            _ledger.insert(0, {
                "slot":          _fake_slot(),
                "metadataLabel": 721,
                "lat":           round(lat, 6),
                "lng":           round(lng, 6),
                "issueType":     issue_type,
                "txHash":        tx_hash,
                "explorerUrl":   "https://preprod.cardanoscan.io/transaction/{}".format(tx_hash),
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
    total    = len(_issues)
    verified = sum(1 for i in _issues if i["isVerified"])
    nodes    = len(set(i["nodeId"] for i in _issues))
    avg_conf = (
        round(sum(i["confidence"] for i in _issues) / total * 100)
        if total > 0 else 0
    )
    return {
        "total_alerts":       total,
        "verified_count":     verified,
        "node_count":         nodes,
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
        raise HTTPException(
            status_code=400,
            detail="Loại sự cố không hợp lệ. Chọn: {}".format(ISSUE_TYPES),
        )

    node_id     = payload.nodeId or "EdgeNode-HN-{:03d}".format(random.randint(1, 99))
    issue_id    = str(uuid.uuid4())[:8]
    ts_iso      = datetime.now(tz=timezone.utc).isoformat()
    nearby      = _nearby_issues(payload.lat, payload.lng, payload.type)
    count       = len(nearby) + 1
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
        tx_seed = "{}-{:.5f}-{:.5f}".format(issue_id, payload.lat, payload.lng)
        tx_hash = _fake_txhash(tx_seed)
        _ledger.insert(0, {
            "slot":          _fake_slot(),
            "metadataLabel": 721,
            "lat":           round(payload.lat, 6),
            "lng":           round(payload.lng, 6),
            "issueType":     payload.type,
            "txHash":        tx_hash,
            "explorerUrl":   "https://preprod.cardanoscan.io/transaction/{}".format(tx_hash),
        })
        if len(_ledger) > 30:
            _ledger.pop()

    return {
        "success":        True,
        "issueId":        issue_id,
        "isVerified":     is_verified,
        "consensusCount": count,
        "txHash":         tx_hash,
    }


# ─────────────────────────────────────────────
# SERVE STATIC FILES + INDEX.HTML
# ─────────────────────────────────────────────
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