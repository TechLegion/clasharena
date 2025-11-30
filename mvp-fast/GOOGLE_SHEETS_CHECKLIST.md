# Google Sheets Integration - Completion Checklist ✅

This checklist will help you complete the Google Sheets integration setup.

## ✅ Code Updates (Already Done)
- [x] Updated `google_sheets.py` to match CSV structure
- [x] Updated `main.py` to include dollar_rate and per_kill_value
- [x] Google API dependencies already in `requirements.txt`

## 📋 Setup Steps Required

### Step 1: Install Python Dependencies
```bash
cd mvp-fast/backend
pip install -r requirements.txt
```

**Verify these packages are installed:**
- `google-api-python-client`
- `google-auth`
- `google-auth-httplib2`

### Step 2: Get Google Cloud Credentials

Follow the detailed guide in `GET_CREDENTIALS.md`:

1. **Create Google Cloud Project**
   - Go to https://console.cloud.google.com/
   - Create a new project (e.g., "ClashArena")

2. **Enable Google Sheets API**
   - Search for "Google Sheets API" in the console
   - Click "Enable"

3. **Create Service Account**
   - Go to "APIs & Services" > "Credentials"
   - Click "+ CREATE CREDENTIALS" > "Service account"
   - Name it: `clasharena-sheets`
   - Click "Create and Continue" > "Done"

4. **Download JSON Key**
   - Click on the service account email
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key" > "JSON"
   - File will download automatically

5. **Place Credentials File**
   - Rename downloaded file to: `credentials.json`
   - Move it to: `mvp-fast/backend/credentials.json`
   - ⚠️ **IMPORTANT:** Never commit this file to Git!

### Step 3: Create/Setup Google Sheet

1. **Create a new Google Sheet** (or use existing one)
   - Go to https://sheets.google.com/
   - Create a new sheet

2. **Share Sheet with Service Account**
   - Click "Share" button (top right)
   - Open `mvp-fast/backend/credentials.json`
   - Copy the `client_email` value (looks like: `clasharena-sheets@project.iam.gserviceaccount.com`)
   - Paste email in Share dialog
   - Set permission to **"Editor"**
   - Uncheck "Notify people"
   - Click "Share"

3. **Get Spreadsheet ID**
   - Look at the Google Sheet URL:
     ```
     https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit
     ```
   - Copy the `SPREADSHEET_ID_HERE` part (long string between `/d/` and `/edit`)

### Step 4: Configure Environment Variables

Create or update `.env` file in `mvp-fast/` directory:

```env
# Google Sheets Integration
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id_here
GOOGLE_SHEET_NAME=Entries
GOOGLE_CREDENTIALS_FILE=credentials.json

# Optional: Customize these if needed (defaults shown)
DOLLAR_RATE=1500
PER_KILL_VALUE=0.6
```

**Replace `your_spreadsheet_id_here`** with the Spreadsheet ID from Step 3.

### Step 5: Verify File Structure

Your `mvp-fast/` directory should have:
```
mvp-fast/
├── .env                    ← Create this if it doesn't exist
├── backend/
│   ├── credentials.json    ← Place your credentials here
│   ├── google_sheets.py    ← Already updated ✅
│   └── main.py            ← Already updated ✅
└── ...
```

### Step 6: Test the Integration

1. **Start the server:**
   ```bash
   cd mvp-fast/backend
   uvicorn main:app --reload
   ```

2. **Submit a test entry** through your application

3. **Check your Google Sheet** - you should see:
   - Header row with columns: Time, Gamer ID Name, Gamer Email, Whatsapp Number, Region, Kill, Per kill Value, Money, Dollar Rate, Naira Amount, (empty), Bank Name, Bank Account Number, Paid
   - A new row with the entry data

## 🔍 Troubleshooting

### Issue: "Google credentials file not found"
**Solution:**
- Verify `credentials.json` is in `mvp-fast/backend/` folder
- Check filename is exactly `credentials.json` (not `credentials.json.json`)
- Verify `GOOGLE_CREDENTIALS_FILE` in `.env` matches

### Issue: "Permission denied" or "Access denied"
**Solution:**
- Make sure you shared the Google Sheet with the service account email
- Double-check the email in `credentials.json` matches what you shared
- Ensure permission is set to "Editor" (not "Viewer")

### Issue: "Spreadsheet not found"
**Solution:**
- Verify `GOOGLE_SPREADSHEET_ID` in `.env` is correct
- Make sure there are no extra spaces in the ID
- Verify the sheet exists and is accessible

### Issue: Data not appearing in sheet
**Solution:**
- Check server logs for error messages
- Verify `GOOGLE_SHEETS_ENABLED=true` in `.env`
- Make sure Google Sheets API is enabled in Google Cloud Console
- Check that the sheet name matches `GOOGLE_SHEET_NAME` (default: "Entries")

### Issue: Wrong data format in sheet
**Solution:**
- The integration now matches the CSV structure from `GAMERS DETAILS 2025 - 8am to 9am.csv`
- If headers don't match, delete the header row and let the system recreate it
- Verify your `.env` has correct `GOOGLE_SHEET_NAME`

## 📊 Expected Sheet Structure

When an entry is saved, the sheet will have these columns (matching your CSV):

| Column | Description | Example |
|--------|-------------|---------|
| Time | Entry time | "8:00 AM" |
| Gamer ID Name | CODM ID | "Enigma" |
| Gamer Email | Email address | "player@email.com" |
| Whatsapp Number | Phone number | "9130398056" |
| Region | Region | "Nigeria" |
| Kill | Kill count | "" (empty initially) |
| Per kill Value | Value per kill | "0.6" |
| Money | USD amount | "$3.60" |
| Dollar Rate | Exchange rate | "1500" |
| Naira Amount | NGN amount | "₦5,400.00" |
| (empty) | Empty column | "" |
| Bank Name | Bank name | "Zenith Bank" |
| Bank Account Number | Account number | "2271293622" |
| Paid | Payment status | "Yes" or "" |

## ✅ Final Checklist

Before considering the integration complete:

- [ ] Python dependencies installed (`pip install -r requirements.txt`)
- [ ] `credentials.json` file placed in `mvp-fast/backend/`
- [ ] Google Sheet created and shared with service account email
- [ ] Spreadsheet ID copied from Google Sheet URL
- [ ] `.env` file created/updated with all required variables
- [ ] `GOOGLE_SHEETS_ENABLED=true` in `.env`
- [ ] Server started successfully
- [ ] Test entry submitted
- [ ] Data appears correctly in Google Sheet

## 🎉 You're Done!

Once all steps are completed and a test entry appears in your Google Sheet, the integration is complete! All future entries will automatically be saved to your Google Sheet with the correct structure matching your CSV format.

