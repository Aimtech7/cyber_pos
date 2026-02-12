"""
Print Job Queue System - Basic Tests
Tests for print job submission, approval, rejection, and printing workflow
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from decimal import Decimal
from uuid import uuid4

from app.main import app
from app.models.print_job import PrintJob, PrintJobStatus
from app.models.service import Service, PricingMode
from app.models.computer import Computer
from app.models.user import User, UserRole
from app.models.shift import Shift


client = TestClient(app)


def test_submit_print_job(db: Session, auth_headers: dict, test_computer: Computer):
    """Test submitting a new print job"""
    # Create printing services
    bw_service = Service(
        name="Printing (Black & White)",
        category="printing",
        pricing_mode=PricingMode.PER_UNIT,
        base_price=Decimal("5.00"),
        is_active=True
    )
    color_service = Service(
        name="Printing (Color)",
        category="printing",
        pricing_mode=PricingMode.PER_UNIT,
        base_price=Decimal("10.00"),
        is_active=True
    )
    db.add_all([bw_service, color_service])
    db.commit()
    
    # Submit print job
    response = client.post(
        "/print-jobs",
        json={
            "computer_id": str(test_computer.id),
            "requested_by": "John Doe",
            "description": "Assignment",
            "pages_bw": 5,
            "pages_color": 2
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["requested_by"] == "John Doe"
    assert data["pages_bw"] == 5
    assert data["pages_color"] == 2
    assert data["status"] == "pending"
    # 5 * 5 + 2 * 10 = 45
    assert float(data["total_amount"]) == 45.0
    assert "job_number" in data


def test_approve_print_job(db: Session, auth_headers: dict, test_shift: Shift):
    """Test approving a print job"""
    # Create services
    bw_service = Service(
        name="Printing (Black & White)",
        category="printing",
        pricing_mode=PricingMode.PER_UNIT,
        base_price=Decimal("5.00"),
        is_active=True
    )
    db.add(bw_service)
    db.commit()
    
    # Create print job
    computer = db.query(Computer).first()
    job = PrintJob(
        computer_id=computer.id,
        requested_by="Test User",
        pages_bw=3,
        pages_color=0,
        total_amount=Decimal("15.00"),
        status=PrintJobStatus.PENDING
    )
    db.add(job)
    db.commit()
    
    # Approve job
    response = client.post(
        f"/print-jobs/{job.id}/approve",
        json={},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["approved_by"] is not None
    assert data["transaction_id"] is not None


def test_reject_print_job(db: Session, auth_headers: dict):
    """Test rejecting a print job"""
    # Create print job
    computer = db.query(Computer).first()
    job = PrintJob(
        computer_id=computer.id,
        requested_by="Test User",
        pages_bw=5,
        pages_color=0,
        total_amount=Decimal("25.00"),
        status=PrintJobStatus.PENDING
    )
    db.add(job)
    db.commit()
    
    # Reject job
    response = client.post(
        f"/print-jobs/{job.id}/reject",
        json={"rejection_reason": "Insufficient funds"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["rejection_reason"] == "Insufficient funds"
    assert data["rejected_by"] is not None


def test_mark_job_printed(db: Session, auth_headers: dict, test_shift: Shift):
    """Test marking job as printed"""
    # Create services
    bw_service = Service(
        name="Printing (Black & White)",
        category="printing",
        pricing_mode=PricingMode.PER_UNIT,
        base_price=Decimal("5.00"),
        is_active=True
    )
    db.add(bw_service)
    db.commit()
    
    # Create approved job
    computer = db.query(Computer).first()
    user = db.query(User).first()
    job = PrintJob(
        computer_id=computer.id,
        requested_by="Test User",
        pages_bw=2,
        pages_color=0,
        total_amount=Decimal("10.00"),
        status=PrintJobStatus.APPROVED,
        approved_by=user.id
    )
    db.add(job)
    db.commit()
    
    # Mark as printed
    response = client.post(
        f"/print-jobs/{job.id}/mark-printed",
        json={},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "printed"
    assert data["printed_by"] is not None


def test_list_print_jobs(db: Session, auth_headers: dict):
    """Test listing print jobs"""
    response = client.get("/print-jobs", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "pending_count" in data
    assert "approved_count" in data


def test_cannot_approve_non_pending_job(db: Session, auth_headers: dict):
    """Test that non-pending jobs cannot be approved"""
    computer = db.query(Computer).first()
    job = PrintJob(
        computer_id=computer.id,
        requested_by="Test User",
        pages_bw=1,
        pages_color=0,
        total_amount=Decimal("5.00"),
        status=PrintJobStatus.REJECTED
    )
    db.add(job)
    db.commit()
    
    response = client.post(
        f"/print-jobs/{job.id}/approve",
        json={},
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "Cannot approve" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
