# 🚀 ClashArena Deployment Guide

## Quick Deploy Options

### Option 1: Vercel + Railway (Recommended)
- **Frontend**: Vercel (free, instant)
- **Backend**: Railway (free tier available)
- **Database**: Railway PostgreSQL

### Option 2: Netlify + Render
- **Frontend**: Netlify (free)
- **Backend**: Render (free tier)
- **Database**: Render PostgreSQL

## 🎯 Step-by-Step Deployment

### 1. Push to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial ClashArena deployment"

# Add remote
git remote add origin https://github.com/TechLegion/clasharena.git

# Push to GitHub
git push -u origin main
```

### 2. Deploy Backend to Railway

1. **Go to [Railway.app](https://railway.app)**
2. **Sign up/Login with GitHub**
3. **Click "New Project"**
4. **Select "Deploy from GitHub repo"**
5. **Choose your clasharena repository**
6. **Select the backend folder**
7. **Add environment variables**:
   ```
   DATABASE_URL=postgresql://postgres:password@host:port/database
   REDIS_URL=redis://host:port
   SECRET_KEY=your-super-secret-key
   PAYSTACK_SECRET_KEY=sk_live_...
   PAYSTACK_PUBLIC_KEY=pk_live_...
   FLUTTERWAVE_SECRET_KEY=FLWSECK_...
   ```
8. **Add PostgreSQL service** (Railway will auto-configure)
9. **Add Redis service** (Railway will auto-configure)
10. **Deploy!**

### 3. Deploy Frontend to Vercel

1. **Go to [Vercel.com](https://vercel.com)**
2. **Sign up/Login with GitHub**
3. **Click "New Project"**
4. **Import your GitHub repository**
5. **Set Root Directory**: `frontend`
6. **Add Environment Variables**:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
   ```
7. **Deploy!**

### 4. Configure Domains

#### Railway Backend
- Railway provides: `https://clasharena-production.railway.app`
- Custom domain: `api.clasharena.com` (optional)

#### Vercel Frontend
- Vercel provides: `https://clasharena.vercel.app`
- Custom domain: `clasharena.com` (optional)

## 🔧 Environment Variables

### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://postgres:password@host:port/database
REDIS_URL=redis://host:port

# JWT
SECRET_KEY=your-super-secret-key-here

# Payment Gateways
PAYSTACK_SECRET_KEY=sk_live_...
PAYSTACK_PUBLIC_KEY=pk_live_...
FLUTTERWAVE_SECRET_KEY=FLWSECK_...

# Frontend URL
FRONTEND_URL=https://clasharena.vercel.app

# Admin
ADMIN_EMAIL=admin@clasharena.com
ADMIN_PASSWORD=secure-admin-password
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
```

## 🗄️ Database Setup

### Railway PostgreSQL
1. **Railway auto-creates database**
2. **Tables auto-migrate on startup**
3. **Admin user auto-created** (if configured)

### Manual Database Setup
```sql
-- Connect to your Railway PostgreSQL
-- Tables will be created automatically by SQLAlchemy
```

## 📱 Testing Your Deployment

### 1. Test Backend
```bash
curl https://your-backend-url.railway.app/health
```

### 2. Test Frontend
- Visit: `https://your-frontend-url.vercel.app`
- Try signing up
- Test login functionality

### 3. Test Admin Panel
- Login with admin credentials
- Access `/admin` route
- Test user management

## 🔒 Security Checklist

- [ ] **HTTPS enabled** on all domains
- [ ] **Environment variables** properly set
- [ ] **SECRET_KEY** is strong and unique
- [ ] **Payment keys** are live/production keys
- [ ] **Admin password** is secure
- [ ] **CORS** configured for frontend domain
- [ ] **Rate limiting** enabled

## 🚨 Troubleshooting

### Backend Issues
```bash
# Check Railway logs
railway logs

# Common issues:
# 1. Missing environment variables
# 2. Database connection issues
# 3. Port configuration (use $PORT)
```

### Frontend Issues
```bash
# Check Vercel logs
vercel logs

# Common issues:
# 1. API URL not configured
# 2. Build errors
# 3. Environment variables
```

### Database Issues
```bash
# Check Railway database logs
# Ensure DATABASE_URL is correct
# Verify tables are created
```

## 💰 Cost Estimation

### Free Tier Limits
- **Railway**: $5/month after free tier
- **Vercel**: Free for hobby projects
- **Database**: Included with Railway

### Production Costs
- **Railway Pro**: $20/month
- **Vercel Pro**: $20/month
- **Custom Domain**: $10-15/year
- **Total**: ~$40-50/month

## 🎯 Next Steps After Deployment

1. **Configure Custom Domain**
2. **Set up SSL Certificates**
3. **Configure Payment Webhooks**
4. **Set up Monitoring**
5. **Create Admin User**
6. **Test All Features**

## 📞 Support

If you encounter issues:
1. **Check logs** on Railway/Vercel
2. **Verify environment variables**
3. **Test locally** first
4. **Check GitHub issues**

---

**Your ClashArena platform will be live in minutes! 🚀**
