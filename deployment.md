# 🚀 Production Deployment Guide (100% Free Stack)

Since your domain nameservers are managed by **Cloudflare**, your frontend is hosted on **GitHub Pages**, and you want to keep everything free, here is the complete plan to deploy this application.

We will keep the interactive HTML/CSS/JS frontend on **GitHub Pages** (on `uhskaparpurakanti.in`) and host the Python FastAPI backend on **Render.com** (at `arrear-api.uhskaparpurakanti.in`).

---

## 🔹 Part 1: Prepare your GitHub Repository

Your GitHub repository should contain the following folders at the root level:
* `/app` (FastAPI backend modules)
* `/templates` (Excel template folder containing `DPO_Muzaffarpur_Arrear_Forms.xlsx`)
* `/frontend` (HTML/CSS/JS files)
* `requirements.txt` (Python backend dependencies)

---

## 🔹 Part 2: Deploy Backend to Render (Free)

1. Sign up/Log in to [Render.com](https://render.com) using your GitHub account.
2. Click **New +** and select **Web Service**.
3. Connect your GitHub repository.
4. Configure the Web Service settings:
   * **Name**: `bihar-arrear-api` (or any name you like)
   * **Region**: Choose the closest one (e.g., Singapore or Oregon)
   * **Branch**: `main`
   * **Runtime**: `Python`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   * **Instance Type**: **Free** ($0/month)
5. Add an **Environment Variable**:
   * Click the **Environment** tab on Render.
   * Add Key: `PYTHONPATH` and Value: `.` (This ensures python finds the `app` package).
6. Click **Deploy Web Service**. Render will build and deploy your FastAPI app. It will give you a default URL like `https://bihar-arrear-api.onrender.com`.

---

## 🔹 Part 3: Map Subdomain on Cloudflare

We want the backend to be accessible at `https://arrear-api.uhskaparpurakanti.in`.

1. Go to your **Cloudflare Dashboard** and select `uhskaparpurakanti.in`.
2. Click **DNS** -> **Records**.
3. Click **Add Record**:
   * **Type**: `CNAME`
   * **Name**: `arrear-api`
   * **Target**: `your-render-app-name.onrender.com` (copy this from Render's dashboard)
   * **Proxy status**: **DNS Only** (Gray cloud) *[Note: Change it to gray cloud initially so Render can verify and issue the SSL certificate. You can change it back to Proxied/Orange cloud later if you want CDN protection.]*
4. Click **Save**.

---

## 🔹 Part 4: Add Custom Domain in Render

1. On your Render dashboard, select your web service.
2. Go to **Settings** -> Scroll down to **Custom Domains**.
3. Click **Add Custom Domain** and enter:
   `arrear-api.uhskaparpurakanti.in`
4. Click **Save**. Render will verify the CNAME record and automatically issue a free SSL certificate.

---

## 🔹 Part 5: Deploy Frontend to GitHub Pages

1. Go to your GitHub repository settings -> **Pages**.
2. Make sure it is configured to serve your frontend.
   * *If you serve from the root of your repo, you can copy the files inside `/frontend` (`index.html`, `style.css`, `script.js`) to the root of your repository.*
3. Ensure your custom domain `uhskaparpurakanti.in` is configured in GitHub Pages.
4. When you visit `https://uhskaparpurakanti.in`, the frontend JavaScript ([script.js](file:///Volumes/Eternal%20T7/Project%20ARREAR/frontend/script.js#L9-L13)) will automatically detect it is not running on localhost, and will direct all API requests to `https://arrear-api.uhskaparpurakanti.in`!

---

## 💡 Keeping Render Awake (Preventing Spin-down Sleep)
Render's free tier spins down (goes to sleep) after 15 minutes of inactivity.
To keep the server awake 24/7 so that it loads instantly for teachers, you can use a free pinging service:
1. Go to [UptimeRobot.com](https://uptimerobot.com) (which has a free plan).
2. Set up an HTTP monitor to ping:
   `https://arrear-api.uhskaparpurakanti.in/docs`
3. Configure it to ping once every **10 minutes**.
This will keep the Render container awake indefinitely at $0 cost!
