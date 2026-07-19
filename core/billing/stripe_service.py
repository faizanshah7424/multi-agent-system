"""
Stripe Billing Service for synchronization of Stripe subscription state with database.
"""
from typing import Dict, Any, Optional
from core.database import get_db_session, Subscription, Organization
from core.logging import get_logger

logger = get_logger("StripeBillingService")


class StripeBillingService:
    """
    Handles subscription synchronization and management for Stripe events.
    """

    @staticmethod
    def sync_stripe_subscription(subscription_id: str, data: Dict[str, Any]) -> Optional[Subscription]:
        """
        Synchronizes a Stripe subscription payload with local database.
        """
        org_id = data.get("org_id")
        customer_id = data.get("customer_id")
        plan = data.get("plan", "free")
        status = data.get("status", "active")
        seats = data.get("seats", 1)

        with get_db_session() as session:
            sub = session.query(Subscription).filter_by(stripe_subscription_id=subscription_id).first()
            if not sub and customer_id:
                sub = session.query(Subscription).filter_by(customer_id=customer_id).first()

            if sub:
                sub.plan = plan
                sub.status = status
                sub.seats = seats
                if org_id:
                    sub.org_id = org_id
            else:
                sub = Subscription(
                    stripe_subscription_id=subscription_id,
                    customer_id=customer_id,
                    org_id=org_id,
                    plan=plan,
                    status=status,
                    seats=seats,
                )
                session.add(sub)

            session.commit()
            session.refresh(sub)
            logger.info(f"Synchronized Stripe subscription {subscription_id} for org {org_id}")
            return sub
