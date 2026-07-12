from typing import List, Dict
from pydantic import BaseModel, Field


class BusinessSpecs(BaseModel):
    domain: str
    stakeholders: List[str] = Field(default_factory=list)
    user_roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    workflows: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    reports: List[str] = Field(default_factory=list)
    kpis: List[str] = Field(default_factory=list)


class BusinessAnalyzer:
    """
    Analyzes business ideas, mapping domains, stakeholders, roles, permissions, and KPIs.
    """

    def analyze_business_idea(self, idea: str) -> BusinessSpecs:
        idea_lower = idea.lower()
        if "hospital" in idea_lower:
            return BusinessSpecs(
                domain="Healthcare / Medical Operations",
                stakeholders=["Patients", "Doctors", "Hospital Admin", "Nurses"],
                user_roles=["Doctor", "Patient", "Admin", "Nurse"],
                permissions=[
                    "read_patient_record",
                    "write_prescription",
                    "manage_billing",
                ],
                workflows=[
                    "Patient Check-in",
                    "Doctor consultation & Prescription",
                    "Discharge & Billing",
                ],
                entities=[
                    "Patient",
                    "Doctor",
                    "Appointment",
                    "Prescription",
                    "Invoice",
                ],
                reports=["Daily Admissions", "Billing Summary", "Bed Occupancy Rates"],
                kpis=[
                    "Average Wait Time",
                    "Patient Satisfaction Index",
                    "Bed Turnover Rate",
                ],
            )
        elif "restaurant" in idea_lower or "pos" in idea_lower:
            return BusinessSpecs(
                domain="Food & Beverage / Retail Point of Sale",
                stakeholders=[
                    "Customers",
                    "Waitstaff",
                    "Kitchen Chef",
                    "Store Manager",
                ],
                user_roles=["Cashier", "Waiter", "Chef", "Manager"],
                permissions=[
                    "place_order",
                    "process_payment",
                    "modify_menu",
                    "refund_transaction",
                ],
                workflows=[
                    "Order creation",
                    "Kitchen notification",
                    "Payment checkout",
                ],
                entities=["Order", "MenuProduct", "Payment", "TableRecord"],
                reports=["Hourly Sales Volume", "Top Selling Items", "Staff Tips Log"],
                kpis=[
                    "Average Ticket Size",
                    "Order Cycle Time",
                    "Inventory Waste Rate",
                ],
            )
        else:
            return BusinessSpecs(
                domain=f"Custom Domain: {idea}",
                stakeholders=["End Users", "Administrators", "Operators"],
                user_roles=["Admin", "User", "Guest"],
                permissions=["read_data", "write_data", "configure_system"],
                workflows=["User onboarding", "Data entry", "Approval lifecycle"],
                entities=["UserRecord", "Configuration", "Transaction"],
                reports=["Activity logs", "System health report"],
                kpis=["Daily Active Users", "Transaction Success Rate"],
            )
