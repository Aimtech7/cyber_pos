"""
Unit Tests for Alert Detection Engine
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.alert import Alert, AlertType, AlertSeverity, AlertStatus
from app.models.user import User, UserRole
from app.models.transaction import Transaction, PaymentMethod, TransactionStatus
from app.models.shift import Shift
from app.models.audit import AuditLog
from app.services.alert_engine import AlertEngine, AlertThresholds


@pytest.fixture
def alert_engine(db: Session):
    """Create alert engine instance"""
    return AlertEngine(db)


@pytest.fixture
def test_user(db: Session):
    """Create test user"""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        role=UserRole.ATTENDANT
    )
    user.set_password("password")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestVoidRefundAbuse:
    """Test void/refund abuse detection"""
    
    def test_no_alerts_below_threshold(self, alert_engine, test_user, db):
        """Should not create alert when below threshold"""
        # Create 4 void actions (below medium threshold of 5)
        for i in range(4):
            db.add(AuditLog(
                user_id=test_user.id,
                action="VOID_TRANSACTION",
                details={"transaction_id": f"test-{i}"}
            ))
        db.commit()
        
        alerts = alert_engine.check_void_refund_abuse()
        assert len(alerts) == 0
    
    def test_medium_severity_alert(self, alert_engine, test_user, db):
        """Should create medium severity alert at threshold"""
        # Create 6 void actions (medium threshold)
        for i in range(6):
            db.add(AuditLog(
                user_id=test_user.id,
                action="VOID_TRANSACTION",
                details={"transaction_id": f"test-{i}"}
            ))
        db.commit()
        
        alerts = alert_engine.check_void_refund_abuse()
        assert len(alerts) == 1
        assert alerts[0].type == AlertType.VOID_ABUSE
        assert alerts[0].severity == AlertSeverity.MEDIUM
    
    def test_critical_severity_alert(self, alert_engine, test_user, db):
        """Should create critical severity alert"""
        # Create 16 void actions (critical threshold)
        for i in range(16):
            db.add(AuditLog(
                user_id=test_user.id,
                action="REFUND_TRANSACTION",
                details={"transaction_id": f"test-{i}"}
            ))
        db.commit()
        
        alerts = alert_engine.check_void_refund_abuse()
        assert len(alerts) == 1
        assert alerts[0].severity == AlertSeverity.CRITICAL


class TestDiscountAbuse:
    """Test discount abuse detection"""
    
    def test_no_alerts_below_threshold(self, alert_engine, test_user, db):
        """Should not create alert when below threshold"""
        # Create transaction with KES 3000 discount (below threshold)
        db.add(Transaction(
            created_by=test_user.id,
            shift_id="test-shift",
            total_amount=10000,
            discount_amount=3000,
            final_amount=7000,
            payment_method=PaymentMethod.CASH,
            status=TransactionStatus.COMPLETED
        ))
        db.commit()
        
        alerts = alert_engine.check_discount_abuse()
        assert len(alerts) == 0
    
    def test_high_severity_alert(self, alert_engine, test_user, db):
        """Should create high severity alert"""
        # Create transactions totaling KES 12000 discount
        for i in range(3):
            db.add(Transaction(
                created_by=test_user.id,
                shift_id="test-shift",
                total_amount=10000,
                discount_amount=4000,
                final_amount=6000,
                payment_method=PaymentMethod.CASH,
                status=TransactionStatus.COMPLETED
            ))
        db.commit()
        
        alerts = alert_engine.check_discount_abuse()
        assert len(alerts) == 1
        assert alerts[0].type == AlertType.DISCOUNT_ABUSE
        assert alerts[0].severity == AlertSeverity.HIGH


class TestCashDiscrepancy:
    """Test cash discrepancy detection"""
    
    def test_no_alerts_below_threshold(self, alert_engine, test_user, db):
        """Should not create alert when below threshold"""
        db.add(Shift(
            user_id=test_user.id,
            opening_cash=5000,
            expected_cash=10000,
            counted_cash=10500,  # KES 500 difference (below low threshold)
            cash_difference=500,
            status='closed',
            closed_at=datetime.utcnow()
        ))
        db.commit()
        
        alerts = alert_engine.check_cash_discrepancy()
        assert len(alerts) == 0
    
    def test_medium_severity_alert(self, alert_engine, test_user, db):
        """Should create medium severity alert"""
        db.add(Shift(
            user_id=test_user.id,
            opening_cash=5000,
            expected_cash=10000,
            counted_cash=13500,  # KES 3500 difference
            cash_difference=3500,
            status='closed',
            closed_at=datetime.utcnow()
        ))
        db.commit()
        
        alerts = alert_engine.check_cash_discrepancy()
        assert len(alerts) == 1
        assert alerts[0].type == AlertType.CASH_DISCREPANCY
        assert alerts[0].severity == AlertSeverity.MEDIUM


class TestInventoryManipulation:
    """Test inventory manipulation detection"""
    
    def test_critical_alert(self, alert_engine, test_user, db):
        """Should create critical alert for excessive adjustments"""
        # Create 250 inventory adjustments (critical threshold)
        for i in range(250):
            db.add(AuditLog(
                user_id=test_user.id,
                action="INVENTORY_ADJUSTMENT",
                details={"item_id": f"item-{i}", "quantity": 10}
            ))
        db.commit()
        
        alerts = alert_engine.check_inventory_manipulation()
        assert len(alerts) == 1
        assert alerts[0].type == AlertType.INVENTORY_MANIPULATION
        assert alerts[0].severity == AlertSeverity.CRITICAL


class TestPriceTampering:
    """Test price tampering detection"""
    
    def test_high_severity_alert(self, alert_engine, test_user, db):
        """Should create high severity alert"""
        # Create 6 price changes in the past week
        for i in range(6):
            db.add(AuditLog(
                user_id=test_user.id,
                action="UPDATE_SERVICE",
                details={"field": "base_price", "old_value": 100, "new_value": 150}
            ))
        db.commit()
        
        alerts = alert_engine.check_price_tampering()
        assert len(alerts) == 1
        assert alerts[0].type == AlertType.PRICE_TAMPERING
        assert alerts[0].severity == AlertSeverity.HIGH


class TestAlertEngine:
    """Test alert engine overall functionality"""
    
    def test_run_all_checks(self, alert_engine, test_user, db):
        """Should run all detection rules"""
        # Create various suspicious activities
        # Voids
        for i in range(6):
            db.add(AuditLog(user_id=test_user.id, action="VOID_TRANSACTION", details={}))
        
        # Discounts
        db.add(Transaction(
            created_by=test_user.id,
            shift_id="test-shift",
            total_amount=20000,
            discount_amount=6000,
            final_amount=14000,
            payment_method=PaymentMethod.CASH,
            status=TransactionStatus.COMPLETED
        ))
        
        db.commit()
        
        alerts = alert_engine.run_all_checks()
        assert len(alerts) >= 2  # At least void and discount alerts
        
        # Check alert types
        alert_types = [a.type for a in alerts]
        assert AlertType.VOID_ABUSE in alert_types
        assert AlertType.DISCOUNT_ABUSE in alert_types
    
    def test_no_duplicate_alerts(self, alert_engine, test_user, db):
        """Should not create duplicate alerts for same issue"""
        # Create suspicious activity
        for i in range(10):
            db.add(AuditLog(user_id=test_user.id, action="VOID_TRANSACTION", details={}))
        db.commit()
        
        # Run checks twice
        alerts1 = alert_engine.check_void_refund_abuse()
        alerts2 = alert_engine.check_void_refund_abuse()
        
        assert len(alerts1) == 1
        assert len(alerts2) == 0  # Should not create duplicate
