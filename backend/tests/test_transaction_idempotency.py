"""
Tests for Transaction Idempotency (Offline Mode)
"""
import pytest
from uuid import uuid4
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.transaction import Transaction, TransactionItem, PaymentMethod, TransactionStatus
from app.models.shift import Shift, ShiftStatus
from app.models.user import User, UserRole
from app.models.service import Service
from app.schemas.transaction import TransactionCreate, TransactionItemCreate
from app.api.transactions import create_transaction
from fastapi import HTTPException


class TestTransactionIdempotency:
    """Test idempotency of transaction creation"""

    @pytest.fixture
    def setup_data(self, db: Session):
        """Setup test data"""
        # Create user
        user = User(
            username="test_attendant",
            email="attendant@test.com",
            role=UserRole.ATTENDANT,
            is_active=True
        )
        user.set_password("password123")
        db.add(user)
        db.flush()

        # Create service
        service = Service(
            name="Test Service",
            base_price=Decimal("100.00"),
            is_active=True
        )
        db.add(service)
        db.flush()

        # Create open shift
        shift = Shift(
            user_id=user.id,
            status=ShiftStatus.OPEN,
            opening_cash=Decimal("1000.00")
        )
        db.add(shift)
        db.flush()

        db.commit()

        return {
            "user": user,
            "service": service,
            "shift": shift
        }

    def test_create_transaction_with_client_generated_id(self, db: Session, setup_data):
        """Test creating transaction with client_generated_id"""
        client_id = uuid4()
        
        transaction_data = TransactionCreate(
            items=[
                TransactionItemCreate(
                    service_id=setup_data["service"].id,
                    description="Test Service",
                    quantity=Decimal("1"),
                    unit_price=Decimal("100.00")
                )
            ],
            payment_method=PaymentMethod.CASH,
            client_generated_id=client_id,
            offline_receipt_number="OFF-20260212-0001"
        )

        # Create transaction
        transaction = create_transaction(
            transaction_data=transaction_data,
            db=db,
            current_user=setup_data["user"]
        )

        assert transaction.client_generated_id == client_id
        assert transaction.offline_receipt_number == "OFF-20260212-0001"
        assert transaction.synced_at is not None  # Should be set when created with client_generated_id

    def test_idempotency_same_client_generated_id_returns_same_transaction(self, db: Session, setup_data):
        """Test that same client_generated_id returns the same transaction"""
        client_id = uuid4()
        
        transaction_data = TransactionCreate(
            items=[
                TransactionItemCreate(
                    service_id=setup_data["service"].id,
                    description="Test Service",
                    quantity=Decimal("1"),
                    unit_price=Decimal("100.00")
                )
            ],
            payment_method=PaymentMethod.CASH,
            client_generated_id=client_id,
            offline_receipt_number="OFF-20260212-0001"
        )

        # Create transaction first time
        transaction1 = create_transaction(
            transaction_data=transaction_data,
            db=db,
            current_user=setup_data["user"]
        )

        # Try to create again with same client_generated_id
        transaction2 = create_transaction(
            transaction_data=transaction_data,
            db=db,
            current_user=setup_data["user"]
        )

        # Should return the same transaction
        assert transaction1.id == transaction2.id
        assert transaction1.transaction_number == transaction2.transaction_number
        assert transaction1.client_generated_id == transaction2.client_generated_id

        # Verify only one transaction exists in database
        count = db.query(Transaction).filter(
            Transaction.client_generated_id == client_id
        ).count()
        assert count == 1

    def test_different_client_generated_ids_create_different_transactions(self, db: Session, setup_data):
        """Test that different client_generated_ids create different transactions"""
        client_id1 = uuid4()
        client_id2 = uuid4()

        transaction_data1 = TransactionCreate(
            items=[
                TransactionItemCreate(
                    service_id=setup_data["service"].id,
                    description="Test Service",
                    quantity=Decimal("1"),
                    unit_price=Decimal("100.00")
                )
            ],
            payment_method=PaymentMethod.CASH,
            client_generated_id=client_id1,
            offline_receipt_number="OFF-20260212-0001"
        )

        transaction_data2 = TransactionCreate(
            items=[
                TransactionItemCreate(
                    service_id=setup_data["service"].id,
                    description="Test Service",
                    quantity=Decimal("1"),
                    unit_price=Decimal("100.00")
                )
            ],
            payment_method=PaymentMethod.CASH,
            client_generated_id=client_id2,
            offline_receipt_number="OFF-20260212-0002"
        )

        # Create two transactions
        transaction1 = create_transaction(
            transaction_data=transaction_data1,
            db=db,
            current_user=setup_data["user"]
        )

        transaction2 = create_transaction(
            transaction_data=transaction_data2,
            db=db,
            current_user=setup_data["user"]
        )

        # Should be different transactions
        assert transaction1.id != transaction2.id
        assert transaction1.transaction_number != transaction2.transaction_number
        assert transaction1.client_generated_id != transaction2.client_generated_id

    def test_transaction_without_client_generated_id_works_normally(self, db: Session, setup_data):
        """Test that transactions without client_generated_id work normally"""
        transaction_data = TransactionCreate(
            items=[
                TransactionItemCreate(
                    service_id=setup_data["service"].id,
                    description="Test Service",
                    quantity=Decimal("1"),
                    unit_price=Decimal("100.00")
                )
            ],
            payment_method=PaymentMethod.CASH
            # No client_generated_id
        )

        transaction = create_transaction(
            transaction_data=transaction_data,
            db=db,
            current_user=setup_data["user"]
        )

        assert transaction.client_generated_id is None
        assert transaction.offline_receipt_number is None
        assert transaction.synced_at is None

    def test_offline_receipt_number_stored_correctly(self, db: Session, setup_data):
        """Test that offline receipt numbers are stored correctly"""
        offline_receipt = "OFF-20260212-1234"
        
        transaction_data = TransactionCreate(
            items=[
                TransactionItemCreate(
                    service_id=setup_data["service"].id,
                    description="Test Service",
                    quantity=Decimal("1"),
                    unit_price=Decimal("100.00")
                )
            ],
            payment_method=PaymentMethod.CASH,
            client_generated_id=uuid4(),
            offline_receipt_number=offline_receipt
        )

        transaction = create_transaction(
            transaction_data=transaction_data,
            db=db,
            current_user=setup_data["user"]
        )

        assert transaction.offline_receipt_number == offline_receipt

        # Verify can query by offline receipt number
        found = db.query(Transaction).filter(
            Transaction.offline_receipt_number == offline_receipt
        ).first()
        
        assert found is not None
        assert found.id == transaction.id
