from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from core.database import (
    get_db_session, PatientRecord, DoctorRecord, AppointmentRecord, 
    BillingRecord, PharmacyItemRecord, PrescriptionRecord, LabTestRecord
)
from core.auth.dependencies import get_current_user

router = APIRouter(prefix="/hospital", tags=["Hospital Management System"])

# Pydantic Schemas
class PatientCreateSchema(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: str
    gender: str
    medical_history: Optional[str] = None

class DoctorCreateSchema(BaseModel):
    name: str
    specialty: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_available: bool = True

class AppointmentCreateSchema(BaseModel):
    patient_id: str
    doctor_id: str
    appointment_date: str  # ISO format string
    reason: str
    notes: Optional[str] = None

class BillingCreateSchema(BaseModel):
    patient_id: str
    appointment_id: Optional[str] = None
    amount: float

class PayBillSchema(BaseModel):
    payment_method: str

class PharmacyItemCreateSchema(BaseModel):
    name: str
    dosage: str
    stock_quantity: int
    unit_price: float

class PrescriptionCreateSchema(BaseModel):
    patient_id: str
    doctor_id: str
    medication_name: str
    dosage_instruction: str

class LabTestCreateSchema(BaseModel):
    patient_id: str
    test_name: str

class LabResultSchema(BaseModel):
    result: str
    technician_notes: Optional[str] = None


# ==========================================
# PATIENTS ENDPOINTS
# ==========================================
@router.get("/patients")
def get_patients(current_user: dict = Depends(get_current_user)):
    with get_db_session() as session:
        patients = session.query(PatientRecord).all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "email": p.email,
                "phone": p.phone,
                "date_of_birth": p.date_of_birth,
                "gender": p.gender,
                "medical_history": p.medical_history,
                "created_at": p.created_at
            }
            for p in patients
        ]

@router.post("/patients")
def create_patient(payload: PatientCreateSchema, current_user: dict = Depends(get_current_user)):
    with get_db_session() as session:
        patient = PatientRecord(
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            date_of_birth=payload.date_of_birth,
            gender=payload.gender,
            medical_history=payload.medical_history
        )
        session.add(patient)
        session.commit()
        return {"message": "Patient created successfully.", "id": patient.id}


# ==========================================
# DOCTORS ENDPOINTS
# ==========================================
@router.get("/doctors")
def get_doctors(current_user: dict = Depends(get_current_user)):
    with get_db_session() as session:
        doctors = session.query(DoctorRecord).all()
        return [
            {
                "id": d.id,
                "name": d.name,
                "specialty": d.specialty,
                "email": d.email,
                "phone": d.phone,
                "is_available": d.is_available,
                "created_at": d.created_at
            }
            for d in doctors
        ]

@router.post("/doctors")
def create_doctor(payload: DoctorCreateSchema, current_user: dict = Depends(get_current_user)):
    with get_db_session() as session:
        doctor = DoctorRecord(
            name=payload.name,
            specialty=payload.specialty,
            email=payload.email,
            phone=payload.phone,
            is_available=payload.is_available
        )
        session.add(doctor)
        session.commit()
        return {"message": "Doctor registered successfully.", "id": doctor.id}


# ==========================================
# APPOINTMENTS ENDPOINTS
# ==========================================
@router.get("/appointments")
def get_appointments(current_user: dict = Depends(get_current_user)):
    with get_db_session() as session:
        appointments = session.query(AppointmentRecord).all()
        result = []
        for appt in appointments:
            patient = session.query(PatientRecord).filter(PatientRecord.id == appt.patient_id).first()
            doctor = session.query(DoctorRecord).filter(DoctorRecord.id == appt.doctor_id).first()
            result.append({
                "id": appt.id,
                "patient_id": appt.patient_id,
                "patient_name": patient.name if patient else "Unknown Patient",
                "doctor_id": appt.doctor_id,
                "doctor_name": doctor.name if doctor else "Unknown Doctor",
                "appointment_date": appt.appointment_date,
                "reason": appt.reason,
                "status": appt.status,
                "notes": appt.notes,
                "created_at": appt.created_at
            })
        return result

