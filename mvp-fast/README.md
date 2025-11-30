# ClashArena Fast MVP

A fast MVP implementation for ClashArena tournament platform with payment processing, player intake, and admin dashboard.

## Features

- ✅ Accept $1 entry fee (NGN equivalent) via hosted checkout (Paystack/Flutterwave)
- ✅ Player intake form (CODM ID, contact, bank info)
- ✅ Admin dashboard to view entries, mark winners, and trigger payouts
- ✅ Notification system (email/WhatsApp/SMS) - ready for integration
- ✅ PostgreSQL database
- ✅ Clean, responsive UI

## Quick Start

### 1. Install Dependencies

```bash
cd mvp-fast/backend
pip install -r requirements.txt
```

### 2. Setup PostgreSQL Database

Make sure PostgreSQL is running and create the database:

```sql
CREATE DATABASE clasharena_fastmvp;
```

Or use the setup script:

```bash
python setup_database.py
```

### 3. Configure Environment

Create a `.env` file in the `mvp-fast` directory with your database and payment gateway credentials:

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

### 4. Initialize Database Tables

The database tables will be created automatically on first run. To create an admin user:

```bash
cd backend
python create_admin.py
```

### 5. Run the Application

```bash
cd backend
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Access the Application

- Landing Page: http://localhost:8000/
- Admin Dashboard: http://localhost:8000/admin/dashboard
- Admin Login: http://localhost:8000/admin/login

## User Flow

1. **Landing Page** → User clicks "Enter Tournament"
2. **Payment** → Redirected to payment gateway (Paystack/Flutterwave)
3. **Player Intake** → After payment, user fills registration form
4. **Thank You** → Confirmation page with WhatsApp group link
5. **Admin** → Admin marks winners and triggers payouts

## Payment Gateway Setup

### Paystack

1. Sign up at https://paystack.com
2. Get your secret key from the dashboard
3. Add to `.env`: `PAYSTACK_SECRET_KEY=sk_test_...`
4. Set `PAYMENT_GATEWAY=paystack`

### Flutterwave

1. Sign up at https://flutterwave.com
2. Get your secret key from the dashboard
3. Add to `.env`: `FLUTTERWAVE_SECRET_KEY=FLWSECK_TEST_...`
4. Set `PAYMENT_GATEWAY=flutterwave`

## Admin Functions

- View all paid entries
- Mark winners
- Trigger payouts
- View statistics (total entries, winners, payouts)

## Database Schema

- **Entry**: Player entries with payment and registration details
- **Payment**: Payment transaction records
- **Payout**: Payout transaction records
- **AdminUser**: Admin user accounts
- **Notification**: Notification log

## Notification Integration

The notification system is set up but requires integration with:
- Email service (SMTP)
- WhatsApp API (Twilio, WhatsApp Business API)
- SMS service (Twilio, etc.)

Currently, notifications are logged in the database. Update the `send_notification` function in `main.py` to integrate with your preferred services.

## Project Structure

```
mvp-fast/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── create_admin.py      # Admin user creation script
├── database/
│   ├── db.py                # Database configuration
│   └── models.py            # SQLAlchemy models
├── frontend/
│   ├── templates/           # HTML templates
│   └── static/              # CSS and JavaScript
│       ├── css/
│       └── js/
└── README.md
```

## Development Notes

- This is a fast MVP - not production-ready
- Uses SQLite for simplicity (switch to PostgreSQL for production)
- Password hashing is basic (use bcrypt for production)
- Session management is simple (use proper auth for production)
- Payment gateway integration needs webhook setup for production

## Next Steps

1. Set up payment gateway webhooks
2. Integrate email/SMS/WhatsApp services
3. Add proper authentication and session management
4. Switch to PostgreSQL for production
5. Add error handling and logging
6. Add tests
7. Deploy to production server

## License

MIT

