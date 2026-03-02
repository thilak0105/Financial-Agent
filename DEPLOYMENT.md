# FinSight Deployment Guide

## 🚀 Quick Start: How to Deploy Your App

Your app is now configured for deployment! Follow these steps:

---

## 📋 Prerequisites
- ✅ GitHub account (done - your code is at: https://github.com/thilak0105/Financial-Agent.git)
- Render account (free) - [Sign up here](https://render.com)
- Vercel account (free) - [Sign up here](https://vercel.com)

---

## 🎯 Deployment Steps

### Step 1: Deploy Backend on Render (5 minutes)

1. **Go to Render**: https://render.com
2. **Click "New +" → "Web Service"**
3. **Connect your GitHub** repository: `thilak0105/Financial-Agent`
4. **Configure the service**:
   - **Name**: `finsight-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`

5. **Add Environment Variables** (click "Add Environment Variable"):
   ```
   GEMINI_API_KEY=your_gemini_key
   GROQ_API_KEY=your_groq_key
   OPENAI_API_KEY=your_openai_key
   ALPACA_API_KEY=your_alpaca_key
   ALPACA_SECRET_KEY=your_alpaca_secret
   NEWS_API_KEY=your_news_key
   FRONTEND_URL=https://your-app.vercel.app
   ```
   *(You'll update FRONTEND_URL after Step 2)*

6. **Click "Create Web Service"**
7. **Wait 3-5 minutes** for deployment
8. **Copy your backend URL**: `https://finsight-backend-xxxx.onrender.com`

---

### Step 2: Deploy Frontend on Vercel (3 minutes)

1. **Go to Vercel**: https://vercel.com
2. **Click "Add New" → "Project"**
3. **Import your GitHub repository**: `thilak0105/Financial-Agent`
4. **Configure the project**:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

5. **Add Environment Variable**:
   ```
   VITE_API_URL=https://finsight-backend-xxxx.onrender.com
   ```
   *(Use the URL from Step 1)*

6. **Click "Deploy"**
7. **Wait 2-3 minutes** for deployment
8. **Your app is live!** 🎉

---

### Step 3: Update Backend CORS (1 minute)

1. Go back to **Render Dashboard**
2. Select your `finsight-backend` service
3. Go to **Environment** tab
4. Update `FRONTEND_URL` with your Vercel URL: `https://your-app.vercel.app`
5. Save and wait for automatic redeploy

---

## ✅ Verify Deployment

Visit your Vercel URL and:
- Check if the app loads
- Try asking the AI a question (e.g., "What's the stock price of AAPL?")
- If there's an error, check the browser console (F12)

---

## 🔄 Future Updates

When you make changes to your code:

```bash
# In your finsight folder
git add .
git commit -m "Your update message"
git push origin main
```

**Both Render and Vercel will auto-deploy** your changes! 🚀

---

## 🐛 Troubleshooting

### Backend doesn't start:
- Check Render logs for errors
- Verify all environment variables are set correctly
- Ensure your API keys are valid

### Frontend can't connect to backend:
- Check `VITE_API_URL` in Vercel environment variables
- Verify backend is running (visit backend URL)
- Check CORS is allowing your Vercel domain

### "Module not found" errors:
- Make sure `requirements.txt` has all dependencies
- Try manual deployment on Render

---

## 📊 Architecture

```
User Browser
     ↓
Vercel (Frontend)
     ↓
Render (Backend API)
     ↓
External APIs (Stock, News, AI)
```

---

## 💰 Cost Estimate

- **Render Free Tier**: $0/month (backend may sleep after 15 min inactivity)
- **Vercel Free Tier**: $0/month
- **Total**: **$FREE** 🎉

**Note**: Render free tier has 750 hours/month. For 24/7 uptime, upgrade to paid plan ($7/month).

---

## 📝 Important Files

- `render.yaml` - Backend deployment config for Render
- `vercel.json` - Frontend deployment config for Vercel
- `Procfile` - Alternative deployment config (Railway, Heroku)
- `.gitignore` - Files to exclude from Git

---

## 🎓 Optional: Alternative Platforms

### Backend alternatives:
- **Railway** ($5 free credit): https://railway.app
- **Fly.io** (Free tier): https://fly.io
- **PythonAnywhere** (Free tier): https://www.pythonanywhere.com

### Frontend alternatives:
- **Netlify**: https://netlify.com
- **GitHub Pages**: Limited (no API proxy)

---

## 🆘 Need Help?

If something doesn't work:
1. Check deployment logs on Render/Vercel
2. Verify environment variables
3. Test backend URL directly in browser: `https://your-backend.onrender.com/api/health`
4. Check browser console for frontend errors

Good luck with your deployment! 🚀
