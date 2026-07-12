from typing import List, Optional
from fastapi import Header, HTTPException, status, Depends
from core.auth.security import decode_token
from core.database import get_db_session, User

def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header credentials."
        )
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token."
        )
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload."
        )

    with get_db_session() as session:
        user = session.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found."
            )
        return {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "is_verified": user.is_verified,
            "is_active": user.is_active
        }

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: dict = Depends(get_current_user)) -> dict:
        if not current_user.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated."
            )
        if current_user.get("role") not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for this user role."
            )
        return current_user


def log_auth_audit(event_type: str, user_id: str, details: str, org_id: str = None, workspace_id: str = None):
    from core.database import get_db_session, AuthAuditLogRecord
    with get_db_session() as session:
        log = AuthAuditLogRecord(
            event_type=event_type,
            user_id=user_id,
            details=details,
            org_id=org_id,
            workspace_id=workspace_id
        )
        session.add(log)
        session.commit()


class PermissionChecker:
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def __call__(self, current_user: dict = Depends(get_current_user)) -> dict:
        if not current_user.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated."
            )
        
        user_role = current_user.get("role")
        user_id = current_user.get("id")
        
        from core.database import get_db_session, RoleRecord, PermissionRecord, RolePermissionRecord
        
        with get_db_session() as session:
            role = session.query(RoleRecord).filter(RoleRecord.name == user_role).first()
            if not role:
                log_auth_audit(
                    event_type="ROLE_DENIED",
                    user_id=user_id,
                    details=f"User tried to access permission '{self.required_permission}' but has invalid role '{user_role}'"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Operation not permitted: invalid user role."
                )
            
            has_permission = session.query(PermissionRecord).join(
                RolePermissionRecord, RolePermissionRecord.permission_id == PermissionRecord.id
            ).filter(
                RolePermissionRecord.role_id == role.id,
                PermissionRecord.name == self.required_permission
            ).first() is not None
            
            if not has_permission:
                log_auth_audit(
                    event_type="ROLE_DENIED",
                    user_id=user_id,
                    details=f"Access denied: user role '{user_role}' lacks permission '{self.required_permission}'"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Operation not permitted. Required permission: '{self.required_permission}'"
                )
                
            return current_user
