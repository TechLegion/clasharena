# Manual Transaction Verification

## Transaction Details
- **Reference**: `dep_989127c9-dcce-4042-8552-460d2d15be6a`
- **Amount**: ₦100.00
- **Email**: sammyokorie0@gmail.com

## Step 1: Login to get JWT Token

Replace `YOUR_PASSWORD` with your actual password:

```bash
curl -X POST "https://clash-arena-production.up.railway.app/api/v1/auth/login-direct" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "sammyokorie0@gmail.com",
    "password": "YOUR_PASSWORD"
  }'
```

Copy the `access_token` from the response.

## Step 2: Verify Transaction

Replace `YOUR_JWT_TOKEN` with the token from Step 1:

```bash
curl -X POST "https://clash-arena-production.up.railway.app/api/v1/payments/deposit/verify" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reference": "dep_989127c9-dcce-4042-8552-460d2d15be6a"
  }'
```

## Expected Result

You should see something like:
```json
{
  "status": "success",
  "message": "Deposit of ₦100.00 credited successfully",
  "amount": 100.0,
  "balance": 100.0
}
```

## Alternative: Direct API Test

You can also test this directly in your browser's developer console or using Postman/Insomnia.

## Why This Happened

The Paystack webhook didn't fire or wasn't received by your backend. This is common and can happen due to:
1. Webhook URL not configured in Paystack dashboard
2. Network issues
3. Webhook signature verification failures

The manual verification will credit your wallet immediately.
