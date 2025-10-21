# ClashArena Match System Guide

## 🎮 How Matches Work

Your ClashArena app now has a comprehensive match system that handles competitive gaming matches from creation to completion. Here's how it all works:

## 📋 Match Flow Overview

### 1. **Match Creation**
- Player creates a match through the app
- Entry fee is deducted from wallet
- Match status: `pending` → `active`

### 2. **Game Data Integration**
- Real-time game data flows from the actual game to your backend
- Multiple integration methods supported
- Automatic validation and anti-cheat detection

### 3. **Match Completion**
- Final results are processed and validated
- Winnings are distributed automatically
- Match status: `active` → `completed`

## 🔄 Game Data Flow

### **Method 1: Direct Game Client Integration**
```
Game Client → Your App API → Match Processing
```

**How it works:**
1. Player plays the actual game (PUBG Mobile, Free Fire, etc.)
2. Game client sends match data to your webhook endpoints
3. Your backend processes and validates the data
4. Results are updated in real-time

**Example API calls from game client:**
```javascript
// Match start
POST /api/v1/webhooks/game-data
{
  "match_id": "match_123",
  "game_type": "pubg_mobile",
  "player_id": "player_456",
  "event_type": "match_start",
  "timestamp": "2024-01-15T10:00:00Z",
  "data": {
    "game_mode": "battle_royale",
    "map": "erangel",
    "players": 100
  }
}

// Match end
POST /api/v1/webhooks/match-result
{
  "match_id": "match_123",
  "player_id": "player_456",
  "final_score": {
    "placement": 1,
    "kills": 15,
    "damage": 2500,
    "survival_time": 1200
  },
  "screenshots": ["https://screenshot1.jpg", "https://screenshot2.jpg"],
  "replay_data": {
    "duration": 1200,
    "events": [...],
    "player_actions": [...]
  }
}
```

### **Method 2: Third-Party Game API Integration**
```
Game API → Your Integration Service → Match Processing
```

**How it works:**
1. Your backend polls game APIs (PUBG API, Free Fire API, etc.)
2. Integration service formats the data
3. Match results are automatically updated

**Supported Game APIs:**
- **PUBG Mobile**: Official PUBG API
- **Free Fire**: Garena API
- **Call of Duty Mobile**: Activision API

### **Method 3: Manual Result Submission**
```
Player → App Interface → Manual Verification → Match Processing
```

**How it works:**
1. Player submits screenshots and match details
2. Your system validates the submission
3. Results are processed after verification

## 🛡️ Anti-Cheat & Validation

### **Multi-Layer Validation System**

#### 1. **Data Validation**
- Required fields verification
- Data type and range validation
- Game-specific rule validation

#### 2. **Screenshot Verification**
- Image metadata analysis
- EXIF data validation
- File size and dimension checks
- Reverse image search for duplicates

#### 3. **Replay Data Analysis**
- Event sequence validation
- Timing consistency checks
- Impossible action detection
- Rapid action pattern analysis

#### 4. **Statistical Analysis**
- Unrealistic score detection
- Suspicious pattern recognition
- Cross-reference with game APIs
- Machine learning-based fraud detection

### **Validation Rules by Game**

#### PUBG Mobile
- Max kills: 30
- Max damage: 5,000
- Survival time: 30s - 30min
- Max accuracy: 95%

#### Free Fire
- Max kills: 25
- Max damage: 3,000
- Survival time: 1min - 20min
- Max accuracy: 90%

#### Call of Duty Mobile
- Max kills: 40
- Max damage: 6,000
- Survival time: 2min - 40min
- Max accuracy: 98%

## 🔌 Webhook Endpoints

### **Game Data Webhook**
```http
POST /api/v1/webhooks/game-data
Content-Type: application/json
X-Signature: sha256=...

{
  "match_id": "string",
  "game_type": "string",
  "player_id": "string",
  "event_type": "string",
  "timestamp": "2024-01-15T10:00:00Z",
  "data": {},
  "verification_hash": "string"
}
```

### **Match Result Webhook**
```http
POST /api/v1/webhooks/match-result
Content-Type: application/json
X-Signature: sha256=...

{
  "match_id": "string",
  "player_id": "string",
  "final_score": {},
  "placement": 1,
  "kills": 15,
  "damage": 2500,
  "survival_time": 1200,
  "screenshots": ["url1", "url2"],
  "replay_data": {},
  "verification_data": {}
}
```

