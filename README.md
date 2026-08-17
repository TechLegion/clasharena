#  ClashArena - Gaming Platform

A modern gaming platform for competitive mobile gaming with real money tournaments and matches.

##  Features

### Core Gaming Features
- **Real Money Matches**: Head-to-head battles with cash prizes
- **Tournament System**: Multi-player competitions with prize pools
- **Leaderboards**: Track top players and rankings
- **Wallet System**: Secure deposits and withdrawals

### Admin Features
- **User Management**: Comprehensive user administration
- **Match Oversight**: Monitor and manage all matches
- **Financial Management**: Handle transactions and bulk payments
- **Analytics Dashboard**: System metrics and insights

### Payment Integration
- **Paystack**: For user deposits and withdrawals
- **Flutterwave**: For cost-effective bulk payments
- **Hybrid System**: 50% cost savings on bulk operations

##  Tech Stack

### Frontend
- **Next.js 14** with TypeScript
- **Tailwind CSS** for styling
- **React Query** for data fetching
- **Heroicons** for UI icons

### Backend
- **FastAPI** with Python
- **PostgreSQL** database
- **Redis** for caching and queues
- **Celery** for async task processing

### Infrastructure
- **Docker** containerization
- **Nginx** reverse proxy
- **SSL/TLS** encryption
- **Rate limiting** and security

## 🛠️ Development Setup

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Database Setup
```bash
# Create database
createdb clasharena

# Run migrations (automatic on startup)
```

### Environment Variables
Create `.env` file with:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/clasharena
REDIS_URL=redis://localhost:6379

# JWT
SECRET_KEY=your-super-secret-key-here

# Payment Gateways
PAYSTACK_SECRET_KEY=sk_live_...
PAYSTACK_PUBLIC_KEY=pk_live_...
FLUTTERWAVE_SECRET_KEY=FLWSECK_...

# Email (Optional)
SENDGRID_API_KEY=your-sendgrid-key
```

## 🚀 Production Deployment

### Quick Deploy with Docker
```bash
# Clone repository
git clone https://github.com/TechLegion/clasharena.git
cd clasharena

# Set environment variables
cp .env.example .env
# Edit .env with your production values

# Deploy
./deploy.sh
```

### Manual Deployment
1. **Frontend**: Deploy to Vercel/Netlify
2. **Backend**: Deploy to Railway/Render
3. **Database**: Use Railway PostgreSQL or Neon
4. **Domain**: Configure custom domain

##  Usage

### For Players
1. **Sign Up** with email/phone
2. **Deposit Funds** via Paystack
3. **Create/Join Matches** in your favorite games
4. **Win Cash Prizes** and withdraw earnings

### For Admins
1. **Access Admin Panel** from dashboard
2. **Manage Users** and their accounts
3. **Monitor Matches** and transactions
4. **Process Bulk Payments** efficiently

## 🔒 Security Features

- **JWT Authentication** with refresh tokens
- **Rate Limiting** to prevent abuse
- **Input Validation** with Pydantic
- **SQL Injection Protection**
- **XSS Protection**
- **HTTPS Enforcement**
- **Secure Payment Processing**

##  Cost Optimization

### Payment Fees Comparison
- **Paystack Only**: ₦50 per bulk transfer
- **Hybrid System**: ₦25 per bulk transfer
- **Savings**: 50% reduction in fees

##  Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

##  License

This project is licensed under the MIT License.

##  Support

For support and questions:
- **Email**: techlegion01@gmail.com
- **GitHub Issues**: [Create an issue](https://github.com/TechLegion/clasharena/issues)

##  Roadmap

### Phase 1 (Current)
- ✅ User authentication and wallet
- ✅ Match creation and management
- ✅ Payment integration
- ✅ Admin panel

### Phase 2 (Next)
- 🔄 Mobile app development
- 🔄 Advanced analytics
- 🔄 Tournament automation
- 🔄 Referral system

### Phase 3 (Future)
-  Machine learning matchmaking
- 🌍 International expansion
- 🎮 More game integrations
-  Cryptocurrency support

---

**Built by TechLegion**
