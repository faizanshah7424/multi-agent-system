import unittest
from fastapi.testclient import TestClient
from api.app import app
from core.database import get_db_session, User, RefreshTokenRecord

class TestAuthSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from core.database import Base, engine
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    def setUp(self):
        with get_db_session() as session:
            session.query(RefreshTokenRecord).delete()
            session.query(User).delete()
            session.commit()

    def test_signup_login_refresh_flow(self):
        signup_res = self.client.post("/auth/signup", json={
            "email": "user@orbit.ai",
            "password": "securepassword123",
            "role": "developer"
        })
        self.assertEqual(signup_res.status_code, 201)
        self.assertIn("verification_token", signup_res.json())
        token = signup_res.json()["verification_token"]

        verify_res = self.client.get(f"/auth/verify-email?token={token}")
        self.assertEqual(verify_res.status_code, 200)

        login_res = self.client.post("/auth/login", json={
            "email": "user@orbit.ai",
            "password": "securepassword123"
        })
        self.assertEqual(login_res.status_code, 200)
        self.assertIn("access_token", login_res.json())
        self.assertIn("refresh_token", login_res.json())
        login_res.json()["access_token"]
        refresh = login_res.json()["refresh_token"]

        refresh_res = self.client.post("/auth/refresh", json={
            "refresh_token": refresh
        })
        self.assertEqual(refresh_res.status_code, 200)
        self.assertIn("access_token", refresh_res.json())

        # Test Logout
        logout_res = self.client.post("/auth/logout", json={
            "refresh_token": refresh
        })
        self.assertEqual(logout_res.status_code, 200)
        self.assertEqual(logout_res.json()["message"], "Logged out successfully.")

        # Trying to refresh again should fail since token is revoked
        failed_refresh_res = self.client.post("/auth/refresh", json={
            "refresh_token": refresh
        })
        self.assertEqual(failed_refresh_res.status_code, 401)

    def test_forgot_reset_password(self):
        self.client.post("/auth/signup", json={
            "email": "user2@orbit.ai",
            "password": "originalpassword"
        })
        
        forgot_res = self.client.post("/auth/forgot-password", json={
            "email": "user2@orbit.ai"
        })
        self.assertEqual(forgot_res.status_code, 200)
        reset_token = forgot_res.json()["reset_token"]
        
        reset_res = self.client.post("/auth/reset-password", json={
            "token": reset_token,
            "new_password": "newpassword123"
        })
        self.assertEqual(reset_res.status_code, 200)
        
        login_res = self.client.post("/auth/login", json={
            "email": "user2@orbit.ai",
            "password": "newpassword123"
        })
        self.assertEqual(login_res.status_code, 200)

    def test_rbac_validation(self):
        self.client.post("/auth/signup", json={
            "email": "dev@orbit.ai",
            "password": "password123",
            "role": "developer"
        })
        self.client.post("/auth/signup", json={
            "email": "admin@orbit.ai",
            "password": "password123",
            "role": "admin"
        })
        
        dev_login = self.client.post("/auth/login", json={"email": "dev@orbit.ai", "password": "password123"})
        dev_token = dev_login.json()["access_token"]
        
        admin_login = self.client.post("/auth/login", json={"email": "admin@orbit.ai", "password": "password123"})
        admin_token = admin_login.json()["access_token"]
        
        res1 = self.client.get("/auth/admin-only", headers={"Authorization": f"Bearer {dev_token}"})
        self.assertEqual(res1.status_code, 403)
        
        res2 = self.client.get("/auth/dev-or-admin", headers={"Authorization": f"Bearer {dev_token}"})
        self.assertEqual(res2.status_code, 200)
        
        res3 = self.client.get("/auth/admin-only", headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(res3.status_code, 200)
