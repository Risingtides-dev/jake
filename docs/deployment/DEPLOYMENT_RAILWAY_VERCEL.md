# Deployment Guide: Railway (Backend) + Vercel (Frontend)

## Overview

This guide covers deploying the Warner Sound Tracker:
- **Backend (Port 5001)**: Deploy to Railway
- **Frontend (Port 8000)**: Deploy to Vercel

## Prerequisites

- Railway account (https://railway.app)
- Vercel account (https://vercel.com)
- GitHub repository (optional, but recommended)
- yt-dlp installed on Railway (via Nixpacks or custom build)

## Backend Deployment (Railway)

### Step 1: Prepare Repository

1. Ensure all files are committed to git
2. Verify `requirements.txt` includes all dependencies
3. Verify `Procfile` exists with gunicorn command
4. Verify `init_db.py` can run successfully

### Step 2: Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo" (recommended) or "Deploy from local directory"
4. Select your repository

### Step 3: Configure Railway Service

1. Railway will automatically detect Python
2. Set environment variables:
   - `PORT` - Railway will set this automatically
   - `SECRET_KEY` - Generate a secure secret key
   - `FLASK_ENV=production`
   - `CORS_ORIGINS` - Your Vercel frontend URL (e.g., `https://your-app.vercel.app`)

### Step 4: Install yt-dlp on Railway

Railway uses Nixpacks. Add to `nixpacks.toml`:

```toml
[phases.setup]
nixPkgs = ["python311", "pip", "yt-dlp"]
```

Or install via pip in requirements.txt (if available).

### Step 5: Initialize Database

1. Railway will run `init_db.py` during build (if configured in nixpacks.toml)
2. Or run manually after first deployment:
   - Open Railway shell
   - Run: `python3 init_db.py`

### Step 6: Deploy

1. Railway will automatically deploy on push to main branch
2. Get your Railway URL (e.g., `https://your-app.railway.app`)
3. Test the API: `https://your-app.railway.app/api/v1/health`

## Frontend Deployment (Vercel)

### Step 1: Prepare Frontend

1. Ensure `frontend/` directory exists with all files
2. Verify `frontend/js/api.js` uses environment variable for API URL
3. Create `vercel.json` in project root

### Step 2: Create Vercel Project

1. Go to https://vercel.com
2. Click "New Project"
3. Import your GitHub repository
4. Configure project:
   - **Framework Preset**: Other
   - **Root Directory**: `frontend`
   - **Build Command**: (leave empty, static site)
   - **Output Directory**: `frontend`

### Step 3: Set Environment Variables

In Vercel dashboard, set:
- `VITE_API_BASE_URL` - Your Railway backend URL (e.g., `https://your-app.railway.app/api/v1`)

### Step 4: Configure vercel.json

Create `vercel.json` in project root:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/**",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/frontend/$1"
    }
  ]
}
```

### Step 5: Deploy

1. Vercel will automatically deploy on push to main branch
2. Get your Vercel URL (e.g., `https://your-app.vercel.app`)
3. Test the frontend

## Environment Variables

### Railway (Backend)

```
PORT=5001 (automatically set by Railway)
SECRET_KEY=your-secret-key
FLASK_ENV=production
CORS_ORIGINS=https://your-app.vercel.app
DATABASE_PATH=tracker.db
```

### Vercel (Frontend)

```
VITE_API_BASE_URL=https://your-railway-app.railway.app/api/v1
```

## Testing Deployment

### Backend (Railway)

1. Test health endpoint:
   ```bash
   curl https://your-app.railway.app/api/v1/health
   ```

2. Test sessions endpoint:
   ```bash
   curl https://your-app.railway.app/api/v1/sessions
   ```

### Frontend (Vercel)

1. Open your Vercel URL in browser
2. Check browser console for API connection
3. Test dashboard functionality

## Troubleshooting

### Backend Issues

**Issue**: Database not found
- **Solution**: Run `python3 init_db.py` in Railway shell

**Issue**: yt-dlp not found
- **Solution**: Add to nixpacks.toml or install via pip

**Issue**: CORS errors
- **Solution**: Verify `CORS_ORIGINS` includes your Vercel URL

### Frontend Issues

**Issue**: API calls failing
- **Solution**: Verify `VITE_API_BASE_URL` is set correctly in Vercel

**Issue**: Blank page
- **Solution**: Check browser console for errors, verify API URL

## Maintenance

### Database Backups

Railway provides persistent volumes. To backup:
1. Download database file from Railway volume
2. Or set up automated backups (Railway Pro)

### Updates

1. Push changes to GitHub
2. Railway and Vercel will auto-deploy
3. Monitor deployment logs for errors

## Cost Estimates

- **Railway**: ~$5-20/month (depending on usage)
- **Vercel**: Free tier available (sufficient for most use cases)

## Security Notes

1. **Secret Key**: Use a strong, random secret key in production
2. **CORS**: Restrict CORS origins to your Vercel URL only
3. **Database**: Railway volumes are persistent but consider backups
4. **API Keys**: Never commit API keys to git

## Next Steps

1. Set up monitoring (Railway provides logs)
2. Configure custom domains (optional)
3. Set up automated backups
4. Add authentication (if needed)