@router.post("/appointments")
def create_appointment(payload: AppointmentCreateSchema, current_user: dict = Depends(get_current_user)):
    with get_db_session() as session:
        # Validate patient and doctor exist
        p = session.query(PatientRecord).filter(PatientRecord.id == payload.patient_id).first()
        d = session.query(DoctorRecord).filter(DoctorRecord.id == payload.doctor_id).first()
        if not p or not d:
            raise HTTPException(status_code=400, detail="Invalid Patient or Doctor ID.")
            
        try:
            appt_date = datetime.fromisoformat(payload.appointment_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format.")
            
        appt = AppointmentRecord(
            patient_id=payload.patient_id,
            doctor_id=payload.doctor_id,
            appointment_date=appt_date,
            reason=payload.reason,
            notes=payload.notes,
            status="scheduled"
        )
        session.add(appt)
        session.commit()
        return {"message": "Appointment scheduled successfully.", "id": appt.id}

@router.put("/appointments/{appointment_id}/status")
def update_appointment_status(appointment_id: str, status: str, current_user: dict = Depends(get_current_user)):
    if status not in ("scheduled", "completed", "cancelled"):
        raise HTTPException(status_code=400, detail="Invalid status option.")
        
    with get_db_session() as session:
        appt = session.query(AppointmentRecord).filter(AppointmentRecord.id == appointment_id).first()
        if not appt:
            raise HTTPException(status_code=404, detail="Appointment not found.")
            
        appt.status = status
        session.commit()
        return {"message": f"Appointment status updated to '{status}'."}


# ==========================================
# BILLING ENDPOINTS
# ==========================================
@router.get("/billing")
def get_billing(current_user: dict = Depends(get_current_user)):
    with get_db_session() as session:
        bills = session.query(BillingRecord).all()
        result = []
        for b in bills:
            patient = session.query(PatientRecord).filter(PatientRecord.id == b.patient_id).first()
            result.append({
                "id": b.id,
                "patient_id": b.patient_id,
                "patient_name": patient.name if patient else "Unknown Patient",
                "appointment_id": b.appointment_id,
                "amount": b.amount,
                "status": b.status,
                "payment_method": b.payment_method,
                "billing_date": b.billing_date,
                "created_at": b.created_at
            })
        return result

@router.post("/billing")
def create_billing(payload: BillingCreateSchema, current_user: dict = Depends(get_current_user)):
    with get_db_session() as session:
        # Validate patient
        p = session.query(PatientRecord).filter(PatientRecord.id == payload.patient_id).first()
        if not p:
            raise HTTPException(status_code=400, detail="Invalid Patient ID.")
            
        bill = BillingRecord(
            patient_id=payload.patient_id,
            appointment_id=payload.appointment_id,
            amount=payload.amount,
            status="unpaid"
        )
        session.add(bill)
        session.commit()
        return {"message": "Billing invoice generated successfully.", "id": bill.id}

@router.put("/billing/{billing_id}/pay")
def pay_billing(billing_id: str, payload: PayBillSchema, current_user: dict = Depends(get_current_user)):
    with get_db_session() as session:
        bill = session.query(BillingRecord).filter(BillingRecord.id == billing_id).first()
        if not bill:
            raise HTTPException(status_code=404, detail="Invoice not found.")
            
        bill.status = "paid"
        bill.payment_method = payload.payment_method
        session.commit()
        return {"message": "Invoice paid successfully."}


# ==========================================
# PHARMACY ENDPOINTS
# ==========================================
@router.get("/pharmacy/items")
def get_pharmacy_items(current_user: dict = Depends(get_current_user)):
    with get_db_session() as session:
        items = session.query(PharmacyItemRecord).all()
        return [
            {
                "id": i.id,
                "name": i.name,
                "dosage": i.dosage,
                "stock_quantity": i.stock_quantity,
                "unit_price": i.unit_price,
                "created_at": i.created_at
            }
            for i in items
        ]

@router.post("/pharmacy/items")
def create_pharmacy_item(payload: PharmacyItemCreateSchema, current_user: dict = Depends(get_current_user)):
    with get_db_session() as session:
        # Check duplicate name
        existing = session.query(PharmacyItemRecord).filter(PharmacyItemRecord.name == payload.name).first()
        if existing:
            existing.stock_quantity += payload.stock_quantity
            session.commit()
            return {"message": "Pharmacy item stock updated.", "id": existing.id}
            
        item = PharmacyItemRecord(
            name=payload.name,
            dosage=payload.dosage,
            stock_quantity=payload.stock_quantity,
            unit_price=payload.unit_price
        )
        session.add(item)
        session.commit()
        return {"message": "Pharmacy item registered successfully.", "id": item.id}

@router.get("/pharmacy/prescriptions")
def get_prescriptions(current_user: dict = Depends(get_current_user)):
    with get_db_session() as session:
        prescriptions = session.query(PrescriptionRecord).all()
        result = []
        for pr in prescriptions:
            patient = session.query(PatientRecord).filter(PatientRecord.id == pr.patient_id).first()
            doctor = session.query(DoctorRecord).filter(DoctorRecord.id == pr.doctor_id).first()
            result.append({
                "id": pr.id,
                "patient_id": pr.patient_id,
                "patient_name": patient.name if patient else "Unknown Patient",
                "doctor_id": pr.doctor_id,
                "doctor_name": doctor.name if doctor else "Unknown Doctor",
                "medication_name": pr.medication_name,
                "dosage_instruction": pr.dosage_instruction,
                "status": pr.status,
                "created_at": pr.created_at
            })
        return result

@router.post("/pharmacy/prescriptions")
def create_prescription(payload: PrescriptionCreateSchema, current_user: dict = Depends(get_current_user)):
    with get_db_session() as session:
        p = session.query(PatientRecord).filter(PatientRecord.id == payload.patient_id).first()
        d = session.query(DoctorRecord).filter(DoctorRecord.id == payload.doctor_id).first()
        if not p or not d:
            raise HTTPException(status_code=400, detail="Invalid Patient or Doctor ID.")
            
        pr = PrescriptionRecord(
            patient_id=payload.patient_id,
            doctor_id=payload.doctor_id,
            medication_name=payload.medication_name,
            dosage_instruction=payload.dosage_instruction,
            status="prescribed"
        )
        session.add(pr)
        session.commit()
        return {"message": "Prescription recorded successfully.", "id": pr.id}

@router.put("/pharmacy/prescriptions/{prescription_id}/dispense")
def dispense_prescription(prescription_id: str, current_user: dict = Depends(get_current_user)):
    with get_db_session() as session:
        pr = session.query(PrescriptionRecord).filter(PrescriptionRecord.id == prescription_id).first()
        if not pr:
            raise HTTPException(status_code=404, detail="Prescription not found.")
        if pr.status == "dispensed":
            raise HTTPException(status_code=400, detail="Prescription already dispensed.")
            
        # Deduct stock if item exists in inventory
        item = session.query(PharmacyItemRecord).filter(PharmacyItemRecord.name == pr.medication_name).first()
        if item:
            if item.stock_quantity > 0:
                item.stock_quantity -= 1
            else:
                raise HTTPException(status_code=400, detail="Out of stock for prescribed medication.")
                
        pr.status = "dispensed"
        session.commit()
        return {"message": "Prescription medication dispensed."}


# ==========================================
# LABORATORY ENDPOINTS
# ==========================================
@router.get("/lab/tests")
def get_lab_tests(current_user: dict = Depends(get_current_user)):
    with get_db_session() as session:
        tests = session.query(LabTestRecord).all()
        result = []
        for t in tests:
            patient = session.query(PatientRecord).filter(PatientRecord.id == t.patient_id).first()
            result.append({
                "id": t.id,
                "patient_id": t.patient_id,
                "patient_name": patient.name if patient else "Unknown Patient",
                "test_name": t.test_name,
                "result": t.result,
                "status": t.status,
                "technician_notes": t.technician_notes,
                "created_at": t.created_at,
                "completed_at": t.completed_at
            })
        return result

@router.post("/lab/tests")
def create_lab_test(payload: LabTestCreateSchema, current_user: dict = Depends(get_current_user)):
    with get_db_session() as session:
        p = session.query(PatientRecord).filter(PatientRecord.id == payload.patient_id).first()
        if not p:
            raise HTTPException(status_code=400, detail="Invalid Patient ID.")
            
        test = LabTestRecord(
            patient_id=payload.patient_id,
            test_name=payload.test_name,
            status="pending"
        )
        session.add(test)
        session.commit()
        return {"message": "Laboratory test requested.", "id": test.id}

@router.put("/lab/tests/{test_id}/complete")
def complete_lab_test(test_id: str, payload: LabResultSchema, current_user: dict = Depends(get_current_user)):
    with get_db_session() as session:
        test = session.query(LabTestRecord).filter(LabTestRecord.id == test_id).first()
        if not test:
            raise HTTPException(status_code=404, detail="Lab test not found.")
            
        test.result = payload.result
        test.technician_notes = payload.technician_notes
        test.status = "completed"
        test.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        session.commit()
        return {"message": "Laboratory test results recorded."}


# ==========================================
# DASHBOARD STATS & REPORTS
# ==========================================
@router.get("/stats")
def get_hospital_stats(current_user: dict = Depends(get_current_user)):
    with get_db_session() as session:
        total_patients = session.query(PatientRecord).count()
        total_doctors = session.query(DoctorRecord).count()
        total_appointments = session.query(AppointmentRecord).count()
        scheduled_appts = session.query(AppointmentRecord).filter(AppointmentRecord.status == "scheduled").count()
        
        # Billing metrics
        billing_records = session.query(BillingRecord).all()
        total_billed = sum(b.amount for b in billing_records)
        unpaid_billing = sum(b.amount for b in billing_records if b.status == "unpaid")
        paid_billing = sum(b.amount for b in billing_records if b.status == "paid")
        
        # Pharmacy metrics
        total_drugs = session.query(PharmacyItemRecord).count()
        total_prescriptions = session.query(PrescriptionRecord).count()
        pending_prescriptions = session.query(PrescriptionRecord).filter(PrescriptionRecord.status == "prescribed").count()
        
        # Lab metrics
        total_tests = session.query(LabTestRecord).count()
        pending_tests = session.query(LabTestRecord).filter(LabTestRecord.status == "pending").count()
        
        return {
            "patients": total_patients,
            "doctors": total_doctors,
            "appointments": {
                "total": total_appointments,
                "scheduled": scheduled_appts
            },
            "billing": {
                "total_billed": total_billed,
                "unpaid": unpaid_billing,
                "paid": paid_billing
            },
            "pharmacy": {
                "total_drugs": total_drugs,
                "total_prescriptions": total_prescriptions,
                "pending": pending_prescriptions
            },
            "laboratory": {
                "total_tests": total_tests,
                "pending": pending_tests
            }
        }
