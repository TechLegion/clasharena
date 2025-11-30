"""
Google Sheets integration for saving user data
"""
import os
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Google Sheets configuration
GOOGLE_SHEETS_ENABLED = os.getenv("GOOGLE_SHEETS_ENABLED", "false").lower() == "true"
SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID", "")
SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Entries")
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    
    # Scopes required for Google Sheets API
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    _sheets_service = None
    
    def get_sheets_service():
        """Get or create Google Sheets service"""
        global _sheets_service
        if _sheets_service is None and GOOGLE_SHEETS_ENABLED:
            try:
                creds_path = os.path.join(os.path.dirname(__file__), CREDENTIALS_FILE)
                if not os.path.exists(creds_path):
                    logger.warning(f"Google credentials file not found: {creds_path}")
                    return None
                
                creds = Credentials.from_service_account_file(
                    creds_path, scopes=SCOPES
                )
                _sheets_service = build('sheets', 'v4', credentials=creds)
                logger.info("Google Sheets service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Google Sheets service: {e}")
                return None
        return _sheets_service
    
    def ensure_header_row(spreadsheet_id: str, sheet_name: str):
        """Ensure header row exists in the sheet"""
        service = get_sheets_service()
        if not service:
            return False
        
        try:
            # Get the current values
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A1:Z1"
            ).execute()
            
            values = result.get('values', [])
            
            # If no header row exists, create it
            if not values or len(values) == 0:
                headers = [
                    "Time",
                    "Gamer ID Name",
                    "Gamer Email",
                    "Whatsapp Number",
                    "Region",
                    "Kill",
                    "Per kill Value",
                    "Money",
                    "Dollar Rate",
                    "Naira Amount",
                    "",  # Empty column
                    "Bank Name",
                    "Bank Account Number",
                    "Paid"
                ]
                
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=f"{sheet_name}!A1",
                    valueInputOption='RAW',
                    body={'values': [headers]}
                ).execute()
                logger.info("Header row created in Google Sheet")
            
            return True
        except HttpError as e:
            logger.error(f"Error ensuring header row: {e}")
            return False
    
    def save_entry_to_sheets(entry_data: Dict) -> bool:
        """
        Save entry data to Google Sheets
        
        Args:
            entry_data: Dictionary containing entry information
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not GOOGLE_SHEETS_ENABLED or not SPREADSHEET_ID:
            logger.debug("Google Sheets integration disabled or not configured")
            return False
        
        service = get_sheets_service()
        if not service:
            logger.warning("Google Sheets service not available")
            return False
        
        try:
            # Ensure header row exists
            ensure_header_row(SPREADSHEET_ID, SHEET_NAME)
            
            # Prepare row data matching CSV structure
            # Columns: Time, Gamer ID Name, Gamer Email, Whatsapp Number, Region, 
            #          Kill, Per kill Value, Money, Dollar Rate, Naira Amount, 
            #          (empty), Bank Name, Bank Account Number, Paid
            
            # Format time as "8:00 AM" style (or current time)
            entry_time = datetime.now().strftime("%I:%M %p")
            
            # Get entry fee in NGN
            entry_fee_ngn = entry_data.get("entry_fee", 0) or 0
            
            # Calculate dollar amount (assuming dollar rate from entry_data or default 1500)
            dollar_rate = entry_data.get("dollar_rate", 1500)
            entry_fee_usd = float(entry_fee_ngn) / float(dollar_rate) if dollar_rate > 0 else 0
            
            # Format Naira amount with currency symbol
            naira_amount_str = f"₦{float(entry_fee_ngn):,.2f}" if entry_fee_ngn else "₦0.00"
            
            # Payment status for "Paid" column
            paid_status = "Yes" if entry_data.get("payment_status") == "completed" else ""
            
            row = [
                entry_time,  # Time
                entry_data.get("codm_id", ""),  # Gamer ID Name
                entry_data.get("contact_email", ""),  # Gamer Email
                entry_data.get("contact_phone", ""),  # Whatsapp Number
                entry_data.get("region", ""),  # Region (may not be in entry_data)
                "",  # Kill (to be filled later)
                entry_data.get("per_kill_value", 0.6),  # Per kill Value (default 0.6)
                f"${entry_fee_usd:.2f}",  # Money (USD)
                str(dollar_rate),  # Dollar Rate
                naira_amount_str,  # Naira Amount (formatted)
                "",  # Empty column
                entry_data.get("bank_name", ""),  # Bank Name
                entry_data.get("account_number", ""),  # Bank Account Number
                paid_status  # Paid
            ]
            
            # Find the last row with data to append right after it
            # Get all data in the sheet to find the true last row
            result = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!A:N"
            ).execute()
            
            existing_rows = result.get('values', [])
            
            # Find the last row that has any data by checking from the end
            last_row_with_data = 0
            for i in range(len(existing_rows) - 1, -1, -1):
                row_data = existing_rows[i]
                # Check if row has any non-empty cells
                if row_data and any(cell.strip() if isinstance(cell, str) else cell for cell in row_data):
                    last_row_with_data = i + 1  # +1 because sheets are 1-indexed
                    break
            
            # If no data found, start at row 1 (or row 2 if you want to preserve header)
            if last_row_with_data == 0:
                last_row_with_data = 1
            
            # Insert at the next row after last data
            next_row = last_row_with_data + 1
            
            # Append row to sheet at specific position (right after last data row)
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!A{next_row}",
                valueInputOption='RAW',
                body={'values': [row]}
            ).execute()
            
            logger.info(f"Entry saved to Google Sheets: {entry_data.get('payment_reference')}")
            return True
            
        except HttpError as e:
            logger.error(f"Error saving to Google Sheets: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving to Google Sheets: {e}")
            return False
    
    def update_entry_in_sheets(payment_reference: str, updates: Dict) -> bool:
        """
        Update an existing entry in Google Sheets
        
        Args:
            payment_reference: Payment reference to find the row
            updates: Dictionary of fields to update
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not GOOGLE_SHEETS_ENABLED or not SPREADSHEET_ID:
            return False
        
        service = get_sheets_service()
        if not service:
            return False
        
        try:
            # Find the row with matching CODM ID (Gamer ID Name) in column B
            # Since payment_reference might not be in the sheet, we'll search by CODM ID or email
            result = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!B:C"  # Columns B (Gamer ID Name) and C (Gamer Email)
            ).execute()
            
            values = result.get('values', [])
            row_index = None
            
            # Search by CODM ID first, then by email
            search_codm_id = updates.get("codm_id", "")
            search_email = updates.get("contact_email", "")
            
            # Remove search fields from updates to avoid trying to update them
            search_updates = {k: v for k, v in updates.items() 
                            if k not in ["codm_id", "contact_email"]}
            
            for idx, row in enumerate(values, start=1):
                if row and len(row) >= 2:
                    if (search_codm_id and row[0] == search_codm_id) or \
                       (search_email and len(row) > 1 and row[1] == search_email):
                        row_index = idx + 1  # +1 for header row, +1 for 1-based indexing
                        break
            
            if row_index is None:
                logger.warning(f"Entry not found in sheet: payment_reference={payment_reference}, codm_id={search_codm_id}, email={search_email}")
                return False
            
            # Use search_updates instead of updates for the actual update
            updates = search_updates
            
            # Update specific columns based on updates dict
            # Column mapping: A=Time, B=Gamer ID Name, C=Gamer Email, D=Whatsapp Number, 
            #                 E=Region, F=Kill, G=Per kill Value, H=Money, I=Dollar Rate,
            #                 J=Naira Amount, K=(empty), L=Bank Name, M=Bank Account Number, N=Paid
            column_map = {
                "codm_id": "B",
                "contact_email": "C",
                "contact_phone": "D",
                "region": "E",
                "kill": "F",
                "per_kill_value": "G",
                "bank_name": "L",
                "account_number": "M",
                "payment_status": "N"  # Paid column
            }
            
            update_requests = []
            for field, column in column_map.items():
                if field in updates:
                    value = updates[field]
                    # Format payment_status for Paid column
                    if field == "payment_status":
                        value = "Yes" if value == "completed" else ""
                    # Format per_kill_value and kill as numbers
                    elif field in ["per_kill_value", "kill"]:
                        value = str(value) if value else ""
                    # Format money if dollar amount is being updated
                    elif field == "money" and "entry_fee" in updates:
                        dollar_rate = updates.get("dollar_rate", 1500)
                        entry_fee_ngn = updates.get("entry_fee", 0)
                        value = f"${float(entry_fee_ngn) / float(dollar_rate):.2f}" if dollar_rate > 0 else "$0.00"
                    # Format naira amount if entry_fee is being updated
                    elif field == "naira_amount" and "entry_fee" in updates:
                        entry_fee_ngn = updates.get("entry_fee", 0)
                        value = f"₦{float(entry_fee_ngn):,.2f}" if entry_fee_ngn else "₦0.00"
                    
                    update_requests.append({
                        "range": f"{SHEET_NAME}!{column}{row_index}",
                        "values": [[str(value)]]
                    })
            
            if update_requests:
                body = {
                    "valueInputOption": "RAW",
                    "data": update_requests
                }
                service.spreadsheets().values().batchUpdate(
                    spreadsheetId=SPREADSHEET_ID,
                    body=body
                ).execute()
                logger.info(f"Entry updated in Google Sheets: {payment_reference}")
                return True
            
            return False
            
        except HttpError as e:
            logger.error(f"Error updating Google Sheets: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating Google Sheets: {e}")
            return False

except ImportError:
    logger.warning("Google Sheets API libraries not installed. Install with: pip install google-api-python-client google-auth")
    
    def get_sheets_service():
        return None
    
    def save_entry_to_sheets(entry_data: Dict) -> bool:
        return False
    
    def update_entry_in_sheets(payment_reference: str, updates: Dict) -> bool:
        return False

