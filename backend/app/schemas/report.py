from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from decimal import Decimal
from ..models.transaction import PaymentMethod


class ReportPeriod(BaseModel):
    start_date: date
    end_date: date


class SalesReport(BaseModel):
    period: ReportPeriod
    total_sales: Decimal
    total_cash: Decimal
    total_mpesa: Decimal
    transaction_count: int
    average_transaction: Decimal


class ServicePerformance(BaseModel):
    service_name: str
    quantity_sold: Decimal
    revenue: Decimal


class AttendantPerformance(BaseModel):
    attendant_name: str
    transaction_count: int
    total_sales: Decimal


class ProfitReport(BaseModel):
    period: ReportPeriod
    total_revenue: Decimal
    total_expenses: Decimal
    gross_profit: Decimal
    profit_margin: Decimal


class PaymentBreakdown(BaseModel):
    method: str
    amount: Decimal
    count: int


class DashboardTransaction(BaseModel):
    id: str  # changed from UUID to str to avoid serialization issues if mixed
    transaction_number: int
    amount: Decimal
    time: str
    status: str


class DashboardStats(BaseModel):
    today_sales: Decimal
    today_transactions: int
    active_sessions: int
    low_stock_items: int
    available_computers: int
    
    # New fields
    recent_transactions: List[DashboardTransaction] = []
    top_services: List[ServicePerformance] = []
    payment_breakdown: List[PaymentBreakdown] = []
