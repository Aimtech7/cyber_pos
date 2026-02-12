"""
Unit Tests for Customer and Invoice APIs
"""
import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
from datetime import date, timedelta
from app.main import app
from app.database import get_db
from app.models.customer import Customer, CustomerType
from app.models.invoice import Invoice, InvoiceItem, InvoicePayment, InvoiceStatus
from app.models.user import User, UserRole
from app.core.security import get_password_hash

client = TestClient(app)


@pytest.fixture
def test_admin_token(db_session):
    """Create admin user and return auth token"""
    admin = User(
        username="testadmin",
        email="admin@test.com",
        hashed_password=get_password_hash("testpass"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()
    
    response = client.post("/auth/login", data={
        "username": "testadmin",
        "password": "testpass"
    })
    return response.json()["access_token"]


@pytest.fixture
def test_customer(db_session, test_admin_token):
    """Create test customer"""
    response = client.post(
        "/customers",
        json={
            "name": "Test Customer",
            "phone": "0712345678",
            "email": "test@customer.com",
            "type": "individual",
            "credit_limit": 50000
        },
        headers={"Authorization": f"Bearer {test_admin_token}"}
    )
    return response.json()


class TestCustomerAPI:
    """Test Customer API endpoints"""
    
    def test_create_customer(self, test_admin_token):
        """Test creating a customer"""
        response = client.post(
            "/customers",
            json={
                "name": "New Customer",
                "phone": "0723456789",
                "type": "institution",
                "credit_limit": 100000
            },
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Customer"
        assert data["credit_limit"] == 100000
        assert data["current_balance"] == 0
        assert data["available_credit"] == 100000
        assert "customer_number" in data
    
    def test_list_customers(self, test_admin_token, test_customer):
        """Test listing customers"""
        response = client.get(
            "/customers",
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] > 0
    
    def test_get_customer(self, test_admin_token, test_customer):
        """Test getting customer details"""
        customer_id = test_customer["id"]
        response = client.get(
            f"/customers/{customer_id}",
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == customer_id
        assert data["name"] == "Test Customer"
    
    def test_update_customer(self, test_admin_token, test_customer):
        """Test updating customer"""
        customer_id = test_customer["id"]
        response = client.put(
            f"/customers/{customer_id}",
            json={"credit_limit": 75000},
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["credit_limit"] == 75000
    
    def test_check_credit_sufficient(self, test_admin_token, test_customer):
        """Test credit check with sufficient credit"""
        customer_id = test_customer["id"]
        response = client.post(
            f"/customers/{customer_id}/check-credit",
            json={"amount": 10000},
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["can_proceed"] is True
        assert data["available_credit"] >= 10000
    
    def test_check_credit_insufficient(self, test_admin_token, test_customer):
        """Test credit check with insufficient credit"""
        customer_id = test_customer["id"]
        response = client.post(
            f"/customers/{customer_id}/check-credit",
            json={"amount": 100000},
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["can_proceed"] is False
    
    def test_deactivate_customer(self, test_admin_token, test_customer):
        """Test deactivating customer"""
        customer_id = test_customer["id"]
        response = client.post(
            f"/customers/{customer_id}/deactivate",
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False


class TestInvoiceAPI:
    """Test Invoice API endpoints"""
    
    def test_create_invoice(self, test_admin_token, test_customer):
        """Test creating an invoice"""
        response = client.post(
            "/invoices",
            json={
                "customer_id": test_customer["id"],
                "items": [
                    {
                        "description": "Test Service",
                        "quantity": 2,
                        "unit_price": 1000,
                        "total_price": 2000
                    }
                ],
                "due_days": 30,
                "notes": "Test invoice"
            },
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["customer_id"] == test_customer["id"]
        assert data["status"] == "draft"
        assert data["total_amount"] == 2000
        assert "invoice_number" in data
    
    def test_issue_invoice(self, test_admin_token, test_customer):
        """Test issuing an invoice"""
        # Create draft invoice
        create_response = client.post(
            "/invoices",
            json={
                "customer_id": test_customer["id"],
                "items": [{"description": "Test", "quantity": 1, "unit_price": 5000, "total_price": 5000}],
                "due_days": 30
            },
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        invoice_id = create_response.json()["id"]
        
        # Issue invoice
        response = client.post(
            f"/invoices/{invoice_id}/issue",
            json={},
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "issued"
        assert data["issue_date"] is not None
    
    def test_record_payment(self, test_admin_token, test_customer):
        """Test recording payment on invoice"""
        # Create and issue invoice
        create_response = client.post(
            "/invoices",
            json={
                "customer_id": test_customer["id"],
                "items": [{"description": "Test", "quantity": 1, "unit_price": 10000, "total_price": 10000}],
                "due_days": 30,
                "issue_immediately": True
            },
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        invoice_id = create_response.json()["id"]
        
        # Record payment
        response = client.post(
            f"/invoices/{invoice_id}/payments",
            json={
                "amount": 5000,
                "payment_method": "cash",
                "reference": "CASH001"
            },
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == 5000
        assert data["payment_method"] == "cash"
        
        # Verify invoice status
        invoice_response = client.get(
            f"/invoices/{invoice_id}",
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        invoice_data = invoice_response.json()
        assert invoice_data["status"] == "part_paid"
        assert invoice_data["paid_amount"] == 5000
        assert invoice_data["balance"] == 5000
    
    def test_full_payment(self, test_admin_token, test_customer):
        """Test full payment marks invoice as paid"""
        # Create and issue invoice
        create_response = client.post(
            "/invoices",
            json={
                "customer_id": test_customer["id"],
                "items": [{"description": "Test", "quantity": 1, "unit_price": 8000, "total_price": 8000}],
                "due_days": 30,
                "issue_immediately": True
            },
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        invoice_id = create_response.json()["id"]
        
        # Record full payment
        response = client.post(
            f"/invoices/{invoice_id}/payments",
            json={
                "amount": 8000,
                "payment_method": "mpesa",
                "reference": "MPE123456"
            },
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        
        assert response.status_code == 201
        
        # Verify invoice is paid
        invoice_response = client.get(
            f"/invoices/{invoice_id}",
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        invoice_data = invoice_response.json()
        assert invoice_data["status"] == "paid"
        assert invoice_data["balance"] == 0
    
    def test_cancel_invoice(self, test_admin_token, test_customer):
        """Test cancelling an invoice"""
        # Create invoice
        create_response = client.post(
            "/invoices",
            json={
                "customer_id": test_customer["id"],
                "items": [{"description": "Test", "quantity": 1, "unit_price": 3000, "total_price": 3000}],
                "due_days": 30
            },
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        invoice_id = create_response.json()["id"]
        
        # Cancel invoice
        response = client.post(
            f"/invoices/{invoice_id}/cancel",
            json={"reason": "Customer request"},
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
    
    def test_list_invoices(self, test_admin_token, test_customer):
        """Test listing invoices"""
        response = client.get(
            "/invoices",
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    
    def test_aging_report(self, test_admin_token, test_customer):
        """Test aging report"""
        response = client.get(
            "/invoices/aging-report",
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
