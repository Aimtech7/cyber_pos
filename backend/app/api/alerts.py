"""
Alert API Endpoints
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime

from app.database import get_db
from app.core.permissions import require_role
from app.models.user import User, UserRole
from app.models.alert import Alert, AlertType, AlertSeverity, AlertStatus
from app.schemas.alert import (
    AlertResponse,
    AlertListResponse,
    AlertUpdate,
    AlertAcknowledge,
    AlertResolve,
    AlertStats,
    AlertTypeEnum,
    AlertSeverityEnum,
    AlertStatusEnum
)
from app.services.alert_engine import run_alert_checks
from app.models.audit import AuditLog

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    type_filter: Optional[AlertTypeEnum] = None,
    severity_filter: Optional[AlertSeverityEnum] = None,
    status_filter: Optional[AlertStatusEnum] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """List alerts with filters and pagination"""
    
    query = db.query(Alert)
    
    # Apply filters
    if type_filter:
        query = query.filter(Alert.type == type_filter.value)
    if severity_filter:
        query = query.filter(Alert.severity == severity_filter.value)
    if status_filter:
        query = query.filter(Alert.status == status_filter.value)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    alerts = query.order_by(Alert.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    # Log access
    db.add(AuditLog(
        user_id=current_user.id,
        action="LIST_ALERTS",
        details={"filters": {"type": type_filter, "severity": severity_filter, "status": status_filter}}
    ))
    db.commit()
    
    return AlertListResponse(
        items=alerts,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/stats", response_model=AlertStats)
async def get_alert_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Get alert statistics for dashboard"""
    
    # Count by status
    total_open = db.query(Alert).filter(Alert.status == AlertStatus.OPEN).count()
    total_acknowledged = db.query(Alert).filter(Alert.status == AlertStatus.ACKNOWLEDGED).count()
    total_resolved = db.query(Alert).filter(Alert.status == AlertStatus.RESOLVED).count()
    
    # Count by severity (open only)
    by_severity = {}
    for severity in AlertSeverity:
        count = db.query(Alert).filter(
            and_(
                Alert.severity == severity,
                Alert.status == AlertStatus.OPEN
            )
        ).count()
        by_severity[severity.value] = count
    
    # Count by type (open only)
    by_type = {}
    for alert_type in AlertType:
        count = db.query(Alert).filter(
            and_(
                Alert.type == alert_type,
                Alert.status == AlertStatus.OPEN
            )
        ).count()
        by_type[alert_type.value] = count
    
    # Critical and high open alerts
    critical_open = db.query(Alert).filter(
        and_(
            Alert.severity == AlertSeverity.CRITICAL,
            Alert.status == AlertStatus.OPEN
        )
    ).count()
    
    high_open = db.query(Alert).filter(
        and_(
            Alert.severity == AlertSeverity.HIGH,
            Alert.status == AlertStatus.OPEN
        )
    ).count()
    
    return AlertStats(
        total_open=total_open,
        total_acknowledged=total_acknowledged,
        total_resolved=total_resolved,
        by_severity=by_severity,
        by_type=by_type,
        critical_open=critical_open,
        high_open=high_open
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Get alert details"""
    
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Log access
    db.add(AuditLog(
        user_id=current_user.id,
        action="VIEW_ALERT",
        details={"alert_id": alert_id, "alert_type": alert.type.value}
    ))
    db.commit()
    
    return alert


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: str,
    data: AlertAcknowledge,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Acknowledge an alert"""
    
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if alert.status != AlertStatus.OPEN:
        raise HTTPException(status_code=400, detail="Only open alerts can be acknowledged")
    
    # Update alert
    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()
    
    if data.notes:
        alert.description = (alert.description or "") + f"\n\nAcknowledgment notes: {data.notes}"
    
    # Log action
    db.add(AuditLog(
        user_id=current_user.id,
        action="ACKNOWLEDGE_ALERT",
        details={
            "alert_id": alert_id,
            "alert_type": alert.type.value,
            "notes": data.notes
        }
    ))
    
    db.commit()
    db.refresh(alert)
    
    return alert


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: str,
    data: AlertResolve,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Resolve an alert"""
    
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if alert.status == AlertStatus.RESOLVED:
        raise HTTPException(status_code=400, detail="Alert already resolved")
    
    # Update alert
    alert.status = AlertStatus.RESOLVED
    alert.resolved_by = current_user.id
    alert.resolved_at = datetime.utcnow()
    alert.resolution_notes = data.resolution_notes
    
    # Log action
    db.add(AuditLog(
        user_id=current_user.id,
        action="RESOLVE_ALERT",
        details={
            "alert_id": alert_id,
            "alert_type": alert.type.value,
            "resolution_notes": data.resolution_notes
        }
    ))
    
    db.commit()
    db.refresh(alert)
    
    return alert


@router.post("/run-checks")
async def manual_run_checks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Manually trigger alert detection checks (Admin only)"""
    
    try:
        alerts = run_alert_checks(db)
        
        # Log action
        db.add(AuditLog(
            user_id=current_user.id,
            action="MANUAL_ALERT_CHECK",
            details={"alerts_created": len(alerts)}
        ))
        db.commit()
        
        return {
            "success": True,
            "alerts_created": len(alerts),
            "message": f"Created {len(alerts)} new alerts"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running alert checks: {str(e)}")


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    data: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Update alert (assign to user)"""
    
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if data.assigned_to:
        # Verify user exists
        user = db.query(User).filter(User.id == data.assigned_to).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        alert.assigned_to = data.assigned_to
    
    # Log action
    db.add(AuditLog(
        user_id=current_user.id,
        action="UPDATE_ALERT",
        details={"alert_id": alert_id, "assigned_to": data.assigned_to}
    ))
    
    db.commit()
    db.refresh(alert)
    
    return alert
