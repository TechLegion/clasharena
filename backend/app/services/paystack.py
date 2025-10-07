"""
Paystack payment gateway integration service
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

import requests
import hashlib
import hmac
import json
from typing import Dict, Any, Optional
from decimal import Decimal

from app.core.config import settings
from shared.models import Transaction


class PaystackService:
    """Paystack payment gateway service"""
    
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.public_key = settings.PAYSTACK_PUBLIC_KEY
        self.base_url = "https://api.paystack.co"
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
    
    def initialize_transaction(self, email: str, amount: float, reference: str, 
                             metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Initialize a payment transaction with Paystack (2025 compliant)
        
        Args:
            email: Customer email
            amount: Amount in NGN (naira)
            reference: Unique transaction reference
            metadata: Additional transaction data
            
        Returns:
            Dict containing authorization URL and transaction details
        """
        url = f"{self.base_url}/transaction/initialize"
        
        # Convert NGN to kobo (Paystack 2025 standard: 1 NGN = 100 kobo)
        amount_kobo = int(amount * 100)
        
        payload = {
            "email": email,
            "amount": amount_kobo,  # Paystack expects kobo
            "reference": reference,
            "currency": "NGN",
            "callback_url": f"{settings.BACKEND_CORS_ORIGINS[0]}/payment/callback",
            "metadata": metadata or {}
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Paystack 2025 response format
            if data.get('status'):
                return data
            else:
                return {"status": False, "message": data.get('message', 'Transaction initialization failed')}
                
        except requests.exceptions.RequestException as e:
            return {"status": False, "message": f"Request failed: {str(e)}"}
    
    def verify_transaction(self, reference: str) -> Dict[str, Any]:
        """
        Verify a transaction using Paystack API (2025 compliant)
        
        Args:
            reference: Transaction reference to verify
            
        Returns:
            Dict containing transaction verification details
        """
        url = f"{self.base_url}/transaction/verify/{reference}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            # Paystack 2025 response format
            if data.get('status'):
                return data
            else:
                return {"status": False, "message": data.get('message', 'Transaction verification failed')}
                
        except requests.exceptions.RequestException as e:
            return {"status": False, "message": f"Request failed: {str(e)}"}
    
    def create_transfer_recipient(self, account_number: str, bank_code: str, 
                                account_name: str, email: str) -> Dict[str, Any]:
        """
        Create a transfer recipient for withdrawals (2025 compliant)
        
        Args:
            account_number: Bank account number
            bank_code: Bank code from Paystack
            account_name: Account holder name
            email: Recipient email
            
        Returns:
            Dict containing recipient details
        """
        url = f"{self.base_url}/transferrecipient"
        
        payload = {
            "type": "nuban",
            "name": account_name,
            "account_number": account_number,
            "bank_code": bank_code,
            "currency": "NGN",
            "email": email
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Paystack 2025 response format
            if data.get('status'):
                return data
            else:
                return {"status": False, "message": data.get('message', 'Recipient creation failed')}
                
        except requests.exceptions.RequestException as e:
            return {"status": False, "message": f"Request failed: {str(e)}"}
    
    def initiate_transfer(self, amount: float, recipient_code: str, 
                         reference: str, reason: str = "Withdrawal") -> Dict[str, Any]:
        """
        Initiate a transfer (withdrawal) to a recipient (2025 compliant)
        
        Args:
            amount: Amount to transfer in NGN
            recipient_code: Paystack recipient code
            reference: Unique transfer reference
            reason: Transfer reason
            
        Returns:
            Dict containing transfer details
        """
        url = f"{self.base_url}/transfer"
        
        # Convert NGN to kobo (Paystack 2025 standard)
        amount_kobo = int(amount * 100)
        
        payload = {
            "source": "balance",
            "amount": amount_kobo,  # Paystack expects kobo
            "recipient": recipient_code,
            "reason": reason,
            "reference": reference
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Paystack 2025 response format
            if data.get('status'):
                return data
            else:
                return {"status": False, "message": data.get('message', 'Transfer failed')}
                
        except requests.exceptions.RequestException as e:
            return {"status": False, "message": f"Request failed: {str(e)}"}
    
    def get_banks(self) -> Dict[str, Any]:
        """
        Get list of Nigerian banks for account validation (2025 compliant)
        
        Returns:
            Dict containing list of banks
        """
        url = f"{self.base_url}/bank"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            # Paystack 2025 response format
            if data.get('status'):
                return data
            else:
                return {"status": False, "message": data.get('message', 'Failed to fetch banks')}
                
        except requests.exceptions.RequestException as e:
            return {"status": False, "message": f"Request failed: {str(e)}"}
    
    def resolve_account_number(self, account_number: str, bank_code: str) -> Dict[str, Any]:
        """
        Resolve account number to get account name (2025 compliant)
        
        Args:
            account_number: Bank account number
            bank_code: Bank code
            
        Returns:
            Dict containing account details
        """
        url = f"{self.base_url}/bank/resolve"
        params = {
            "account_number": account_number,
            "bank_code": bank_code
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Paystack 2025 response format
            if data.get('status'):
                return data
            else:
                return {"status": False, "message": data.get('message', 'Account resolution failed')}
                
        except requests.exceptions.RequestException as e:
            return {"status": False, "message": f"Request failed: {str(e)}"}
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify Paystack webhook signature (2025 compliant)
        
        Args:
            payload: Raw webhook payload
            signature: X-Paystack-Signature header value
            
        Returns:
            True if signature is valid, False otherwise
        """
        # Paystack 2025: Use secret key for signature verification (no separate webhook secret)
        if not self.secret_key:
            return False
            
        # Generate expected signature using secret key
        expected_signature = hmac.new(
            self.secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)


# Create service instance
paystack_service = PaystackService()

