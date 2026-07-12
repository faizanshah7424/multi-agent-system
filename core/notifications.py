import logging
from datetime import datetime, timezone, timedelta
from core.database import (
    get_db_session,
    User,
    NotificationPreferenceRecord,
    NotificationRecord,
    NotificationQueueRecord,
    log_debug,
)

# Set up notifications logger
logger = logging.getLogger("notifications")


def get_or_create_preferences(user_id: str, session) -> NotificationPreferenceRecord:
    """Retrieve user's notification preferences, or create defaults if missing."""
    pref = (
        session.query(NotificationPreferenceRecord)
        .filter(NotificationPreferenceRecord.user_id == user_id)
        .first()
    )

    if not pref:
        pref = NotificationPreferenceRecord(
            user_id=user_id,
            email_enabled=True,
            sms_enabled=True,
            in_app_enabled=True,
            marketing_emails=True,
            security_alerts=True,
            task_updates=True,
        )
        session.add(pref)
        session.commit()
    return pref


def update_preferences(
    user_id: str, payload: dict, session
) -> NotificationPreferenceRecord:
    """Update user's notification preferences."""
    pref = get_or_create_preferences(user_id, session)

    for key, val in payload.items():
        if hasattr(pref, key) and key != "user_id" and key != "id":
            setattr(pref, key, val)

    session.commit()
    return pref


def send_notification(
    user_id: str,
    title: str,
    message: str,
    notification_type: str = "info",
    category: str = "general",
    channel: str = None,
) -> dict:
    """
    Sends or queues a notification based on user preferences.
    If channel is not specified, sends to all user's enabled channels.
    """
    result = {"in_app": "skipped", "email": "skipped", "sms": "skipped"}

    with get_db_session() as session:
        # Check user details
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            log_debug(f"Notification error: User '{user_id}' not found.")
            return {"error": "User not found"}

        # Get preferences
        pref = get_or_create_preferences(user_id, session)

        # Check category preferences
        if category == "marketing" and not pref.marketing_emails:
            log_debug(f"Skipping marketing notification for {user.email}")
            return {"status": "skipped_by_category_preference"}
        if category == "security" and not pref.security_alerts:
            # Note: We usually force security alerts, but we respect preferences if explicitly set
            pass
        if category == "task" and not pref.task_updates:
            log_debug(f"Skipping task notification for {user.email}")
            return {"status": "skipped_by_category_preference"}

        # 1. In-App Notification (Direct write)
        if (channel is None or channel == "in_app") and pref.in_app_enabled:
            in_app_rec = NotificationRecord(
                user_id=user_id,
                title=title,
                message=message,
                type=notification_type,
                category=category,
            )
            session.add(in_app_rec)
            result["in_app"] = "sent"

        # 2. Email Notification (Queued)
        if (channel is None or channel == "email") and pref.email_enabled:
            email_addr = user.email
            if email_addr:
                queue_rec = NotificationQueueRecord(
                    user_id=user_id,
                    channel="email",
                    recipient=email_addr,
                    title=title,
                    content=message,
                    status="pending",
                )
                session.add(queue_rec)
                result["email"] = "queued"

        # 3. SMS Notification (Queued)
        if (channel is None or channel == "sms") and pref.sms_enabled:
            # We assume user has a phone field or we use dummy/stored metadata
            # In our database schema, users have no phone column, so we default to user.email or mock phone number
            phone = getattr(user, "phone", None) or f"+15550199{user_id[:4]}"
            queue_rec = NotificationQueueRecord(
                user_id=user_id,
                channel="sms",
                recipient=phone,
                title=title,
                content=message,
                status="pending",
            )
            session.add(queue_rec)
            result["sms"] = "queued"

        session.commit()

    log_debug(f"Notification dispatch triggered for user {user_id}. Result: {result}")
    return result


def send_email_direct(recipient: str, title: str, content: str) -> bool:
    """Mock direct email sending. Simulates API connectivity."""
    log_debug(
        f"[EMAIL SEND] Sending to {recipient} | Subject: {title} | Content: {content[:40]}..."
    )
    # Simulate potential transient API failure for retry testing (10% random chance, unless test forces it)
    if "FAIL_TEST" in content:
        raise ConnectionError("Simulated SMTP Connection Error")
    return True


def send_sms_direct(recipient: str, content: str) -> bool:
    """Mock direct SMS sending. Simulates SMS Gateway connectivity."""
    log_debug(f"[SMS SEND] Sending to {recipient} | Message: {content[:40]}...")
    if "FAIL_TEST" in content:
        raise ConnectionError("Simulated Telephony Provider Error")
    return True


def process_queued_notifications() -> int:
    """
    Background worker loop iteration.
    Processes pending/failed notifications from the queue with retry logic.
    Returns the count of processed notifications.
    """
    processed_count = 0
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    with get_db_session() as session:
        # Fetch pending notifications, or failed ones whose retry backoff time has passed
        queued = (
            session.query(NotificationQueueRecord)
            .filter(
                NotificationQueueRecord.status.in_(["pending", "failed", "retrying"]),
                (NotificationQueueRecord.next_attempt_at.is_(None))
                | (NotificationQueueRecord.next_attempt_at <= now),
            )
            .all()
        )

        for item in queued:
            processed_count += 1
            item.attempts += 1
            item.last_attempt_at = now

            try:
                if item.channel == "email":
                    send_email_direct(
                        item.recipient, item.title or "System Alert", item.content
                    )
                elif item.channel == "sms":
                    send_sms_direct(item.recipient, item.content)
                else:
                    raise ValueError(f"Unknown channel: {item.channel}")

                # Success
                item.status = "sent"
                item.error_message = None
                log_debug(f"Notification queue item {item.id} sent successfully.")
            except Exception as e:
                item.error_message = str(e)
                if item.attempts >= item.max_attempts:
                    item.status = "failed"
                    log_debug(
                        f"Notification queue item {item.id} permanently failed after {item.attempts} attempts."
                    )
                else:
                    item.status = "retrying"
                    # Exponential backoff: retry in attempts * 5 seconds
                    backoff_sec = item.attempts * 5
                    item.next_attempt_at = now + timedelta(seconds=backoff_sec)
                    log_debug(
                        f"Notification queue item {item.id} failed. Retrying in {backoff_sec}s."
                    )

        session.commit()

    return processed_count
