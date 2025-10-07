# ClashArena Bulk Payments System

## Overview

The bulk payments system allows administrators to send money to multiple users simultaneously using Paystack's transfer API. This is perfect for tournament payouts, affiliate commissions, or any scenario where you need to pay multiple users at once.

## Features

- ✅ **Admin-Only Access**: Only administrators can initiate bulk payments
- ✅ **Batch Processing**: Send up to 100 payments in a single batch
- ✅ **Real-time Status**: Track payment progress with detailed status updates
- ✅ **Error Handling**: Comprehensive error handling with detailed error messages
- ✅ **Audit Trail**: Complete logging of all bulk payment activities
- ✅ **Paystack Integration**: Uses Paystack's transfer API for reliable payments
- ✅ **Notification System**: Optional SMS/email notifications to recipients

## API Endpoints

### 1. Initiate Bulk Payment
```http
POST /api/v1/payments/bulk/initiate
```

**Request Body:**
```json
{
  "recipients": [
    {
      "user_id": "user123",
      "amount": 5000,
      "reason": "Tournament win - 1st place",
      "account_number": "0123456789",
      "bank_code": "058",
      "account_name": "John Doe"
    },
    {
      "user_id": "user456", 
      "amount": 3000,
      "reason": "Tournament win - 2nd place",
      "account_number": "0987654321",
      "bank_code": "011",
      "account_name": "Jane Smith"
    }
  ],
  "description": "Monthly tournament payouts",
  "notify_recipients": true
}
```

**Response:**
```json
{
  "status": "success",
  "bulk_payment_id": "bulk_123e4567-e89b-12d3-a456-426614174000",
  "message": "Bulk payment initiated for 2 recipients",
  "total_amount": 8000
}
```

### 2. Get Bulk Payment Status
```http
GET /api/v1/payments/bulk/{bulk_payment_id}/status
```

**Response:**
```json
{
  "id": "bulk_123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "total_amount": 8000,
  "total_recipients": 2,
  "successful_count": 2,
  "failed_count": 0,
  "created_at": "2024-01-15T10:30:00Z",
  "description": "Monthly tournament payouts"
}
```

### 3. Get Recipients List
```http
GET /api/v1/payments/bulk/{bulk_payment_id}/recipients
```

**Response:**
```json
{
  "bulk_payment_id": "bulk_123e4567-e89b-12d3-a456-426614174000",
  "recipients": [
    {
      "id": "recipient_123",
      "user_id": "user123",
      "username": "john_doe",
      "email": "john@example.com",
      "amount": 5000,
      "reason": "Tournament win - 1st place",
      "account_number": "0123456789",
      "bank_code": "058",
      "account_name": "John Doe",
      "status": "completed",
      "paystack_reference": "T1234567890",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 2
}
```

### 4. Get Bulk Payment History
```http
GET /api/v1/payments/bulk/history?page=1&limit=20
```

## Database Schema

