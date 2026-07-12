import unittest
from fastapi.testclient import TestClient
from api.app import create_app
from core.database import (
    get_db_session,
    init_db,
    PatientRecord,
    DoctorRecord,
    AppointmentRecord,
    BillingRecord,
    PharmacyItemRecord,
    PrescriptionRecord,
    LabTestRecord,
)
from datetime import datetime


class TestHospitalSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize test application and client
        cls.app = create_app()
        cls.client = TestClient(cls.app)
        init_db()

    def setUp(self):
        # Clear out hospital tables to ensure test isolation
        with get_db_session() as session:
            from core.database import User, RefreshTokenRecord

            session.query(LabTestRecord).delete()
            session.query(PrescriptionRecord).delete()
            session.query(PharmacyItemRecord).delete()
            session.query(BillingRecord).delete()
            session.query(AppointmentRecord).delete()
            session.query(DoctorRecord).delete()
            session.query(PatientRecord).delete()

            # Delete any existing test user to prevent token unique constraint conflicts
            u = session.query(User).filter(User.email == "nurse@orbit.ai").first()
            if u:
                session.query(RefreshTokenRecord).filter(
                    RefreshTokenRecord.user_id == u.id
                ).delete()
                session.delete(u)
            session.commit()

        # Signup a test doctor/user to use for authenticated endpoints
        signup_res = self.client.post(
            "/auth/signup", json={"email": "nurse@orbit.ai", "password": "password123"}
        )
        self.assertEqual(signup_res.status_code, 201)
        verify_token = signup_res.json()["verification_token"]
        self.client.get(f"/auth/verify-email?token={verify_token}")

        login_res = self.client.post(
            "/auth/login", json={"email": "nurse@orbit.ai", "password": "password123"}
        )
        self.assertEqual(login_res.status_code, 200)
        token = login_res.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {token}"}

    def test_patients_endpoints(self):
        # 1. Create Patient
        res = self.client.post(
            "/hospital/patients",
            json={
                "name": "Jane Doe",
                "email": "jane@doe.com",
                "phone": "555-1234",
                "date_of_birth": "1994-08-24",
                "gender": "Female",
                "medical_history": "Allergic to nuts",
            },
            headers=self.headers,
        )
        self.assertEqual(res.status_code, 200)
        res.json()["id"]

        # 2. Get Patients List
        get_res = self.client.get("/hospital/patients", headers=self.headers)
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(len(get_res.json()), 1)
        self.assertEqual(get_res.json()[0]["name"], "Jane Doe")

    def test_doctors_endpoints(self):
        # 1. Register Doctor
        res = self.client.post(
            "/hospital/doctors",
            json={
                "name": "Dr. Stephen Strange",
                "specialty": "Neurosurgeon",
                "email": "strange@orbit.ai",
                "phone": "555-9999",
                "is_available": True,
            },
            headers=self.headers,
        )
        self.assertEqual(res.status_code, 200)
        res.json()["id"]

        # 2. List Doctors
        get_res = self.client.get("/hospital/doctors", headers=self.headers)
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(len(get_res.json()), 1)
        self.assertEqual(get_res.json()[0]["specialty"], "Neurosurgeon")

    def test_appointments_endpoints(self):
        # Seed Patient & Doctor
        with get_db_session() as session:
            pat = PatientRecord(
                name="Tim Vance", date_of_birth="1980-01-01", gender="Male"
            )
            doc = DoctorRecord(name="Dr. Banner", specialty="Gamma Medicine")
            session.add_all([pat, doc])
            session.commit()
            pat_id = pat.id
            doc_id = doc.id

        # 1. Book Appointment
        res = self.client.post(
            "/hospital/appointments",
            json={
                "patient_id": pat_id,
                "doctor_id": doc_id,
                "appointment_date": "2026-07-15T10:00:00",
                "reason": "Gamma exposure checkup",
                "notes": "Monitor heart rate",
            },
            headers=self.headers,
        )
        self.assertEqual(res.status_code, 200)
        appt_id = res.json()["id"]

        # 2. Complete Appointment
        status_res = self.client.put(
            f"/hospital/appointments/{appt_id}/status?status=completed",
            headers=self.headers,
        )
        self.assertEqual(status_res.status_code, 200)

        # 3. Verify in DB
        with get_db_session() as session:
            appt = (
                session.query(AppointmentRecord)
                .filter(AppointmentRecord.id == appt_id)
                .first()
            )
            self.assertEqual(appt.status, "completed")

    def test_billing_endpoints(self):
        # Seed Patient
        with get_db_session() as session:
            pat = PatientRecord(
                name="Arthur Dent", date_of_birth="1979-05-25", gender="Male"
            )
            session.add(pat)
            session.commit()
            pat_id = pat.id

        # 1. Create Invoice
        res = self.client.post(
            "/hospital/billing",
            json={"patient_id": pat_id, "amount": 250.50},
            headers=self.headers,
        )
        self.assertEqual(res.status_code, 200)
        bill_id = res.json()["id"]

        # 2. Collect Fee / Pay Invoice
        pay_res = self.client.put(
            f"/hospital/billing/{bill_id}/pay",
            json={"payment_method": "Insurance Coverage"},
            headers=self.headers,
        )
        self.assertEqual(pay_res.status_code, 200)

        # 3. Verify Payment
        with get_db_session() as session:
            bill = (
                session.query(BillingRecord).filter(BillingRecord.id == bill_id).first()
            )
            self.assertEqual(bill.status, "paid")
            self.assertEqual(bill.payment_method, "Insurance Coverage")

    def test_pharmacy_dispensary_flow(self):
        # Seed Patient, Doctor, and Stock
        with get_db_session() as session:
            pat = PatientRecord(
                name="Clark Kent", date_of_birth="1938-04-18", gender="Male"
            )
            doc = DoctorRecord(name="Dr. Jor-El", specialty="Kryptonian biology")
            item = PharmacyItemRecord(
                name="Kryptonite Inhibitor",
                dosage="250mg",
                stock_quantity=10,
                unit_price=99.00,
            )
            session.add_all([pat, doc, item])
            session.commit()
            pat_id = pat.id
            doc_id = doc.id
            item_id = item.id

        # 1. Write Prescription
        res = self.client.post(
            "/hospital/pharmacy/prescriptions",
            json={
                "patient_id": pat_id,
                "doctor_id": doc_id,
                "medication_name": "Kryptonite Inhibitor",
                "dosage_instruction": "Take one capsule when feeling weak",
            },
            headers=self.headers,
        )
        self.assertEqual(res.status_code, 200)
        pres_id = res.json()["id"]

        # 2. Dispense Medication (should decrement inventory count from 10 to 9)
        disp_res = self.client.put(
            f"/hospital/pharmacy/prescriptions/{pres_id}/dispense", headers=self.headers
        )
        self.assertEqual(disp_res.status_code, 200)

        # 3. Assert counts
        with get_db_session() as session:
            db_item = (
                session.query(PharmacyItemRecord)
                .filter(PharmacyItemRecord.id == item_id)
                .first()
            )
            self.assertEqual(db_item.stock_quantity, 9)

            db_pres = (
                session.query(PrescriptionRecord)
                .filter(PrescriptionRecord.id == pres_id)
                .first()
            )
            self.assertEqual(db_pres.status, "dispensed")

    def test_laboratory_endpoints(self):
        # Seed Patient
        with get_db_session() as session:
            pat = PatientRecord(
                name="Bruce Wayne", date_of_birth="1939-05-01", gender="Male"
            )
            session.add(pat)
            session.commit()
            pat_id = pat.id

        # 1. Request Lab test
        res = self.client.post(
            "/hospital/lab/tests",
            json={"patient_id": pat_id, "test_name": "Toxin analysis"},
            headers=self.headers,
        )
        self.assertEqual(res.status_code, 200)
        test_id = res.json()["id"]

        # 2. Complete lab test results
        comp_res = self.client.put(
            f"/hospital/lab/tests/{test_id}/complete",
            json={
                "result": "Joker toxin antibodies detected",
                "technician_notes": "Handle with caution",
            },
            headers=self.headers,
        )
        self.assertEqual(comp_res.status_code, 200)

        # 3. Verify lab result in database
        with get_db_session() as session:
            db_test = (
                session.query(LabTestRecord).filter(LabTestRecord.id == test_id).first()
            )
            self.assertEqual(db_test.status, "completed")
            self.assertEqual(db_test.result, "Joker toxin antibodies detected")
            self.assertIsNotNone(db_test.completed_at)

    def test_hospital_dashboard_stats(self):
        # Seed one record in each model to make stats non-zero
        with get_db_session() as session:
            p = PatientRecord(
                name="Test Patient", date_of_birth="2000-01-01", gender="Other"
            )
            d = DoctorRecord(name="Test Doctor", specialty="General Practice")
            session.add_all([p, d])
            session.commit()

            appt = AppointmentRecord(
                patient_id=p.id,
                doctor_id=d.id,
                appointment_date=datetime.now(),
                reason="Checkup",
            )
            bill = BillingRecord(patient_id=p.id, amount=100.0, status="unpaid")
            item = PharmacyItemRecord(
                name="Paracetamol", dosage="500mg", stock_quantity=100, unit_price=0.20
            )
            pres = PrescriptionRecord(
                patient_id=p.id,
                doctor_id=d.id,
                medication_name="Paracetamol",
                dosage_instruction="1 tab as needed",
            )
            lab = LabTestRecord(patient_id=p.id, test_name="COVID Swab")

            session.add_all([appt, bill, item, pres, lab])
            session.commit()

        # Fetch stats
        res = self.client.get("/hospital/stats", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["patients"], 1)
        self.assertEqual(data["doctors"], 1)
        self.assertEqual(data["appointments"]["total"], 1)
        self.assertEqual(data["billing"]["unpaid"], 100.0)
        self.assertEqual(data["pharmacy"]["total_drugs"], 1)
        self.assertEqual(data["laboratory"]["pending"], 1)
