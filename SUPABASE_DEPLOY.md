# Supabase Deployment Guide - CyberCafe POS Pro

This guide will help you deploy the CyberCafe POS Pro application using Supabase (free PostgreSQL database) and Vercel/Netlify for hosting.

## Why Supabase?

- ✅ **Free PostgreSQL database** (500MB storage, 2GB bandwidth)
- ✅ **No credit card required**
- ✅ **Built-in authentication** (optional)
- ✅ **Real-time capabilities**
- ✅ **Automatic backups**
- ✅ **Easy to use dashboard**

---

## Step 1: Create Supabase Project

1. **Go to Supabase**: https://supabase.com/
2. **Sign up/Login** with GitHub, Google, or email
3. **Create a new project**:
   - Click **"New Project"**
   - **Name**: `cybercafe-pos`
   - **Database Password**: Create a strong password (save this!)
   - **Region**: Choose closest to your location
   - **Plan**: Free
   - Click **"Create new project"**

4. **Wait 2-3 minutes** for the project to be provisioned

5. **Get your database URL**:
   - Go to **Project Settings** (gear icon) → **Database**
   - Scroll to **Connection string** → **URI**
   - Copy the connection string (it looks like):
     ```
     postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
     ```
   - Replace `[YOUR-PASSWORD]` with the password you created

---

## Step 2: Run Database Migrations Locally

Since you don't have PostgreSQL installed locally, we'll use Supabase's database directly.

### Install Python and Dependencies

1. **Install Python 3.11** (if not installed):
   - Download from: https://www.python.org/downloads/
   - During installation, check **"Add Python to PATH"**

2. **Open PowerShell/Terminal** and navigate to your project:
   ```powershell
   cd C:\Users\AIMTECH TSHBA\Desktop\pos\backend
   ```

3. **Create virtual environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

5. **Update `.env` file** with your Supabase database URL:
   ```powershell
   notepad .env
   ```
   
   Update the file:
   ```env
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   REDIS_URL=redis://localhost:6379
   SECRET_KEY=your-secret-key-minimum-32-characters-long-change-this
   CORS_ORIGINS=http://localhost:5173,http://localhost:3000
   ```

6. **Run migrations** (this creates tables in Supabase):
   ```powershell
   alembic upgrade head
   ```

7. **Seed initial data**:
   ```powershell
   python -m app.seed
   ```

   You should see:
   ```
   🌱 Seeding database...
   ✓ Created admin user (username: admin, password: admin123)
   ✓ Created manager user (username: manager, password: manager123)
   ✓ Created attendant user (username: attendant, password: attendant123)
   ✓ Created 3 inventory items
   ✓ Created 10 services
   ✓ Created 5 computers
   ✅ Database seeding completed successfully!
   ```

---

## Step 3: Deploy Backend to Render

Render offers free hosting for the backend API.

1. **Create Render account**: https://render.com/
2. **Connect GitHub**:
   - Push your code to GitHub first (if not already)
   - Or use Render's Git integration

3. **Create Web Service**:
   - Click **"New"** → **"Web Service"**
   - Connect your repository
   - Configure:
     - **Name**: `cybercafe-pos-backend`
     - **Region**: Choose closest to you
     - **Branch**: `main`
     - **Root Directory**: `backend`
     - **Runtime**: `Python 3`
     - **Build Command**:
       ```bash
       pip install -r requirements.txt
       ```
     - **Start Command**:
       ```bash
       uvicorn app.main:app --host 0.0.0.0 --port $PORT
       ```

