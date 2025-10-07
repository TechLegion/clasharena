# Paystack Payment Gateway Setup Guide

## 🚀 Quick Setup

### 1. Get Paystack API Keys

1. **Sign up** at [paystack.com](https://paystack.com)
2. **Verify your account** and complete KYC
3. **Go to Settings > API Keys & Webhooks**
4. **Copy your keys:**
   - Secret Key (starts with `sk_test_` for test, `sk_live_` for live)
   - Public Key (starts with `pk_test_` for test, `pk_live_` for live)

### 2. Configure Environment Variables

Create a `.env` file in the `backend/` directory with:

```env
# Paystack Configuration
PAYSTACK_SECRET_KEY=sk_test_your_secret_key_here
PAYSTACK_PUBLIC_KEY=pk_test_your_public_key_here
PAYSTACK_WEBHOOK_SECRET=your_webhook_secret_here
```

### 3. Set Up Webhooks

1. **In Paystack Dashboard:**
   - Go to Settings > API Keys & Webhooks
   - Click "Add Webhook"
   - **URL:** `https://yourdomain.com/api/v1/payments/webhook/paystack`
   - **Events:** Select all payment events
   - **Copy the webhook secret** to your `.env` file

### 4. Test the Integration

#### Test Deposit Flow:
1. Start the backend server
2. Start the frontend
3. Go to Dashboard
4. Click "Deposit" button
5. Enter test amount (₦100 minimum)
6. Use Paystack test card: `4084084084084081`

#### Test Withdrawal Flow:
1. Ensure you have sufficient balance
2. Click "Withdraw" button
3. Enter bank details (use test bank codes)
4. Verify account validation works

## 🔧 API Endpoints

### Deposit
- `POST /api/v1/payments/deposit/initialize` - Initialize deposit
- `POST /api/v1/payments/deposit/verify` - Verify deposit

### Withdrawal
- `POST /api/v1/payments/withdrawal/request` - Request withdrawal
- `GET /api/v1/payments/banks` - Get bank list
- `POST /api/v1/payments/validate-account` - Validate account

### Webhooks
- `POST /api/v1/payments/webhook/paystack` - Paystack webhook handler

## 💳 Test Cards (Nigeria)

### Successful Transactions:
- **Card:** 4084084084084081
- **CVV:** 408
- **Expiry:** Any future date
- **PIN:** 408408

### Failed Transactions:
- **Card:** 4084084084084085
- **CVV:** 408
- **Expiry:** Any future date
- **PIN:** 408408

## 🏦 Test Bank Codes

Common Nigerian banks for testing:
- **Access Bank:** 044
- **GTBank:** 058
- **First Bank:** 011
- **Zenith Bank:** 057
- **UBA:** 033

## 🔒 Security Features

✅ **Webhook Verification** - All webhooks are cryptographically verified
✅ **Transaction Validation** - All transactions are verified with Paystack
✅ **Amount Limits** - Deposit: ₦100-₦1M, Withdrawal: ₦500-₦500K
✅ **Account Validation** - Bank account numbers are verified before withdrawal
✅ **Async Processing** - All payment operations use Celery for reliability

## 📱 Frontend Integration

The frontend includes:
- **DepositModal** - Complete deposit flow with Paystack
- **WithdrawalModal** - Bank account validation and withdrawal
- **Real-time Balance** - Updates automatically after transactions
- **Transaction History** - View all deposits and withdrawals

## 🚨 Important Notes

1. **Test Mode:** Use test keys for development
2. **Live Mode:** Switch to live keys for production
3. **Webhook Security:** Always verify webhook signatures
4. **Rate Limits:** Paystack has API rate limits
5. **Fees:** 2.5% processing fee on withdrawals

## 🐛 Troubleshooting

### Common Issues:

1. **"Invalid API Key"**
   - Check your secret key format
   - Ensure no extra spaces

2. **"Webhook verification failed"**
   - Check webhook secret in environment
   - Verify webhook URL is accessible

3. **"Account validation failed"**
   - Ensure bank code is correct
   - Check account number format (10 digits)

4. **"Insufficient balance"**
   - Check user's wallet balance
   - Verify transaction amounts

### Debug Mode:
Enable debug logging by setting:
```env
DEBUG=true
```

## 📞 Support

- **Paystack Docs:** [paystack.com/docs](https://paystack.com/docs)
- **API Reference:** [paystack.com/docs/api](https://paystack.com/docs/api)
- **Support:** support@paystack.com

---

**Ready to go live?** Switch to live API keys and update your webhook URL to your production domain! 🚀

