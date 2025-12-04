# Admin Dashboard Guide - MVP Fast

## 🎯 Overview

The admin dashboard has been enhanced with the following features:

1. **Registration Counter** - Real-time tracking of total registrations
2. **100 User Milestone Notification** - Automatic admin notification when 100 users register
3. **WhatsApp Link Management** - Admin can update WhatsApp group link from the dashboard

## 📊 Features

### Registration Counter

- **Real-time Display**: Shows total number of completed registrations (users who have paid and submitted intake form)
- **Milestone Tracking**: Automatically tracks when 100 users are reached
- **Auto-refresh**: Updates every 30 seconds automatically
- **Visual Indicator**: Special highlight when 100-user milestone is reached

### 100 User Milestone Notification

- **Automatic Detection**: System automatically detects when 100 users register
- **Admin Notification**: Sends email notification to admin when milestone is reached
- **One-time Notification**: Only notifies once per milestone to avoid spam
- **Dashboard Display**: Shows milestone achievement banner on dashboard

### WhatsApp Link Management

- **Database Storage**: WhatsApp link is now stored in database (not just environment variable)
- **Admin Control**: Admins can update the link directly from the dashboard
- **Real-time Updates**: Changes take effect immediately for new registrations
- **Validation**: Ensures link is a valid URL format

## 🚀 Setup Instructions

### 1. Database Migration

The new features require new database tables. Run the database initialization:

```bash
cd mvp-fast/backend
python setup_database.py
```

### 2. Initialize Settings

Initialize the app settings (WhatsApp link) in the database:

```bash
cd mvp-fast/backend
python init_settings.py
```

This will:
- Create the `app_settings` table if it doesn't exist
- Initialize the WhatsApp link from environment variable or use default

### 3. Environment Variables

Make sure you have the following environment variables set:

```bash
# Admin email for milestone notifications
ADMIN_EMAIL=admin@clasharena.com

# WhatsApp link (will be stored in database, but this is the initial value)
WHATSAPP_GROUP_LINK=https://chat.whatsapp.com/your-group-link
```

## 📱 Using the Admin Dashboard

### Accessing the Dashboard

1. Navigate to `/admin/login`
2. Enter admin credentials
3. You'll be redirected to `/admin/dashboard`

### Viewing Registration Count

The registration counter is displayed prominently at the top of the dashboard:
- Shows total number of completed registrations
- Displays remaining count to reach 100 users (if not reached)
- Shows milestone achievement banner when 100 users are reached

### Updating WhatsApp Link

1. Scroll to the "Settings" section on the dashboard
2. Find the "WhatsApp Group Link" field
3. Enter or modify the WhatsApp link
4. Click "Update Link" button
5. You'll see a success message when updated

**Note**: The link must be a valid URL starting with `http://` or `https://`

### Viewing Milestone Status

- The dashboard automatically shows when 100 users milestone is reached
- A notification email is sent to the admin email address
- The milestone is tracked in the database to prevent duplicate notifications

## 🔧 API Endpoints

### Get Admin Statistics

```bash
GET /api/admin/stats
```

Returns:
```json
{
  "success": true,
  "stats": {
    "total_registrations": 150,
    "total_entries": 150,
    "winners": 5,
    "pending_payouts": 2,
    "whatsapp_link": "https://chat.whatsapp.com/...",
    "milestone_100_reached": true,
    "milestone_100_notified_at": "2024-01-15T10:30:00"
  }
}
```

### Get Registration Count

```bash
GET /api/admin/registration-count
```

Returns:
```json
{
  "success": true,
  "total_registrations": 150,
  "milestone_100_reached": true,
  "remaining_to_100": 0
}
```

### Update WhatsApp Link

```bash
POST /api/admin/update-whatsapp-link
Content-Type: application/json

{
  "whatsapp_link": "https://chat.whatsapp.com/new-link"
}
```

Returns:
```json
{
  "success": true,
  "message": "WhatsApp link updated successfully",
  "whatsapp_link": "https://chat.whatsapp.com/new-link"
}
```

## 🗄️ Database Schema

### New Tables

#### `app_settings`
Stores application settings like WhatsApp link.

```sql
CREATE TABLE app_settings (
    id VARCHAR PRIMARY KEY,
    key VARCHAR UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description VARCHAR,
    updated_by VARCHAR,
    updated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `registration_milestones`
Tracks registration milestones (e.g., 100 users).

```sql
CREATE TABLE registration_milestones (
    id VARCHAR PRIMARY KEY,
    milestone_count INTEGER NOT NULL,
    reached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notified BOOLEAN DEFAULT FALSE,
    notification_sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔔 Notification System

### Milestone Notification

When 100 users register:
1. System detects the milestone
2. Creates a `RegistrationMilestone` record
3. Sends email notification to admin
4. Marks milestone as notified (prevents duplicate notifications)

### Email Notification Format

**Subject**: 🎉 Milestone Reached: 100 Users Registered!

**Message**: 
```
Congratulations! Your tournament has reached 100 registered users. 
Total registrations: 100
```

## 🎨 Dashboard UI Features

### Registration Counter Card

- **Gradient Background**: Eye-catching purple gradient
- **Large Number Display**: Easy to read registration count
- **Milestone Banner**: Gold banner when milestone reached
- **Progress Indicator**: Shows remaining count to 100

### Settings Section

- **Clean Layout**: Organized settings panel
- **Input Validation**: Real-time URL validation
- **Success/Error Messages**: Clear feedback on actions
- **Keyboard Support**: Enter key to submit

## 🔄 Auto-Refresh

The dashboard automatically refreshes the registration count every 30 seconds:
- No page reload required
- Seamless updates
- Maintains current view state

## 🛡️ Security Considerations

### Admin Authentication

Currently, the admin endpoints don't have strict authentication. For production:

1. Implement proper session management
2. Add JWT tokens or secure cookies
3. Add role-based access control
4. Implement rate limiting

### Input Validation

- WhatsApp link must be a valid URL
- Prevents XSS attacks
- SQL injection protection via SQLAlchemy ORM

## 📈 Future Enhancements

Potential improvements:

1. **Multiple Milestones**: Track 100, 200, 500, 1000 users
2. **Email Templates**: Customizable notification templates
3. **Dashboard Analytics**: Charts and graphs for registrations
4. **Export Data**: Export registration data to CSV/Excel
5. **Bulk Actions**: Bulk operations on entries
6. **Activity Log**: Track all admin actions

## 🐛 Troubleshooting

### Registration Count Not Updating

1. Check database connection
2. Verify entries have `payment_status = 'completed'` and `codm_id` is not null
3. Check browser console for JavaScript errors

### WhatsApp Link Not Saving

1. Verify database connection
2. Check `app_settings` table exists
3. Verify admin has proper permissions
4. Check server logs for errors

### Milestone Notification Not Sending

1. Check `ADMIN_EMAIL` environment variable
2. Verify email service is configured
3. Check `registration_milestones` table
4. Review notification logs

## 📞 Support

For issues or questions:
- Check server logs: `docker-compose logs backend`
- Review database: Check `app_settings` and `registration_milestones` tables
- Test API endpoints: Use curl or Postman to test endpoints

---

**The admin dashboard is now fully functional with registration tracking, milestone notifications, and WhatsApp link management!** 🎉
