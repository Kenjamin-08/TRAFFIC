# AI TRAFFIC UTC 🚦

## Chạy local:
```bash
pip install fastapi uvicorn pydantic
python3 ai_traffic_utc.py
```
→ Mở http://localhost:8000

## Nếu muốn mở file HTML riêng bằng VS Code Live Server:
- Chạy `python3 ai_traffic_utc.py` trước (port 8000)
- Mở `backend/static/index.html` bằng Live Server
- script.js tự động nhận diện và gọi đúng backend port 8000

## Deploy Render.com (miễn phí):
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn ai_traffic_utc:app --host 0.0.0.0 --port $PORT`
