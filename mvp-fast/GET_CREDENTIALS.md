# Quick Guide: Getting Google Sheets Credentials

Follow these steps to get your `credentials.json` file:

## Step 1: Go to Google Cloud Console

1. Visit: https://console.cloud.google.com/
2. Sign in with your Google account

## Step 2: Create a New Project

1. Click the project dropdown at the top (next to "Google Cloud")
2. Click **"New Project"**
3. Enter project name: `ClashArena` (or any name)
4. Click **"Create"**
5. Wait a few seconds, then select your new project from the dropdown

## Step 3: Enable Google Sheets API

1. In the search bar at the top, type: **"Google Sheets API"**
2. Click on **"Google Sheets API"** from the results
3. Click the blue **"Enable"** button
4. Wait for it to enable (usually takes 10-20 seconds)

## Step 4: Create Service Account

1. In the left sidebar, click **"APIs & Services"** > **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"** at the top
3. Select **"Service account"**

### Fill in the form:
- **Service account name**: `clasharena-sheets` (or any name)
- **Service account ID**: Will auto-fill (leave as is)
- **Description**: `For ClashArena Google Sheets integration` (optional)

4. Click **"Create and Continue"**
5. Skip the optional steps (click **"Continue"** then **"Done"**)

## Step 5: Create and Download JSON Key

1. You should now see your service account in the list
2. **Click on the service account name** (the email address)
3. Go to the **"Keys"** tab
4. Click **"Add Key"** > **"Create new key"**
5. Select **"JSON"** format
6. Click **"Create"**
7. A JSON file will automatically download to your computer

## Step 6: Rename and Move the File

1. **Rename the downloaded file** to: `credentials.json`
   - The file will have a long name like `your-project-xxxxx-xxxxx.json`
   - Right-click > Rename > `credentials.json`

2. **Move it to the backend folder**:
   - Copy `credentials.json`
   - Navigate to: `mvp-fast/backend/`
   - Paste the file there

   **Full path should be:** `mvp-fast/backend/credentials.json`

## Step 7: Create or Open Your Google Sheet

1. Go to: https://sheets.google.com/
2. Create a new sheet (or open an existing one)
3. **Name it** (e.g., "ClashArena Entries") - this is optional, just for organization

## Step 8: Share Sheet with Service Account

1. Click the **"Share"** button (top right)
2. **Open your `credentials.json` file** (in `mvp-fast/backend/`)
3. Find the line that says `"client_email"` - it looks like:
   ```json
   "client_email": "clasharena-sheets@your-project.iam.gserviceaccount.com"
   ```
4. **Copy the entire email address** (the part after `"client_email": "` and before `"`)
5. **Paste it** into the Google Sheet "Share" dialog
6. Make sure permissions are set to **"Editor"**
7. **Uncheck** "Notify people" (you don't need to notify a service account)
8. Click **"Share"**

## Step 9: Get Your Spreadsheet ID

1. Look at your Google Sheet URL in the browser
2. It will look like:
   ```
   https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
   ```
3. **Copy the long string** between `/d/` and `/edit`
   - In the example above, it's: `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms`
   - This is your **Spreadsheet ID**

## Step 10: Update Your .env File

Open `mvp-fast/.env` and add these lines:

```env
# Google Sheets Integration
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SPREADSHEET_ID=paste_your_spreadsheet_id_here
GOOGLE_SHEET_NAME=Entries
GOOGLE_CREDENTIALS_FILE=credentials.json
```

**Replace `paste_your_spreadsheet_id_here`** with the ID you copied in Step 9.

## Step 11: Install Dependencies

```bash
cd mvp-fast/backend
pip install -r requirements.txt
```

## Step 12: Test It!

1. Start your server:
   ```bash
   uvicorn main:app --reload
   ```

2. Register a test entry through your app

3. Check your Google Sheet - you should see a new row!

---

## Troubleshooting

### "File not found" error
- Make sure `credentials.json` is in `mvp-fast/backend/` folder
- Check the filename is exactly `credentials.json` (not `credentials.json.json`)

### "Permission denied" error
- Make sure you shared the Google Sheet with the service account email
- Double-check the email in `credentials.json` matches what you shared

### "Spreadsheet not found" error
- Verify the Spreadsheet ID in `.env` is correct
- Make sure there are no extra spaces in the ID

### Still having issues?
Check the server logs - they will show specific error messages to help debug.

