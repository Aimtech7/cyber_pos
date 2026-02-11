from typing import Optional
from datetime import datetime
from decimal import Decimal


def calculate_session_charge(
    start_time: datetime,
    end_time: datetime,
    rate_per_minute: Decimal
) -> tuple[int, Decimal]:
    """
    Calculate session duration and charge
    
    Args:
        start_time: Session start time
        end_time: Session end time
        rate_per_minute: Billing rate per minute
    
    Returns:
        Tuple of (duration_minutes, amount_charged)
    """
    duration = end_time - start_time
    duration_minutes = int(duration.total_seconds() / 60)
    
    # Round up to nearest minute
    if duration.total_seconds() % 60 > 0:
        duration_minutes += 1
    
    amount_charged = Decimal(duration_minutes) * rate_per_minute
    
    return duration_minutes, amount_charged


def calculate_service_charge(
    quantity: Decimal,
    unit_price: Decimal,
    discount_percent: Decimal = Decimal(0)
) -> Decimal:
    """
    Calculate service charge with optional discount
    
    Args:
        quantity: Quantity of service
        unit_price: Price per unit
        discount_percent: Discount percentage (0-100)
    
    Returns:
        Total charge after discount
    """
    subtotal = quantity * unit_price
    discount_amount = subtotal * (discount_percent / Decimal(100))
    total = subtotal - discount_amount
    
    return total.quantize(Decimal('0.01'))


def calculate_transaction_totals(
    items: list[dict],
    discount_amount: Decimal = Decimal(0)
) -> tuple[Decimal, Decimal]:
    """
    Calculate transaction totals
    
    Args:
        items: List of transaction items with 'total_price' key
        discount_amount: Fixed discount amount
    
    Returns:
        Tuple of (total_amount, final_amount)
    """
    total_amount = sum(Decimal(item['total_price']) for item in items)
    final_amount = total_amount - discount_amount
    
    return (
        total_amount.quantize(Decimal('0.01')),
        final_amount.quantize(Decimal('0.01'))
    )
