# ClashArena MVP Setup Guide

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Paystack or Flutterwave account (for payments)

## Installation Steps

### 1. Navigate to the project directory

```bash
cd mvp-fast
```

### 2. Create a virtual environment (recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the `mvp-fast` directory (or copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and add your configuration:

```env
# Database (SQLite by default)
DATABASE_URL=sqlite:///./database/clasharena_mvp.db

# Payment Gateway
PAYMENT_GATEWAY=paystack
PAYSTACK_SECRET_KEY=sk_test_your_secret_key_here
FLUTTERWAVE_SECRET_KEY=FLWSECK_TEST_your_secret_key_here

# Entry Fee (in NGN)
ENTRY_FEE_NGN=1500

# WhatsApp Group Link
WHATSAPP_GROUP_LINK=https://chat.whatsapp.com/your-group-link

# Base URL (for callbacks)
BASE_URL=http://localhost:8000
```

### 5. Create admin user

```bash
cd backend
python create_admin.py
```

Follow the prompts to create an admin account.

### 6. Run the application

```bash
python main.py
```

Or using uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Access the application

- **Landing Page**: http://localhost:8000/
- **Admin Login**: http://localhost:8000/admin/login
- **Admin Dashboard**: http://localhost:8000/admin/dashboard

## Payment Gateway Setup

### Paystack

1. Sign up at https://paystack.com
2. Go to Settings → API Keys & Webhooks
3. Copy your **Secret Key** (starts with `sk_test_` for test mode)
4. Add it to `.env`: `PAYSTACK_SECRET_KEY=sk_test_...`
5. Set `PAYMENT_GATEWAY=paystack`

### Flutterwave

1. Sign up at https://flutterwave.com
2. Go to Settings → API Keys
3. Copy your **Secret Key** (starts with `FLWSECK_TEST_` for test mode)
4. Add it to `.env`: `FLUTTERWAVE_SECRET_KEY=FLWSECK_TEST_...`
5. Set `PAYMENT_GATEWAY=flutterwave`

## Testing

### Test Payment Flow

1. Go to http://localhost:8000/
2. Enter your email address
3. Click "Enter Tournament"
4. You'll be redirected to the payment gateway
5. Use test card details:
   - **Paystack**: Card: `4084 0840 8408 4081`, CVV: `408`, Expiry: Any future date
   - **Flutterwave**: Use test card from Flutterwave dashboard

### Test Admin Functions

1. Login at http://localhost:8000/admin/login
2. View all entries
3. Mark winners
4. Trigger payouts

## Troubleshooting

### Database not found

The database will be created automatically on first run. If you encounter issues, make sure the `database` directory exists and is writable.

### Payment gateway errors

- Check that your API keys are correct
- Verify you're using test keys for development
- Check that your callback URL is accessible (use ngrok for local development)

### Template not found

Make sure the `frontend/templates` directory exists and contains all HTML files.

### Import errors

Make sure you're running the application from the `backend` directory, or adjust the Python path accordingly.

## Production Deployment

Before deploying to production:

1. Switch to production database (PostgreSQL recommended)
2. Use production API keys (not test keys)
3. Set up proper authentication and session management
4. Configure webhooks for payment verification
5. Set up email/SMS/WhatsApp services
6. Use environment variables for sensitive data
7. Enable HTTPS
8. Set up proper logging and error handling
9. Add rate limiting and security measures

## Support

For issues or questions, please check the main README.md file or contact the development team.

