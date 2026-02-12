"""
Alert Detection Engine for Anti-Theft Analytics
Implements rule-based detection for suspicious activities
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.models.alert import Alert, AlertType, AlertSeverity, AlertStatus
from app.models.audit import AuditLog
from app.models.transaction import Transaction
from app.models.shift import Shift
from app.models.user import User

logger = logging.getLogger(__name__)


class AlertThresholds:
    """Configurable thresholds for alert detection"""
    
    # Void/Refund abuse thresholds
    VOID_REFUND_MEDIUM = 5
    VOID_REFUND_HIGH = 10
    VOID_REFUND_CRITICAL = 15
    
    # Discount abuse thresholds (in KES)
    DISCOUNT_MEDIUM = 5000
    DISCOUNT_HIGH = 10000
    DISCOUNT_CRITICAL = 20000
    
    # Cash discrepancy thresholds (in KES)
    CASH_DIFF_LOW = 1000
    CASH_DIFF_MEDIUM = 3000
    CASH_DIFF_HIGH = 5000
    CASH_DIFF_CRITICAL = 10000
    
    # Inventory adjustment thresholds (units)
    INVENTORY_MEDIUM = 50
    INVENTORY_HIGH = 100
    INVENTORY_CRITICAL = 200
    
    # Price change frequency thresholds (per week)
    PRICE_CHANGE_MEDIUM = 3
    PRICE_CHANGE_HIGH = 5
    PRICE_CHANGE_CRITICAL = 10


class AlertEngine:
    """Main alert detection engine"""
    
    def __init__(self, db: Session):
        self.db = db
        self.thresholds = AlertThresholds()
    
    def run_all_checks(self) -> List[Alert]:
        """Run all detection rules and return created alerts"""
        logger.info("Running all alert detection checks...")
        
        alerts = []
        
        # Run each detection rule
        alerts.extend(self.check_void_refund_abuse())
        alerts.extend(self.check_discount_abuse())
        alerts.extend(self.check_cash_discrepancy())
        alerts.extend(self.check_inventory_manipulation())
        alerts.extend(self.check_price_tampering())
        
        logger.info(f"Alert detection complete. Created {len(alerts)} new alerts.")
        return alerts
    
    def check_void_refund_abuse(self) -> List[Alert]:
        """Detect excessive voids/refunds by user per day"""
        logger.info("Checking for void/refund abuse...")
        
        alerts = []
        today = datetime.utcnow().date()
        
        # Query audit logs for void/refund actions today
        void_refund_counts = (
            self.db.query(
                AuditLog.user_id,
                User.username,
                func.count(AuditLog.id).label('count')
            )
            .join(User, AuditLog.user_id == User.id)
            .filter(
                and_(
                    AuditLog.action.in_(['VOID_TRANSACTION', 'REFUND_TRANSACTION']),
                    func.date(AuditLog.created_at) == today
                )
            )
            .group_by(AuditLog.user_id, User.username)
            .all()
        )
        
        for user_id, username, count in void_refund_counts:
            severity = None
            
            if count >= self.thresholds.VOID_REFUND_CRITICAL:
                severity = AlertSeverity.CRITICAL
            elif count >= self.thresholds.VOID_REFUND_HIGH:
                severity = AlertSeverity.HIGH
            elif count >= self.thresholds.VOID_REFUND_MEDIUM:
                severity = AlertSeverity.MEDIUM
            
            if severity:
                # Check if alert already exists for this user today
                existing = self.db.query(Alert).filter(
                    and_(
                        Alert.type == AlertType.VOID_ABUSE,
                        Alert.related_entity['user_id'].astext == str(user_id),
                        func.date(Alert.created_at) == today,
                        Alert.status != AlertStatus.RESOLVED
                    )
                ).first()
                
                if not existing:
                    alert = Alert(
                        type=AlertType.VOID_ABUSE,
                        severity=severity,
                        message=f"User {username} performed {count} void/refund operations today",
                        description=f"Threshold exceeded: {count} operations (threshold: {self.thresholds.VOID_REFUND_MEDIUM}+)",
                        related_entity={
                            "type": "user",
                            "id": str(user_id),
                            "name": username
                        },
                        metadata={
                            "count": count,
                            "date": today.isoformat(),
                            "threshold_medium": self.thresholds.VOID_REFUND_MEDIUM,
                            "threshold_high": self.thresholds.VOID_REFUND_HIGH,
                            "threshold_critical": self.thresholds.VOID_REFUND_CRITICAL
                        }
                    )
                    self.db.add(alert)
                    alerts.append(alert)
        
        if alerts:
            self.db.commit()
        
        return alerts
    
    def check_discount_abuse(self) -> List[Alert]:
        """Detect excessive discounts by user per day"""
        logger.info("Checking for discount abuse...")
        
        alerts = []
        today = datetime.utcnow().date()
        
        # Query transactions with discounts today
        discount_totals = (
            self.db.query(
                Transaction.created_by,
                User.username,
                func.sum(Transaction.discount_amount).label('total_discount')
            )
            .join(User, Transaction.created_by == User.id)
            .filter(
                and_(
                    func.date(Transaction.created_at) == today,
                    Transaction.discount_amount > 0
                )
            )
            .group_by(Transaction.created_by, User.username)
            .all()
        )
        
        for user_id, username, total_discount in discount_totals:
            total_discount = float(total_discount)
            severity = None
            
            if total_discount >= self.thresholds.DISCOUNT_CRITICAL:
                severity = AlertSeverity.CRITICAL
            elif total_discount >= self.thresholds.DISCOUNT_HIGH:
                severity = AlertSeverity.HIGH
            elif total_discount >= self.thresholds.DISCOUNT_MEDIUM:
                severity = AlertSeverity.MEDIUM
            
            if severity:
                existing = self.db.query(Alert).filter(
                    and_(
                        Alert.type == AlertType.DISCOUNT_ABUSE,
                        Alert.related_entity['user_id'].astext == str(user_id),
                        func.date(Alert.created_at) == today,
                        Alert.status != AlertStatus.RESOLVED
                    )
                ).first()
                
                if not existing:
                    alert = Alert(
                        type=AlertType.DISCOUNT_ABUSE,
                        severity=severity,
                        message=f"User {username} applied KES {total_discount:,.2f} in discounts today",
                        description=f"Total discounts exceed threshold (KES {self.thresholds.DISCOUNT_MEDIUM:,}+)",
                        related_entity={
                            "type": "user",
                            "id": str(user_id),
                            "name": username
                        },
                        metadata={
                            "total_discount": total_discount,
                            "date": today.isoformat(),
                            "threshold_medium": self.thresholds.DISCOUNT_MEDIUM,
                            "threshold_high": self.thresholds.DISCOUNT_HIGH,
                            "threshold_critical": self.thresholds.DISCOUNT_CRITICAL
                        }
                    )
                    self.db.add(alert)
                    alerts.append(alert)
        
        if alerts:
            self.db.commit()
        
        return alerts
    
    def check_cash_discrepancy(self) -> List[Alert]:
        """Detect cash discrepancies at shift close"""
        logger.info("Checking for cash discrepancies...")
        
        alerts = []
        today = datetime.utcnow().date()
        
        # Query closed shifts with cash discrepancies today
        shifts_with_discrepancy = (
            self.db.query(Shift, User.username)
            .join(User, Shift.user_id == User.id)
            .filter(
                and_(
                    Shift.status == 'closed',
                    func.date(Shift.closed_at) == today,
                    Shift.cash_difference != None,
                    func.abs(Shift.cash_difference) > 0
                )
            )
            .all()
        )
        
        for shift, username in shifts_with_discrepancy:
            cash_diff = abs(float(shift.cash_difference))
            severity = None
            
            if cash_diff >= self.thresholds.CASH_DIFF_CRITICAL:
                severity = AlertSeverity.CRITICAL
            elif cash_diff >= self.thresholds.CASH_DIFF_HIGH:
                severity = AlertSeverity.HIGH
            elif cash_diff >= self.thresholds.CASH_DIFF_MEDIUM:
                severity = AlertSeverity.MEDIUM
            elif cash_diff >= self.thresholds.CASH_DIFF_LOW:
                severity = AlertSeverity.LOW
            
            if severity:
                existing = self.db.query(Alert).filter(
                    and_(
                        Alert.type == AlertType.CASH_DISCREPANCY,
                        Alert.related_entity['shift_id'].astext == str(shift.id),
                        Alert.status != AlertStatus.RESOLVED
                    )
                ).first()
                
                if not existing:
                    alert = Alert(
                        type=AlertType.CASH_DISCREPANCY,
                        severity=severity,
                        message=f"Cash discrepancy of KES {cash_diff:,.2f} in shift by {username}",
                        description=f"Expected: KES {shift.expected_cash:,.2f}, Counted: KES {shift.counted_cash:,.2f}",
                        related_entity={
                            "type": "shift",
                            "id": str(shift.id),
                            "user_id": str(shift.user_id),
                            "user_name": username
                        },
                        metadata={
                            "cash_difference": float(shift.cash_difference),
                            "expected_cash": float(shift.expected_cash),
                            "counted_cash": float(shift.counted_cash),
                            "shift_date": shift.closed_at.isoformat() if shift.closed_at else None
                        }
                    )
                    self.db.add(alert)
                    alerts.append(alert)
        
        if alerts:
            self.db.commit()
        
        return alerts
    
    def check_inventory_manipulation(self) -> List[Alert]:
        """Detect excessive inventory adjustments"""
        logger.info("Checking for inventory manipulation...")
        
        alerts = []
        today = datetime.utcnow().date()
        
        # Query audit logs for inventory adjustments today
        inventory_adjustments = (
            self.db.query(
                AuditLog.user_id,
                User.username,
                func.count(AuditLog.id).label('count')
            )
            .join(User, AuditLog.user_id == User.id)
            .filter(
                and_(
                    AuditLog.action == 'INVENTORY_ADJUSTMENT',
                    func.date(AuditLog.created_at) == today
                )
            )
            .group_by(AuditLog.user_id, User.username)
            .all()
        )
        
        for user_id, username, count in inventory_adjustments:
            severity = None
            
            if count >= self.thresholds.INVENTORY_CRITICAL:
                severity = AlertSeverity.CRITICAL
            elif count >= self.thresholds.INVENTORY_HIGH:
                severity = AlertSeverity.HIGH
            elif count >= self.thresholds.INVENTORY_MEDIUM:
                severity = AlertSeverity.MEDIUM
            
            if severity:
                existing = self.db.query(Alert).filter(
                    and_(
                        Alert.type == AlertType.INVENTORY_MANIPULATION,
                        Alert.related_entity['user_id'].astext == str(user_id),
                        func.date(Alert.created_at) == today,
                        Alert.status != AlertStatus.RESOLVED
                    )
                ).first()
                
                if not existing:
                    alert = Alert(
                        type=AlertType.INVENTORY_MANIPULATION,
                        severity=severity,
                        message=f"User {username} made {count} inventory adjustments today",
                        description=f"Excessive inventory adjustments detected (threshold: {self.thresholds.INVENTORY_MEDIUM}+)",
                        related_entity={
                            "type": "user",
                            "id": str(user_id),
                            "name": username
                        },
                        metadata={
                            "adjustment_count": count,
                            "date": today.isoformat(),
                            "threshold_medium": self.thresholds.INVENTORY_MEDIUM,
                            "threshold_high": self.thresholds.INVENTORY_HIGH,
                            "threshold_critical": self.thresholds.INVENTORY_CRITICAL
                        }
                    )
                    self.db.add(alert)
                    alerts.append(alert)
        
        if alerts:
            self.db.commit()
        
        return alerts
    
    def check_price_tampering(self) -> List[Alert]:
        """Detect frequent service price changes"""
        logger.info("Checking for price tampering...")
        
        alerts = []
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Query audit logs for service price changes in the past week
        price_changes = (
            self.db.query(
                AuditLog.user_id,
                User.username,
                func.count(AuditLog.id).label('count')
            )
            .join(User, AuditLog.user_id == User.id)
            .filter(
                and_(
                    AuditLog.action == 'UPDATE_SERVICE',
                    AuditLog.details.contains({'field': 'base_price'}),
                    AuditLog.created_at >= week_ago
                )
            )
            .group_by(AuditLog.user_id, User.username)
            .all()
        )
        
        for user_id, username, count in price_changes:
            severity = None
            
            if count >= self.thresholds.PRICE_CHANGE_CRITICAL:
                severity = AlertSeverity.CRITICAL
            elif count >= self.thresholds.PRICE_CHANGE_HIGH:
                severity = AlertSeverity.HIGH
            elif count >= self.thresholds.PRICE_CHANGE_MEDIUM:
                severity = AlertSeverity.MEDIUM
            
            if severity:
                # Check for existing alert this week
                existing = self.db.query(Alert).filter(
                    and_(
                        Alert.type == AlertType.PRICE_TAMPERING,
                        Alert.related_entity['user_id'].astext == str(user_id),
                        Alert.created_at >= week_ago,
                        Alert.status != AlertStatus.RESOLVED
                    )
                ).first()
                
                if not existing:
                    alert = Alert(
                        type=AlertType.PRICE_TAMPERING,
                        severity=severity,
                        message=f"User {username} changed service prices {count} times this week",
                        description=f"Frequent price changes detected (threshold: {self.thresholds.PRICE_CHANGE_MEDIUM}+ per week)",
                        related_entity={
                            "type": "user",
                            "id": str(user_id),
                            "name": username
                        },
                        metadata={
                            "change_count": count,
                            "period_days": 7,
                            "threshold_medium": self.thresholds.PRICE_CHANGE_MEDIUM,
                            "threshold_high": self.thresholds.PRICE_CHANGE_HIGH,
                            "threshold_critical": self.thresholds.PRICE_CHANGE_CRITICAL
                        }
                    )
                    self.db.add(alert)
                    alerts.append(alert)
        
        if alerts:
            self.db.commit()
        
        return alerts


def run_alert_checks(db: Session) -> List[Alert]:
    """Convenience function to run all alert checks"""
    engine = AlertEngine(db)
    return engine.run_all_checks()
