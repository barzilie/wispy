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

- **DO NOT use `main.py`** - That's the old CLI version
- **Use `start_wispy.py`** - The new launcher
- You need **both** Flask and React running
- Requires Kali Linux with a compatible wireless adapter — see `INSTALLATION.md`

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
python start_wispy.py
```

---

## That's It!

See `STARTUP_GUIDE.md` for detailed instructions.
