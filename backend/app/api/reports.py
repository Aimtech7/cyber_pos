from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timedelta
from decimal import Decimal
from ..database import get_db
from ..schemas.report import (
    ReportPeriod,
    SalesReport,
    ServicePerformance,
    AttendantPerformance,
    ProfitReport,
    DashboardStats
)
from ..models.transaction import Transaction, TransactionItem, TransactionStatus, PaymentMethod
from ..models.session import Session as SessionModel, SessionStatus
from ..models.computer import Computer, ComputerStatus
from ..models.expense import Expense
from ..models.inventory import InventoryItem
from ..models.user import User
from ..models.service import Service
from ..core.permissions import Permission
from ..api.deps import get_current_user, require_permission
from typing import List

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/sales", response_model=SalesReport)
async def get_sales_report(
    period: ReportPeriod,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VIEW_REPORTS))
):
    """Get sales report for a period"""
    transactions = db.query(Transaction).filter(
        Transaction.created_at >= datetime.combine(period.start_date, datetime.min.time()),
        Transaction.created_at <= datetime.combine(period.end_date, datetime.max.time()),
        Transaction.status == TransactionStatus.COMPLETED
    ).all()
    
    total_sales = sum(t.final_amount for t in transactions)
    total_cash = sum(t.final_amount for t in transactions if t.payment_method == PaymentMethod.CASH)
    total_mpesa = sum(t.final_amount for t in transactions if t.payment_method == PaymentMethod.MPESA)
    transaction_count = len(transactions)
    average_transaction = total_sales / transaction_count if transaction_count > 0 else Decimal(0)
    
    return SalesReport(
        period=period,
        total_sales=total_sales,
        total_cash=total_cash,
        total_mpesa=total_mpesa,
        transaction_count=transaction_count,
        average_transaction=average_transaction
    )


@router.post("/services", response_model=List[ServicePerformance])
async def get_service_performance(
    period: ReportPeriod,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VIEW_REPORTS))
):
    """Get service performance report"""
    results = db.query(
        Service.name,
        func.sum(TransactionItem.quantity).label("quantity_sold"),
        func.sum(TransactionItem.total_price).label("revenue")
    ).join(
        TransactionItem, Service.id == TransactionItem.service_id
    ).join(
        Transaction, TransactionItem.transaction_id == Transaction.id
    ).filter(
        Transaction.created_at >= datetime.combine(period.start_date, datetime.min.time()),
        Transaction.created_at <= datetime.combine(period.end_date, datetime.max.time()),
        Transaction.status == TransactionStatus.COMPLETED
    ).group_by(Service.name).all()
    
    return [
        ServicePerformance(
            service_name=r.name,
            quantity_sold=r.quantity_sold or Decimal(0),
            revenue=r.revenue or Decimal(0)
        )
        for r in results
    ]


@router.post("/attendants", response_model=List[AttendantPerformance])
async def get_attendant_performance(
    period: ReportPeriod,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VIEW_REPORTS))
):
    """Get attendant performance report"""
    results = db.query(
        User.full_name,
        func.count(Transaction.id).label("transaction_count"),
        func.sum(Transaction.final_amount).label("total_sales")
    ).join(
        Transaction, User.id == Transaction.created_by
    ).filter(
        Transaction.created_at >= datetime.combine(period.start_date, datetime.min.time()),
        Transaction.created_at <= datetime.combine(period.end_date, datetime.max.time()),
        Transaction.status == TransactionStatus.COMPLETED
    ).group_by(User.full_name).all()
    
    return [
        AttendantPerformance(
            attendant_name=r.full_name,
            transaction_count=r.transaction_count or 0,
            total_sales=r.total_sales or Decimal(0)
        )
        for r in results
    ]


@router.post("/profit", response_model=ProfitReport)
async def get_profit_report(
    period: ReportPeriod,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VIEW_REPORTS))
):
    """Get profit report"""
    # Calculate revenue
    total_revenue = db.query(func.sum(Transaction.final_amount)).filter(
        Transaction.created_at >= datetime.combine(period.start_date, datetime.min.time()),
        Transaction.created_at <= datetime.combine(period.end_date, datetime.max.time()),
        Transaction.status == TransactionStatus.COMPLETED
    ).scalar() or Decimal(0)
    
    # Calculate expenses
    total_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.expense_date >= period.start_date,
        Expense.expense_date <= period.end_date
    ).scalar() or Decimal(0)
    
    gross_profit = total_revenue - total_expenses
    profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else Decimal(0)
    
    return ProfitReport(
        period=period,
        total_revenue=total_revenue,
        total_expenses=total_expenses,
        gross_profit=gross_profit,
        profit_margin=profit_margin
    )


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics"""
    today = date.today()
    
    # Today's sales
    today_sales = db.query(func.sum(Transaction.final_amount)).filter(
        func.date(Transaction.created_at) == today,
        Transaction.status == TransactionStatus.COMPLETED
    ).scalar() or Decimal(0)
    
    # Today's transaction count
    today_transactions = db.query(func.count(Transaction.id)).filter(
        func.date(Transaction.created_at) == today,
        Transaction.status == TransactionStatus.COMPLETED
    ).scalar() or 0
    
    # Active sessions
    active_sessions = db.query(func.count(SessionModel.id)).filter(
        SessionModel.status == SessionStatus.ACTIVE
    ).scalar() or 0
    
    # Low stock items
    low_stock_items = db.query(func.count(InventoryItem.id)).filter(
        InventoryItem.current_stock <= InventoryItem.min_stock_level
    ).scalar() or 0
    
    # Available computers
    available_computers = db.query(func.count(Computer.id)).filter(
        Computer.status == ComputerStatus.AVAILABLE
    ).scalar() or 0
    
    return DashboardStats(
        today_sales=today_sales,
        today_transactions=today_transactions,
        active_sessions=active_sessions,
        low_stock_items=low_stock_items,
        available_computers=available_computers
    )
