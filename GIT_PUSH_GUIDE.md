# How to Push to GitHub

## ✅ Your Commit is Ready!

Your changes are committed locally. Now you need to push to GitHub.

## 🔐 Authentication Required

GitHub requires authentication. You have two options:

### Option 1: Personal Access Token (Recommended)

1. **Generate a token:**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Give it a name: "WiSpy Development"
   - Select scopes: ✅ `repo` (full control of private repositories)
   - Click "Generate token"
   - **Copy the token** (you won't see it again!)

2. **Push with token:**
   ```bash
   git push https://YOUR_TOKEN@github.com/barzilie/wispy.git main
   ```

3. **Or cache credentials:**
   ```bash
   git config credential.helper store
   git push origin main
   # Enter username: barzilie
   # Enter password: YOUR_TOKEN
   ```

### Option 2: SSH Key

1. **Generate SSH key:**
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   # Press Enter to accept default location
   # Add passphrase (optional)
   ```

2. **Add to GitHub:**
   ```bash
   cat ~/.ssh/id_ed25519.pub
   # Copy the output
   ```
   - Go to: https://github.com/settings/keys
   - Click "New SSH key"
   - Paste your public key
   - Click "Add SSH key"

3. **Change remote to SSH:**
   ```bash
   git remote set-url origin git@github.com:barzilie/wispy.git
   git push origin main
   ```

## 📊 What You're Pushing

**60 files changed, 3799 insertions**

**New Files:**
- ✅ All React frontend code
- ✅ Mock data system
- ✅ Configuration files
- ✅ Documentation (7 markdown files)
- ✅ Launcher scripts

**Ignored (NOT pushed):**
- ❌ `node_modules/` (React dependencies - too large)
- ❌ `.venv/` (Python virtual environment)
- ❌ `data/wispy.db` (Database with local data)
- ❌ `.env` (Contains API keys)

## 🎯 After Pushing

Once pushed, anyone can clone and run:

```bash
# Clone
git clone https://github.com/barzilie/wispy.git
cd wispy

# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd web/frontend && npm install && cd ../..

# Generate mock data
python mock_data.py

# Run
python start_wispy.py
```

## ⚠️ Important Notes

1. **`.env` file is ignored** - Create a `.env.example` if you want to share config template
2. **Database is ignored** - Others will need to run `python mock_data.py`
3. **node_modules is ignored** - Others will run `npm install` to get dependencies
4. **Virtual env is ignored** - Others will create their own with `python3 -m venv .venv`

## 🚀 Quick Push Command

After setting up authentication:

```bash
git push origin main
```

That's it! Your code will be on GitHub.
