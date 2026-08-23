# ParcelPilot AI — Deployment & Shareable Link Guide

This guide outlines practical, free, and robust ways to deploy ParcelPilot AI to generate a **publicly shareable live link** that evaluators, stakeholders, and team members can test immediately.

---

## 📊 Deployment Options Summary

| Method | Platform / Tool | Cost | Setup Time | Public URL Format | Best For |
|---|---|---|---|---|---|
| **Option 1 (Recommended Cloud)** | **[Render.com](https://render.com)** | **100% Free** | ~5 mins | `https://parcelpilot-ai.onrender.com` | Permanent cloud hosting with automatic GitHub deployments (Python native) |
| **Option 2 (Instant Local Tunnel)** | **[Cloudflare Tunnel / Localtunnel](https://localtunnel.github.io)** | **100% Free** | **30 seconds** | `https://*.trycloudflare.com` or `*.loca.lt` | Instant demo link straight from your local running machine (Zero cloud setup) |
| **Option 3 (Free Cloud AI Container)** | **[Koyeb.com](https://koyeb.com)** | **100% Free Eco Tier** | ~3 mins | `https://parcelpilot-ai.koyeb.app` | Global edge hosting with native git & Docker deployment |
| **Option 4 (Hugging Face Free Tier)** | **[Hugging Face Spaces (Gradio/FastAPI)](https://huggingface.co/spaces)** | **100% Free** (16GB RAM) | ~3 mins | `https://hf.space/spaces/user/parcelpilot-ai` | Fast Python AI hosting on free 16GB RAM tier using Gradio SDK mount |

---

## 🚀 Option 1: Render.com (100% Free Cloud Web Service — Recommended)

Render provides free native Python web service hosting without requiring Docker or a credit card.

### Step-by-Step Instructions:

1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "feat: complete ParcelPilot AI platform"
   git remote add origin https://github.com/YOUR_USERNAME/ParcelPilot_Chatbot.git
   git push -u origin main
   ```

2. **Create a Free Web Service on Render**:
   - Go to [dashboard.render.com](https://dashboard.render.com) and click **New +** $\rightarrow$ **Web Service**.
   - Connect your GitHub repository.

3. **Configure Settings**:
   - **Name**: `parcelpilot-ai`
   - **Region**: Singapore, Frankfurt, or Oregon
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && python -m backend.db.seed && python backend/rag/indexer.py
     ```
   - **Start Command**:
     ```bash
     uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type**: `Free` ($0/month)

4. **Set Environment Variables**:
   In the **Environment** tab on Render, add:
   - `LLM_PROVIDER` = `groq` (or `gemini`)
   - `GROQ_API_KEY` = `your_groq_api_key`
   - `GROQ_MODEL` = `openai/gpt-oss-120b` (or `llama-3.3-70b-versatile`)
   - `GEMINI_API_KEY` = `your_gemini_api_key`
   - `GEMINI_MODEL` = `gemini-3.7-flash`

5. **Deploy**:
   - Click **Create Web Service**.
   - Your live shareable link will be: **`https://parcelpilot-ai.onrender.com`**

---

## ⚡ Option 2: Instant Public Tunnel (Zero Cloud Setup / 30-Second Link)

If you already have ParcelPilot running locally on your computer and need a **quick, shareable HTTPS link** for evaluators to test immediately:

### Method A: Using Cloudflare Tunnel (No Account Required)
1. Ensure the server is running locally:
   ```bash
   python run_server.py
   ```
2. In a separate terminal, run:
   ```bash
   # On Windows (via winget or direct download)
   winget install Cloudflare.cloudflared
   cloudflared tunnel --url http://localhost:8000
   ```
3. Cloudflare will output an instant HTTPS link (e.g., `https://random-words.trycloudflare.com`). Share this URL!

### Method B: Using Localtunnel (via Node/NPX)
1. Ensure your local server is running on port 8000.
2. In another terminal, run:
   ```bash
   npx localtunnel --port 8000
   ```
3. It will give you a public URL like `https://sweet-badger-42.loca.lt`.

---

## 🌐 Option 3: Koyeb (100% Free Eco Tier Cloud Hosting)

Koyeb offers a free Eco tier for web services deployed directly from GitHub with automatic global edge routing and SSL.

### Step-by-Step Instructions:

1. Go to [app.koyeb.com](https://app.koyeb.com) and click **Create Service** $\rightarrow$ **GitHub**.
2. Select your `ParcelPilot_Chatbot` repository.
3. **Builder**: Select **Buildpack** (or **Dockerfile**).
4. **Environment Variables**:
   - `PORT` = `8000`
   - `LLM_PROVIDER` = `groq`
   - `GROQ_API_KEY` = `your_groq_key`
   - `GEMINI_API_KEY` = `your_gemini_key`
5. Click **Deploy**. Your service will be live at `https://<app-name>.koyeb.app`.

---

## 🤗 Option 4: Hugging Face Spaces (Free Gradio SDK with FastAPI Mount)

Hugging Face Spaces offers a **100% free tier (16GB RAM / 2 vCPUs)** when using the **Gradio** SDK (Docker is paid/restricted, but Gradio is completely free).

### How to Deploy on Free Gradio Space:

1. Create a Space on [huggingface.co/spaces](https://huggingface.co/spaces):
   - **Space Name**: `parcelpilot-ai`
   - **SDK**: Select **Gradio** (Free 16GB RAM tier).
2. Create an `app.py` in the Space root that mounts our FastAPI application:
   ```python
   import gradio as gr
   from backend.api.main import app
   
   # Mount the full FastAPI dashboard inside Gradio
   demo = gr.mount_gradio_app(app, gr.Blocks(), path="/")
   
   if __name__ == "__main__":
       import uvicorn
       uvicorn.run(app, host="0.0.0.0", port=7860)
   ```
3. Add `GROQ_API_KEY` and `GEMINI_API_KEY` under Space **Settings** $\rightarrow$ **Variables and secrets**.
4. Your Space is live at: `https://huggingface.co/spaces/YOUR_USERNAME/parcelpilot-ai`

---

## 🔒 Security & Environment Secrets Checklist

When deploying to any public platform, ensure:
1. `.env` is listed in [`.gitignore`](file:///c:/Users/krish/OneDrive/Documents/Projects/ParcelPilot_Chatbot/.gitignore) so API keys are never leaked to public git history.
2. All API keys (`GROQ_API_KEY`, `GEMINI_API_KEY`) are set via platform secret managers or dashboard environment variables.
3. CORS middleware in [`backend/api/main.py`](file:///c:/Users/krish/OneDrive/Documents/Projects/ParcelPilot_Chatbot/backend/api/main.py) is already enabled for seamless web access.

---

## 🧪 Post-Deployment Verification (Smoke Test)

After deploying, verify the live link with these quick checks:

1. **Health Check**:
   - Navigate to `https://YOUR_DEPLOYED_URL/api/health`
   - Expected JSON output:
     ```json
     {
       "status": "healthy",
       "service": "ParcelPilot AI",
       "llm_provider": "groq",
       "groq_configured": true,
       "gemini_configured": true,
       "active_model": "openai/gpt-oss-120b"
     }
     ```
2. **Customer Persona Test**:
   - Select **Northstar Logistics** in the UI dropdown.
   - Enter: `"can I cancel order 1001?"`
   - Verify that the fee is computed as ₹0.00 (waived under Agreement Clause 2) and the proposal card is displayed.
3. **Internal Persona Test**:
   - Select **ParcelPilot Support Desk** in the UI dropdown.
   - Enter: `"Evaluate SLA status for ticket TKT-501"`
   - Verify that the P1 15-minute SLA breach calculation is displayed with escalation telemetry.