4. **Add Environment Variables**:
   - Click **"Environment"** tab
   - Add these variables:
     - `DATABASE_URL`: (Your Supabase connection string)
     - `SECRET_KEY`: (Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)
     - `CORS_ORIGINS`: `https://your-frontend-url.vercel.app` (we'll update this later)
     - `REDIS_URL`: `redis://red-xxxxx.render.com:6379` (optional, or create free Redis on Render)

5. **Deploy**:
   - Click **"Create Web Service"**
   - Wait for deployment (5-10 minutes)
   - Copy your backend URL: `https://cybercafe-pos-backend.onrender.com`

---

## Step 4: Deploy Frontend to Vercel

Vercel offers free hosting for React applications.

1. **Create Vercel account**: https://vercel.com/
2. **Install Vercel CLI** (optional):
   ```powershell
   npm install -g vercel
   ```

3. **Update frontend `.env`**:
   ```powershell
   cd C:\Users\AIMTECH TSHBA\Desktop\pos\frontend
   notepad .env
   ```
   
   Update:
   ```env
   VITE_API_URL=https://cybercafe-pos-backend.onrender.com
   VITE_WS_URL=wss://cybercafe-pos-backend.onrender.com
   ```

4. **Deploy via Vercel Dashboard**:
   - Go to https://vercel.com/new
   - Import your Git repository
   - Configure:
     - **Framework Preset**: Vite
     - **Root Directory**: `frontend`
     - **Build Command**: `npm run build`
     - **Output Directory**: `dist`
   - **Environment Variables**:
     - `VITE_API_URL`: `https://cybercafe-pos-backend.onrender.com`
     - `VITE_WS_URL`: `wss://cybercafe-pos-backend.onrender.com`
   - Click **"Deploy"**

5. **Get your frontend URL**: `https://your-app.vercel.app`

---

## Step 5: Update CORS Settings

1. **Go back to Render** (backend service)
2. **Update Environment Variables**:
   - Edit `CORS_ORIGINS` to include your Vercel URL:
     ```
     https://your-app.vercel.app
     ```
3. **Save** (service will auto-redeploy)

---

## Step 6: Test Your Application

1. **Open your frontend URL**: `https://your-app.vercel.app`
2. **Login with default credentials**:
   - Username: `admin`
   - Password: `admin123`

3. **Test features**:
   - Create a new sale
   - Start a computer session
   - View reports
   - Manage services

---

## Alternative: Local Development with Supabase

If you want to run locally without deploying:

### Backend (Local)
```powershell
cd C:\Users\AIMTECH TSHBA\Desktop\pos\backend
.\venv\Scripts\activate
uvicorn app.main:app --reload
```

### Frontend (Local)
```powershell
cd C:\Users\AIMTECH TSHBA\Desktop\pos\frontend
npm install
npm run dev
```

Access at: `http://localhost:5173`

---

## Supabase Dashboard Features

You can manage your database directly from Supabase:

1. **Table Editor**: View and edit data
2. **SQL Editor**: Run custom queries
3. **Database**: View schema and relationships
4. **Logs**: Monitor database activity
5. **Backups**: Automatic daily backups (paid plans)

### Useful SQL Queries

**View all users:**
```sql
SELECT * FROM users;
```

**View today's sales:**
```sql
SELECT * FROM transactions 
WHERE DATE(created_at) = CURRENT_DATE;
```

**Check inventory:**
```sql
SELECT name, current_stock, min_stock_level 
FROM inventory_items 
WHERE current_stock < min_stock_level;
```

---

## Cost Breakdown

| Service | Plan | Cost | Limits |
|---------|------|------|--------|
| Supabase | Free | $0 | 500MB DB, 2GB bandwidth |
| Render (Backend) | Free | $0 | Spins down after 15min inactivity |
| Vercel (Frontend) | Free | $0 | 100GB bandwidth |
| **Total** | | **$0/month** | |

### Upgrade Recommendations

When you outgrow free tier:
- **Supabase Pro**: $25/month (8GB DB, 50GB bandwidth, daily backups)
- **Render Starter**: $7/month (always-on, no spin-down)
- **Vercel Pro**: $20/month (unlimited bandwidth)

---

## Troubleshooting

### "Connection refused" error
- Check your Supabase connection string
- Ensure password is correct
- Verify database is active in Supabase dashboard

### "CORS error" in browser
- Update `CORS_ORIGINS` in Render backend
- Include your exact frontend URL
- Redeploy backend after changes

### "Module not found" error
- Run `pip install -r requirements.txt` in backend
- Run `npm install` in frontend

### Migrations fail
- Check DATABASE_URL is correct
- Ensure Supabase project is active
- Try: `alembic downgrade base` then `alembic upgrade head`

---

## Quick Commands Reference

### Backend
```powershell
# Activate virtual environment
cd C:\Users\AIMTECH TSHBA\Desktop\pos\backend
.\venv\Scripts\activate

# Run migrations
alembic upgrade head

# Seed data
python -m app.seed

# Start server
uvicorn app.main:app --reload
```

### Frontend
```powershell
# Install dependencies
cd C:\Users\AIMTECH TSHBA\Desktop\pos\frontend
npm install

# Start dev server
npm run dev

# Build for production
npm run build
```

---

## Next Steps

1. ✅ Set up Supabase database
2. ✅ Run migrations and seed data
3. ✅ Deploy backend to Render
4. ✅ Deploy frontend to Vercel
5. ✅ Update CORS settings
6. ✅ Test the application
7. 🔒 **Change default passwords!**
8. 📊 Monitor usage in Supabase dashboard

---

## Support

- **Supabase Docs**: https://supabase.com/docs
- **Render Docs**: https://render.com/docs
- **Vercel Docs**: https://vercel.com/docs

Your application is now live and using Supabase PostgreSQL! 🎉
