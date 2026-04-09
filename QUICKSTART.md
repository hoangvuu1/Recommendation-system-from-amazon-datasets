# 🚀 Quick Start Guide - Recommendation System

Hướng dẫn nhanh để chạy toàn bộ hệ thống trong 5 phút.

## ⚡ TL;DR (30 seconds)

```bash
# 1. Go to web folder
cd web

# 2. Install & Run
pip install -r backend/requirements.txt
python run.py

# 3. Open browser
# http://localhost:8000
```

---

## 📋 Requirements

- Python 3.8+
- pip (Python package manager)
- Modern web browser
- ~2GB disk space (for data files)

---

## 🎯 Step-by-Step Setup

### Step 1: Prepare Dependencies

```bash
# Windows - Create virtual environment
python -m venv venv
venv\Scripts\activate

# Linux/Mac - Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r web/backend/requirements.txt
```

### Step 2: Ensure Data Files Exist

Check these files exist:
- ✅ `Hybrid/final_recommendations.parquet`
- ✅ `Hybrid/popular_items.parquet`
- ✅ `RS-20260405T032136Z-1-001/RS/meta_rs.parquet` (optional but recommended)

If not, run Parts 1-4 notebooks first.

### Step 3: Run Backend Server

**Option A: Simple (Recommended)**
```bash
cd web
python run.py
```

**Option B: Manual**
```bash
cd web/backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Option C: Docker**
```bash
docker-compose up
```

### Step 4: Access Frontend

Open your browser to any of these:

1. **Direct Frontend** (if backend serves static files)
   ```
   http://localhost:8000
   ```

2. **API Docs** (Interactive testing)
   ```
   http://localhost:8000/docs
   ```

3. **Simple HTTP Server** (Terminal 2)
   ```bash
   cd web/frontend
   python -m http.server 8080
   # Then visit: http://localhost:8080
   ```

---

## 🌐 Available Pages

| Page | URL | Purpose |
|------|-----|---------|
| Homepage | `/` | Popular products |
| User Recs | `/recommend.html` | Recommendations for known user |
| Similar | `/similar.html` | Find similar products |
| Cold Start | `/coldstart.html` | New user recommendations |
| API Docs | `/docs` | Interactive API testing |

---

## 🧪 Quick API Test

### Using Browser (Swagger UI)
1. Open `http://localhost:8000/docs`
2. Click on any endpoint
3. Click "Try it out"
4. Fill in parameters
5. Click "Execute"

### Using cURL

```bash
# Popular items
curl http://localhost:8000/recommend/popular?top_k=5

# User recommendations (replace with real user_id)
curl http://localhost:8000/recommend/user/A1234567890?top_k=10

# Similar products (replace with real item_id)
curl http://localhost:8000/recommend/item/B1234567890?top_k=10

# New user recommendations
curl -X POST http://localhost:8000/recommend/new-user \
  -H "Content-Type: application/json" \
  -d '{
    "interactions": [
      {"item_id": "B00000JBLQ", "rating": 5},
      {"item_id": "B00004S7P0", "rating": 4}
    ],
    "top_k": 10
  }'
```

---

## 📊 Architecture Overview

```
┌─────────────────────────────────┐
│   Your Browser (Frontend)        │
│  ○ Popular Products             │
│  ○ User Recommendations         │
│  ○ Similar Products             │
│  ○ Cold Start                   │
└────────────┬────────────────────┘
             │ HTTP Requests
             │ (Fetch API)
             ▼
┌──────────────────────────────────┐
│  FastAPI Backend (port 8000)      │
│  ✓ Load Parquet data              │
│  ✓ Rank recommendations           │
│  ✓ Return JSON responses          │
└────────────┬─────────────────────┘
             │ Read/Transform
             ▼
  ┌──────────────────────────┐
  │  Data Files (Hybrid/)     │
  │  - final_recommendations  │
  │  - popular_items          │
  │  - metadata (optional)    │
  └──────────────────────────┘
```

---

## 🔧 Troubleshooting

### ❌ "ModuleNotFoundError: No module named 'fastapi'"

**Solution:**
```bash
# Make sure you're in correct venv (see activation steps)
pip install -r web/backend/requirements.txt
```

### ❌ "Port 8000 already in use"

**Solution:**
```bash
# Find and kill process on port 8000
# Linux/Mac
lsof -ti:8000 | xargs kill -9

# Windows (PowerShell)
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
```

### ❌ "ParquetException: Could not find file"

**Solution:**
```bash
# Check if data files exist
ls Hybrid/
# Should show:
# - final_recommendations.parquet/
# - popular_items.parquet/

# If not, run Parts 1-4 notebooks first
```

### ❌ Frontend not loading / CORS errors

**Solution:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Use Swagger UI instead
# http://localhost:8000/docs

# Or run separate HTTP server for frontend
cd web/frontend
python -m http.server 8080
# Visit http://localhost:8080
```

---

## 📈 Next Steps

After running successfully:

1. **Test All Endpoints** - Use API docs carefully
2. **Explore Data** - Try different user_ids and item_ids
3. **Read Full Docs** - Check `web/README.md` for details
4. **Deploy** - See `DEPLOYMENT.md` for production setup
5. **Customize** - Modify `web/frontend/style.css` for branding

---

## 📚 Full Documentation

- [Part 5 README](web/README.md) - Complete web guide
- [API Testing Guide](web/API_TESTING.md) - More API examples
- [Deployment Guide](web/DEPLOYMENT.md) - Production setup
- [Structure Doc](web/STRUCTURE.md) - Architecture details
- [Main Project README](README.md) - Overview of all parts

---

## 💡 Tips & Tricks

### Tip 1: Use Real User IDs
You need actual user_id from the database. Check notebooks for available IDs.

### Tip 2: API Documentation
Swagger UI (`/docs`) is your best friend. It:
- Shows all endpoints
- Provides try-it-out interface
- Validates inputs
- Shows response schemas

### Tip 3: Browser Console
- Press F12 to open developer tools
- Check "Network" tab to see API calls
- Check "Console" for JavaScript errors

### Tip 4: Save Results
Copy-paste JSON responses to analyze locally using:
```python
import json
data = json.loads(your_json_string)
print(json.dumps(data, indent=2))
```

---

## 🎓 Learning Path

1. **Start here**: Homepage (`/`) - See popular items
2. **Try API**: `/docs` - Explore all endpoints
3. **Mock user**: `/recommend.html` - Use test user_id
4. **Explore similar**: `/similar.html` - Find related products
5. **New user**: `/coldstart.html` - Cold start scenario
6. **Read code**: Check `backend/main.py` and `frontend/*.html`
7. **Deploy**: Try Docker or cloud deployment

---

## ✅ Verification Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed: `pip list | grep fastapi`
- [ ] Data files exist: `ls Hybrid/`
- [ ] Backend running: `curl http://localhost:8000/health`
- [ ] Frontend accessible: Browser at `http://localhost:8000`
- [ ] API Docs working: `http://localhost:8000/docs`
- [ ] Popular items loading: Check homepage
- [ ] No errors in browser console (F12)

---

## 🆘 Get Help

- **API not responding?** → Check backend terminal for errors
- **CORS errors?** → Backend has CORS enabled, try `/docs` instead
- **Missing data?** → Run Parts 1-4 notebooks to generate data
- **Memory issues?** → Reduce data size or use smaller top_k values
- **Timeout errors?** → Increase timeout in browser network settings

---

**Ready to go!** Start with Step 1 above. 🚀
