"""
Flutterwave API integration service for bank transfers
"""
import httpx
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class FlutterwaveService:
    def __init__(self):
        self.secret_key = settings.FLUTTERWAVE_SECRET_KEY
        self.base_url = "https://api.flutterwave.com/v3"
        
    async def get_banks(self) -> Dict[str, Any]:
        """Get list of Nigerian banks"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/banks/NG",
                    headers={
                        "Authorization": f"Bearer {self.secret_key}",
                        "Content-Type": "application/json"
                    }
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    return {
                        "status": True,
                        "data": result["data"]
                    }
                else:
                    logger.error(f"Flutterwave banks API error: {result.get('message')}")
                    return {"status": False, "message": result.get("message", "Failed to fetch banks")}
            else:
                logger.error(f"Flutterwave banks API HTTP error: {response.status_code}")
                return {"status": False, "message": f"HTTP {response.status_code}"}
                
        except httpx.TimeoutException:
            logger.error("Flutterwave banks API timeout")
            return {"status": False, "message": "Request timeout"}
        except Exception as e:
            logger.error(f"Flutterwave banks API error: {str(e)}")
            return {"status": False, "message": str(e)}
    
    async def resolve_account_number(self, account_number: str, bank_code: str) -> Dict[str, Any]:
        """Resolve bank account number to get account name"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/accounts/resolve",
                    headers={
                        "Authorization": f"Bearer {self.secret_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "account_number": account_number,
                        "account_bank": bank_code
                    }
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    return {
                        "status": True,
                        "data": {
                            "account_number": result["data"]["account_number"],
                            "account_name": result["data"]["account_name"],
                            "bank_code": bank_code
                        }
                    }
                else:
                    logger.error(f"Flutterwave account resolution error: {result.get('message')}")
                    return {"status": False, "message": result.get("message", "Account resolution failed")}
            else:
                logger.error(f"Flutterwave account resolution HTTP error: {response.status_code}")
                return {"status": False, "message": f"HTTP {response.status_code}"}
                
        except httpx.TimeoutException:
            logger.error("Flutterwave account resolution timeout")
            return {"status": False, "message": "Request timeout"}
        except Exception as e:
            logger.error(f"Flutterwave account resolution error: {str(e)}")
            return {"status": False, "message": str(e)}
    
    async def transfer_to_bank(
        self, 
        account_number: str, 
        bank_code: str, 
        amount: float, 
        narration: str,
        recipient_name: str
    ) -> Dict[str, Any]:
        """Transfer money to bank account"""
        try:
            # Create transfer data
            transfer_data = {
                "account_bank": bank_code,
                "account_number": account_number,
                "amount": amount,
                "narration": narration,
                "currency": "NGN",
                "reference": f"clasharena_{account_number}_{amount}",
                "beneficiary_name": recipient_name,
                "meta": {
                    "source": "clasharena",
                    "recipient": recipient_name
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/transfers",
                    headers={
                        "Authorization": f"Bearer {self.secret_key}",
                        "Content-Type": "application/json"
                    },
                    json=transfer_data
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    return {
                        "status": True,
                        "data": {
                            "reference": result["data"]["reference"],
                            "transfer_id": result["data"]["id"],
                            "amount": result["data"]["amount"],
                            "status": result["data"]["status"]
                        }
                    }
                else:
                    logger.error(f"Flutterwave transfer error: {result.get('message')}")
                    return {"status": False, "message": result.get("message", "Transfer failed")}
            else:
                logger.error(f"Flutterwave transfer HTTP error: {response.status_code}")
                return {"status": False, "message": f"HTTP {response.status_code}"}
                
        except httpx.TimeoutException:
            logger.error("Flutterwave transfer timeout")
            return {"status": False, "message": "Request timeout"}
        except Exception as e:
            logger.error(f"Flutterwave transfer error: {str(e)}")
            return {"status": False, "message": str(e)}
    
    async def get_transfer_status(self, transfer_id: str) -> Dict[str, Any]:
        """Get status of a transfer"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/transfers/{transfer_id}",
                    headers={
                        "Authorization": f"Bearer {self.secret_key}",
                        "Content-Type": "application/json"
                    }
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    return {
                        "status": True,
                        "data": {
                            "id": result["data"]["id"],
                            "status": result["data"]["status"],
                            "amount": result["data"]["amount"],
                            "reference": result["data"]["reference"],
                            "complete_message": result["data"].get("complete_message", "")
                        }
                    }
                else:
                    logger.error(f"Flutterwave transfer status error: {result.get('message')}")
                    return {"status": False, "message": result.get("message", "Failed to get transfer status")}
            else:
                logger.error(f"Flutterwave transfer status HTTP error: {response.status_code}")
                return {"status": False, "message": f"HTTP {response.status_code}"}
                
        except httpx.TimeoutException:
            logger.error("Flutterwave transfer status timeout")
            return {"status": False, "message": "Request timeout"}
        except Exception as e:
            logger.error(f"Flutterwave transfer status error: {str(e)}")
            return {"status": False, "message": str(e)}

# Global instance
flutterwave_service = FlutterwaveService()
