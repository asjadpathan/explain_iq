# 🚀 Deploying Explain IQ Studio to Vercel

The **Explain IQ Studio** frontend is engineered for instantaneous, zero-build deployment to **Vercel**.

---

## ⚡ Option 1: Direct Vercel CLI Deployment (Fastest)

1. Open your terminal in the `frontend` folder:
   ```bash
   cd frontend
   npx vercel
   ```
2. Follow the 2-step prompt (select your Vercel team/account and accept defaults).
3. Vercel will immediately deploy the static studio application and output your production URL (e.g. `https://explain-iq-studio.vercel.app`).

---

## 🌐 Option 2: Deploy from GitHub / Git Repository

1. Push your repository to GitHub.
2. In the [Vercel Dashboard](https://vercel.com/new), import your `explain_iq` repository.
3. In the project configuration:
   - **Framework Preset**: `Other`
   - **Root Directory**: `frontend` (or leave as root `/` — root `vercel.json` will automatically route to `frontend`)
   - **Build Command**: Leave empty (no build step needed)
   - **Output Directory**: Leave empty
4. Click **Deploy**.

---

## 🔗 Connecting Your Vercel Frontend to Your Backend

Because the frontend is running on Vercel (`https://your-app.vercel.app`) and your FastAPI backend may be running on a cloud host (Render, Railway, Fly.io, or VPS):

1. Open your deployed Vercel site.
2. Click the ⚙️ **Settings icon** in the top navigation bar.
3. Enter your backend URL (e.g., `https://explain-iq-api.onrender.com` or your live API server).
4. Click **Test Connection** to verify green latency ping.
5. Click **Save & Apply** — this persists in `localStorage` so all generation jobs, polling, and video streaming will route to your live backend server seamlessly.

> [!NOTE]
> FastAPI is already configured with permissive CORS headers (`allow_origins=["*"]`) in `main.py`, allowing your Vercel domain to communicate with your backend without cross-origin blocks.
