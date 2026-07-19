# Deploying the live web app

The interactive dashboard (`app.py`) is a **Streamlit** app. The easiest free
way to host it publicly is **Streamlit Community Cloud**, which deploys straight
from this GitHub repo.

## Option A — Streamlit Community Cloud (recommended, free)

1. Go to **https://share.streamlit.io** and click **“Sign in with GitHub”**
   (use the same account, `DEVANGDIXIT04`). Authorize Streamlit when asked.
2. Click **“Create app”** → **“Deploy a public app from GitHub”**.
3. Fill the form:
   - **Repository:** `DEVANGDIXIT04/network-performance-analyzer`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL (optional):** pick a subdomain, e.g. `network-performance-analyzer`
     → your live link becomes
     `https://network-performance-analyzer.streamlit.app`
4. Click **Deploy**. First build takes ~2–3 minutes while it installs
   `requirements.txt`. After that the app is live at the URL above — share it
   with anyone, no install needed.

Whenever you `git push` to `main`, the live app auto-updates.

## Option B — Hugging Face Spaces (alternative)

1. Create a Space at **https://huggingface.co/new-space**, SDK = **Streamlit**.
2. Push this repo’s files into the Space (or connect the GitHub repo).
3. It builds and hosts automatically at `https://huggingface.co/spaces/<you>/<space>`.

## Notes
- `app.py` renders all graphs in-memory (no file writes), so it runs cleanly on
  a read-only cloud host.
- `.streamlit/config.toml` sets the theme; `requirements.txt` lists all
  dependencies the host installs automatically.
- Nothing secret is needed — no API keys, no `secrets.toml`.
