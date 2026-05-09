# 🚀 How to Start WiSpy

## TL;DR - Just Run This:

```bash
python start_wispy.py
```

Then open: **http://localhost:3001**

---

## What Gets Started:

1. **Flask Backend** (API server) → Port 5000
2. **React Frontend** (UI) → Port 3001

---

## ⚠️ Important Notes:

- **DO NOT use `main.py`** - That's the old version
- **Use `start_wispy.py`** - The new launcher
- You need **both** Flask and React running
- Mock mode is automatic on macOS

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

# 3. Generate mock data
python mock_data.py

# 4. Start the app
python start_wispy.py
```

---

## That's It!

See `STARTUP_GUIDE.md` for detailed instructions.
