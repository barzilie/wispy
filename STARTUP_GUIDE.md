# 🚀 WiSpy Startup Guide

## Quick Start (Easiest)

### Option 1: One-Command Startup (Recommended)
```bash
sudo .venv/bin/python start_wispy.py
```

This automatically starts both Flask and React!

### Option 2: Manual Startup (Two Terminals)

**Terminal 1 - Flask Backend:**
```bash
source .venv/bin/activate
sudo .venv/bin/python web/app.py
```

**Terminal 2 - React Frontend:**
```bash
cd web/frontend
npm start
```

Then open: **http://localhost:3001**

---

## ⚙️ Platform Notes

WiSpy requires Kali Linux with a compatible wireless adapter for scanning and rogue AP deployment. See `INSTALLATION.md` for driver and sudoers setup.

On Kali, the sniffer may need root. If capture stays empty after a client connects, run in a second terminal:

```bash
sudo .venv/bin/python core/sniffer.py
```

Or set `WISPY_SNIFFER_SUDO=true` in `.env` with passwordless sudo configured.

---

## 🛑 Stopping WiSpy

**If using `start_wispy.py`:**
- Press `Ctrl+C` once (stops both servers automatically)

**If using manual startup:**
- Press `Ctrl+C` in each terminal separately

---

## ❓ What About `main.py`?

**`main.py` is the OLD launcher** for the command-line version.

**DO NOT USE `main.py`** with the new React UI!

The new multi-screen app uses:
- `web/app.py` → Flask backend (API server)
- `web/frontend/` → React frontend (UI)

`main.py` was for the original terminal-based version and is **not compatible** with the new UI.

---

## 🔍 Verification

After starting, check that both servers are running:

```bash
# Check Flask backend
curl http://localhost:5000/api/status

# Expected response:
# {"monitoring": false, "scanning": false, ...}

# Check React frontend
# Open browser: http://localhost:3001
# Should see "INITIATE SCAN" screen
```

---

## 🐛 Troubleshooting

### Port Already in Use

**Port 5000 (Flask):**
```bash
lsof -ti:5000 | xargs kill -9
```

**Port 3001 (React):**
```bash
lsof -ti:3001 | xargs kill -9
```

### Virtual Environment Not Found
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### React Dependencies Missing
```bash
cd web/frontend
npm install
cd ../..
```

### Scanner Finds No Networks
Check the wireless driver per `INSTALLATION.md` — `rtl8xxxu` must not be loaded; use `8188eu` for the TL-WN722N.

---

## 📊 Startup Flow

```
start_wispy.py
    ↓
[Check Dependencies]
    ↓
[Start Flask Backend] → http://localhost:5000
    ↓
[Wait 3 seconds]
    ↓
[Start React Frontend] → http://localhost:3001
    ↓
[Open Browser] → http://localhost:3001
    ↓
[See Start Screen with "INITIATE SCAN" button]
```

---

## 📝 Quick Reference

| Command | What It Does |
|---------|--------------|
| `python start_wispy.py` | Start both servers automatically |
| `python web/app.py` | Start Flask backend only |
| `cd web/frontend && npm start` | Start React frontend only |
| `curl localhost:5000/api/status` | Check Flask status |

---

## 🎯 First Time Setup Checklist

- [ ] Clone repository
- [ ] Create virtual environment: `python3 -m venv .venv`
- [ ] Activate venv: `source .venv/bin/activate`
- [ ] Install Python deps: `pip install -r requirements.txt`
- [ ] Install React deps: `cd web/frontend && npm install`
- [ ] Create `.env` file (copy from `.env.example`)
- [ ] Configure wireless driver and sudoers per `INSTALLATION.md`
- [ ] Start app: `python start_wispy.py`
- [ ] Open browser: `http://localhost:3001`

Done! 🎉
