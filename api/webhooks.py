import hmac
import hashlib
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Header, HTTPException
from typing import Dict, Any

from config import settings
from core.database import get_db_session, User, Organization, OrganizationMembership, Project, Subscription
from core.billing.stripe_service import StripeBillingService
from core.logging import get_logger

logger = get_logger("Webhooks")
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

# ==========================================
# 1. Clerk Webhook Signature Verification
# ==========================================
def verify_clerk_signature(body: bytes, headers: dict, secret: str) -> bool:
    """
    Verify Svix HMAC-SHA256 signature for Clerk webhooks.
    """
    if not secret:
        # Default pass in local development / testing if secret is not set
        return True
        
    msg_id = headers.get("svix-id")
    msg_timestamp = headers.get("svix-timestamp")
    msg_signature = headers.get("svix-signature")
    
    if not all([msg_id, msg_timestamp, msg_signature]):
        return False
        
    # Construct signature payload
    to_sign = f"{msg_id}.{msg_timestamp}.".encode() + body
    secret_bytes = secret.encode()
    computed = hmac.new(secret_bytes, to_sign, hashlib.sha256).hexdigest()
    
    for part in msg_signature.split(" "):
        if part.startswith("v1,"):
            sig = part[3:]
            if hmac.compare_digest(sig, computed):
                return True
    return False

# ==========================================
# 2. Clerk Webhook Receiver Endpoint
# ==========================================
@router.post("/clerk")
async def clerk_webhook(
    request: Request,
    svix_id: str = Header(None, alias="svix-id"),
    svix_timestamp: str = Header(None, alias="svix-timestamp"),
    svix_signature: str = Header(None, alias="svix-signature")
):
    """
    Receives events from Clerk to synchronize users, organizations, and memberships.
    """
    body = await request.body()
    headers = {
        "svix-id": svix_id,
        "svix-timestamp": svix_timestamp,
        "svix-signature": svix_signature
    }
    
    secret = os.environ.get("CLERK_WEBHOOK_SECRET", "")
    if not secret:
        from config import settings
        if settings.authentication_backend != "mock":
            logger.error("CLERK_WEBHOOK_SECRET environment variable is missing in production. Rejecting Clerk webhook.")
            raise HTTPException(status_code=500, detail="Webhook configuration error")
        logger.warning("CLERK_WEBHOOK_SECRET is missing. Bypassing signature verification because AUTHENTICATION_BACKEND is 'mock'.")
    elif not verify_clerk_signature(body, headers, secret):
        logger.warning("Clerk webhook signature verification failed.")
        raise HTTPException(status_code=400, detail="Invalid signature")
        
    try:
        data = json.loads(body.decode())
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
    event_type = data.get("type")
    event_data = data.get("data", {})
    
    logger.info(f"Received Clerk Webhook: {event_type}")
    
    with get_db_session() as session:
        # User synchronization
        if event_type in ("user.created", "user.updated"):
            user_id = event_data.get("id")
            email_addresses = event_data.get("email_addresses", [])
            email = email_addresses[0].get("email_address") if email_addresses else f"{user_id}@clerk.local"
            
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                user = User(
                    id=user_id,
                    email=email,
                    hashed_password="clerk_oauth_login",
                    is_active=True
                )
                session.add(user)
            else:
                user.email = email
            session.commit()
            logger.info(f"Synced User {user_id} via Clerk webhook.")
            
        elif event_type == "user.deleted":
            user_id = event_data.get("id")
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.is_active = False # Deactivate
                session.commit()
                logger.info(f"Deactivated deleted user {user_id}.")

        # Organization synchronization
        elif event_type in ("organization.created", "organization.updated"):
            org_id = event_data.get("id")
            name = event_data.get("name", "Unnamed Organization")
            
            org = session.query(Organization).filter_by(id=org_id).first()
            if not org:
                org = Organization(id=org_id, name=name)
                session.add(org)
                session.commit()
                
                # Auto-provision Default Workspace (Project) for new organizations
                project = Project(
                    org_id=org_id,
                    name="Default Workspace",
                    repository_url="",
                    agent_config={"auto_repair": True, "strict_confinement": True}
                )
                session.add(project)
                session.commit()
                logger.info(f"Provisioned default project workspace for Org {org_id}")
            else:
                org.name = name
                session.commit()
            logger.info(f"Synced Organization {org_id} via Clerk webhook.")
            
        elif event_type == "organization.deleted":
            org_id = event_data.get("id")
            org = session.query(Organization).filter_by(id=org_id).first()
            if org:
                session.delete(org)
                session.commit()
                logger.info(f"Deleted Organization {org_id}.")

        # Role / Membership synchronization
        elif event_type in ("organizationMembership.created", "organizationMembership.updated"):
            membership_id = event_data.get("id")
            org_id = event_data.get("organization", {}).get("id")
            user_id = event_data.get("public_user_data", {}).get("user_id")
            role_claim = event_data.get("role", "org_member").upper()
            
            # Map role
            role = "USER"
            if role_claim in ("ADMIN", "ORG_ADMIN", "OWNER", "ADMINISTRATOR"):
                role = "ORG_ADMIN"
                
            membership = session.query(OrganizationMembership).filter_by(id=membership_id).first()
            if not membership:
                membership = OrganizationMembership(
                    id=membership_id,
                    user_id=user_id,
                    org_id=org_id,
                    role=role
                )
                session.add(membership)
            else:
                membership.role = role
            session.commit()
            logger.info(f"Synced Membership {membership_id} (User: {user_id}, Org: {org_id}, Role: {role})")
            
        elif event_type == "organizationMembership.deleted":
            membership_id = event_data.get("id")
            membership = session.query(OrganizationMembership).filter_by(id=membership_id).first()
            if membership:
                session.delete(membership)
                session.commit()
                logger.info(f"Deleted membership record {membership_id}")

    return {"status": "success", "event_processed": event_type}

