import unittest
from fastapi.testclient import TestClient
from api.app import app
from core.database import (
    get_db_session,
    User,
    RoleRecord,
    PermissionRecord,
    RolePermissionRecord,
    AuthAuditLogRecord,
    RefreshTokenRecord,
)


class TestRBACSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from core.database import Base, engine, init_db

        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        init_db()
        cls.client = TestClient(app)

    def setUp(self):
        with get_db_session() as session:
            # Clear test users and audit logs
            session.query(RefreshTokenRecord).delete()
            session.query(AuthAuditLogRecord).delete()
            session.query(User).delete()
            session.commit()

    def test_database_seeding(self):
        with get_db_session() as session:
            roles = session.query(RoleRecord).all()
            permissions = session.query(PermissionRecord).all()

            role_names = [r.name for r in roles]
            perm_names = [p.name for p in permissions]

            self.assertIn("admin", role_names)
            self.assertIn("developer", role_names)
            self.assertIn("member", role_names)

            self.assertIn("users:read", perm_names)
            self.assertIn("users:write", perm_names)
            self.assertIn("roles:read", perm_names)
            self.assertIn("roles:write", perm_names)
            self.assertIn("audit:read", perm_names)

    def test_rbac_endpoint_protection(self):
        # Create an admin, a developer, and a member
        signup_admin = self.client.post(
            "/auth/signup",
            json={
                "email": "admin@orbit.ai",
                "password": "password123",
                "role": "admin",
            },
        )
        admin_token = signup_admin.json()["verification_token"]
        self.client.get(f"/auth/verify-email?token={admin_token}")

        signup_dev = self.client.post(
            "/auth/signup",
            json={
                "email": "dev@orbit.ai",
                "password": "password123",
                "role": "developer",
            },
        )
        dev_token = signup_dev.json()["verification_token"]
        self.client.get(f"/auth/verify-email?token={dev_token}")

        signup_mem = self.client.post(
            "/auth/signup",
            json={"email": "mem@orbit.ai", "password": "password123", "role": "member"},
        )
        mem_token = signup_mem.json()["verification_token"]
        self.client.get(f"/auth/verify-email?token={mem_token}")

        # Log in to retrieve JWT access tokens
        login_admin = self.client.post(
            "/auth/login", json={"email": "admin@orbit.ai", "password": "password123"}
        )
        jwt_admin = login_admin.json()["access_token"]

        login_dev = self.client.post(
            "/auth/login", json={"email": "dev@orbit.ai", "password": "password123"}
        )
        jwt_dev = login_dev.json()["access_token"]

        login_mem = self.client.post(
            "/auth/login", json={"email": "mem@orbit.ai", "password": "password123"}
        )
        jwt_mem = login_mem.json()["access_token"]

        # 1. Admin checks (should access all)
        res_users_admin = self.client.get(
            "/admin/users", headers={"Authorization": f"Bearer {jwt_admin}"}
        )
        self.assertEqual(res_users_admin.status_code, 200)
        self.assertEqual(len(res_users_admin.json()), 3)

        res_audit_admin = self.client.get(
            "/admin/audit-logs", headers={"Authorization": f"Bearer {jwt_admin}"}
        )
        self.assertEqual(res_audit_admin.status_code, 200)

        # 2. Developer checks
        # Developer has users:read and audit:read, so this should pass (200)
        res_users_dev = self.client.get(
            "/admin/users", headers={"Authorization": f"Bearer {jwt_dev}"}
        )
        self.assertEqual(res_users_dev.status_code, 200)

        res_audit_dev = self.client.get(
            "/admin/audit-logs", headers={"Authorization": f"Bearer {jwt_dev}"}
        )
        self.assertEqual(res_audit_dev.status_code, 200)

        # Developer does NOT have roles:read, so this should fail (403)
        res_roles_dev = self.client.get(
            "/admin/roles", headers={"Authorization": f"Bearer {jwt_dev}"}
        )
        self.assertEqual(res_roles_dev.status_code, 403)

        # 3. Member checks
        # Member only has users:read, so audit:read should fail (403)
        res_audit_mem = self.client.get(
            "/admin/audit-logs", headers={"Authorization": f"Bearer {jwt_mem}"}
        )
        self.assertEqual(res_audit_mem.status_code, 403)

    def test_user_management_and_audit_logging(self):
        # Create admin and developer
        self.client.post(
            "/auth/signup",
            json={
                "email": "admin2@orbit.ai",
                "password": "password123",
                "role": "admin",
            },
        )
        admin_login = self.client.post(
            "/auth/login", json={"email": "admin2@orbit.ai", "password": "password123"}
        )
        jwt_admin = admin_login.json()["access_token"]

        signup_dev = self.client.post(
            "/auth/signup",
            json={
                "email": "dev2@orbit.ai",
                "password": "password123",
                "role": "developer",
            },
        )
        dev_id = signup_dev.json()["user_id"]

        # Admin updates developer active status to False
        update_res = self.client.put(
            f"/admin/users/{dev_id}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {jwt_admin}"},
        )
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.json()["user"]["is_active"], False)

        # Verify Audit Log got written
        audit_res = self.client.get(
            "/admin/audit-logs", headers={"Authorization": f"Bearer {jwt_admin}"}
        )
        self.assertEqual(audit_res.status_code, 200)
        logs = audit_res.json()
        self.assertTrue(len(logs) > 0)
        self.assertEqual(logs[0]["event_type"], "USER_UPDATED")
        self.assertIn("is_active", logs[0]["details"])

    def test_role_permissions_updating(self):
        # Create admin
        self.client.post(
            "/auth/signup",
            json={
                "email": "admin3@orbit.ai",
                "password": "password123",
                "role": "admin",
            },
        )
        admin_login = self.client.post(
            "/auth/login", json={"email": "admin3@orbit.ai", "password": "password123"}
        )
        jwt_admin = admin_login.json()["access_token"]

        # Create developer for testing access later
        self.client.post(
            "/auth/signup",
            json={
                "email": "dev3@orbit.ai",
                "password": "password123",
                "role": "developer",
            },
        )
        dev_login = self.client.post(
            "/auth/login", json={"email": "dev3@orbit.ai", "password": "password123"}
        )
        jwt_dev = dev_login.json()["access_token"]

        # Developer has tasks:create by default, let's verify dev has access to users list
        pre_check = self.client.get(
            "/admin/users", headers={"Authorization": f"Bearer {jwt_dev}"}
        )
        self.assertEqual(pre_check.status_code, 200)

        # Get roles to find developer role id
        roles_res = self.client.get(
            "/admin/roles", headers={"Authorization": f"Bearer {jwt_admin}"}
        )
        roles_list = roles_res.json()
        dev_role_id = next(r["id"] for r in roles_list if r["name"] == "developer")

        # Update developer role permissions: strip users:read, only leave tasks:create
        update_perms_res = self.client.post(
            f"/admin/roles/{dev_role_id}/permissions",
            json={"permission_names": ["tasks:create"]},
            headers={"Authorization": f"Bearer {jwt_admin}"},
        )
        self.assertEqual(update_perms_res.status_code, 200)

        # Now Developer tries to view users again - should fail with 403 Forbidden!
        post_check = self.client.get(
            "/admin/users", headers={"Authorization": f"Bearer {jwt_dev}"}
        )
        self.assertEqual(post_check.status_code, 403)

        # Verify Audit Log
        audit_res = self.client.get(
            "/admin/audit-logs", headers={"Authorization": f"Bearer {jwt_admin}"}
        )
        logs = audit_res.json()
        event_types = [log_item["event_type"] for log_item in logs]
        self.assertIn("ROLE_PERMISSIONS_UPDATED", event_types)