### **Real-time Events Webhook**
```http
POST /api/v1/webhooks/game-events
Content-Type: application/json
X-Signature: sha256=...

[
  {
    "match_id": "string",
    "player_id": "string",
    "event_type": "kill",
    "timestamp": "2024-01-15T10:05:00Z",
    "event_data": {
      "target": "enemy_player",
      "weapon": "m416",
      "distance": 150
    }
  }
]
```

## 📡 Real-time Updates

### **WebSocket Connections**
Players can connect to real-time match updates:

```javascript
// Connect to match updates
const ws = new WebSocket('ws://localhost:8001/ws/match/match_123');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Match update:', data);
};

// Subscribe to match events
ws.send(JSON.stringify({
  type: 'subscribe_match',
  match_id: 'match_123'
}));
```

### **Update Types**
- `match_start`: Match has begun
- `match_update`: Real-time game events
- `match_end`: Match completed
- `result_processing`: Results being validated
- `winnings_distributed`: Winnings paid out

## 🔧 Integration Setup

### **1. Configure Webhook Security**
```python
# Set webhook secret
WEBHOOK_SECRET = "your-secure-webhook-secret"

# Verify signatures
def verify_webhook_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

### **2. Set up Game API Keys**
```python
# Environment variables
PUBG_API_KEY = "your-pubg-api-key"
FREE_FIRE_API_KEY = "your-freefire-api-key"
COD_API_KEY = "your-cod-api-key"
```

### **3. Configure Validation Rules**
```python
# Customize validation rules
VALIDATION_RULES = {
    "pubg_mobile": {
        "max_kills": 30,
        "max_damage": 5000,
        "min_survival_time": 30,
        "max_survival_time": 1800
    }
}
```

## 🎯 Match Types Supported

### **Battle Royale Games**
- PUBG Mobile (Solo, Duo, Squad)
- Free Fire (Solo, Duo, Squad)
- Call of Duty Mobile (Battle Royale)

### **Strategy Games**
- Clash Royale (Ladder, Challenges, Tournaments)
- Brawl Stars (Gem Grab, Brawl Ball, Heist)

### **Sports Games**
- FIFA Mobile (Friendly, League, Tournament)

## 📊 Match Analytics

### **Player Statistics**
- Win rate tracking
- Average kills per match
- Survival time analysis
- Damage per match

### **Match Analytics**
- Popular game types
- Average match duration
- Prize pool distribution
- Fraud detection metrics

### **Real-time Dashboard**
- Live match monitoring
- Player performance tracking
- System health metrics
- Fraud detection alerts

## 🚀 Getting Started

### **1. Start the Match System**
```bash
# Start the backend
docker-compose up -d

# Start monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

### **2. Test Match Creation**
```bash
# Create a test match
curl -X POST http://localhost:8001/api/v1/matches \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "game_type": "pubg_mobile",
    "match_type": "solo",
    "entry_fee": 100.0
  }'
```

### **3. Test Webhook Integration**
```bash
# Test webhook endpoint
curl -X POST http://localhost:8001/api/v1/webhooks/match-result \
  -H "Content-Type: application/json" \
  -H "X-Signature: sha256=..." \
  -d '{
    "match_id": "test_match_123",
    "player_id": "player_456",
    "placement": 1,
    "kills": 10,
    "damage": 2000
  }'
```

## 🔍 Monitoring & Debugging

### **Health Checks**
```bash
# Check match system health
python scripts/health_check.py

# Check specific match
curl http://localhost:8001/api/v1/webhooks/match/test_match_123/status
```

### **Logs**
```bash
# View match processing logs
docker-compose logs -f backend

# View validation logs
docker-compose logs -f worker
```

### **Metrics**
- Match creation rate
- Validation success rate
- Fraud detection rate
- Average processing time

## 🛠️ Customization

### **Adding New Games**
1. Create game integration service
2. Add validation rules
3. Configure API endpoints
4. Test integration

### **Custom Validation Rules**
```python
# Add custom validation
def custom_validation(match_data):
    # Your custom logic
    return validation_result
```

### **Custom Webhook Handlers**
```python
# Add custom webhook handler
@router.post("/custom-webhook")
async def custom_webhook(data: dict):
    # Your custom processing
    pass
```

## 📞 Support

For issues with the match system:
1. Check the logs: `docker-compose logs -f backend`
2. Verify webhook signatures
3. Check validation rules
4. Review match data format

---

**The match system is now fully automated and ready to handle competitive gaming matches with real-time data integration, comprehensive validation, and anti-cheat protection!** 🎮