# ==========================================
# 3. Stripe Webhook Receiver Endpoint
# ==========================================
@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """
    Receives events from Stripe to synchronize subscriptions, payments, and seat updates.
    """
    body = await request.body()
    
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    event = None
    
    from config import settings
    is_mock = settings.authentication_backend == "mock"
    
    if not webhook_secret and not is_mock:
        logger.error("STRIPE_WEBHOOK_SECRET environment variable is missing in production. Rejecting Stripe webhook.")
        raise HTTPException(status_code=500, detail="Webhook configuration error")
        
    try:
        if webhook_secret and stripe_signature:
            import stripe
            event = stripe.Webhook.construct_event(
                payload=body,
                sig_header=stripe_signature,
                secret=webhook_secret
            )
        elif is_mock:
            # Parse directly in mock/testing environments
            event = json.loads(body.decode())
        else:
            logger.error("Stripe signature missing in production. Rejecting Stripe webhook.")
            raise HTTPException(status_code=400, detail="Missing signature")
    except Exception as e:
        logger.warning(f"Stripe webhook parsing failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook request")
        
    event_type = event.get("type") if isinstance(event, dict) else getattr(event, "type", None)
    event_data = event.get("data", {}).get("object", {}) if isinstance(event, dict) else getattr(getattr(event, "data", {}), "object", {})
    
    logger.info(f"Received Stripe Webhook: {event_type}")
    
    # 1. Handle completed subscription checkouts
    if event_type == "checkout.session.completed":
        org_id = event_data.get("client_reference_id") or event_data.get("metadata", {}).get("org_id")
        sub_id = event_data.get("subscription")
        customer_id = event_data.get("customer")
        plan = event_data.get("metadata", {}).get("plan", "pro")
        
        if org_id and sub_id:
            sync_data = {
                "org_id": org_id,
                "customer_id": customer_id,
                "plan": plan,
                "status": "active",
                "seats": 1 # Default starting seat
            }
            StripeBillingService.sync_stripe_subscription(sub_id, sync_data)
            logger.info(f"Successfully processed checkout for Org {org_id} (Subscription: {sub_id})")

    # 2. Handle subscription modifications (seat scaling, plan changes)
    elif event_type in ("customer.subscription.created", "customer.subscription.updated"):
        sub_id = event_data.get("id")
        customer_id = event_data.get("customer")
        status = event_data.get("status", "active")
        
        # Read seats from quantity of the first subscription item
        items = event_data.get("items", {}).get("data", [])
        seats = items[0].get("quantity", 1) if items else 1
        
        # Read metadata for org mapping
        metadata = event_data.get("metadata", {})
        org_id = metadata.get("org_id")
        plan = metadata.get("plan", "pro")
        
        trial_start = event_data.get("trial_start")
        trial_end = event_data.get("trial_end")
        period_end = event_data.get("current_period_end")
        
        # Format timestamps
        dt_trial_start = datetime.fromtimestamp(trial_start, tz=timezone.utc).replace(tzinfo=None) if trial_start else None
        dt_trial_end = datetime.fromtimestamp(trial_end, tz=timezone.utc).replace(tzinfo=None) if trial_end else None
        dt_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc).replace(tzinfo=None) if period_end else None
        
        if not org_id:
            # Lookup org_id by customer_id if metadata is absent
            with get_db_session() as session:
                sub = session.query(Subscription).filter_by(customer_id=customer_id).first()
                if sub:
                    org_id = sub.org_id
                    
        if org_id:
            sync_data = {
                "org_id": org_id,
                "customer_id": customer_id,
                "plan": plan,
                "status": status,
                "seats": seats,
                "trial_start": dt_trial_start,
                "trial_end": dt_trial_end,
                "current_period_end": dt_period_end
            }
            StripeBillingService.sync_stripe_subscription(sub_id, sync_data)

    # 3. Handle subscription cancellations / delinquencies
    elif event_type == "customer.subscription.deleted":
        sub_id = event_data.get("id")
        customer_id = event_data.get("customer")
        
        with get_db_session() as session:
            sub = session.query(Subscription).filter_by(id=sub_id).first()
            if sub:
                sub.status = "canceled"
                sub.plan = "free" # Downgrade automatically to free plan limits
                session.commit()
                logger.info(f"Canceled subscription {sub_id} and downgraded Org {sub.org_id} to Free.")

    return {"status": "success", "event_processed": event_type}

import os
