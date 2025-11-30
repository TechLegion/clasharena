# Railway Deployment Guide for ClashArena

## Step 1: Set up Database Service

1. Go to your Railway project dashboard
2. Click "New Service" → "Database" → "PostgreSQL"
3. Railway will automatically provision a PostgreSQL database
4. Note down the connection details

## Step 2: Set up Redis Service

1. Click "New Service" → "Database" → "Redis"
2. Railway will provision a Redis instance
3. Note down the connection details

## Step 3: Configure Environment Variables

Go to your backend service → Variables tab and add these environment variables:

### Database Configuration
```
DATABASE_URL=postgresql://username:password@host:port/database
POSTGRES_USER=clasharena
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=clasharena_prod
POSTGRES_HOST=your_postgres_host
POSTGRES_PORT=5432
```

### Redis Configuration
```
REDIS_URL=redis://username:password@host:port
REDIS_HOST=your_redis_host
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
```

### Security Configuration
```
SECRET_KEY=your_super_secret_key_here_change_this_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### API Configuration
```
PROJECT_NAME=ClashArena
DESCRIPTION=ClashArena - Gaming Tournament Platform
VERSION=1.0.0
API_V1_STR=/api/v1
```

### CORS Configuration
```
BACKEND_CORS_ORIGINS=["https://your-frontend-domain.railway.app"]
```

### Payment Integration (Optional)
```
PAYSTACK_SECRET_KEY=your_paystack_secret_key
PAYSTACK_PUBLIC_KEY=your_paystack_public_key
```

### Email Configuration (Optional)
```
SENDGRID_API_KEY=your_sendgrid_api_key
MAILGUN_API_KEY=your_mailgun_api_key
RESEND_API_KEY=your_resend_api_key
```

### SMS Configuration (Optional)
```
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
```

### Celery Configuration
```
CELERY_BROKER_URL=redis://username:password@host:port/0
CELERY_RESULT_BACKEND=redis://username:password@host:port/0
```

### Environment
```
ENVIRONMENT=production
DEBUG=false
```

## Step 4: Deploy Backend

1. Make sure you're in the backend directory
2. Run: `railway up`
3. Railway will build and deploy your backend

## Step 5: Deploy Frontend

### Option A: Deploy to Railway
1. Go to your project dashboard
2. Click "New Service" → "GitHub Repo"
3. Select your repository
4. Set the root directory to `frontend`
5. Set build command: `npm run build`
6. Set start command: `npm start`
7. Add environment variables:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
   ```

### Option B: Deploy to Vercel
1. Go to vercel.com
2. Import your GitHub repository
3. Set root directory to `frontend`
4. Add environment variable:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
   ```

## Step 6: Set up Celery Workers (Optional)

1. Add a new service for Celery workers
2. Set the same environment variables as the backend
3. Set start command: `celery -A app.core.celery_app:celery_app worker --loglevel=info`

## Step 7: Database Migration

After deployment, run database migrations:
```bash
railway run alembic upgrade head
```

## Step 8: Test Deployment

1. Visit your backend URL: `https://your-backend-url.railway.app/health`
2. Visit your frontend URL
3. Test login and registration

## Troubleshooting

- Check Railway logs for any deployment issues
- Ensure all environment variables are set correctly
- Verify database and Redis connections
- Check CORS settings match your frontend URL