### BulkPayment Table
```sql
CREATE TABLE bulk_payments (
    id VARCHAR PRIMARY KEY,
    admin_id VARCHAR REFERENCES users(id),
    description VARCHAR NOT NULL,
    total_amount FLOAT NOT NULL,
    total_recipients INTEGER NOT NULL,
    status VARCHAR DEFAULT 'pending',
    notify_recipients BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### BulkPaymentRecipient Table
```sql
CREATE TABLE bulk_payment_recipients (
    id VARCHAR PRIMARY KEY,
    bulk_payment_id VARCHAR REFERENCES bulk_payments(id),
    user_id VARCHAR REFERENCES users(id),
    amount FLOAT NOT NULL,
    reason VARCHAR NOT NULL,
    account_number VARCHAR NOT NULL,
    bank_code VARCHAR NOT NULL,
    account_name VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'pending',
    error_message TEXT,
    paystack_reference VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Payment Statuses

### Bulk Payment Statuses
- `pending`: Payment batch created, waiting to be processed
- `processing`: Currently processing individual transfers
- `completed`: All transfers successful
- `failed`: All transfers failed
- `partially_completed`: Some transfers successful, some failed

### Individual Recipient Statuses
- `pending`: Waiting to be processed
- `processing`: Currently being sent via Paystack
- `completed`: Successfully sent
- `failed`: Failed to send (check error_message)

## Limits and Validation

- **Maximum recipients per batch**: 100
- **Maximum total amount per batch**: ₦10,000,000
- **Maximum individual payment**: ₦500,000
- **Minimum individual payment**: ₦100
- **Account number validation**: Must be 10 digits
- **Bank code validation**: Must be valid Paystack bank code

## Error Handling

The system handles various error scenarios:

1. **Invalid Account Details**: Invalid bank code or account number
2. **Insufficient Balance**: Not enough funds in Paystack account
3. **Network Issues**: Timeout or connection errors
4. **Paystack API Errors**: API-specific error responses
5. **Database Errors**: Transaction rollback on failures

## Security Features

- **Admin-Only Access**: Only users with `is_admin = true` can initiate bulk payments
- **Input Validation**: Comprehensive validation of all input data
- **Audit Logging**: All bulk payment activities are logged
- **Transaction Safety**: Database transactions ensure data consistency
- **Rate Limiting**: Prevents abuse of bulk payment endpoints

## Usage Examples

### Tournament Payouts
```javascript
const tournamentPayouts = {
  recipients: [
    {
      user_id: "winner_1",
      amount: 50000,
      reason: "Clash Royale Tournament - 1st Place",
      account_number: "0123456789",
      bank_code: "058",
      account_name: "Winner One"
    },
    {
      user_id: "winner_2", 
      amount: 25000,
      reason: "Clash Royale Tournament - 2nd Place",
      account_number: "0987654321",
      bank_code: "011",
      account_name: "Winner Two"
    }
  ],
  description: "Clash Royale Monthly Tournament Payouts",
  notify_recipients: true
};
```

### Affiliate Commissions
```javascript
const affiliateCommissions = {
  recipients: [
    {
      user_id: "affiliate_1",
      amount: 15000,
      reason: "Affiliate Commission - January 2024",
      account_number: "1234567890",
      bank_code: "044",
      account_name: "Affiliate Partner"
    }
  ],
  description: "Monthly Affiliate Commissions",
  notify_recipients: true
};
```

## Frontend Integration

The admin panel includes a dedicated bulk payments page at `/admin/bulk-payments` with:

- **Payment History**: View all previous bulk payments
- **Status Tracking**: Real-time status updates
- **Recipient Details**: Detailed view of each recipient's status
- **Create New**: Interface to create new bulk payments (coming soon)

## Setup Instructions

1. **Create Database Tables**:
   ```bash
   cd backend
   python create_bulk_payment_tables.py
   ```

2. **Configure Paystack**:
   - Ensure you have sufficient balance in your Paystack account
   - Verify your Paystack secret key is correct
   - Test with small amounts first

3. **Start Celery Workers** (for background processing):
   ```bash
   celery -A app.core.celery_app:celery_app worker --loglevel=info --queues=bulk_payments
   ```

4. **Access Admin Panel**:
   - Login as admin user
   - Navigate to `/admin/bulk-payments`
   - Start creating bulk payments

## Monitoring and Maintenance

- **Check Payment Status**: Regularly monitor bulk payment statuses
- **Handle Failures**: Review failed payments and retry if necessary
- **Balance Monitoring**: Ensure sufficient Paystack balance
- **Log Analysis**: Monitor logs for any issues or patterns

## Best Practices

1. **Test First**: Always test with small amounts and few recipients
2. **Verify Details**: Double-check account numbers and bank codes
3. **Monitor Progress**: Keep track of payment processing
4. **Handle Failures**: Have a process for handling failed payments
5. **Maintain Records**: Keep detailed records of all bulk payments
6. **Notify Users**: Always notify recipients when payments are sent

## Troubleshooting

### Common Issues

1. **"Insufficient Balance"**: Add funds to your Paystack account
2. **"Invalid Bank Code"**: Verify bank codes using the banks API
3. **"Account Number Not Found"**: Verify account numbers with users
4. **"Transfer Failed"**: Check Paystack logs for specific error details

### Support

For technical issues:
1. Check application logs
2. Verify Paystack account status
3. Review database records
4. Contact Paystack support if needed

## Future Enhancements

- [ ] CSV/Excel upload for bulk payment creation
- [ ] Scheduled bulk payments
- [ ] Bulk payment templates
- [ ] Advanced reporting and analytics
- [ ] Integration with tournament system for automatic payouts
