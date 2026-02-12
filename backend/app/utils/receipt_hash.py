"""
Receipt Hashing Utility
Generates tamper-evident hashes for receipts
"""
import hashlib
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any


def generate_receipt_hash(
    transaction_number: int,
    amount: Decimal,
    payment_method: str,
    timestamp: datetime,
    items_summary: str
) -> str:
    """
    Generate SHA-256 hash for receipt tamper detection
    
    Args:
        transaction_number: Transaction number
        amount: Final amount
        payment_method: Payment method used
        timestamp: Transaction timestamp
        items_summary: Summary of items (e.g., "Service1:2,Service2:1")
    
    Returns:
        Hexadecimal hash string
    """
    # Create hash input string
    hash_input = (
        f"{transaction_number}|"
        f"{amount}|"
        f"{payment_method}|"
        f"{timestamp.isoformat()}|"
        f"{items_summary}"
    )
    
    # Generate SHA-256 hash
    hash_obj = hashlib.sha256(hash_input.encode('utf-8'))
    return hash_obj.hexdigest()


def verify_receipt_hash(
    transaction_number: int,
    amount: Decimal,
    payment_method: str,
    timestamp: datetime,
    items_summary: str,
    stored_hash: str
) -> bool:
    """
    Verify receipt hash matches stored hash
    
    Returns:
        True if hash matches, False otherwise
    """
    calculated_hash = generate_receipt_hash(
        transaction_number=transaction_number,
        amount=amount,
        payment_method=payment_method,
        timestamp=timestamp,
        items_summary=items_summary
    )
    
    return calculated_hash == stored_hash


def create_items_summary(items: list) -> str:
    """
    Create items summary string for hashing
    
    Args:
        items: List of transaction items with service_id and quantity
    
    Returns:
        Summary string (e.g., "uuid1:2,uuid2:1")
    """
    summary_parts = []
    for item in items:
        service_id = str(item.get('service_id', ''))
        quantity = str(item.get('quantity', 0))
        summary_parts.append(f"{service_id}:{quantity}")
    
    return ",".join(sorted(summary_parts))  # Sort for consistency
