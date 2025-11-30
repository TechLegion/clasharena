# ClashArena MVP - Quick Start Guide

## What This MVP Does

This is a fast MVP implementation for ClashArena tournament platform that handles the complete user flow:

1. **Landing Page** → User enters email and clicks "Enter Tournament"
2. **Payment** → User is redirected to Paystack/Flutterwave for payment
3. **Player Intake** → After payment, user fills registration form (CODM ID, contact, bank info)
4. **Thank You** → Confirmation page with WhatsApp group link
5. **Admin Dashboard** → Admin can view entries, mark winners, and trigger payouts

## Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
cd mvp-fast/backend
pip install -r requirements.txt
```

### 2. Setup PostgreSQL Database

Make sure PostgreSQL is running, then create the database:

```sql
CREATE DATABASE clasharena_fastmvp;
```

Or use the setup script:

```bash
cd backend
python setup_database.py
```

### 3. Configure Environment

Create `.env` file in `mvp-fast` directory:

```env
# Database Configuration (using same credentials as main app)
DB_HOST=localhost
DB_PORT=5432
DB_USER=clasharena_user
DB_PASSWORD=clasharena_password
DB_NAME=clasharena_fastmvp

# Payment Gateway (using same Paystack keys as main app)
PAYMENT_GATEWAY=paystack
PAYSTACK_SECRET_KEY=sk_live_2ab66b1fe6bf3073420cf0d8513cd965de1dd021
PAYSTACK_PUBLIC_KEY=pk_live_bcace690c5b14739346161a501307ad4f9688e30
ENTRY_FEE_NGN=1500
WHATSAPP_GROUP_LINK=https://chat.whatsapp.com/your-link
BASE_URL=http://localhost:8000
```

### 4. Create Admin User

```bash
cd backend
python create_admin.py
```

### 5. Run Application

```bash
python main.py
```

### 5. Access

- **Landing**: http://localhost:8000/
- **Admin**: http://localhost:8000/admin/login

## File Structure

```
mvp-fast/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Dependencies
│   └── create_admin.py      # Admin user creation
├── database/
│   ├── db.py                # Database configuration
│   └── models.py            # Database models
├── frontend/
│   ├── templates/           # HTML templates
│   └── static/              # CSS and JavaScript
└── README.md                # Full documentation
```

## Key Features

✅ Payment gateway integration (Paystack/Flutterwave)
✅ Player registration form
✅ Admin dashboard
✅ Payment verification
✅ Winner management
✅ Payout triggering
✅ Notification system (ready for integration)
✅ PostgreSQL database
✅ Responsive UI

## Testing

### Test Payment

1. Use test cards from Paystack/Flutterwave
2. Complete payment flow
3. Fill intake form
4. Check admin dashboard

### Test Admin

1. Login to admin dashboard
2. View entries
3. Mark winners
4. Trigger payouts

## Next Steps

1. Set up payment gateway webhooks
2. Integrate email/SMS/WhatsApp services
3. Add proper authentication
4. Deploy to production

For detailed setup instructions, see `SETUP.md` or `README.md`.

