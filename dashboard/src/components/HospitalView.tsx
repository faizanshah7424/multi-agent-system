'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useDashboard } from '../context/DashboardContext';
import { 
  api, HospitalPatient, HospitalDoctor, HospitalAppointment, 
  HospitalBilling, HospitalPharmacyItem, HospitalPrescription, HospitalLabTest, HospitalStats 
} from '../lib/api';
import { 
  Activity, Users, UserCheck, Calendar, CreditCard,
  FlaskConical, ClipboardList, PlusCircle, DollarSign, Pill, 
  CheckCircle, XCircle, FileText, Loader2
} from 'lucide-react';

// MOCK DATA for local offline testing
const mockStats: HospitalStats = {
  patients: 12,
  doctors: 5,
  appointments: { total: 18, scheduled: 6 },
  billing: { total_billed: 4500, unpaid: 1200, paid: 3300 },
  pharmacy: { total_drugs: 8, total_prescriptions: 14, pending: 3 },
  laboratory: { total_tests: 9, pending: 2 }
};

const mockPatients: HospitalPatient[] = [
  { id: 'pat_1', name: 'Alice Smith', email: 'alice@gmail.com', phone: '555-0144', date_of_birth: '1990-05-15', gender: 'Female', medical_history: 'No known allergies. History of mild asthma.' },
  { id: 'pat_2', name: 'Bob Jones', email: 'bob@yahoo.com', phone: '555-0177', date_of_birth: '1982-11-20', gender: 'Male', medical_history: 'Hypertension. Takes lisinopril daily.' },
  { id: 'pat_3', name: 'Charlie Miller', email: 'charlie@outlook.com', phone: '555-0188', date_of_birth: '1995-02-03', gender: 'Male', medical_history: 'Allergies to penicillin.' }
];

const mockDoctors: HospitalDoctor[] = [
  { id: 'doc_1', name: 'Dr. Gregory House', specialty: 'Diagnostic Medicine', email: 'house@orbit.ai', phone: '555-0911', is_available: true },
  { id: 'doc_2', name: 'Dr. Allison Cameron', specialty: 'Immunology', email: 'cameron@orbit.ai', phone: '555-0922', is_available: true },
  { id: 'doc_3', name: 'Dr. Eric Foreman', specialty: 'Neurology', email: 'foreman@orbit.ai', phone: '555-0933', is_available: false }
];

const mockAppointments: HospitalAppointment[] = [
  { id: 'appt_1', patient_id: 'pat_1', patient_name: 'Alice Smith', doctor_id: 'doc_1', doctor_name: 'Dr. Gregory House', appointment_date: '2026-07-11T10:00:00Z', reason: 'Unexplained persistent joint pain.', status: 'scheduled', notes: 'Needs comprehensive lab blood panels.' },
  { id: 'appt_2', patient_id: 'pat_2', patient_name: 'Bob Jones', doctor_id: 'doc_2', doctor_name: 'Dr. Allison Cameron', appointment_date: '2026-07-10T14:00:00Z', reason: 'Routine immunology checkup.', status: 'completed', notes: 'Vitals stable. Continue current prescription.' }
];

const mockBills: HospitalBilling[] = [
  { id: 'bill_1', patient_id: 'pat_1', patient_name: 'Alice Smith', appointment_id: 'appt_1', amount: 350.00, status: 'unpaid', payment_method: null, billing_date: '2026-07-10T18:00:00Z' },
  { id: 'bill_2', patient_id: 'pat_2', patient_name: 'Bob Jones', appointment_id: 'appt_2', amount: 150.00, status: 'paid', payment_method: 'Credit Card', billing_date: '2026-07-10T14:30:00Z' }
];

const mockPharmacyItems: HospitalPharmacyItem[] = [
  { id: 'phar_1', name: 'Lisinopril', dosage: '10mg', stock_quantity: 150, unit_price: 1.20 },
  { id: 'phar_2', name: 'Amoxicillin', dosage: '500mg', stock_quantity: 80, unit_price: 2.50 },
  { id: 'phar_3', name: 'Albuterol Inhaler', dosage: '90mcg', stock_quantity: 12, unit_price: 25.00 }
];

const mockPrescriptions: HospitalPrescription[] = [
  { id: 'pres_1', patient_id: 'pat_2', patient_name: 'Bob Jones', doctor_id: 'doc_2', doctor_name: 'Dr. Allison Cameron', medication_name: 'Lisinopril', dosage_instruction: 'Take 1 tablet daily in the morning.', status: 'prescribed', created_at: '2026-07-10T14:15:00Z' },
  { id: 'pres_2', patient_id: 'pat_1', patient_name: 'Alice Smith', doctor_id: 'doc_1', doctor_name: 'Dr. Gregory House', medication_name: 'Albuterol Inhaler', dosage_instruction: 'Use 2 puffs every 4 hours as needed for shortness of breath.', status: 'dispensed', created_at: '2026-07-10T10:30:00Z' }
];

const mockLabTests: HospitalLabTest[] = [
  { id: 'lab_1', patient_id: 'pat_1', patient_name: 'Alice Smith', test_name: 'Complete Blood Count (CBC)', result: null, status: 'pending', technician_notes: null, created_at: '2026-07-10T11:00:00Z', completed_at: null },
  { id: 'lab_2', patient_id: 'pat_2', patient_name: 'Bob Jones', test_name: 'Basic Metabolic Panel (BMP)', result: 'Sodium: 140 mEq/L, Potassium: 4.1 mEq/L, Glucose: 92 mg/dL. All parameters within reference margins.', status: 'completed', technician_notes: 'Specimen processed successfully.', created_at: '2026-07-09T09:00:00Z', completed_at: '2026-07-09T11:30:00Z' }
];

type HospitalTabType = 'dashboard' | 'patients' | 'doctors' | 'appointments' | 'billing' | 'pharmacy' | 'laboratory' | 'reports';

