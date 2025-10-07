# 📧 OTP Email Verification Setup Guide

## 🚀 **Quick Setup (5 Minutes)**

### 1. **Database Migration**
The OTP system adds new tables to your database. Run this to update:

```bash
# Your database will automatically create the new tables when you restart
# No manual migration needed - SQLAlchemy handles it!
```

### 2. **Install Dependencies**
```bash
cd backend
pip install slowapi==0.1.9  # For rate limiting
```

### 3. **Restart Backend**
```bash
python main.py
```

### 4. **Test OTP System**
```bash
# Send OTP
curl -X POST http://localhost:8001/api/v1/otp/send \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "purpose": "email_verification"}'

# Verify OTP (check backend console for the code)
curl -X POST http://localhost:8001/api/v1/otp/verify \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"otp_code": "123456", "purpose": "email_verification"}'
```

## 🔧 **How It Works**

### **Development Mode (Current):**
- ✅ **OTP codes printed to console** - Check backend logs
- ✅ **No email sending** - Perfect for testing
- ✅ **6-digit codes** - 10-minute expiry
- ✅ **Rate limited** - Max 10 requests per minute

### **Production Mode (Future):**
- 📧 **Real email sending** via SMTP
- 🔒 **Secure delivery** to user's inbox
- 📱 **Mobile-friendly** codes

## 📋 **API Endpoints**

### **Send OTP**
```http
POST /api/v1/otp/send
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "user@example.com",
  "purpose": "email_verification"
}
```

### **Verify OTP**
```http
POST /api/v1/otp/verify
Authorization: Bearer <token>
Content-Type: application/json

{
  "otp_code": "123456",
  "purpose": "email_verification"
}
```

### **Resend OTP**
```http
POST /api/v1/otp/resend?purpose=email_verification
Authorization: Bearer <token>
```

### **Check Status**
```http
GET /api/v1/otp/status
Authorization: Bearer <token>
```

## 🎯 **Integration Examples**

### **Frontend Usage:**
```typescript
// Send OTP after registration
const response = await fetch('/api/v1/otp/send', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: user.email,
    purpose: 'email_verification'
  })
})

// Poll for result
const data = await response.json()
const result = await taskService.pollTask(data.task_id)

if (result.success) {
  // Show OTP verification modal
}
```

### **Backend Usage:**
```python
# In your auth tasks
from app.tasks.otp_tasks import send_otp_email_task

# Send OTP after user creation
send_otp_email_task.delay(user.id, user.email, "email_verification")
```

## 🔒 **Security Features**

- ✅ **6-digit random codes** - Cryptographically secure
- ✅ **10-minute expiry** - Short window for security
- ✅ **One-time use** - Codes become invalid after use
- ✅ **Rate limiting** - Prevents spam/abuse
- ✅ **IP tracking** - Monitors suspicious activity
- ✅ **Purpose validation** - Different OTPs for different uses

## 📊 **OTP Purposes**

1. **`email_verification`** - Verify email after signup
2. **`password_reset`** - Reset forgotten password
3. **`two_factor`** - Additional security layer

## 🐛 **Troubleshooting**

### **"OTP not found"**
- Check if code is exactly 6 digits
- Verify code hasn't expired (10 minutes)
- Ensure code hasn't been used already

### **"Rate limit exceeded"**
- Wait 1 minute between requests
- Check if you're sending too many requests

### **"User not found"**
- Ensure user is logged in
- Check JWT token is valid

## 🚀 **Production Setup**

### **Enable Real Email Sending:**
```env
# Add to your .env file
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### **Update Email Function:**
In `backend/app/tasks/otp_tasks.py`, uncomment the SMTP email sending code.

---

**Your OTP system is ready for tomorrow's launch!** 🎉
