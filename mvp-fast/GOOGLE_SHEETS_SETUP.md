# Google Sheets Integration Setup Guide

This guide will help you set up Google Sheets integration to automatically save user registration data.

## Prerequisites

1. A Google account
2. A Google Sheet where you want to save the data

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the **Google Sheets API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click "Enable"

## Step 2: Create Service Account Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in the service account details:
   - **Name**: `clasharena-sheets` (or any name you prefer)
   - **Description**: `Service account for ClashArena Google Sheets integration`
4. Click "Create and Continue"
5. Skip the optional steps and click "Done"

## Step 3: Generate JSON Key

1. Click on the service account you just created
2. Go to the "Keys" tab
3. Click "Add Key" > "Create new key"
4. Select "JSON" format
5. Click "Create" - this will download a JSON file
6. **Rename the file to `credentials.json`**
7. **Move it to `mvp-fast/backend/` directory**

## Step 4: Share Google Sheet with Service Account

1. Open your Google Sheet (or create a new one)
2. Click the "Share" button
3. **Copy the email address** from the `credentials.json` file (it's in the `client_email` field)
   - Example: `clasharena-sheets@your-project.iam.gserviceaccount.com`
4. Paste this email in the "Share" dialog
5. Give it **Editor** permissions
6. Click "Send" (you don't need to notify)

## Step 5: Get Your Spreadsheet ID

1. Open your Google Sheet
2. Look at the URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
3. Copy the `SPREADSHEET_ID` (the long string between `/d/` and `/edit`)

## Step 6: Configure Environment Variables

Add these to your `.env` file in `mvp-fast/`:

```env
# Google Sheets Integration
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id_here
GOOGLE_SHEET_NAME=Entries
GOOGLE_CREDENTIALS_FILE=credentials.json
```

**Example:**
```env
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SPREADSHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
GOOGLE_SHEET_NAME=Entries
GOOGLE_CREDENTIALS_FILE=credentials.json
```

## Step 7: Install Dependencies

```bash
cd mvp-fast/backend
pip install -r requirements.txt
```

## Step 8: Test the Integration

1. Start your server:
   ```bash
   uvicorn main:app --reload
   ```

2. Register a test entry through your application

3. Check your Google Sheet - you should see a new row with the entry data

## Sheet Structure

The integration will automatically create a header row with these columns:

- **Timestamp** - When the entry was saved to the sheet
- **Payment Reference** - Unique payment reference
- **Email** - Player's email address
- **CODM ID** - Call of Duty Mobile ID
- **Phone** - Contact phone number
- **Bank Name** - Bank name
- **Account Number** - Bank account number
- **Account Name** - Account holder name
- **Entry Fee (NGN)** - Entry fee amount
- **Payment Status** - Payment status (pending/completed)
- **Is Winner** - Whether player is a winner (Yes/No)
- **Payout Status** - Payout status (pending/processing/completed)
- **Created At** - When the entry was created in the database

## Troubleshooting

### "Google credentials file not found"
- Make sure `credentials.json` is in the `mvp-fast/backend/` directory
- Check that `GOOGLE_CREDENTIALS_FILE` in `.env` matches the filename

### "Permission denied" or "Access denied"
- Make sure you shared the Google Sheet with the service account email
- Verify the service account email in `credentials.json` matches the one you shared with

### "Spreadsheet not found"
- Verify `GOOGLE_SPREADSHEET_ID` in `.env` is correct
- Make sure the sheet exists and is accessible

### Data not appearing in sheet
- Check server logs for any error messages
- Verify `GOOGLE_SHEETS_ENABLED=true` in `.env`
- Make sure the Google Sheets API is enabled in your Google Cloud project

## Disabling Google Sheets Integration

To disable the integration without removing the code:

```env
GOOGLE_SHEETS_ENABLED=false
```

The application will continue to work normally, but won't save data to Google Sheets.

## Security Notes

- **Never commit `credentials.json` to Git** - it's already in `.gitignore`
- Keep your service account credentials secure
- Only share the Google Sheet with trusted service accounts
- Consider using environment-specific service accounts for production vs development

