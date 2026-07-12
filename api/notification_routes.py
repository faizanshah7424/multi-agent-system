from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from core.database import get_db_session, NotificationRecord, NotificationQueueRecord
from core.auth.dependencies import get_current_user, PermissionChecker
from core.notifications import (
    send_notification, get_or_create_preferences, 
    update_preferences, process_queued_notifications
)

router = APIRouter(prefix="/notifications", tags=["Notification System"])

class PreferencesUpdateSchema(BaseModel):
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    marketing_emails: Optional[bool] = None
    security_alerts: Optional[bool] = None
    task_updates: Optional[bool] = None

class TestNotificationSchema(BaseModel):
    title: str
    message: str
    category: str = "general"
    channel: Optional[str] = None
    force_failure: bool = False

@router.get("")
def get_notifications(
    limit: int = 50,
    offset: int = 0,
    unread_only: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Retrieve in-app notifications for the authenticated user."""
    with get_db_session() as session:
        query = session.query(NotificationRecord).filter(NotificationRecord.user_id == current_user["id"])
        if unread_only:
            query = query.filter(NotificationRecord.is_read.is_(False))
        
        notifications = query.order_by(NotificationRecord.created_at.desc()).limit(limit).offset(offset).all()
        
        return [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "type": n.type,
                "category": n.category,
                "is_read": n.is_read,
                "created_at": n.created_at,
                "read_at": n.read_at
            }
            for n in notifications
        ]

@router.put("/{notification_id}/read")
def read_notification(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a specific in-app notification as read."""
    with get_db_session() as session:
        n = session.query(NotificationRecord).filter(
            NotificationRecord.id == notification_id,
            NotificationRecord.user_id == current_user["id"]
        ).first()
        
        if not n:
            raise HTTPException(status_code=404, detail="Notification not found.")
            
        n.is_read = True
        n.read_at = datetime.now(timezone.utc).replace(tzinfo=None)
        session.commit()
        return {"message": "Notification marked as read."}

@router.post("/read-all")
def read_all_notifications(current_user: dict = Depends(get_current_user)):
    """Mark all unread in-app notifications as read."""
    with get_db_session() as session:
        unread = session.query(NotificationRecord).filter(
            NotificationRecord.user_id == current_user["id"],
            NotificationRecord.is_read.is_(False)
        ).all()
        
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        for n in unread:
            n.is_read = True
            n.read_at = now
            
        session.commit()
        return {"message": f"Marked {len(unread)} notifications as read."}

@router.get("/preferences")
def get_preferences_endpoint(current_user: dict = Depends(get_current_user)):
    """Get the current user's notification preferences."""
    with get_db_session() as session:
        pref = get_or_create_preferences(current_user["id"], session)
        return {
            "email_enabled": pref.email_enabled,
            "sms_enabled": pref.sms_enabled,
            "in_app_enabled": pref.in_app_enabled,
            "marketing_emails": pref.marketing_emails,
            "security_alerts": pref.security_alerts,
            "task_updates": pref.task_updates
        }

@router.put("/preferences")
def update_preferences_endpoint(payload: PreferencesUpdateSchema, current_user: dict = Depends(get_current_user)):
    """Update notification preferences for the user."""
    with get_db_session() as session:
        pref = update_preferences(current_user["id"], payload.model_dump(exclude_none=True), session)
        return {
            "message": "Preferences updated successfully.",
            "preferences": {
                "email_enabled": pref.email_enabled,
                "sms_enabled": pref.sms_enabled,
                "in_app_enabled": pref.in_app_enabled,
                "marketing_emails": pref.marketing_emails,
                "security_alerts": pref.security_alerts,
                "task_updates": pref.task_updates
            }
        }

@router.get("/stats")
def get_notification_stats(current_user: dict = Depends(PermissionChecker("audit:read"))):
    """Retrieve system-wide notification performance, channels volume, and queue metrics (Admin/Developer)."""
    with get_db_session() as session:
        # In-App stats
        total_in_app = session.query(NotificationRecord).count()
        unread_in_app = session.query(NotificationRecord).filter(NotificationRecord.is_read.is_(False)).count()
        
        # Queue stats
        total_queued = session.query(NotificationQueueRecord).count()
        pending_queued = session.query(NotificationQueueRecord).filter(NotificationQueueRecord.status == "pending").count()
        sent_queued = session.query(NotificationQueueRecord).filter(NotificationQueueRecord.status == "sent").count()
        failed_queued = session.query(NotificationQueueRecord).filter(NotificationQueueRecord.status == "failed").count()
        retrying_queued = session.query(NotificationQueueRecord).filter(NotificationQueueRecord.status == "retrying").count()
        
        # Channels split
        email_queued = session.query(NotificationQueueRecord).filter(NotificationQueueRecord.channel == "email").count()
        sms_queued = session.query(NotificationQueueRecord).filter(NotificationQueueRecord.channel == "sms").count()
        
        # Recent queue items for display
        recent_items = session.query(NotificationQueueRecord).order_by(NotificationQueueRecord.created_at.desc()).limit(10).all()
        recent_list = [
            {
                "id": item.id,
                "channel": item.channel,
                "recipient": item.recipient,
                "title": item.title,
                "content": item.content,
                "status": item.status,
                "attempts": item.attempts,
                "error_message": item.error_message,
                "created_at": item.created_at
            }
            for item in recent_items
        ]
        
        return {
            "in_app": {
                "total": total_in_app,
                "unread": unread_in_app
            },
            "queue": {
                "total": total_queued,
                "pending": pending_queued,
                "sent": sent_queued,
                "failed": failed_queued,
                "retrying": retrying_queued
            },
            "channels": {
                "email": email_queued,
                "sms": sms_queued
            },
            "recent_queue": recent_list
        }

@router.post("/test")
def trigger_test_notification(payload: TestNotificationSchema, current_user: dict = Depends(get_current_user)):
    """Trigger a test notification flow. Supports forcing failures to check retries."""
    message = payload.message
    if payload.force_failure:
        message += " FAIL_TEST"
        
    res = send_notification(
        user_id=current_user["id"],
        title=payload.title,
        message=message,
        notification_type="info",
        category=payload.category,
        channel=payload.channel
    )
    return {
        "message": "Test notification dispatched.",
        "result": res
    }

@router.post("/process-queue")
def trigger_process_queue(current_user: dict = Depends(PermissionChecker("tasks:create"))):
    """Manually trigger queue processing (Admin/Developer)."""
    count = process_queued_notifications()
    return {"message": f"Processed {count} notification queue items."}
