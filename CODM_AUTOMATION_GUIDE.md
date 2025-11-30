# CODM Match Automation Guide for ClashArena

## 🎮 Overview

This guide covers the implementation of Call of Duty Mobile (CODM) match automation for ClashArena, using a hybrid semi-automated approach that combines manual result submission, Discord bot integration, admin verification tools, and workflow automation.

## 🚀 Implementation Strategy

Given the constraints around CODM automation (no official API access), we've implemented a **hybrid semi-automated system** that includes:

1. **Manual Result Submission** (Primary method)
2. **Discord Bot Integration** (Community management)
3. **Admin Verification Tools** (Quality control)
4. **Workflow Automation** (Airtable/Zapier integration)

## 📋 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Player        │    │   Discord Bot    │    │   Admin Panel   │
│   Submission    │    │   Management     │    │   Verification  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ClashArena Backend                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   CODM API      │  │   Celery Tasks  │  │   Airtable      │ │
│  │   Endpoints     │  │   Processing    │  │   Integration   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Database      │    │   Zapier         │    │   Notifications │
│   Storage       │    │   Workflows      │    │   & Alerts      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🔧 Setup Instructions

### 1. Environment Configuration

Add the following environment variables to your `.env` file:

```bash
# CODM Integration
CODM_ENABLED=true
CODM_DISCORD_TOKEN=your-discord-bot-token
CODM_DISCORD_CHANNEL_ID=your-discord-channel-id

# Airtable Integration
AIRTABLE_API_KEY=your-airtable-api-key
AIRTABLE_BASE_ID=your-airtable-base-id

# Zapier Integration
ZAPIER_WEBHOOK_URL=your-zapier-webhook-url

# Admin Configuration
ADMIN_EMAIL=admin@clasharena.com
ADMIN_DISCORD_ID=your-discord-user-id
```

### 2. Database Setup

The CODM system uses your existing database with additional fields for CODM-specific data:

```sql
-- Add CODM-specific fields to existing tables
ALTER TABLE matches ADD COLUMN codm_game_mode VARCHAR(50);
ALTER TABLE matches ADD COLUMN codm_kills INTEGER DEFAULT 0;
ALTER TABLE matches ADD COLUMN codm_deaths INTEGER DEFAULT 0;
ALTER TABLE matches ADD COLUMN codm_assists INTEGER DEFAULT 0;
ALTER TABLE matches ADD COLUMN codm_score INTEGER DEFAULT 0;
ALTER TABLE matches ADD COLUMN codm_placement INTEGER DEFAULT 0;
ALTER TABLE matches ADD COLUMN codm_screenshots TEXT;
ALTER TABLE matches ADD COLUMN codm_confidence_score FLOAT DEFAULT 0.0;
ALTER TABLE matches ADD COLUMN codm_requires_review BOOLEAN DEFAULT FALSE;
```

### 3. Airtable Setup

Create the following tables in your Airtable base:

#### CODM_Matches Table
- Match ID (Single line text)
- Player ID (Single line text)
- Player Name (Single line text)
- Game Mode (Single select: Battle Royale, Multiplayer, Ranked)
- Kills (Number)
- Deaths (Number)
- Assists (Number)
- Score (Number)
- Placement (Number)
- Status (Single select: Pending, Approved, Rejected, Flagged)
- Created At (Date)
- Updated At (Date)
- Admin Notes (Long text)
- Confidence Score (Number)
- Requires Review (Checkbox)
- Screenshots (Attachment)

#### Admin_Notifications Table
- Match ID (Single line text)
- Player ID (Single line text)
- Player Name (Single line text)
- Notification Type (Single select: New Submission, Approval, Rejection)
- Priority (Single select: High, Medium, Low)
- Message (Long text)
- Status (Single select: Unread, Read, Archived)
- Created At (Date)
- Action Required (Single line text)

#### Player_Notifications Table
- Match ID (Single line text)
- Player ID (Single line text)
- Notification Type (Single select: Match Approved, Match Rejected, Winnings)
- Message (Long text)
- Status (Single select: Unread, Read, Archived)
- Created At (Date)

### 4. Discord Bot Setup

1. **Create Discord Application:**
   - Go to https://discord.com/developers/applications
   - Create new application
   - Go to Bot section and create bot
   - Copy the bot token

2. **Invite Bot to Server:**
   - Go to OAuth2 > URL Generator
   - Select scopes: `bot`, `applications.commands`
   - Select permissions: `Send Messages`, `Read Message History`, `Manage Roles`
   - Use generated URL to invite bot

3. **Configure Bot:**
   ```bash
   # Set environment variables
   export DISCORD_BOT_TOKEN=your-bot-token
   export DISCORD_CHANNEL_ID=your-channel-id
   ```

### 5. Zapier Integration Setup

1. **Create Zapier Account:**
   - Sign up at https://zapier.com
   - Create new Zap

2. **Configure Webhook:**
   - Use "Webhooks by Zapier" as trigger
   - Copy webhook URL
   - Set up actions (email notifications, Slack messages, etc.)

## 🎯 Usage Guide

### For Players

#### 1. Submit Match Result

**Via API:**
```bash
curl -X POST http://localhost:8001/api/v1/codm_matches/submit-result \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "match_id": "match_123",
    "game_mode": "battle_royale",
    "kills": 15,
    "deaths": 3,
    "assists": 5,
    "score": 2500,
    "placement": 1
  }'
```

**Via Discord:**
```
!submit_result match_123 15 3 2500
```

#### 2. View Your Matches

**Via API:**
```bash
curl -X GET http://localhost:8001/api/v1/codm_matches/submissions \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Via Discord:**
```
!my_matches
```

#### 3. View Your Statistics

**Via API:**
```bash
curl -X GET http://localhost:8001/api/v1/codm_matches/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Via Discord:**
```
!my_stats
```

