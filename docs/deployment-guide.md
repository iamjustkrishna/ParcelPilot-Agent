# 🚀 ParcelPilot AI — Production Deployment Guide (Render.com & Live Links)

This guide provides the exact, tested steps to deploy ParcelPilot AI on **Render.com** (100% Free) to obtain a permanent, publicly shareable HTTPS link.

---

## 📊 Deployment Summary

| Method | Platform | Cost | Build Time | Public URL | Notes |
|---|---|---|---|---|---|
| **Primary (Cloud Hosting)** | **[Render.com](https://render.com)** | **100% Free** | ~3–4 mins | `https://parcelpilot-ai.onrender.com` | Permanent cloud hosting, auto-deploys on `git push` |
| **Instant Alternative (Zero Setup)** | **Cloudflare Tunnel / Localtunnel** | **100% Free** | **30 seconds** | `https://*.trycloudflare.com` | Instant demo link from your running local instance |

---

## 🌐 Deploying to Render.com (Step-by-Step)

Render provides free native Python web service hosting without requiring a credit card or paid Docker tiers.

### Step 1: Push Code to GitHub

Ensure all files (including `requirements.txt`, `render.yaml`, and `runtime.txt`) are committed to your GitHub repository:

```bash
git add .
git commit -m "feat: configure production deployment for Render.com"
git push -u origin main
```

---

### Step 2: Create Web Service on Render

1. Log in to [dashboard.render.com](https://dashboard.render.com).
2. Click the **New +** button at the top and select **Web Service**.
3. Under **Connect a repository**, select your `ParcelPilot-AI` repository.

---

### Step 3: Configure Service Parameters

Fill in the settings as follows:

* **Name**: `parcelpilot-ai` (determines your URL, e.g. `https://parcelpilot-ai.onrender.com`)
* **Region**: `Singapore` / `Frankfurt` / `Oregon` (choose the region closest to you)
* **Branch**: `main`
* **Runtime**: `Python 3`
* **Build Command**:
  ```bash
  pip install -r requirements.txt && python -m backend.db.seed && python backend/rag/ingest.py
  ```
* **Start Command**:
  ```bash
  uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT
  ```
* **Instance Type**: **Free** ($0 / month)

---

### Step 4: Add Environment Variables

Click the **Environment** tab in Render and add the following keys:

| Key | Value | Description |
|---|---|---|
| `LLM_PROVIDER` | `groq` | Primary LLM provider |
| `GROQ_API_KEY` | `gsk_...` | Your Groq API key |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Model name |
| `GEMINI_API_KEY` | `AIzaSy...` | Your Gemini API key (fallback) |
| `GEMINI_MODEL` | `gemini-3.7-flash` | Fallback model name |
| `PYTHON_VERSION` | `3.11.9` | Python runtime version |

---

### Step 5: Deploy & Verify

1. Click **Create Web Service**.
2. Render will automatically:
   - Install Python dependencies from `requirements.txt`.
   - Seed the SQLite database (`parcelpilot.db`).
   - Ingest PDFs and build the ChromaDB vector embeddings.
   - Start the FastAPI backend and serve the static dashboard UI.
3. Once the build status turns green (**Live**), click your public URL (e.g. `https://parcelpilot-ai.onrender.com`).

---

## ⚡ Instant Alternative: Shareable Link in 30 Seconds (Cloudflare Tunnel)

If you have ParcelPilot running locally on your machine and want to share a live HTTPS link with someone immediately:

1. **Start the local server**:
   ```bash
   python run_server.py
   ```
2. **In a second terminal, start the tunnel**:
   ```bash
   # Using Cloudflare Tunnel (no signup needed)
   cloudflared tunnel --url http://localhost:8000
   
   # OR using Localtunnel (via Node/NPX)
   npx localtunnel --port 8000
   ```
3. Copy and share the generated HTTPS link (`https://*.trycloudflare.com` or `https://*.loca.lt`).

---

## 🧪 Smoke Test Checklist for Your Deployed URL

After deploying, verify that your live instance is fully operational:

1. **Health API**: Open `https://YOUR-APP.onrender.com/api/health`
   - Should return `{"status": "healthy", "service": "ParcelPilot AI", ...}`
2. **Customer Persona (Northstar)**:
   - Ask: `"Can I cancel order 1001?"`
   - Verify fee is waived to ₹0.00 under Northstar Agreement Clause 2 and proposal card appears.
3. **Internal Persona (Support)**:
   - Switch persona to **ParcelPilot Support Desk**.
   - Ask: `"Evaluate SLA for ticket TKT-501"`
   - Verify P1 SLA calculation and 15-minute breach diagnosis.
