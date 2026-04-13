"""
Google Sheets integration for saving user data.

Tab routing: the caller (main.py) passes the current admin lobby name as
``target_sheet``.  When provided the entry is written directly to that tab
(creating it + header if it doesn't exist yet).  The old env-based rotation
(``GOOGLE_SHEET_NAME`` / ``MAX_ENTRIES_PER_SHEET``) is used only as a
fallback when no explicit name is given.
"""
import os
import logging
import re
import time
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Google Sheets configuration
GOOGLE_SHEETS_ENABLED = os.getenv("GOOGLE_SHEETS_ENABLED", "false").lower() == "true"
SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID", "")
SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Entries")
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON", "")
MAX_ENTRIES_PER_SHEET = int(os.getenv("MAX_ENTRIES_PER_SHEET", "100"))
SHEET_COUNT_CACHE_SECONDS = float(os.getenv("GOOGLE_SHEET_COUNT_CACHE_SECONDS", "30"))
_sheet_row_count_cache: dict[str, tuple[int, float]] = {}


def _parse_lobby_sheet_name(sheet_name: str) -> Optional[tuple[str, int]]:
    """
    If `GOOGLE_SHEET_NAME` is set like `lobby 1`, return ("lobby", 1).
    This enables lobby-synced tab naming: lobby 1, lobby 2, lobby 3, ...
    """
    if not sheet_name:
        return None

    match = re.match(r"^\s*([Ll]obby)\s*(\d+)\s*$", sheet_name, flags=re.IGNORECASE)
    if not match:
        return None

    prefix_word = match.group(1)
    start_index = int(match.group(2))
    return prefix_word, start_index

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
                # PRIORITY 1: Check if credentials are provided as JSON string (environment variable)
                # This is preferred for Railway/deployment where files might not be accessible
                if GOOGLE_CREDENTIALS_JSON:
                    import json
                    import base64
                    try:
                        # Try to decode as base64 first, if that fails, use as plain JSON
                        try:
                            credentials_json = base64.b64decode(GOOGLE_CREDENTIALS_JSON).decode('utf-8')
                            logger.info("Decoded base64 encoded credentials from GOOGLE_CREDENTIALS_JSON")
                        except:
                            credentials_json = GOOGLE_CREDENTIALS_JSON
                            logger.info("Using plain JSON credentials from GOOGLE_CREDENTIALS_JSON")
                        
                        creds_dict = json.loads(credentials_json)
                        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
                        _sheets_service = build('sheets', 'v4', credentials=creds)
                        logger.info("Google Sheets service initialized successfully from environment variable")
                        return _sheets_service
                    except Exception as e:
                        logger.error(f"Failed to parse credentials from GOOGLE_CREDENTIALS_JSON: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                        return None
                
                # PRIORITY 2: Try to find credentials file (for local development)
                # Try multiple possible paths for credentials file
                # Check if CREDENTIALS_FILE is already an absolute path
                if os.path.isabs(CREDENTIALS_FILE) and os.path.exists(CREDENTIALS_FILE):
                    creds_path = CREDENTIALS_FILE
                else:
                    possible_paths = [
                        CREDENTIALS_FILE,  # Try as-is first (might be absolute or relative)
                        os.path.join(os.path.dirname(__file__), CREDENTIALS_FILE),  # backend/credentials.json
                        os.path.join(os.path.dirname(__file__), "..", CREDENTIALS_FILE),  # mvp-fast/credentials.json
                        os.path.join(os.getcwd(), CREDENTIALS_FILE),  # Current working directory
                        os.path.join("/app", CREDENTIALS_FILE),  # Railway/Docker path
                        os.path.join("/app", "backend", CREDENTIALS_FILE),  # Railway backend path
                        os.path.join("/app", "mvp-fast", CREDENTIALS_FILE),  # Railway mvp-fast path
                    ]
                    
                    creds_path = None
                    for path in possible_paths:
                        if os.path.exists(path):
                            creds_path = path
                            break
                
                if not creds_path:
                    logger.warning(f"Google credentials file not found. Tried paths:")
                    for path in possible_paths if 'possible_paths' in locals() else [CREDENTIALS_FILE]:
                        exists = os.path.exists(path) if (not os.path.isabs(path) or os.path.exists(path)) else False
                        logger.warning(f"  - {path} (exists: {exists})")
                    logger.warning(f"Current working directory: {os.getcwd()}")
                    logger.warning(f"File directory: {os.path.dirname(__file__)}")
                    logger.warning(f"CREDENTIALS_FILE env var: {CREDENTIALS_FILE}")
                    logger.warning("Consider using GOOGLE_CREDENTIALS_JSON environment variable instead")
                    return None
                
                logger.info(f"Using credentials file: {creds_path}")
                creds = Credentials.from_service_account_file(
                    creds_path, scopes=SCOPES
                )
                
                _sheets_service = build('sheets', 'v4', credentials=creds)
                logger.info("Google Sheets service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Google Sheets service: {e}")
                import traceback
                logger.error(traceback.format_exc())
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
                    "In Game Name (IGN)",
                    "Number",
                    "Region",
                    "Bank Name",
                    "Bank Account Number",
                    "Kill",
                    "Payout",
                    "Paid",
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
    
    def _count_data_rows_from_values(rows: list) -> int:
        """Count non-header data rows in A:I values (matches app + manual layout)."""
        entry_count = 0
        for row in rows:
            if row and len(row) > 0:
                has_data = any(cell.strip() if isinstance(cell, str) else cell for cell in row)
                if has_data and len(row) > 0 and row[0] != "Time":
                    entry_count += 1
        return entry_count

    def count_entries_in_sheet(spreadsheet_id: str, sheet_name: str) -> int:
        """Count the number of data entries (excluding header) in a sheet"""
        service = get_sheets_service()
        if not service:
            return 0

        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A:I"
            ).execute()
            rows = result.get('values', [])
            return _count_data_rows_from_values(rows)
        except Exception as e:
            logger.error(f"Error counting entries: {e}")
            return 0

    def fetch_sheet_data_row_count(tab_name: str) -> Optional[int]:
        """
        Read current data row count for a tab. Returns None if Sheets is off, misconfigured,
        or the API call fails (so callers can fall back to DB-only counts).
        """
        if not GOOGLE_SHEETS_ENABLED or not SPREADSHEET_ID or not tab_name:
            return None
        service = get_sheets_service()
        if not service:
            return None
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{tab_name}!A:I"
            ).execute()
            rows = result.get("values", [])
            return _count_data_rows_from_values(rows)
        except HttpError as e:
            logger.warning("Could not read sheet row count for tab %r: %s", tab_name, e)
            return None
        except Exception as e:
            logger.warning("Could not read sheet row count for tab %r: %s", tab_name, e)
            return None

    def get_sheet_data_row_count_cached(tab_name: str) -> Optional[int]:
        """Cached fetch of tab row count for public spot math (manual rows included)."""
        if not tab_name:
            return None
        now = time.time()
        hit = _sheet_row_count_cache.get(tab_name)
        if hit is not None and (now - hit[1]) < SHEET_COUNT_CACHE_SECONDS:
            return hit[0]
        n = fetch_sheet_data_row_count(tab_name)
        if n is not None:
            _sheet_row_count_cache[tab_name] = (n, now)
        return n
    
    def create_new_sheet(spreadsheet_id: str, base_sheet_name: str) -> Optional[str]:
        """Create a new sheet and return its name"""
        service = get_sheets_service()
        if not service:
            return None
        
        try:
            # Get all existing sheets to find the next number
            spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheets = spreadsheet.get('sheets', [])
            
            # Find existing sheets with the same base name
            existing_numbers = []
            for sheet in sheets:
                sheet_title = sheet['properties']['title']
                if sheet_title.startswith(base_sheet_name):
                    # Try to extract number from names like "8am to 9am - Part 2"
                    if " - Part " in sheet_title:
                        try:
                            part_num = int(sheet_title.split(" - Part ")[1])
                            existing_numbers.append(part_num)
                        except:
                            pass
                    elif sheet_title == base_sheet_name:
                        existing_numbers.append(1)  # Original sheet is part 1
            
            # Determine next part number
            if existing_numbers:
                next_part = max(existing_numbers) + 1
            else:
                next_part = 2  # First new sheet is Part 2
            
            new_sheet_name = f"{base_sheet_name} - Part {next_part}"
            
            # Create the new sheet
            request_body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': new_sheet_name
                        }
                    }
                }]
            }
            
            response = service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=request_body
            ).execute()
            
            logger.info(f"Created new sheet: {new_sheet_name}")
            
            # Create header row in the new sheet
            ensure_header_row(spreadsheet_id, new_sheet_name)
            
            return new_sheet_name
            
        except Exception as e:
            logger.error(f"Error creating new sheet: {e}")
            return None
    
    def get_active_sheet_name() -> str:
        """Get the active sheet name, rotating/creating tabs at 100 entries."""
        if not GOOGLE_SHEETS_ENABLED or not SPREADSHEET_ID:
            return SHEET_NAME

        # Lobby-style naming:
        # If `GOOGLE_SHEET_NAME` is set like `lobby 1`, rotate tabs as:
        #   lobby 1, lobby 2, lobby 3, ...
        lobby_info = _parse_lobby_sheet_name(SHEET_NAME)
        if lobby_info:
            prefix_word, start_index = lobby_info

            service = get_sheets_service()
            if not service:
                return SHEET_NAME

            try:
                spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
                sheets = spreadsheet.get("sheets", [])

                existing_titles = [
                    (sheet.get("properties", {}).get("title", "") or "") for sheet in sheets
                ]
                existing_titles_lower = {t.lower() for t in existing_titles}

                lobby_regex = re.compile(
                    rf"^\s*{re.escape(prefix_word)}\s*(\d+)\s*$",
                    flags=re.IGNORECASE,
                )
                matching_indices = []
                for title in existing_titles:
                    m = lobby_regex.match(title)
                    if m:
                        matching_indices.append(int(m.group(1)))

                current_index = max(matching_indices) if matching_indices else start_index
                current_sheet = f"{prefix_word} {current_index}"

                # Ensure the current lobby tab exists (create if missing).
                if current_sheet.lower() not in existing_titles_lower:
                    request_body = {
                        "requests": [
                            {"addSheet": {"properties": {"title": current_sheet}}}
                        ]
                    }
                    service.spreadsheets().batchUpdate(
                        spreadsheetId=SPREADSHEET_ID, body=request_body
                    ).execute()
                    ensure_header_row(SPREADSHEET_ID, current_sheet)

                entry_count = count_entries_in_sheet(SPREADSHEET_ID, current_sheet)

                # If we've reached the limit, create the next lobby tab.
                if entry_count >= MAX_ENTRIES_PER_SHEET:
                    next_index = current_index + 1
                    new_sheet_name = f"{prefix_word} {next_index}"
                    logger.info(
                        f"Sheet '{current_sheet}' has {entry_count} entries (limit: {MAX_ENTRIES_PER_SHEET}). "
                        f"Creating new lobby sheet: {new_sheet_name}"
                    )

                    request_body = {
                        "requests": [
                            {"addSheet": {"properties": {"title": new_sheet_name}}}
                        ]
                    }
                    service.spreadsheets().batchUpdate(
                        spreadsheetId=SPREADSHEET_ID, body=request_body
                    ).execute()
                    ensure_header_row(SPREADSHEET_ID, new_sheet_name)
                    return new_sheet_name

                return current_sheet

            except Exception as e:
                logger.error(f"Error getting active lobby sheet: {e}")
                return SHEET_NAME

        # Default behavior (part-style tabs) - existing logic.
        base_name = SHEET_NAME.split(" - Part ")[0] if " - Part " in SHEET_NAME else SHEET_NAME

        service = get_sheets_service()
        if not service:
            return SHEET_NAME

        try:
            spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
            sheets = spreadsheet.get("sheets", [])

            matching_sheets = []
            for sheet in sheets:
                sheet_title = sheet["properties"]["title"]
                if sheet_title == base_name or sheet_title.startswith(f"{base_name} - Part "):
                    matching_sheets.append(sheet_title)

            matching_sheets.sort()
            current_sheet = matching_sheets[-1] if matching_sheets else SHEET_NAME

            entry_count = count_entries_in_sheet(SPREADSHEET_ID, current_sheet)

            if entry_count >= MAX_ENTRIES_PER_SHEET:
                logger.info(
                    f"Sheet '{current_sheet}' has {entry_count} entries (limit: {MAX_ENTRIES_PER_SHEET}). Creating new sheet..."
                )
                new_sheet_name = create_new_sheet(SPREADSHEET_ID, base_name)
                if new_sheet_name:
                    logger.info(f"Created and switched to new sheet: {new_sheet_name}")
                    return new_sheet_name
                else:
                    logger.warning("Failed to create new sheet, continuing with current sheet")

            return current_sheet

        except Exception as e:
            logger.error(f"Error getting active sheet: {e}")
            return SHEET_NAME
    
    def ensure_sheet_tab(service, spreadsheet_id: str, tab_name: str) -> bool:
        """Create the named tab if it doesn't exist yet, then ensure the header row."""
        try:
            spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            existing = {
                (s.get("properties", {}).get("title", "") or "")
                for s in spreadsheet.get("sheets", [])
            }
            if tab_name not in existing:
                service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={"requests": [{"addSheet": {"properties": {"title": tab_name}}}]},
                ).execute()
                logger.info("Created new sheet tab: %s", tab_name)
            ensure_header_row(spreadsheet_id, tab_name)
            return True
        except Exception as e:
            logger.error("Error ensuring sheet tab '%s': %s", tab_name, e)
            return False

    def list_sheet_tabs(spreadsheet_id: str) -> Optional[list]:
        """Return a list of all tab (sheet) titles in the spreadsheet, or None on failure."""
        if not GOOGLE_SHEETS_ENABLED or not spreadsheet_id:
            return None
        service = get_sheets_service()
        if not service:
            return None
        try:
            spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            return [
                s.get("properties", {}).get("title", "")
                for s in spreadsheet.get("sheets", [])
            ]
        except Exception as e:
            logger.error("Error listing sheet tabs: %s", e)
            return None

    def rename_sheet_tab(spreadsheet_id: str, old_name: str, new_name: str) -> bool:
        """Rename an existing Google Sheet tab from old_name to new_name."""
        if not GOOGLE_SHEETS_ENABLED or not spreadsheet_id:
            return False
        if not old_name or not new_name or old_name.strip() == new_name.strip():
            return False

        service = get_sheets_service()
        if not service:
            return False

        old_name = old_name.strip()
        new_name = new_name.strip()

        try:
            spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheets = spreadsheet.get("sheets", [])

            sheet_id = None
            new_exists = False
            for sheet in sheets:
                title = sheet.get("properties", {}).get("title", "")
                if title == old_name:
                    sheet_id = sheet["properties"]["sheetId"]
                if title == new_name:
                    new_exists = True

            if sheet_id is None:
                logger.warning("Cannot rename: tab '%s' not found in spreadsheet", old_name)
                return False

            if new_exists:
                logger.warning("Cannot rename: tab '%s' already exists in spreadsheet", new_name)
                return False

            request_body = {
                "requests": [
                    {
                        "updateSheetProperties": {
                            "properties": {
                                "sheetId": sheet_id,
                                "title": new_name,
                            },
                            "fields": "title",
                        }
                    }
                ]
            }
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body=request_body
            ).execute()
            logger.info("Renamed sheet tab '%s' -> '%s'", old_name, new_name)
            return True
        except Exception as e:
            logger.error("Error renaming sheet tab '%s' -> '%s': %s", old_name, new_name, e)
            return False

    def save_entry_to_sheets(entry_data: Dict, target_sheet: Optional[str] = None) -> bool:
        """
        Save entry data to Google Sheets.

        Args:
            entry_data: Dictionary containing entry information.
            target_sheet: Explicit tab name from admin lobby name.
                          Falls back to the old auto-rotation logic when empty/None.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not GOOGLE_SHEETS_ENABLED:
            logger.warning("Google Sheets integration is disabled (GOOGLE_SHEETS_ENABLED=false)")
            return False
        
        if not SPREADSHEET_ID:
            logger.error("Google Sheets SPREADSHEET_ID is not configured")
            return False
        
        logger.info(f"Google Sheets enabled. Spreadsheet ID: {SPREADSHEET_ID[:20]}...")
        
        service = get_sheets_service()
        if not service:
            logger.warning("Google Sheets service not available")
            return False
        
        try:
            if target_sheet and target_sheet.strip():
                current_sheet = target_sheet.strip()
                ensure_sheet_tab(service, SPREADSHEET_ID, current_sheet)
            else:
                current_sheet = get_active_sheet_name()
            
            # Ensure header row exists
            ensure_header_row(SPREADSHEET_ID, current_sheet)
            
            # Client sheet layout: Time, Gamer ID Name, Number, Region, Bank Name,
            # Bank Account Number, Kill, Payout, Paid
            entry_time = datetime.now().strftime("%I:%M %p")
            entry_fee_ngn = float(entry_data.get("entry_fee", 0) or 0)
            dollar_rate = float(entry_data.get("dollar_rate", 1500) or 1500)
            per_kill = float(entry_data.get("per_kill_value", 0.6) or 0.6)
            kill_count = int(entry_data.get("kill_count", 0) or 0)
            payout_ngn = kill_count * per_kill * dollar_rate
            payout_str = (
                f"₦{payout_ngn:,.2f}" if kill_count else f"₦{entry_fee_ngn:,.2f}"
            )
            paid_status = "Yes" if entry_data.get("payment_status") == "completed" else ""
            row = [
                entry_time,
                entry_data.get("codm_id", ""),
                entry_data.get("contact_phone", ""),
                entry_data.get("region", ""),
                entry_data.get("bank_name", ""),
                entry_data.get("account_number", ""),
                kill_count,
                payout_str,
                paid_status,
            ]
            
            # Find the last row with data to append right after it
            # Get all data in the sheet to find the true last row
            result = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{current_sheet}!A:I"
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
                range=f"{current_sheet}!A{next_row}",
                valueInputOption='RAW',
                body={'values': [row]}
            ).execute()
            
            logger.info(f"Entry saved to Google Sheets ({current_sheet}): {entry_data.get('payment_reference')}")
            return True
            
        except HttpError as e:
            logger.error(f"Error saving to Google Sheets: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving to Google Sheets: {e}")
            return False
    
    def update_entry_in_sheets(payment_reference: str, updates: Dict, target_sheet: Optional[str] = None) -> bool:
        """
        Update an existing entry in Google Sheets.

        Args:
            payment_reference: Payment reference to find the row.
            updates: Dictionary of fields to update.
            target_sheet: Explicit tab name; falls back to auto-rotation when empty.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not GOOGLE_SHEETS_ENABLED or not SPREADSHEET_ID:
            return False
        
        service = get_sheets_service()
        if not service:
            return False
        
        try:
            if target_sheet and target_sheet.strip():
                current_sheet = target_sheet.strip()
            else:
                current_sheet = get_active_sheet_name()
            
            # Match row by Gamer ID (B) or Number (C — phone; legacy sheets may have email in C)
            result = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{current_sheet}!B:C",
            ).execute()
            
            values = result.get('values', [])
            row_index = None
            
            search_codm_id = updates.get("codm_id", "")
            search_phone = updates.get("contact_phone", "")
            search_email = updates.get("contact_email", "")
            
            search_updates = {
                k: v
                for k, v in updates.items()
                if k not in ["codm_id", "contact_phone", "contact_email"]
            }
            
            for idx, row in enumerate(values, start=1):
                if not row:
                    continue
                second = row[1] if len(row) > 1 else ""
                if (search_codm_id and row[0] == search_codm_id) or (
                    search_phone and second == search_phone
                ) or (search_email and second == search_email):
                    row_index = idx + 1
                    break
            
            if row_index is None:
                logger.warning(f"Entry not found in sheet: payment_reference={payment_reference}, codm_id={search_codm_id}, email={search_email}")
                return False
            
            # Use search_updates instead of updates for the actual update
            updates = search_updates
            
            # A=Time, B=Gamer ID Name, C=Number, D=Region, E=Bank Name, F=Bank Account,
            # G=Kill, H=Payout, I=Paid
            column_map = {
                "codm_id": "B",
                "contact_phone": "C",
                "region": "D",
                "bank_name": "E",
                "account_number": "F",
                "kill": "G",
                "payout": "H",
                "payment_status": "I",
            }
            
            update_requests = []
            for field, column in column_map.items():
                if field in updates:
                    value = updates[field]
                    # Format payment_status for Paid column
                    if field == "payment_status":
                        value = "Yes" if value == "completed" else ""
                    elif field == "kill":
                        value = str(value) if value is not None and value != "" else ""
                    
                    update_requests.append({
                        "range": f"{current_sheet}!{column}{row_index}",
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
    
    def get_active_sheet_name() -> str:
        return SHEET_NAME
    
    def save_entry_to_sheets(entry_data: Dict, target_sheet: Optional[str] = None) -> bool:
        return False
    
    def update_entry_in_sheets(payment_reference: str, updates: Dict, target_sheet: Optional[str] = None) -> bool:
        return False

    def list_sheet_tabs(spreadsheet_id: str) -> Optional[list]:
        return None

    def rename_sheet_tab(spreadsheet_id: str, old_name: str, new_name: str) -> bool:
        return False

    def get_sheet_data_row_count_cached(tab_name: str) -> Optional[int]:
        return None

