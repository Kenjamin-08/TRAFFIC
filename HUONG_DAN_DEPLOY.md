# 🚀 HƯỚNG DẪN TRIỂN KHAI — AI TRAFFIC UTC

> Toàn bộ hệ thống gồm **1 file duy nhất**: `ai_traffic_utc.py`  
> Frontend (HTML/CSS/JS) đã được nhúng bên trong — không cần build, không cần CDN riêng.

---

## 📁 CẤU TRÚC FILE

```
📦 Bạn cần:
├── ai_traffic_utc.py          ← File all-in-one (chạy cái này là xong)
│
📦 Hoặc nếu muốn cấu trúc tách biệt (dễ sửa FE hơn):
├── backend/
│   ├── main.py                ← FastAPI backend
│   ├── requirements.txt       ← Danh sách thư viện
│   └── static/
│       ├── index.html
│       ├── style.css
│       ├── script.js
│       └── utc-logo.png
```

---

## ⚡ CÁCH 1: CHẠY LOCAL (Máy tính cá nhân)

### Bước 1 — Cài Python (nếu chưa có)
```bash
# Kiểm tra phiên bản (cần ≥ 3.9)
python3 --version

# Nếu chưa có: tải tại https://python.org/downloads
```

### Bước 2 — Cài thư viện
```bash
pip install fastapi uvicorn pydantic
```

### Bước 3 — Chạy server
```bash
python3 ai_traffic_utc.py
```

### Bước 4 — Mở trình duyệt
```
http://localhost:8000
```

> 🟢 Web tự động cập nhật mỗi 5 giây — **không cần làm gì thêm**.

---

## ☁️ CÁCH 2: DEPLOY LÊN RENDER.COM (FREE — khuyến nghị)

**Render** cho phép chạy Python server miễn phí, có HTTPS, tên miền `.onrender.com`.

### Bước 1 — Đẩy code lên GitHub
```bash
# Tạo repo mới trên github.com, sau đó:
git init
git add ai_traffic_utc.py requirements.txt
git commit -m "Initial deploy"
git remote add origin https://github.com/YOUR_USERNAME/ai-traffic-utc.git
git push -u origin main
```

Tạo file `requirements.txt`:
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
pydantic==2.7.1
```

### Bước 2 — Tạo Web Service trên Render
1. Vào **https://render.com** → Đăng ký miễn phí
2. Click **"New +"** → **"Web Service"**
3. Connect GitHub repo vừa tạo
4. Điền thông tin:

| Trường | Giá trị |
|--------|---------|
| **Name** | `ai-traffic-utc` |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn ai_traffic_utc:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | `Free` |

5. Click **"Create Web Service"**
6. Chờ ~2 phút → URL dạng `https://ai-traffic-utc.onrender.com` ✅

> ⚠️ **Lưu ý Render Free**: Server ngủ sau 15 phút không có request. Lần đầu truy cập sau khi ngủ mất ~30 giây để khởi động lại.

---

## ☁️ CÁCH 3: DEPLOY LÊN RAILWAY.APP (FREE — nhanh hơn)

**Railway** không có giới hạn sleep, free $5/tháng credit (đủ cho ~500h).

### Bước 1 — Chuẩn bị
Tạo file `Procfile` (không có đuôi):
```
web: uvicorn ai_traffic_utc:app --host 0.0.0.0 --port $PORT
```

### Bước 2 — Deploy
1. Vào **https://railway.app** → Đăng nhập bằng GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Chọn repo → Railway tự detect Python và deploy
4. Lấy domain: **Settings** → **Domains** → **"Generate Domain"**

---

## ☁️ CÁCH 4: DEPLOY LÊN KOYEB (FREE — không sleep)

1. Vào **https://koyeb.com** → Đăng ký miễn phí
2. **"Create App"** → **"GitHub"** → chọn repo
3. **Run command**: `uvicorn ai_traffic_utc:app --host 0.0.0.0 --port 8000`
4. **Port**: `8000`
5. Deploy → Nhận URL `.koyeb.app`

---

## 🖥️ CÁCH 5: DEPLOY LÊN VPS / SERVER RIÊNG

### Dùng systemd (chạy nền, tự khởi động khi reboot)

```bash
# 1. Upload file lên server
scp ai_traffic_utc.py requirements.txt user@your-server:/opt/ai-traffic/

# 2. SSH vào server
ssh user@your-server

# 3. Cài thư viện
cd /opt/ai-traffic
pip3 install -r requirements.txt

# 4. Tạo service
sudo nano /etc/systemd/system/ai-traffic.service
```

Nội dung file service:
```ini
[Unit]
Description=AI Traffic UTC Server
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/ai-traffic
ExecStart=/usr/bin/python3 -m uvicorn ai_traffic_utc:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# 5. Kích hoạt và chạy
sudo systemctl daemon-reload
sudo systemctl enable ai-traffic
sudo systemctl start ai-traffic

# Kiểm tra trạng thái
sudo systemctl status ai-traffic
```

---

## 🔌 API ENDPOINTS (tài liệu kỹ thuật)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `GET` | `/` | Giao diện web chính |
| `GET` | `/api/stats` | Thống kê dashboard |
| `GET` | `/api/issues` | Danh sách sự cố (live feed) |
| `GET` | `/api/blockchain` | Sổ cái blockchain |
| `POST` | `/api/report` | Gửi báo cáo từ edge node |
| `GET` | `/docs` | Swagger UI — thử API trực tiếp |

### Ví dụ gửi báo cáo từ Edge Node (curl):
```bash
curl -X POST https://your-domain/api/report \
  -H "Content-Type: application/json" \
  -d '{"lat": 21.0285, "lng": 105.8542, "type": "Ổ gà", "confidence": 0.92, "nodeId": "EdgeNode-HN-001"}'
```

### Ví dụ gửi báo cáo bằng Python:
```python
import requests

requests.post("https://your-domain/api/report", json={
    "lat": 21.0285,
    "lng": 105.8542,
    "type": "Ổ gà",          # hoặc: "Mặt đường lún", "Ngập nước nhẹ", "Nắp cống hỏng"
    "confidence": 0.92,
    "nodeId": "EdgeNode-HN-001"
})
```

---

## 🔧 BIẾN MÔI TRƯỜNG (tuỳ chọn)

| Biến | Mặc định | Mô tả |
|------|----------|-------|
| `PORT` | `8000` | Cổng server (Render/Railway tự set) |
| `BLOCKFROST_KEY` | _(trống)_ | API key Blockfrost cho blockchain thật |

---

## ❓ XỬ LÝ LỖI THƯỜNG GẶP

**Lỗi: `ModuleNotFoundError: No module named 'fastapi'`**
```bash
pip install fastapi uvicorn pydantic
# Hoặc nếu dùng pip3:
pip3 install fastapi uvicorn pydantic
```

**Lỗi: `Address already in use` (cổng 8000 bị chiếm)**
```bash
python3 ai_traffic_utc.py  # Đổi port trong file, dòng cuối: port=8001
```

**Web không cập nhật dữ liệu:**
- Mở DevTools (F12) → Console → kiểm tra lỗi fetch
- Đảm bảo server đang chạy tại đúng URL

---

*© 2026 Nhóm Nghiên Cứu AI & Blockchain — Trường Đại học Giao thông Vận tải (UTC)*
