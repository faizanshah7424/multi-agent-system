import unittest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from api.app import app
from core.database import (
    get_db_session,
    User,
    NotificationPreferenceRecord,
    NotificationRecord,
    NotificationQueueRecord,
    RefreshTokenRecord,
    Base,
    engine,
    init_db,
)
from core.notifications import (
    send_notification,
    get_or_create_preferences,
    update_preferences,
    process_queued_notifications,
)


class TestNotificationSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        init_db()
        cls.client = TestClient(app)

    def setUp(self):
        with get_db_session() as session:
            session.query(RefreshTokenRecord).delete()
            session.query(NotificationQueueRecord).delete()
            session.query(NotificationRecord).delete()
            session.query(NotificationPreferenceRecord).delete()
            session.query(User).delete()
            session.commit()

    def test_preferences_flow(self):
        # Create user
        signup_res = self.client.post(
            "/auth/signup", json={"email": "notify@orbit.ai", "password": "password123"}
        )
        user_id = signup_res.json()["user_id"]

        # Verify preferences automatically created on demand
        with get_db_session() as session:
            pref = get_or_create_preferences(user_id, session)
            self.assertEqual(pref.user_id, user_id)
            self.assertTrue(pref.email_enabled)
            self.assertTrue(pref.in_app_enabled)

            # Update preferences
            update_preferences(
                user_id, {"email_enabled": False, "sms_enabled": True}, session
            )

            pref2 = get_or_create_preferences(user_id, session)
            self.assertFalse(pref2.email_enabled)
            self.assertTrue(pref2.sms_enabled)

    def test_notification_dispatch_respects_preferences(self):
        # Create user
        signup_res = self.client.post(
            "/auth/signup",
            json={"email": "respect@orbit.ai", "password": "password123"},
        )
        user_id = signup_res.json()["user_id"]

        # 1. Update preferences to disable SMS, enable Email and In-App
        with get_db_session() as session:
            update_preferences(
                user_id,
                {"email_enabled": True, "sms_enabled": False, "in_app_enabled": True},
                session,
            )

        # 2. Trigger notification dispatch
        res = send_notification(
            user_id=user_id,
            title="Telemetry Warning",
            message="Agent latency exceeded threshold.",
            notification_type="warning",
            category="task",
        )

        # Assertions
        self.assertEqual(res["in_app"], "sent")
        self.assertEqual(res["email"], "queued")
        self.assertEqual(res["sms"], "skipped")

        # Verify database logs
        with get_db_session() as session:
            # Check In-App Record exists
            in_app = (
                session.query(NotificationRecord)
                .filter(NotificationRecord.user_id == user_id)
                .first()
            )
            self.assertIsNotNone(in_app)
            self.assertEqual(in_app.title, "Telemetry Warning")
            self.assertEqual(in_app.type, "warning")
            self.assertFalse(in_app.is_read)

            # Check Email Queue Record exists
            email_q = (
                session.query(NotificationQueueRecord)
                .filter(
                    NotificationQueueRecord.user_id == user_id,
                    NotificationQueueRecord.channel == "email",
                )
                .first()
            )
            self.assertIsNotNone(email_q)
            self.assertEqual(email_q.status, "pending")
            self.assertEqual(email_q.recipient, "respect@orbit.ai")

    def test_queue_worker_success_and_retry(self):
        signup_res = self.client.post(
            "/auth/signup", json={"email": "worker@orbit.ai", "password": "password123"}
        )
        user_id = signup_res.json()["user_id"]

        # 1. Send normal queued notification
        send_notification(
            user_id=user_id,
            title="Task Started",
            message="Execution code initiated.",
            channel="email",
        )

        # 2. Send notification that forces SMTP failure
        send_notification(
            user_id=user_id,
            title="Connection Error Test",
            message="Task sync failed FAIL_TEST",
            channel="email",
        )

        # Run worker processing
        processed = process_queued_notifications()
        self.assertEqual(processed, 2)

        # Verify status in database
        with get_db_session() as session:
            success_item = (
                session.query(NotificationQueueRecord)
                .filter(NotificationQueueRecord.title == "Task Started")
                .first()
            )
            self.assertEqual(success_item.status, "sent")
            self.assertEqual(success_item.attempts, 1)
            self.assertIsNone(success_item.error_message)

            failed_item = (
                session.query(NotificationQueueRecord)
                .filter(NotificationQueueRecord.title == "Connection Error Test")
                .first()
            )
            self.assertEqual(failed_item.status, "retrying")
            self.assertEqual(failed_item.attempts, 1)
            self.assertIsNotNone(failed_item.error_message)
            self.assertIsNotNone(failed_item.next_attempt_at)

            # Set next_attempt_at to past to force reprocessing
            failed_item.next_attempt_at = datetime.now(timezone.utc).replace(
                tzinfo=None
            ) - timedelta(minutes=1)
            session.commit()

        # Run worker processing again - attempt 2
        process_queued_notifications()

        with get_db_session() as session:
            failed_item = (
                session.query(NotificationQueueRecord)
                .filter(NotificationQueueRecord.title == "Connection Error Test")
                .first()
            )
            self.assertEqual(failed_item.status, "retrying")
            self.assertEqual(failed_item.attempts, 2)

            # Reprocess once more to hit max attempts (3)
            failed_item.next_attempt_at = datetime.now(timezone.utc).replace(
                tzinfo=None
            ) - timedelta(minutes=1)
            session.commit()

        # Run worker processing again - attempt 3 (should mark as failed)
        process_queued_notifications()

        with get_db_session() as session:
            failed_item = (
                session.query(NotificationQueueRecord)
                .filter(NotificationQueueRecord.title == "Connection Error Test")
                .first()
            )
            self.assertEqual(failed_item.status, "failed")
            self.assertEqual(failed_item.attempts, 3)

    def test_notification_endpoints(self):
        # Signup user and login
        signup_res = self.client.post(
            "/auth/signup", json={"email": "client@orbit.ai", "password": "password123"}
        )
        self.assertEqual(signup_res.status_code, 201)
        verify_token = signup_res.json()["verification_token"]

        # Verify email to make active
        verify_res = self.client.get(f"/auth/verify-email?token={verify_token}")
        self.assertEqual(verify_res.status_code, 200)

        login_res = self.client.post(
            "/auth/login", json={"email": "client@orbit.ai", "password": "password123"}
        )
        self.assertEqual(login_res.status_code, 200)
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Test Preferences endpoint GET
        get_pref = self.client.get("/notifications/preferences", headers=headers)
        self.assertEqual(get_pref.status_code, 200)
        self.assertTrue(get_pref.json()["email_enabled"])

        # 2. Test Preferences endpoint PUT
        put_pref = self.client.put(
            "/notifications/preferences", json={"email_enabled": False}, headers=headers
        )
        self.assertEqual(put_pref.status_code, 200)
        self.assertFalse(put_pref.json()["preferences"]["email_enabled"])

        # 3. Test triggering test notification
        test_trigger = self.client.post(
            "/notifications/test",
            json={
                "title": "API Test Alert",
                "message": "Verify endpoint routing.",
                "category": "security",
                "channel": "in_app",
            },
            headers=headers,
        )
        self.assertEqual(test_trigger.status_code, 200)

        # 4. Test GET notifications list
        get_list = self.client.get("/notifications", headers=headers)
        self.assertEqual(get_list.status_code, 200)
        self.assertEqual(len(get_list.json()), 1)
        notif_id = get_list.json()[0]["id"]

        # 5. Test read notification
        read_res = self.client.put(f"/notifications/{notif_id}/read", headers=headers)
        self.assertEqual(read_res.status_code, 200)

        # Verify read status
        get_list2 = self.client.get("/notifications?unread_only=true", headers=headers)
        self.assertEqual(len(get_list2.json()), 0)
