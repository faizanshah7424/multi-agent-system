def check_patient_status(vitals: dict) -> str:
    """
    Evaluates patient vitals and returns the clinical status: STABLE, WARNING, or CRITICAL.
    """
    heart_rate = vitals.get("heart_rate", 70)
    temperature = vitals.get("temperature", 98.6)

    if heart_rate < 40 or heart_rate > 130 or temperature < 94.0 or temperature > 104.0:
        return "CRITICAL"
    elif (
        heart_rate < 60 or heart_rate > 100 or temperature < 96.5 or temperature > 100.4
    ):
        return "WARNING"
    return "STABLE"
