# ClashArena MVP - Production Deployment Guide

## 📋 Pre-Deployment Checklist

### 1. Environment Configuration

Create a production `.env` file with these settings:

```env
# Database
DB_HOST=your_production_db_host
DB_PORT=5432
DB_USER=your_db_user
DB_PASSWORD=your_strong_password
DB_NAME=clasharena_production

# Paystack (PRODUCTION KEYS)
PAYSTACK_SECRET_KEY=sk_live_YOUR_ACTUAL_LIVE_KEY
PAYSTACK_PUBLIC_KEY=pk_live_YOUR_ACTUAL_LIVE_KEY
PAYMENT_GATEWAY=paystack

# Entry Fee (REAL AMOUNT)
ENTRY_FEE_NGN=5400

# Google Sheets Integration
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SPREADSHEET_ID=1CQpdYSq3QT6Cgz1d-WiPCzAKqj1ew6GlRGcM8r2VEMY
GOOGLE_SHEET_NAME=8am to 9am
GOOGLE_CREDENTIALS_FILE=credentials.json

# Tournament Settings
DOLLAR_RATE=1500
PER_KILL_VALUE=0.6

# WhatsApp Group
WHATSAPP_GROUP_LINK=https://chat.whatsapp.com/DCa9QBuytJnDUbxLANnBaN

# Application Settings
BASE_URL=https://your-domain.com
```

### 2. Security Checklist

- [ ] Update entry fee from ₦100 to actual amount (₦5,400)
- [ ] Use LIVE Paystack keys (not test keys)
- [ ] Strong database password
- [ ] HTTPS enabled (SSL certificate)
- [ ] credentials.json NOT committed to Git
- [ ] .env file NOT committed to Git

### 3. Files to Deploy

```
mvp-fast/
├── .env (production config)
├── backend/
│   ├── credentials.json (Google Sheets)
│   ├── main.py
│   ├── google_sheets.py
│   ├── exchange_rate.py
│   ├── requirements.txt
│   └── ...
├── database/
├── frontend/
└── ...
```

## 🌐 Deployment Options

### Option 1: Railway.app (Recommended - Easiest)

**Pros:**
- Free tier available
- PostgreSQL database included
- Easy deployment from GitHub
- Auto SSL/HTTPS
- Domain support

**Steps:**
1. Create account at https://railway.app
2. Create new project
3. Add PostgreSQL database
4. Deploy from GitHub
5. Add environment variables
6. Deploy!

**Railway Database Connection (if you see "server closed the connection unexpectedly"):**
1. Use `DATABASE_PRIVATE_URL` – Reference `${{Postgres.DATABASE_PRIVATE_URL}}` in Variables (internal network, more stable)
2. Try `DATABASE_SSL_MODE=disable` – Add this env var; some Railway app+DB same-project setups need SSL disabled
3. The app uses NullPool (fresh connection per request) and 1 worker to minimize connection issues

**Cost:** Free tier → $5/month for production

---

### Option 2: Render.com

**Pros:**
- Free tier
- PostgreSQL included
- GitHub integration
- Auto SSL

**Steps:**
1. Create account at https://render.com
2. New Web Service → Connect GitHub repo
3. Add PostgreSQL database
4. Configure environment variables
5. Deploy

**Cost:** Free tier available

---

### Option 3: DigitalOcean App Platform

**Pros:**
- Reliable
- Scalable
- PostgreSQL managed database

**Cost:** $5/month for basic app + $15/month for database

---

### Option 4: Heroku

**Pros:**
- Popular platform
- PostgreSQL add-on
- Easy deployment

**Cost:** ~$7/month (no free tier anymore)

---

### Option 5: VPS (DigitalOcean Droplet / AWS EC2)

**Pros:**
- Full control
- Can run multiple apps
- Cheaper at scale

**Cons:**
- More setup required
- Manual configuration

**Cost:** $6/month (DigitalOcean) or $5/month (AWS Lightsail)

---

## 🔧 Production Setup Commands

### 1. Install Dependencies

```bash
cd mvp-fast/backend
pip install -r requirements.txt
```

### 2. Setup Database

```bash
python setup_database.py
python create_admin.py
```

### 3. Run Production Server

```bash
# Using Gunicorn (recommended for production)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

Or

```bash
# Using Uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🔗 Webhook Configuration

After deployment, update Paystack webhook URL:

1. Go to Paystack Dashboard: https://dashboard.paystack.com/
2. Settings → Webhooks
3. Add: `https://your-domain.com/api/webhook/paystack`
4. Save

## 🧪 Testing Checklist

Before going live:

- [ ] Test payment flow end-to-end
- [ ] Verify Google Sheets integration
- [ ] Test webhook notifications
- [ ] Verify email in Google Sheet
- [ ] Test WhatsApp group link
- [ ] Check live exchange rates working
- [ ] Admin dashboard accessible
- [ ] Database backups configured

## 📊 Monitoring

After deployment:

- Monitor server logs
- Check Paystack dashboard for payments
- Verify Google Sheets updating
- Monitor database size
- Check error logs

## 🆘 Troubleshooting

### Issue: Payments not updating

- Check webhook URL in Paystack dashboard
- Verify domain is accessible (not localhost)
- Check server logs for webhook errors

### Issue: Google Sheets not updating

- Verify credentials.json uploaded to server
- Check sheet is shared with service account
- Verify GOOGLE_SHEETS_ENABLED=true

### Issue: Database connection failed

- Check database credentials
- Verify database is running
- Check firewall/security group settings

## 📝 Post-Deployment

1. Test with small entry fee first
2. Monitor for 24 hours
3. Gradually increase to full amount
4. Set up database backups
5. Monitor transaction logs