export const HospitalView: React.FC = () => {
  const { useMockData } = useDashboard();
  
  const [activeTab, setActiveTab] = useState<HospitalTabType>('dashboard');
  
  // Data States
  const [stats, setStats] = useState<HospitalStats | null>(null);
  const [patients, setPatients] = useState<HospitalPatient[]>([]);
  const [doctors, setDoctors] = useState<HospitalDoctor[]>([]);
  const [appointments, setAppointments] = useState<HospitalAppointment[]>([]);
  const [billing, setBilling] = useState<HospitalBilling[]>([]);
  const [pharmacyItems, setPharmacyItems] = useState<HospitalPharmacyItem[]>([]);
  const [prescriptions, setPrescriptions] = useState<HospitalPrescription[]>([]);
  const [labTests, setLabTests] = useState<HospitalLabTest[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Form Submission States
  const [submitting, setSubmitting] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);

  // Form Inputs: Patient
  const [patName, setPatName] = useState('');
  const [patEmail, setPatEmail] = useState('');
  const [patPhone, setPatPhone] = useState('');
  const [patDOB, setPatDOB] = useState('1990-01-01');
  const [patGender, setPatGender] = useState('Female');
  const [patHistory, setPatHistory] = useState('');

  // Form Inputs: Doctor
  const [docName, setDocName] = useState('');
  const [docSpecialty, setDocSpecialty] = useState('');
  const [docEmail, setDocEmail] = useState('');
  const [docPhone, setDocPhone] = useState('');

  // Form Inputs: Appointment
  const [apptPatientId, setApptPatientId] = useState('');
  const [apptDoctorId, setApptDoctorId] = useState('');
  const [apptDate, setApptDate] = useState('');
  const [apptReason, setApptReason] = useState('');
  const [apptNotes, setApptNotes] = useState('');

  // Form Inputs: Billing
  const [billPatientId, setBillPatientId] = useState('');
  const [billAmount, setBillAmount] = useState('');
  const [billApptId, setBillApptId] = useState('');

  // Form Inputs: Pharmacy Item
  const [pharName, setPharName] = useState('');
  const [pharDosage, setPharDosage] = useState('');
  const [pharStock, setPharStock] = useState('100');
  const [pharPrice, setPharPrice] = useState('1.50');

  // Form Inputs: Prescription
  const [presPatientId, setPresPatientId] = useState('');
  const [presDoctorId, setPresDoctorId] = useState('');
  const [presMedicationName, setPresMedicationName] = useState('');
  const [presInstruction, setPresInstruction] = useState('');

  // Form Inputs: Lab Request
  const [labPatientId, setLabPatientId] = useState('');
  const [labTestName, setLabTestName] = useState('');

  // Form Inputs: Lab Result Completion
  const [activeLabId, setActiveLabId] = useState<string | null>(null);
  const [labResultText, setLabResultText] = useState('');
  const [labResultNotes, setLabResultNotes] = useState('');

  // Form Inputs: Billing payment
  const [activeBillId, setActiveBillId] = useState<string | null>(null);
  const [paymentMethod, setPaymentMethod] = useState('Cash');

  const fetchHospitalData = useCallback(async () => {
    setLoading(true);
    setMessage(null);
    try {
      if (useMockData) {
        setStats(mockStats);
        setPatients(mockPatients);
        setDoctors(mockDoctors);
        setAppointments(mockAppointments);
        setBilling(mockBills);
        setPharmacyItems(mockPharmacyItems);
        setPrescriptions(mockPrescriptions);
        setLabTests(mockLabTests);
      } else {
        const [statsData, patientsData, doctorsData, apptsData, billsData, pharData, presData, labsData] = await Promise.all([
          api.getHospitalStats(),
          api.getHospitalPatients(),
          api.getHospitalDoctors(),
          api.getHospitalAppointments(),
          api.getHospitalBilling(),
          api.getHospitalPharmacyItems(),
          api.getHospitalPrescriptions(),
          api.getHospitalLabTests()
        ]);
        setStats(statsData);
        setPatients(patientsData);
        setDoctors(doctorsData);
        setAppointments(apptsData);
        setBilling(billsData);
        setPharmacyItems(pharData);
        setPrescriptions(presData);
        setLabTests(labsData);
      }
    } catch (err) {
      console.error(err);
      const msg = err instanceof Error ? err.message : 'Failed to fetch hospital records.';
      setMessage({ type: 'error', text: msg });
    } finally {
      setLoading(false);
    }
  }, [useMockData]);

  useEffect(() => {
    fetchHospitalData();
  }, [fetchHospitalData]);

  const resetAllForms = () => {
    setPatName(''); setPatEmail(''); setPatPhone(''); setPatHistory('');
    setDocName(''); setDocSpecialty(''); setDocEmail(''); setDocPhone('');
    setApptPatientId(''); setApptDoctorId(''); setApptDate(''); setApptReason(''); setApptNotes('');
    setBillPatientId(''); setBillAmount(''); setBillApptId('');
    setPharName(''); setPharDosage(''); setPharStock('100'); setPharPrice('1.50');
    setPresPatientId(''); setPresDoctorId(''); setPresMedicationName(''); setPresInstruction('');
    setLabPatientId(''); setLabTestName('');
    setActiveLabId(null); setLabResultText(''); setLabResultNotes('');
    setActiveBillId(null);
    setShowAddForm(false);
  };

  // Actions
  const handleAddPatient = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (useMockData) {
        const newPat: HospitalPatient = {
          id: 'pat_' + Math.random().toString(36).substr(2, 4),
          name: patName,
          email: patEmail || null,
          phone: patPhone || null,
          date_of_birth: patDOB,
          gender: patGender,
          medical_history: patHistory || null
        };
        setPatients([...patients, newPat]);
        if (stats) setStats({ ...stats, patients: stats.patients + 1 });
        setMessage({ type: 'success', text: `Patient ${patName} registered successfully.` });
      } else {
        await api.createHospitalPatient({
          name: patName,
          email: patEmail || null,
          phone: patPhone || null,
          date_of_birth: patDOB,
          gender: patGender,
          medical_history: patHistory || null
        });
        await fetchHospitalData();
        setMessage({ type: 'success', text: `Patient ${patName} registered on database.` });
      }
      resetAllForms();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error creating patient.';
      setMessage({ type: 'error', text: msg });
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddDoctor = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (useMockData) {
        const newDoc: HospitalDoctor = {
          id: 'doc_' + Math.random().toString(36).substr(2, 4),
          name: docName,
          specialty: docSpecialty,
          email: docEmail || null,
          phone: docPhone || null,
          is_available: true
        };
        setDoctors([...doctors, newDoc]);
        if (stats) setStats({ ...stats, doctors: stats.doctors + 1 });
        setMessage({ type: 'success', text: `Doctor ${docName} registered successfully.` });
      } else {
        await api.createHospitalDoctor({
          name: docName,
          specialty: docSpecialty,
          email: docEmail || null,
          phone: docPhone || null,
          is_available: true
        });
        await fetchHospitalData();
        setMessage({ type: 'success', text: `Doctor ${docName} registered on database.` });
      }
      resetAllForms();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error registering doctor.';
      setMessage({ type: 'error', text: msg });
    } finally {
      setSubmitting(false);
    }
  };

  const handleBookAppointment = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const formattedDate = new Date(apptDate).toISOString();
      if (useMockData) {
        const pName = patients.find(p => p.id === apptPatientId)?.name || 'Unknown Patient';
        const dName = doctors.find(d => d.id === apptDoctorId)?.name || 'Unknown Doctor';
        const newAppt: HospitalAppointment = {
          id: 'appt_' + Math.random().toString(36).substr(2, 4),
          patient_id: apptPatientId,
          patient_name: pName,
          doctor_id: apptDoctorId,
          doctor_name: dName,
          appointment_date: formattedDate,
          reason: apptReason,
          status: 'scheduled',
          notes: apptNotes || null
        };
        setAppointments([...appointments, newAppt]);
        if (stats) setStats({ 
          ...stats, 
          appointments: { total: stats.appointments.total + 1, scheduled: stats.appointments.scheduled + 1 } 
        });
        setMessage({ type: 'success', text: 'Appointment booked successfully.' });
      } else {
        await api.createHospitalAppointment({
          patient_id: apptPatientId,
          doctor_id: apptDoctorId,
          appointment_date: formattedDate,
          reason: apptReason,
          notes: apptNotes || undefined
        });
        await fetchHospitalData();
        setMessage({ type: 'success', text: 'Appointment scheduled on database.' });
      }
      resetAllForms();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error booking appointment.';
      setMessage({ type: 'error', text: msg });
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdateApptStatus = async (apptId: string, newStatus: string) => {
    try {
      if (useMockData) {
        setAppointments(prev => prev.map(a => a.id === apptId ? { ...a, status: newStatus } : a));
        if (stats && newStatus !== 'scheduled') {
          setStats({
            ...stats,
            appointments: { ...stats.appointments, scheduled: Math.max(0, stats.appointments.scheduled - 1) }
          });
        }
        setMessage({ type: 'success', text: `Appointment marked as ${newStatus}.` });
      } else {
        await api.updateHospitalAppointmentStatus(apptId, newStatus);
        await fetchHospitalData();
        setMessage({ type: 'success', text: `Appointment updated to ${newStatus}.` });
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error updating status.';
      setMessage({ type: 'error', text: msg });
    }
  };

  const handleAddBill = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const amt = parseFloat(billAmount);
      if (isNaN(amt)) throw new Error('Invalid amount.');
      
      if (useMockData) {
        const pName = patients.find(p => p.id === billPatientId)?.name || 'Unknown Patient';
        const newBill: HospitalBilling = {
          id: 'bill_' + Math.random().toString(36).substr(2, 4),
          patient_id: billPatientId,
          patient_name: pName,
          appointment_id: billApptId || null,
          amount: amt,
          status: 'unpaid',
          payment_method: null,
          billing_date: new Date().toISOString()
        };
        setBilling([...billing, newBill]);
        if (stats) setStats({
          ...stats,
          billing: {
            ...stats.billing,
            total_billed: stats.billing.total_billed + amt,
            unpaid: stats.billing.unpaid + amt
          }
        });
        setMessage({ type: 'success', text: 'Invoice generated successfully.' });
      } else {
        await api.createHospitalBilling({
          patient_id: billPatientId,
          appointment_id: billApptId || undefined,
          amount: amt
        });
        await fetchHospitalData();
        setMessage({ type: 'success', text: 'Invoice registered on database.' });
      }
      resetAllForms();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error creating invoice.';
      setMessage({ type: 'error', text: msg });
    } finally {
      setSubmitting(false);
    }
  };

  const handlePayBill = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeBillId) return;
    try {
      if (useMockData) {
        const b = billing.find(bill => bill.id === activeBillId);
        if (b) {
          setBilling(prev => prev.map(bill => bill.id === activeBillId ? { ...bill, status: 'paid', payment_method: paymentMethod } : bill));
          if (stats) setStats({
            ...stats,
            billing: {
              ...stats.billing,
              unpaid: Math.max(0, stats.billing.unpaid - b.amount),
              paid: stats.billing.paid + b.amount
            }
          });
        }
        setMessage({ type: 'success', text: 'Payment completed successfully.' });
      } else {
        await api.payHospitalBill(activeBillId, { payment_method: paymentMethod });
        await fetchHospitalData();
        setMessage({ type: 'success', text: 'Payment recorded on database.' });
      }
      resetAllForms();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error making payment.';
      setMessage({ type: 'error', text: msg });
    }
  };

  const handleAddPharmacyItem = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const qty = parseInt(pharStock);
      const prc = parseFloat(pharPrice);
      if (isNaN(qty) || isNaN(prc)) throw new Error('Invalid input numbers.');
      
      if (useMockData) {
        const existing = pharmacyItems.find(i => i.name.toLowerCase() === pharName.toLowerCase());
        if (existing) {
          setPharmacyItems(prev => prev.map(i => i.id === existing.id ? { ...i, stock_quantity: i.stock_quantity + qty } : i));
        } else {
          const newItem: HospitalPharmacyItem = {
            id: 'phar_' + Math.random().toString(36).substr(2, 4),
            name: pharName,
            dosage: pharDosage,
            stock_quantity: qty,
            unit_price: prc
          };
          setPharmacyItems([...pharmacyItems, newItem]);
          if (stats) setStats({ ...stats, pharmacy: { ...stats.pharmacy, total_drugs: stats.pharmacy.total_drugs + 1 } });
        }
        setMessage({ type: 'success', text: 'Pharmacy stock updated successfully.' });
      } else {
        await api.createHospitalPharmacyItem({
          name: pharName,
          dosage: pharDosage,
          stock_quantity: qty,
          unit_price: prc
        });
        await fetchHospitalData();
        setMessage({ type: 'success', text: 'Pharmacy stock recorded on database.' });
      }
      resetAllForms();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error updating pharmacy inventory.';
      setMessage({ type: 'error', text: msg });
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddPrescription = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (useMockData) {
        const pName = patients.find(p => p.id === presPatientId)?.name || 'Unknown Patient';
        const dName = doctors.find(d => d.id === presDoctorId)?.name || 'Unknown Doctor';
        const newPres: HospitalPrescription = {
          id: 'pres_' + Math.random().toString(36).substr(2, 4),
          patient_id: presPatientId,
          patient_name: pName,
          doctor_id: presDoctorId,
          doctor_name: dName,
          medication_name: presMedicationName,
          dosage_instruction: presInstruction,
          status: 'prescribed',
          created_at: new Date().toISOString()
        };
        setPrescriptions([newPres, ...prescriptions]);
        if (stats) setStats({
          ...stats,
          pharmacy: { ...stats.pharmacy, total_prescriptions: stats.pharmacy.total_prescriptions + 1, pending: stats.pharmacy.pending + 1 }
        });
        setMessage({ type: 'success', text: 'Prescription generated successfully.' });
      } else {
        await api.createHospitalPrescription({
          patient_id: presPatientId,
          doctor_id: presDoctorId,
          medication_name: presMedicationName,
          dosage_instruction: presInstruction
        });
        await fetchHospitalData();
        setMessage({ type: 'success', text: 'Prescription recorded on database.' });
      }
      resetAllForms();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error recording prescription.';
      setMessage({ type: 'error', text: msg });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDispensePrescription = async (presId: string) => {
    try {
      if (useMockData) {
        const pres = prescriptions.find(p => p.id === presId);
        if (pres) {
          const item = pharmacyItems.find(i => i.name.toLowerCase() === pres.medication_name.toLowerCase());
          if (item && item.stock_quantity <= 0) {
            throw new Error('Out of stock for prescribed medication.');
          }
          if (item) {
            setPharmacyItems(prev => prev.map(i => i.id === item.id ? { ...i, stock_quantity: i.stock_quantity - 1 } : i));
          }
          setPrescriptions(prev => prev.map(p => p.id === presId ? { ...p, status: 'dispensed' } : p));
          if (stats) setStats({
            ...stats,
            pharmacy: { ...stats.pharmacy, pending: Math.max(0, stats.pharmacy.pending - 1) }
          });
        }
        setMessage({ type: 'success', text: 'Prescription dispensed.' });
      } else {
        await api.dispenseHospitalPrescription(presId);
        await fetchHospitalData();
        setMessage({ type: 'success', text: 'Prescription marked as dispensed.' });
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error dispensing medication.';
      setMessage({ type: 'error', text: msg });
    }
  };

  const handleAddLabRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (useMockData) {
        const pName = patients.find(p => p.id === labPatientId)?.name || 'Unknown Patient';
        const newLab: HospitalLabTest = {
          id: 'lab_' + Math.random().toString(36).substr(2, 4),
          patient_id: labPatientId,
          patient_name: pName,
          test_name: labTestName,
          result: null,
          status: 'pending',
          technician_notes: null,
          created_at: new Date().toISOString(),
          completed_at: null
        };
        setLabTests([newLab, ...labTests]);
        if (stats) setStats({ ...stats, laboratory: { ...stats.laboratory, total_tests: stats.laboratory.total_tests + 1, pending: stats.laboratory.pending + 1 } });
        setMessage({ type: 'success', text: 'Lab test requested.' });
      } else {
        await api.createHospitalLabTest({
          patient_id: labPatientId,
          test_name: labTestName
        });
        await fetchHospitalData();
        setMessage({ type: 'success', text: 'Lab test requested on database.' });
      }
      resetAllForms();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error requesting laboratory test.';
      setMessage({ type: 'error', text: msg });
    } finally {
      setSubmitting(false);
    }
  };

  const handleCompleteLabTest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeLabId) return;
    try {
      if (useMockData) {
        setLabTests(prev => prev.map(t => t.id === activeLabId ? { 
          ...t, 
          result: labResultText, 
          technician_notes: labResultNotes || null, 
          status: 'completed', 
          completed_at: new Date().toISOString() 
        } : t));
        if (stats) setStats({ ...stats, laboratory: { ...stats.laboratory, pending: Math.max(0, stats.laboratory.pending - 1) } });
        setMessage({ type: 'success', text: 'Lab results saved successfully.' });
      } else {
        await api.completeHospitalLabTest(activeLabId, {
          result: labResultText,
          technician_notes: labResultNotes || undefined
        });
        await fetchHospitalData();
        setMessage({ type: 'success', text: 'Lab test results recorded on database.' });
      }
      resetAllForms();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error saving lab results.';
      setMessage({ type: 'error', text: msg });
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center">
            <Activity className="h-6 w-6 text-indigo-400 mr-2.5 animate-pulse" />
            Hospital Administration Portal
          </h2>
          <p className="text-sm text-zinc-400 mt-1">
            Manage electronic health records, schedule doctors, handle laboratory tests, and process pharmacy prescriptions.
          </p>
        </div>
      </div>

      {/* Message Notifications */}
      {message && (
        <div className={`p-4 rounded-xl border flex items-start space-x-3 text-sm animate-in fade-in duration-200 ${
          message.type === 'success' 
            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' 
            : 'bg-red-500/10 border-red-500/20 text-red-400'
        }`}>
          {message.type === 'success' ? <CheckCircle className="h-5 w-5 shrink-0" /> : <XCircle className="h-5 w-5 shrink-0" />}
          <span>{message.text}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-zinc-800 space-x-2 overflow-x-auto pb-1 scrollbar-none">
        <button
          onClick={() => { setActiveTab('dashboard'); resetAllForms(); }}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === 'dashboard' ? 'border-indigo-500 text-indigo-400 font-bold' : 'border-transparent text-zinc-400 hover:text-zinc-200'
          } flex items-center space-x-2`}
        >
          <Activity className="h-4 w-4" />
          <span>Dashboard</span>
        </button>
        <button
          onClick={() => { setActiveTab('patients'); resetAllForms(); }}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === 'patients' ? 'border-indigo-500 text-indigo-400 font-bold' : 'border-transparent text-zinc-400 hover:text-zinc-200'
          } flex items-center space-x-2`}
        >
          <Users className="h-4 w-4" />
          <span>Patients</span>
        </button>
        <button
          onClick={() => { setActiveTab('doctors'); resetAllForms(); }}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === 'doctors' ? 'border-indigo-500 text-indigo-400 font-bold' : 'border-transparent text-zinc-400 hover:text-zinc-200'
          } flex items-center space-x-2`}
        >
          <UserCheck className="h-4 w-4" />
          <span>Doctors</span>
        </button>
        <button
          onClick={() => { setActiveTab('appointments'); resetAllForms(); }}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === 'appointments' ? 'border-indigo-500 text-indigo-400 font-bold' : 'border-transparent text-zinc-400 hover:text-zinc-200'
          } flex items-center space-x-2`}
        >
          <Calendar className="h-4 w-4" />
          <span>Appointments</span>
        </button>
        <button
          onClick={() => { setActiveTab('billing'); resetAllForms(); }}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === 'billing' ? 'border-indigo-500 text-indigo-400 font-bold' : 'border-transparent text-zinc-400 hover:text-zinc-200'
          } flex items-center space-x-2`}
        >
          <CreditCard className="h-4 w-4" />
          <span>Billing</span>
        </button>
        <button
          onClick={() => { setActiveTab('pharmacy'); resetAllForms(); }}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === 'pharmacy' ? 'border-indigo-500 text-indigo-400 font-bold' : 'border-transparent text-zinc-400 hover:text-zinc-200'
          } flex items-center space-x-2`}
        >
          <Pill className="h-4 w-4" />
          <span>Pharmacy</span>
        </button>
        <button
          onClick={() => { setActiveTab('laboratory'); resetAllForms(); }}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === 'laboratory' ? 'border-indigo-500 text-indigo-400 font-bold' : 'border-transparent text-zinc-400 hover:text-zinc-200'
          } flex items-center space-x-2`}
        >
          <FlaskConical className="h-4 w-4" />
          <span>Laboratory</span>
        </button>
        <button
          onClick={() => { setActiveTab('reports'); resetAllForms(); }}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === 'reports' ? 'border-indigo-500 text-indigo-400 font-bold' : 'border-transparent text-zinc-400 hover:text-zinc-200'
          } flex items-center space-x-2`}
        >
          <FileText className="h-4 w-4" />
          <span>Reports</span>
        </button>
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="flex flex-col items-center space-y-3">
            <Loader2 className="h-10 w-10 text-indigo-500 animate-spin" />
            <span className="text-sm text-zinc-400">Fetching electronic health records...</span>
          </div>
        </div>
      ) : (
        <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl p-6 shadow-xl backdrop-blur-md animate-in fade-in duration-300">
          
          {/* TAB 1: HOSPITAL CLINICAL DASHBOARD */}
          {activeTab === 'dashboard' && stats && (
            <div className="space-y-8 animate-in fade-in duration-300">
              
              {/* Stats Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {/* Patients */}
                <div className="bg-zinc-950/40 border border-zinc-800 p-4 rounded-xl flex flex-col justify-between">
                  <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-widest">Total Patients</span>
                  <div className="flex items-baseline space-x-2 mt-2">
                    <span className="text-2xl font-bold text-indigo-400">{stats.patients}</span>
                    <span className="text-xs text-zinc-400">profiles</span>
                  </div>
                </div>

                {/* Appointments */}
                <div className="bg-zinc-950/40 border border-zinc-800 p-4 rounded-xl flex flex-col justify-between">
                  <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-widest">Scheduled Visits</span>
                  <div className="flex items-baseline space-x-2 mt-2">
                    <span className="text-2xl font-bold text-amber-400">{stats.appointments.scheduled}</span>
                    <span className="text-xs text-zinc-400">/{stats.appointments.total} total</span>
                  </div>
                </div>

                {/* Total Billing */}
                <div className="bg-zinc-950/40 border border-zinc-800 p-4 rounded-xl flex flex-col justify-between">
                  <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-widest">Billed Revenue</span>
                  <div className="flex items-baseline space-x-1.5 mt-2">
                    <DollarSign className="h-4.5 w-4.5 text-emerald-400" />
                    <span className="text-2xl font-bold text-emerald-400">{stats.billing.total_billed}</span>
                    <span className="text-[10px] text-rose-400">(${stats.billing.unpaid} unpaid)</span>
                  </div>
                </div>

                {/* Lab Pending */}
                <div className="bg-zinc-950/40 border border-zinc-800 p-4 rounded-xl flex flex-col justify-between">
                  <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-widest">Pending Lab Tests</span>
                  <div className="flex items-baseline space-x-2 mt-2">
                    <span className="text-2xl font-bold text-indigo-300">{stats.laboratory.pending}</span>
                    <span className="text-xs text-zinc-400">/ {stats.laboratory.total_tests} orders</span>
                  </div>
                </div>
              </div>

              {/* Doctors & Quick Details */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                
                {/* Left Columns: Available Doctors */}
                <div className="lg:col-span-2 space-y-4">
                  <h3 className="text-sm font-bold text-zinc-300 uppercase tracking-wider flex items-center">
                    <UserCheck className="h-4 w-4 text-indigo-400 mr-2" />
                    Medical Staff Availability
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {doctors.slice(0, 4).map(doc => (
                      <div key={doc.id} className="p-4 rounded-xl border border-zinc-800/80 bg-zinc-950/30 flex items-center justify-between">
                        <div className="space-y-1">
                          <span className="block text-sm font-bold text-white">{doc.name}</span>
                          <span className="block text-xs text-indigo-400">{doc.specialty}</span>
                        </div>
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                          doc.is_available ? 'bg-emerald-500/10 text-emerald-500 animate-pulse' : 'bg-zinc-800 text-zinc-500'
                        }`}>
                          {doc.is_available ? 'On Duty' : 'Off Duty'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Right: Quick Stats and Pharmacy stock */}
                <div className="space-y-4 bg-zinc-950/30 border border-zinc-800/80 p-5 rounded-xl">
                  <h3 className="text-sm font-bold text-zinc-300 uppercase tracking-wider flex items-center">
                    <Pill className="h-4 w-4 text-indigo-400 mr-2" />
                    Pharmacy Dispensary
                  </h3>
                  <div className="divide-y divide-zinc-800/60 text-xs">
                    <div className="py-2.5 flex justify-between">
                      <span className="text-zinc-400">Total drug formulas</span>
                      <span className="font-bold text-white">{stats.pharmacy.total_drugs}</span>
                    </div>
                    <div className="py-2.5 flex justify-between">
                      <span className="text-zinc-400">Total Prescriptions</span>
                      <span className="font-bold text-white">{stats.pharmacy.total_prescriptions}</span>
                    </div>
                    <div className="py-2.5 flex justify-between">
                      <span className="text-zinc-400">Pending Refills</span>
                      <span className="font-bold text-amber-400">{stats.pharmacy.pending}</span>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          )}

          {/* TAB 2: PATIENTS LIST & REGISTER */}
          {activeTab === 'patients' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-bold text-white flex items-center">
                  <Users className="h-5 w-5 text-indigo-400 mr-2" />
                  EHR Patients Registry
                </h3>
                <button
                  onClick={() => setShowAddForm(!showAddForm)}
                  className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition"
                >
                  <PlusCircle className="h-3.5 w-3.5" />
                  <span>Register Patient</span>
                </button>
              </div>

              {showAddForm && (
                <form onSubmit={handleAddPatient} className="bg-zinc-950/30 border border-zinc-850 p-5 rounded-xl space-y-4 animate-in slide-in-from-top duration-200">
                  <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">New Patient Details</h4>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase">Full Name</label>
                      <input
                        type="text"
                        value={patName}
                        onChange={(e) => setPatName(e.target.value)}
                        required
                        className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                      />
                    </div>
                    
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase">DOB</label>
                      <input
                        type="date"
                        value={patDOB}
                        onChange={(e) => setPatDOB(e.target.value)}
                        required
                        className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                      />
                    </div>
                    
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase">Gender</label>
                      <select
                        value={patGender}
                        onChange={(e) => setPatGender(e.target.value)}
                        className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                      >
                        <option value="Female">Female</option>
                        <option value="Male">Male</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase">Email Address</label>
                      <input
                        type="email"
                        value={patEmail}
                        onChange={(e) => setPatEmail(e.target.value)}
                        className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                      />
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase">Phone Number</label>
                      <input
                        type="text"
                        value={patPhone}
                        onChange={(e) => setPatPhone(e.target.value)}
                        className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                      />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-zinc-400 uppercase">Medical History & Allergies</label>
                    <textarea
                      value={patHistory}
                      onChange={(e) => setPatHistory(e.target.value)}
                      rows={2}
                      className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition resize-none"
                    />
                  </div>

                  <div className="flex justify-end space-x-2">
                    <button
                      type="button"
                      onClick={() => setShowAddForm(false)}
                      className="px-3.5 py-1.5 border border-zinc-800 text-zinc-400 text-xs rounded-lg transition hover:bg-zinc-800"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={submitting}
                      className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-lg flex items-center space-x-1.5 transition"
                    >
                      {submitting && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                      <span>Save Patient Record</span>
                    </button>
                  </div>
                </form>
              )}

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="border-b border-zinc-800 text-zinc-400 font-semibold uppercase tracking-wider text-xs">
                      <th className="py-3 px-4">Patient Name</th>
                      <th className="py-3 px-4">Gender / DOB</th>
                      <th className="py-3 px-4">Contact info</th>
                      <th className="py-3 px-4">Medical History Summary</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/60">
                    {patients.map(p => (
                      <tr key={p.id} className="hover:bg-zinc-800/10 transition">
                        <td className="py-3.5 px-4 font-medium text-white">{p.name}</td>
                        <td className="py-3.5 px-4 text-xs text-zinc-400">
                          {p.gender} / {p.date_of_birth}
                        </td>
                        <td className="py-3.5 px-4 text-xs text-zinc-300">
                          <div>{p.phone || '-'}</div>
                          <div className="text-zinc-500">{p.email || ''}</div>
                        </td>
                        <td className="py-3.5 px-4 text-xs text-zinc-400 max-w-[250px] truncate" title={p.medical_history || ''}>
                          {p.medical_history || <span className="text-zinc-650">No medical history logged</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 3: DOCTORS REGISTRY */}
          {activeTab === 'doctors' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-bold text-white flex items-center">
                  <UserCheck className="h-5 w-5 text-indigo-400 mr-2" />
                  Medical Practitioners Directory
                </h3>
                <button
                  onClick={() => setShowAddForm(!showAddForm)}
                  className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition"
                >
                  <PlusCircle className="h-3.5 w-3.5" />
                  <span>Register Doctor</span>
                </button>
              </div>

              {showAddForm && (
                <form onSubmit={handleAddDoctor} className="bg-zinc-950/30 border border-zinc-850 p-5 rounded-xl space-y-4 animate-in slide-in-from-top duration-200">
                  <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Doctor Registration</h4>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase">Full Name</label>
                      <input
                        type="text"
                        value={docName}
                        onChange={(e) => setDocName(e.target.value)}
                        required
                        className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                      />
                    </div>
                    
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase">Medical Specialty</label>
                      <input
                        type="text"
                        value={docSpecialty}
                        onChange={(e) => setDocSpecialty(e.target.value)}
                        required
                        placeholder="Pediatrics, Cardiology, etc."
                        className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase">Email Address</label>
                      <input
                        type="email"
                        value={docEmail}
                        onChange={(e) => setDocEmail(e.target.value)}
                        className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                      />
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase">Phone Number</label>
                      <input
                        type="text"
                        value={docPhone}
                        onChange={(e) => setDocPhone(e.target.value)}
                        className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                      />
                    </div>
                  </div>

                  <div className="flex justify-end space-x-2">
                    <button
                      type="button"
                      onClick={() => setShowAddForm(false)}
                      className="px-3.5 py-1.5 border border-zinc-800 text-zinc-400 text-xs rounded-lg transition hover:bg-zinc-800"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={submitting}
                      className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-lg flex items-center space-x-1.5 transition"
                    >
                      {submitting && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                      <span>Register Practitioner</span>
                    </button>
                  </div>
                </form>
              )}

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="border-b border-zinc-800 text-zinc-400 font-semibold uppercase tracking-wider text-xs">
                      <th className="py-3 px-4">Doctor Name</th>
                      <th className="py-3 px-4">Specialty</th>
                      <th className="py-3 px-4">Contact info</th>
                      <th className="py-3 px-4 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/60">
                    {doctors.map(doc => (
                      <tr key={doc.id} className="hover:bg-zinc-800/10 transition">
                        <td className="py-3.5 px-4 font-medium text-white">{doc.name}</td>
                        <td className="py-3.5 px-4 text-xs text-indigo-400">{doc.specialty}</td>
                        <td className="py-3.5 px-4 text-xs text-zinc-350">
                          <div>{doc.phone || '-'}</div>
                          <div className="text-zinc-500">{doc.email || ''}</div>
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            doc.is_available ? 'bg-emerald-500/10 text-emerald-400' : 'bg-zinc-800 text-zinc-550'
                          }`}>
                            {doc.is_available ? 'Available' : 'On Leave'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 4: APPOINTMENTS SCHEDULER */}
          {activeTab === 'appointments' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-bold text-white flex items-center">
                  <Calendar className="h-5 w-5 text-indigo-400 mr-2" />
                  Scheduled Medical Consultations
                </h3>
                <button
                  onClick={() => setShowAddForm(!showAddForm)}
                  className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition"
                >
                  <PlusCircle className="h-3.5 w-3.5" />
                  <span>Book Consultation</span>
                </button>
              </div>

              {showAddForm && (
                <form onSubmit={handleBookAppointment} className="bg-zinc-950/30 border border-zinc-850 p-5 rounded-xl space-y-4 animate-in slide-in-from-top duration-200">
                  <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Book Appointment</h4>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase">Select Patient</label>
                      <select
                        value={apptPatientId}
                        onChange={(e) => setApptPatientId(e.target.value)}
                        required
                        className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                      >
                        <option value="">-- Select Patient --</option>
                        {patients.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                      </select>
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase">Select Doctor</label>
                      <select
                        value={apptDoctorId}
                        onChange={(e) => setApptDoctorId(e.target.value)}
                        required
                        className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                      >
                        <option value="">-- Select Doctor --</option>
                        {doctors.map(d => <option key={d.id} value={d.id}>{d.name} ({d.specialty})</option>)}
                      </select>
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase">Consultation Date/Time</label>
                      <input
                        type="datetime-local"
                        value={apptDate}
                        onChange={(e) => setApptDate(e.target.value)}
                        required
                        className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                      />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-zinc-400 uppercase">Reason for Visit</label>
                    <input
                      type="text"
                      value={apptReason}
                      onChange={(e) => setApptReason(e.target.value)}
                      required
                      className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-zinc-400 uppercase">Initial Nurse/Doctor Notes</label>
                    <textarea
                      value={apptNotes}
                      onChange={(e) => setApptNotes(e.target.value)}
                      rows={2}
                      className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition resize-none"
                    />
                  </div>

                  <div className="flex justify-end space-x-2">
                    <button
                      type="button"
                      onClick={() => setShowAddForm(false)}
                      className="px-3.5 py-1.5 border border-zinc-800 text-zinc-400 text-xs rounded-lg transition hover:bg-zinc-800"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={submitting}
                      className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-lg flex items-center space-x-1.5 transition"
                    >
                      {submitting && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                      <span>Schedule Consultation</span>
                    </button>
                  </div>
                </form>
              )}

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="border-b border-zinc-800 text-zinc-400 font-semibold uppercase tracking-wider text-xs">
                      <th className="py-3 px-4">Patient</th>
                      <th className="py-3 px-4">Doctor</th>
                      <th className="py-3 px-4">Date & Time</th>
                      <th className="py-3 px-4">Reason / Notes</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/60">
                    {appointments.map(appt => (
                      <tr key={appt.id} className="hover:bg-zinc-800/10 transition">
                        <td className="py-3.5 px-4 font-medium text-white">{appt.patient_name}</td>
                        <td className="py-3.5 px-4 text-xs text-indigo-400">{appt.doctor_name}</td>
                        <td className="py-3.5 px-4 text-xs text-zinc-350">
                          {new Date(appt.appointment_date).toLocaleString()}
                        </td>
                        <td className="py-3.5 px-4 text-xs text-zinc-400">
                          <div>{appt.reason}</div>
                          {appt.notes && <div className="text-[10px] text-zinc-550 italic mt-0.5">Notes: {appt.notes}</div>}
                        </td>
                        <td className="py-3.5 px-4 text-right space-x-1.5">
                          {appt.status === 'scheduled' ? (
                            <>
                              <button
                                onClick={() => handleUpdateApptStatus(appt.id, 'completed')}
                                className="text-[10px] bg-emerald-500/10 hover:bg-emerald-500/25 text-emerald-400 px-2 py-1 rounded transition"
                              >
                                Complete
                              </button>
                              <button
                                onClick={() => handleUpdateApptStatus(appt.id, 'cancelled')}
                                className="text-[10px] bg-rose-500/10 hover:bg-rose-500/25 text-rose-400 px-2 py-1 rounded transition"
                              >
                                Cancel
                              </button>
                            </>
                          ) : (
                            <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${
                              appt.status === 'completed' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-rose-500/10 text-rose-500'
                            }`}>
                              {appt.status}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 5: BILLING & PAYMENT STATUS */}
          {activeTab === 'billing' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-bold text-white flex items-center">
                  <CreditCard className="h-5 w-5 text-indigo-400 mr-2" />
                  Clinical Invoices & Payments Ledger
                </h3>
                <button
                  onClick={() => setShowAddForm(!showAddForm)}
                  className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition"
                >
                  <PlusCircle className="h-3.5 w-3.5" />
                  <span>Generate Invoice</span>
                </button>
              </div>

              {showAddForm && (
                <form onSubmit={handleAddBill} className="bg-zinc-950/30 border border-zinc-850 p-5 rounded-xl space-y-4 animate-in slide-in-from-top duration-200">
                  <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Generate Invoice</h4>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase">Select Patient</label>
                      <select
                        value={billPatientId}
                        onChange={(e) => setBillPatientId(e.target.value)}
                        required
                        className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                      >
                        <option value="">-- Select Patient --</option>
                        {patients.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                      </select>
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase">Total Amount ($)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={billAmount}
                        onChange={(e) => setBillAmount(e.target.value)}
                        required
                        placeholder="150.00"
                        className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                      />
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase">Linked Appointment ID (Optional)</label>
                      <select
                        value={billApptId}
                        onChange={(e) => setBillApptId(e.target.value)}
                        className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                      >
                        <option value="">-- Select Appointment --</option>
                        {appointments.map(a => <option key={a.id} value={a.id}>{a.patient_name} - {a.reason}</option>)}
                      </select>
                    </div>
                  </div>

                  <div className="flex justify-end space-x-2">
                    <button
                      type="button"
                      onClick={() => setShowAddForm(false)}
                      className="px-3.5 py-1.5 border border-zinc-800 text-zinc-400 text-xs rounded-lg transition hover:bg-zinc-800"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={submitting}
                      className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-lg flex items-center space-x-1.5 transition"
                    >
                      {submitting && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                      <span>Generate Invoice</span>
                    </button>
                  </div>
                </form>
              )}

              {/* Payment Modal/Overlay inline */}
              {activeBillId && (
                <form onSubmit={handlePayBill} className="bg-zinc-950/60 border border-indigo-500/20 p-5 rounded-xl space-y-4 animate-in fade-in duration-200 max-w-sm">
                  <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center">
                    <DollarSign className="h-4 w-4 mr-1" />
                    Record Invoice Payment
                  </h4>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-zinc-400 uppercase">Payment Method</label>
                    <select
                      value={paymentMethod}
                      onChange={(e) => setPaymentMethod(e.target.value)}
                      className="w-full bg-zinc-950 border border-zinc-850 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                    >
                      <option value="Cash">Cash</option>
                      <option value="Credit Card">Credit Card</option>
                      <option value="Insurance Coverage">Insurance Coverage</option>
                      <option value="Bank Wire">Bank Wire</option>
                    </select>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      type="submit"
                      className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg transition"
                    >
                      Submit Payment
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveBillId(null)}
                      className="px-3.5 py-1.5 border border-zinc-850 text-zinc-400 text-xs rounded-lg transition hover:bg-zinc-850"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              )}

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="border-b border-zinc-800 text-zinc-400 font-semibold uppercase tracking-wider text-xs">
                      <th className="py-3 px-4">Invoice ID</th>
                      <th className="py-3 px-4">Patient Name</th>
                      <th className="py-3 px-4">Invoice Amount</th>
                      <th className="py-3 px-4">Payment Method</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/60 font-mono text-xs">
                    {billing.map(bill => (
                      <tr key={bill.id} className="hover:bg-zinc-800/10 transition">
                        <td className="py-3.5 px-4 text-zinc-500">#{bill.id.substr(0, 8)}</td>
                        <td className="py-3.5 px-4 font-sans text-sm font-medium text-white">{bill.patient_name}</td>
                        <td className="py-3.5 px-4 text-zinc-300 font-bold">${bill.amount.toFixed(2)}</td>
                        <td className="py-3.5 px-4 text-zinc-400">{bill.payment_method || '-'}</td>
                        <td className="py-3.5 px-4">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            bill.status === 'paid' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-rose-500/10 text-rose-500'
                          }`}>
                            {bill.status}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          {bill.status === 'unpaid' && (
                            <button
                              onClick={() => setActiveBillId(bill.id)}
                              className="text-[10px] bg-indigo-600 hover:bg-indigo-500 text-white px-2.5 py-1 rounded transition"
                            >
                              Collect Fee
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 6: PHARMACY (INVENTORY & PRESCRIPTIONS) */}
          {activeTab === 'pharmacy' && (
            <div className="space-y-8">
              
              {/* Top Section: Inventory & Prescription selectors */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                
                {/* Pharmacy stock items */}
                <div className="space-y-4">
                  <div className="flex justify-between items-center border-b border-zinc-800 pb-2">
                    <h3 className="text-sm font-bold text-zinc-300 uppercase tracking-wider flex items-center">
                      <Pill className="h-4 w-4 text-indigo-400 mr-2" />
                      Pharmacy Inventory Stock
                    </h3>
                    <button
                      onClick={() => setShowAddForm(!showAddForm)}
                      className="text-[10px] bg-indigo-600 hover:bg-indigo-500 text-white px-2 py-1 rounded transition flex items-center space-x-1"
                    >
                      <PlusCircle className="h-3 w-3" />
                      <span>Add Medicine</span>
                    </button>
                  </div>

                  {showAddForm && (
                    <form onSubmit={handleAddPharmacyItem} className="bg-zinc-950/30 border border-zinc-850 p-4 rounded-xl space-y-3">
                      <h4 className="text-[11px] font-bold text-zinc-400 uppercase">Register stock item</h4>
                      <div className="grid grid-cols-2 gap-3">
                        <input
                          type="text"
                          value={pharName}
                          onChange={(e) => setPharName(e.target.value)}
                          placeholder="Aspirin"
                          required
                          className="bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                        />
                        <input
                          type="text"
                          value={pharDosage}
                          onChange={(e) => setPharDosage(e.target.value)}
                          placeholder="100mg"
                          required
                          className="bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <input
                          type="number"
                          value={pharStock}
                          onChange={(e) => setPharStock(e.target.value)}
                          placeholder="Quantity"
                          required
                          className="bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                        />
                        <input
                          type="number"
                          step="0.01"
                          value={pharPrice}
                          onChange={(e) => setPharPrice(e.target.value)}
                          placeholder="Unit Price ($)"
                          required
                          className="bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                        />
                      </div>
                      <div className="flex justify-end space-x-2">
                        <button
                          type="submit"
                          className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold px-3 py-1 rounded-lg"
                        >
                          Save Item
                        </button>
                        <button
                          type="button"
                          onClick={() => setShowAddForm(false)}
                          className="border border-zinc-850 text-zinc-400 text-xs px-3 py-1 rounded-lg"
                        >
                          Close
                        </button>
                      </div>
                    </form>
                  )}

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-zinc-850 text-zinc-500 font-bold uppercase tracking-wider">
                          <th className="py-2 px-3">Drug Name</th>
                          <th className="py-2 px-3">Dosage</th>
                          <th className="py-2 px-3 text-center">In Stock</th>
                          <th className="py-2 px-3 text-right">Unit Cost</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-850/60 font-mono text-[11px]">
                        {pharmacyItems.map(item => (
                          <tr key={item.id} className="hover:bg-zinc-800/5 transition">
                            <td className="py-2 px-3 font-sans text-white font-medium">{item.name}</td>
                            <td className="py-2 px-3 text-zinc-400">{item.dosage}</td>
                            <td className={`py-2 px-3 text-center font-bold ${
                              item.stock_quantity <= 15 ? 'text-amber-500 animate-pulse' : 'text-zinc-300'
                            }`}>{item.stock_quantity} units</td>
                            <td className="py-2 px-3 text-right text-zinc-300">${item.unit_price.toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Prescription request form */}
                <div className="space-y-4 bg-zinc-950/20 border border-zinc-800/80 p-5 rounded-xl">
                  <h3 className="text-sm font-bold text-zinc-300 uppercase tracking-wider flex items-center border-b border-zinc-800 pb-2">
                    <ClipboardList className="h-4 w-4 text-indigo-400 mr-2" />
                    Record Doctor Prescription
                  </h3>

                  <form onSubmit={handleAddPrescription} className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-1.5">
                        <label className="text-[10px] font-bold text-zinc-500 uppercase">Select Patient</label>
                        <select
                          value={presPatientId}
                          onChange={(e) => setPresPatientId(e.target.value)}
                          required
                          className="w-full bg-zinc-950 border border-zinc-850 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                        >
                          <option value="">-- Select Patient --</option>
                          {patients.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                        </select>
                      </div>

                      <div className="space-y-1.5">
                        <label className="text-[10px] font-bold text-zinc-500 uppercase">Attending Doctor</label>
                        <select
                          value={presDoctorId}
                          onChange={(e) => setPresDoctorId(e.target.value)}
                          required
                          className="w-full bg-zinc-950 border border-zinc-850 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                        >
                          <option value="">-- Select Doctor --</option>
                          {doctors.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                        </select>
                      </div>
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-zinc-500 uppercase">Medication Prescribed</label>
                      <input
                        type="text"
                        value={presMedicationName}
                        onChange={(e) => setPresMedicationName(e.target.value)}
                        placeholder="e.g. Amoxicillin (must match stock name to deduct inventory)"
                        required
                        className="w-full bg-zinc-950 border border-zinc-850 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                      />
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-zinc-500 uppercase">Dosage & Instructions</label>
                      <textarea
                        value={presInstruction}
                        onChange={(e) => setPresInstruction(e.target.value)}
                        placeholder="Take 1 capsule twice daily for 7 days."
                        required
                        rows={2}
                        className="w-full bg-zinc-950 border border-zinc-850 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition resize-none"
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={submitting}
                      className="w-full px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-lg flex items-center justify-center space-x-1.5 transition"
                    >
                      {submitting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <ClipboardList className="h-3.5 w-3.5" />}
                      <span>Save Prescription</span>
                    </button>
                  </form>
                </div>
              </div>

              {/* Prescriptions List Table */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest border-b border-zinc-800 pb-2">
                  Recent Prescription Logs & Dispensary Actions
                </h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-zinc-800 text-zinc-400 font-semibold uppercase tracking-wider text-[10px]">
                        <th className="py-2.5 px-3">Patient</th>
                        <th className="py-2.5 px-3">Doctor</th>
                        <th className="py-2.5 px-3">Medication</th>
                        <th className="py-2.5 px-3">Dosage Instructions</th>
                        <th className="py-2.5 px-3">Status</th>
                        <th className="py-2.5 px-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-850/60 font-sans text-xs">
                      {prescriptions.map(pres => (
                        <tr key={pres.id} className="hover:bg-zinc-800/10 transition">
                          <td className="py-3 px-3 font-medium text-white">{pres.patient_name}</td>
                          <td className="py-3 px-3 text-zinc-400">{pres.doctor_name}</td>
                          <td className="py-3 px-3 font-mono text-zinc-300 font-bold">{pres.medication_name}</td>
                          <td className="py-3 px-3 text-zinc-400 max-w-[200px] truncate" title={pres.dosage_instruction}>
                            {pres.dosage_instruction}
                          </td>
                          <td className="py-3 px-3">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                              pres.status === 'dispensed' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-amber-500/10 text-amber-500'
                            }`}>
                              {pres.status}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-right">
                            {pres.status === 'prescribed' && (
                              <button
                                onClick={() => handleDispensePrescription(pres.id)}
                                className="text-[10px] bg-emerald-600 hover:bg-emerald-500 text-white px-2 py-1 rounded transition"
                              >
                                Dispense
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          )}

          {/* TAB 7: LABORATORY ORDERS & RESULTS */}
          {activeTab === 'laboratory' && (
            <div className="space-y-8">
              
              {/* Order Lab Form & Result Form */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                
                {/* Lab request form */}
                <div className="bg-zinc-950/20 border border-zinc-800/80 p-5 rounded-xl space-y-4">
                  <h3 className="text-sm font-bold text-zinc-300 uppercase tracking-wider flex items-center border-b border-zinc-800 pb-2">
                    <FlaskConical className="h-4 w-4 text-indigo-400 mr-2" />
                    Request Diagnostic Test
                  </h3>

                  <form onSubmit={handleAddLabRequest} className="space-y-4">
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-zinc-500 uppercase">Select Patient</label>
                      <select
                        value={labPatientId}
                        onChange={(e) => setLabPatientId(e.target.value)}
                        required
                        className="w-full bg-zinc-950 border border-zinc-850 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                      >
                        <option value="">-- Select Patient --</option>
                        {patients.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                      </select>
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-zinc-500 uppercase">Test Name</label>
                      <input
                        type="text"
                        value={labTestName}
                        onChange={(e) => setLabTestName(e.target.value)}
                        placeholder="CBC, Lipid Profile, Liver Panel, etc."
                        required
                        className="w-full bg-zinc-950 border border-zinc-850 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={submitting}
                      className="w-full px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-lg flex items-center justify-center space-x-1.5 transition"
                    >
                      {submitting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <FlaskConical className="h-3.5 w-3.5" />}
                      <span>Order Laboratory Test</span>
                    </button>
                  </form>
                </div>

                {/* Laboratory result recorder (if test_id active) */}
                <div className="lg:col-span-2 bg-zinc-950/20 border border-zinc-800/80 p-5 rounded-xl space-y-4">
                  <h3 className="text-sm font-bold text-zinc-300 uppercase tracking-wider flex items-center border-b border-zinc-800 pb-2">
                    <FileText className="h-4 w-4 text-indigo-400 mr-2" />
                    Record Lab Test Findings
                  </h3>

                  {activeLabId ? (
                    <form onSubmit={handleCompleteLabTest} className="space-y-4">
                      <div className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg text-xs">
                        <span className="font-bold text-white">Target Order ID: </span>
                        <span className="font-mono text-zinc-400">#{activeLabId}</span>
                        <div className="text-zinc-400 mt-1">
                          Patient: <span className="font-bold text-white">{labTests.find(t => t.id === activeLabId)?.patient_name}</span> | 
                          Test: <span className="font-bold text-white">{labTests.find(t => t.id === activeLabId)?.test_name}</span>
                        </div>
                      </div>

                      <div className="space-y-1.5">
                        <label className="text-[10px] font-bold text-zinc-500 uppercase">Test Result Metrics</label>
                        <textarea
                          value={labResultText}
                          onChange={(e) => setLabResultText(e.target.value)}
                          placeholder="Hematocrit: 42%, Hemoglobin: 14.2 g/dL, WBC: 6.8 x10^3/uL."
                          required
                          rows={2}
                          className="w-full bg-zinc-950 border border-zinc-850 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition resize-none"
                        />
                      </div>

                      <div className="space-y-1.5">
                        <label className="text-[10px] font-bold text-zinc-500 uppercase">Technician Notes</label>
                        <input
                          type="text"
                          value={labResultNotes}
                          onChange={(e) => setLabResultNotes(e.target.value)}
                          placeholder="Specimen handled properly. Controls verified."
                          className="w-full bg-zinc-950 border border-zinc-850 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                        />
                      </div>

                      <div className="flex space-x-2">
                        <button
                          type="submit"
                          className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg transition"
                        >
                          Complete Lab Test
                        </button>
                        <button
                          type="button"
                          onClick={() => setActiveLabId(null)}
                          className="px-3.5 py-1.5 border border-zinc-850 text-zinc-450 text-xs rounded-lg transition hover:bg-zinc-850"
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  ) : (
                    <div className="h-44 flex items-center justify-center text-zinc-500 text-xs border border-dashed border-zinc-800 rounded-xl">
                      Select a pending test from the table below to log diagnostic findings.
                    </div>
                  )}
                </div>

              </div>

              {/* Lab test queue table */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest border-b border-zinc-800 pb-2">
                  Diagnostic Laboratories queue
                </h4>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-zinc-800 text-zinc-400 font-semibold uppercase tracking-wider text-[10px]">
                        <th className="py-2.5 px-3">Patient</th>
                        <th className="py-2.5 px-3">Test Ordered</th>
                        <th className="py-2.5 px-3">Findings / Results</th>
                        <th className="py-2.5 px-3">Status</th>
                        <th className="py-2.5 px-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-850/60 font-sans text-xs">
                      {labTests.map(test => (
                        <tr key={test.id} className="hover:bg-zinc-800/10 transition">
                          <td className="py-3 px-3 font-medium text-white">{test.patient_name}</td>
                          <td className="py-3 px-3 text-indigo-400">{test.test_name}</td>
                          <td className="py-3 px-3 text-zinc-400 max-w-[250px] truncate" title={test.result || ''}>
                            {test.result || <span className="text-zinc-650 italic">No results loaded yet</span>}
                            {test.technician_notes && (
                              <div className="text-[10px] text-zinc-550 mt-0.5">Tech Note: {test.technician_notes}</div>
                            )}
                          </td>
                          <td className="py-3 px-3">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                              test.status === 'completed' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-amber-500/10 text-amber-500'
                            }`}>
                              {test.status}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-right font-sans">
                            {test.status === 'pending' && (
                              <button
                                onClick={() => {
                                  setActiveLabId(test.id);
                                  setLabResultText('');
                                  setLabResultNotes('');
                                }}
                                className="text-[10px] bg-indigo-650 hover:bg-indigo-500 text-white px-2 py-1 rounded transition"
                              >
                                Log Result
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          )}

          {/* TAB 8: DIAGNOSTIC STATS & EXPORT REPORTS */}
          {activeTab === 'reports' && stats && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center">
                  <FileText className="h-5 w-5 text-indigo-400 mr-2" />
                  Clinical Metrics & Summary Report
                </h3>
                <p className="text-xs text-zinc-400 mt-1">Review operational execution percentages, patient load distribution, and financial statements.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                
                {/* Financial Summary Table */}
                <div className="bg-zinc-950/20 border border-zinc-800 p-5 rounded-xl space-y-4">
                  <h4 className="text-xs font-bold text-zinc-450 uppercase tracking-wider border-b border-zinc-800 pb-2">Financial Statement</h4>
                  <div className="divide-y divide-zinc-800 text-xs font-mono">
                    <div className="py-3 flex justify-between">
                      <span className="text-zinc-400">Total Billed revenue</span>
                      <span className="font-bold text-white">${stats.billing.total_billed.toFixed(2)}</span>
                    </div>
                    <div className="py-3 flex justify-between">
                      <span className="text-zinc-400 font-semibold text-emerald-400">Paid / Received Fees</span>
                      <span className="font-bold text-emerald-400">${stats.billing.paid.toFixed(2)}</span>
                    </div>
                    <div className="py-3 flex justify-between">
                      <span className="text-zinc-400 font-semibold text-rose-400">Unpaid / Outstanding Fees</span>
                      <span className="font-bold text-rose-400">${stats.billing.unpaid.toFixed(2)}</span>
                    </div>
                    <div className="py-3 flex justify-between text-zinc-200">
                      <span>Collections Rate</span>
                      <span className="font-bold">
                        {stats.billing.total_billed > 0 
                          ? ((stats.billing.paid / stats.billing.total_billed) * 100).toFixed(1)
                          : '100'}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Operations Summary */}
                <div className="bg-zinc-950/20 border border-zinc-800 p-5 rounded-xl space-y-4">
                  <h4 className="text-xs font-bold text-zinc-450 uppercase tracking-wider border-b border-zinc-800 pb-2">Operations Performance Metrics</h4>
                  <div className="divide-y divide-zinc-800 text-xs">
                    <div className="py-3 flex justify-between">
                      <span className="text-zinc-400">Doctor Utilization Rate</span>
                      <span className="font-bold text-white">
                        {doctors.length > 0
                          ? ((doctors.filter(d => d.is_available).length / doctors.length) * 100).toFixed(1)
                          : '0'}% Active
                      </span>
                    </div>
                    <div className="py-3 flex justify-between">
                      <span className="text-zinc-400">Appointment Completion Rate</span>
                      <span className="font-bold text-white">
                        {appointments.length > 0
                          ? ((appointments.filter(a => a.status === 'completed').length / appointments.length) * 100).toFixed(1)
                          : '0'}% Completed
                      </span>
                    </div>
                    <div className="py-3 flex justify-between">
                      <span className="text-zinc-400">Prescription Dispatch Rate</span>
                      <span className="font-bold text-white">
                        {prescriptions.length > 0
                          ? ((prescriptions.filter(p => p.status === 'dispensed').length / prescriptions.length) * 100).toFixed(1)
                          : '0'}% Dispensed
                      </span>
                    </div>
                    <div className="py-3 flex justify-between">
                      <span className="text-zinc-400">Diagnostics Lab Success Rate</span>
                      <span className="font-bold text-white">
                        {labTests.length > 0
                          ? ((labTests.filter(l => l.status === 'completed').length / labTests.length) * 100).toFixed(1)
                          : '0'}% Completed
                      </span>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          )}

        </div>
      )}

    </div>
  );
};
