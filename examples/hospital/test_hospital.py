from patients import check_patient_status


def test_patient_stable():
    vitals = {"heart_rate": 72, "temperature": 98.6}
    assert check_patient_status(vitals) == "STABLE"


def test_patient_warning():
    vitals = {"heart_rate": 55, "temperature": 98.6}
    assert check_patient_status(vitals) == "WARNING"


def test_patient_critical():
    vitals = {"heart_rate": 140, "temperature": 98.6}
    assert check_patient_status(vitals) == "CRITICAL"