### For Admins

#### 1. View Pending Submissions

**Via API:**
```bash
curl -X GET http://localhost:8001/api/v1/codm_matches/admin/pending \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Via Discord:**
```
!admin_pending
```

#### 2. Approve Submission

**Via API:**
```bash
curl -X POST http://localhost:8001/api/v1/codm_matches/admin/approve/match_123 \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"admin_notes": "Verified screenshots and stats"}'
```

**Via Discord:**
```
!admin_approve match_123 Verified screenshots and stats
```

#### 3. Reject Submission

**Via API:**
```bash
curl -X POST http://localhost:8001/api/v1/codm_matches/admin/reject/match_123 \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rejection_reason": "Suspicious kill count"}'
```

**Via Discord:**
```
!admin_reject match_123 Suspicious kill count
```

## 🔄 Workflow Automation

### Airtable Workflows

1. **New Submission Workflow:**
   - Player submits result → Airtable record created
   - Admin notification sent
   - Status set to "Pending"

2. **Approval Workflow:**
   - Admin approves → Status updated to "Approved"
   - Player notification sent
   - Winnings processed

3. **Rejection Workflow:**
   - Admin rejects → Status updated to "Rejected"
   - Player notification sent
   - Entry fee refunded

### Zapier Workflows

1. **Match Created:**
   - Trigger: New Airtable record
   - Action: Send email to admin
   - Action: Post to Slack channel

2. **Match Approved:**
   - Trigger: Status changed to "Approved"
   - Action: Send email to player
   - Action: Update player balance
   - Action: Post to Discord channel

3. **Match Rejected:**
   - Trigger: Status changed to "Rejected"
   - Action: Send email to player
   - Action: Refund entry fee
   - Action: Post to Discord channel

## 📊 Monitoring & Analytics

### Key Metrics

- **Submission Rate:** Number of submissions per day
- **Approval Rate:** Percentage of approved submissions
- **Processing Time:** Average time from submission to approval
- **Player Engagement:** Active players and match participation

### Airtable Dashboards

Create dashboards in Airtable to track:
- Pending submissions
- Approval rates
- Player statistics
- Admin workload

### Discord Monitoring

Monitor Discord bot activity:
- Command usage
- Error rates
- User engagement
- Admin response times

## 🛡️ Security & Fraud Prevention

### Validation Rules

1. **Kill Count Validation:**
   - Maximum 50 kills per match
   - Suspicious patterns detection
   - Cross-reference with game mode

2. **Screenshot Validation:**
   - Image metadata analysis
   - Timestamp verification
   - Duplicate detection

3. **Statistical Analysis:**
   - K/D ratio validation
   - Score consistency checks
   - Unrealistic performance detection

### Admin Review Process

1. **Automatic Flagging:**
   - High kill counts
   - Perfect scores
   - Suspicious patterns

2. **Manual Review:**
   - Admin verification required
   - Screenshot analysis
   - Player history check

3. **Escalation:**
   - Senior admin review
   - Additional verification
   - Player investigation

## 🚀 Deployment

### 1. Start CODM Services

```bash
# Start Celery worker for CODM tasks
celery -A app.core.celery_app worker -l info -Q codm

# Start Discord bot
python backend/app/discord_bot/codm_bot.py

# Start Airtable integration
python backend/app/workflows/airtable_integration.py
```

### 2. Configure Webhooks

```bash
# Set up Zapier webhooks
export ZAPIER_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/your-webhook-url

# Configure Discord webhooks
export DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-url
```

### 3. Test Integration

```bash
# Test CODM submission
python scripts/test_codm_submission.py

# Test Discord bot
python scripts/test_discord_bot.py

# Test Airtable integration
python scripts/test_airtable_integration.py
```

## 🔧 Troubleshooting

### Common Issues

1. **Discord Bot Not Responding:**
   - Check bot token
   - Verify permissions
   - Check channel access

2. **Airtable Integration Failing:**
   - Verify API key
   - Check base ID
   - Validate table structure

3. **Zapier Webhooks Not Triggering:**
   - Check webhook URL
   - Verify payload format
   - Check Zapier configuration

### Debug Commands

```bash
# Check CODM service status
curl http://localhost:8001/api/v1/codm_matches/stats

# Test Discord bot
!codm_help

# Check Airtable connection
python scripts/test_airtable_connection.py
```

## 📈 Future Enhancements

### Planned Features

1. **Machine Learning Integration:**
   - Fraud detection algorithms
   - Pattern recognition
   - Automated validation

2. **Advanced Analytics:**
   - Player behavior analysis
   - Match prediction
   - Performance insights

3. **Mobile App Integration:**
   - Direct screenshot upload
   - Real-time notifications
   - Match tracking

4. **Tournament System:**
   - Automated tournaments
   - Bracket management
   - Prize distribution

### API Improvements

1. **Real-time Updates:**
   - WebSocket connections
   - Live match tracking
   - Instant notifications

2. **Advanced Validation:**
   - Video analysis
   - Replay verification
   - Cross-platform validation

## 📞 Support

For issues with CODM automation:

1. **Check Logs:**
   ```bash
   docker-compose logs -f backend
   docker-compose logs -f worker
   ```

2. **Verify Configuration:**
   ```bash
   python scripts/verify_codm_config.py
   ```

3. **Test Integration:**
   ```bash
   python scripts/test_codm_integration.py
   ```

4. **Contact Support:**
   - Discord: #codm-support
   - Email: support@clasharena.com
   - Documentation: https://docs.clasharena.com/codm

---

**The CODM automation system is now fully integrated and ready to handle Call of Duty Mobile matches with semi-automated processing, Discord community management, and comprehensive admin tools!** 🎮
