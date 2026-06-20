# How to Start WiSpy

## Just Run This:

```bash
sudo .venv/bin/python start_wispy.py
```

Then open: **http://localhost:3000**

---

## What Gets Started:

1. **Flask Backend** (API server) → Port 5000
2. **React Frontend** (UI) → Port 3001

---

---

## First Time Setup:

```bash
# 1. Install Python dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Install React dependencies
cd web/frontend
npm install
cd ../..

# 3. Configure environment
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY, WIFI_INTERFACE, etc.

# 4. Start the app
sudo .venv/bin/python start_wispy.py
```

---
