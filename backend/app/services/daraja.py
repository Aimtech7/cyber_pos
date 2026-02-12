"""
Safaricom Daraja API Integration Service
Handles OAuth, STK Push, and callback validation
"""
import requests
import base64
import hashlib
import hmac
from datetime import datetime
from typing import Optional, Dict, Any
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class DarajaService:
    """Safaricom Daraja API Service"""
    
    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.shortcode = settings.MPESA_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY
        self.environment = settings.MPESA_ENVIRONMENT
        self.callback_url = settings.MPESA_CALLBACK_URL
        
        # API URLs
        if self.environment == "production":
            self.base_url = "https://api.safaricom.co.ke"
        else:
            self.base_url = "https://sandbox.safaricom.co.ke"
        
        self.oauth_url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        self.stk_push_url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        self.stk_query_url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
    
    def get_access_token(self) -> Optional[str]:
        """
        Generate OAuth access token for Daraja API
        Returns: Access token string or None if failed
        """
        try:
            # Create Basic Auth credentials
            credentials = f"{self.consumer_key}:{self.consumer_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_credentials}"
            }
            
            response = requests.get(self.oauth_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            access_token = data.get("access_token")
            
            if not access_token:
                logger.error("No access token in response")
                return None
            
            logger.info("Successfully generated Daraja access token")
            return access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Daraja access token: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting access token: {e}")
            return None
    
    def generate_password(self, timestamp: str) -> str:
        """
        Generate STK Push password
        Password = Base64(Shortcode + Passkey + Timestamp)
        """
        data_to_encode = f"{self.shortcode}{self.passkey}{timestamp}"
        encoded = base64.b64encode(data_to_encode.encode()).decode()
        return encoded
    
    def initiate_stk_push(
        self, 
        phone_number: str, 
        amount: float, 
        account_reference: str,
        transaction_desc: str = "Payment"
    ) -> Dict[str, Any]:
        """
        Initiate STK Push to customer's phone
        
        Args:
            phone_number: Customer phone in format 254XXXXXXXXX
            amount: Amount in KES (minimum 1)
            account_reference: Reference for the transaction (e.g., transaction_id)
            transaction_desc: Description of the transaction
        
        Returns:
            Dict with response data or error
        """
        try:
            # Get access token
            access_token = self.get_access_token()
            if not access_token:
                return {
                    "success": False,
                    "error": "Failed to get access token"
                }
            
            # Generate timestamp and password
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            password = self.generate_password(timestamp)
            
            # Prepare request payload
            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",  # or CustomerBuyGoodsOnline for Till
                "Amount": int(amount),  # Must be integer
                "PartyA": phone_number,  # Customer phone
                "PartyB": self.shortcode,  # Your shortcode
                "PhoneNumber": phone_number,
                "CallBackURL": self.callback_url,
                "AccountReference": account_reference,
                "TransactionDesc": transaction_desc
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"Initiating STK Push for {phone_number}, amount: {amount}")
            
            response = requests.post(
                self.stk_push_url, 
                json=payload, 
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Check response code
            response_code = data.get("ResponseCode")
            if response_code == "0":
                logger.info(f"STK Push initiated successfully: {data.get('CheckoutRequestID')}")
                return {
                    "success": True,
                    "checkout_request_id": data.get("CheckoutRequestID"),
                    "merchant_request_id": data.get("MerchantRequestID"),
                    "response_code": response_code,
                    "response_description": data.get("ResponseDescription"),
                    "customer_message": data.get("CustomerMessage")
                }
            else:
                logger.error(f"STK Push failed: {data.get('ResponseDescription')}")
                return {
                    "success": False,
                    "error": data.get("ResponseDescription"),
                    "response_code": response_code
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"STK Push request failed: {e}")
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error in STK Push: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def query_stk_status(self, checkout_request_id: str) -> Dict[str, Any]:
        """
        Query the status of an STK Push transaction
        
        Args:
            checkout_request_id: The CheckoutRequestID from initiate response
        
        Returns:
            Dict with status data
        """
        try:
            access_token = self.get_access_token()
            if not access_token:
                return {
                    "success": False,
                    "error": "Failed to get access token"
                }
            
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            password = self.generate_password(timestamp)
            
            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.stk_query_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            return {
                "success": True,
                "data": data
            }
            
        except Exception as e:
            logger.error(f"STK status query failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_callback_signature(self, callback_data: Dict, signature: Optional[str] = None) -> bool:
        """
        Validate M-Pesa callback signature (if provided by Safaricom)
        
        Note: As of 2024, Safaricom doesn't always send signatures for STK Push callbacks.
        This method is here for future-proofing and can validate if signature is provided.
        
        Args:
            callback_data: The callback payload
            signature: HMAC signature from headers (if available)
        
        Returns:
            True if valid or no signature to validate, False if invalid
        """
        # If no signature provided, we can't validate but shouldn't block
        if not signature:
            logger.warning("No signature provided for callback validation")
            return True
        
        try:
            # Generate expected signature using consumer secret as key
            payload_string = str(callback_data)
            expected_signature = hmac.new(
                self.consumer_secret.encode(),
                payload_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            is_valid = hmac.compare_digest(signature, expected_signature)
            
            if not is_valid:
                logger.error("Callback signature validation failed")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating callback signature: {e}")
            return False
    
    def extract_callback_data(self, callback_payload: Dict) -> Optional[Dict[str, Any]]:
        """
        Extract and parse M-Pesa callback data
        
        Args:
            callback_payload: Raw callback payload from Safaricom
        
        Returns:
            Parsed callback data or None if invalid
        """
        try:
            body = callback_payload.get("Body", {})
            stk_callback = body.get("stkCallback", {})
            
            result_code = stk_callback.get("ResultCode")
            result_desc = stk_callback.get("ResultDesc")
            merchant_request_id = stk_callback.get("MerchantRequestID")
            checkout_request_id = stk_callback.get("CheckoutRequestID")
            
            # Extract callback metadata
            callback_metadata = stk_callback.get("CallbackMetadata", {})
            items = callback_metadata.get("Item", [])
            
            # Parse items into dict
            metadata = {}
            for item in items:
                name = item.get("Name")
                value = item.get("Value")
                if name:
                    metadata[name] = value
            
            return {
                "result_code": result_code,
                "result_desc": result_desc,
                "merchant_request_id": merchant_request_id,
                "checkout_request_id": checkout_request_id,
                "amount": metadata.get("Amount"),
                "mpesa_receipt_number": metadata.get("MpesaReceiptNumber"),
                "transaction_date": metadata.get("TransactionDate"),
                "phone_number": metadata.get("PhoneNumber"),
                "metadata": metadata,
                "raw_callback": callback_payload
            }
            
        except Exception as e:
            logger.error(f"Error extracting callback data: {e}")
            return None


# Singleton instance
daraja_service = DarajaService()
