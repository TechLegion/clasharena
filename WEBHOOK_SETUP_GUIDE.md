# Paystack Webhook Setup Guide

## Problem
Transactions are not automatically credited because Paystack webhooks are not configured.

## Solution

### Step 1: Configure Webhook URL in Paystack Dashboard

1. **Go to Paystack Dashboard**: https://dashboard.paystack.com
2. **Navigate to Settings > Webhooks**
3. **Add New Webhook** with these details:
   - **URL**: `https://clash-arena-production.up.railway.app/api/v1/payments/webhook/paystack`
   - **Events**: Select `charge.success` (and optionally `transfer.success`, `transfer.failed`)
   - **Status**: Enable

### Step 2: Test Webhook Connectivity

Test if Paystack can reach your webhook:

```bash
curl -X POST "https://clash-arena-production.up.railway.app/api/v1/payments/webhook/paystack" \
  -H "Content-Type: application/json" \
  -d '{"test": "webhook"}'
```

### Step 3: Verify Webhook Configuration

Your webhook endpoint is already properly configured to:
- ✅ Verify Paystack signatures
- ✅ Handle `charge.success` events
- ✅ Prevent duplicate processing
- ✅ Credit user wallets automatically
- ✅ Log all webhook activity

### Step 4: Test with Real Transaction

After setting up the webhook:
1. Make a small test payment (₦100)
2. Check Railway logs for webhook activity
3. Verify wallet is credited automatically

## Alternative: Webhook URL Configuration via API

If you prefer to set up the webhook programmatically, you can use Paystack's API:

```bash
curl -X POST "https://api.paystack.co/webhook" \
  -H "Authorization: Bearer sk_live_2ab66b1fe6bf3073420cf0d8513cd965de1dd021" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://clash-arena-production.up.railway.app/api/v1/payments/webhook/paystack",
    "events": ["charge.success"]
  }'
```

## Expected Result

After configuring the webhook:
- ✅ All successful payments will be automatically credited
- ✅ No manual verification needed
- ✅ Real-time wallet updates
- ✅ Proper transaction logging

## Troubleshooting

If webhooks still don't work:
1. Check Railway logs for webhook requests
2. Verify webhook URL is accessible
3. Ensure webhook signature verification is working
4. Check Paystack dashboard for webhook delivery status
