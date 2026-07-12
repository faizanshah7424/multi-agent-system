from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from core.database import get_db_session, User, RoleRecord, PermissionRecord, RolePermissionRecord, AuthAuditLogRecord
from core.auth.dependencies import PermissionChecker, log_auth_audit

router = APIRouter(prefix="/admin", tags=["Admin Panel"])

class UserUpdateSchema(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None

class RolePermissionsUpdateSchema(BaseModel):
    permission_names: List[str]

@router.get("/users")
def get_users(current_user: dict = Depends(PermissionChecker("users:read"))):
    with get_db_session() as session:
        users = session.query(User).all()
        return [
            {
                "id": u.id,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "is_verified": u.is_verified,
                "created_at": u.created_at
            }
            for u in users
        ]

@router.put("/users/{user_id}")
def update_user(
    user_id: str,
    payload: UserUpdateSchema,
    current_user: dict = Depends(PermissionChecker("users:write"))
):
    user_data = None
    changes = []
    with get_db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        
        user_email = user.email
        
        if payload.role is not None and payload.role != user.role:
            role_exists = session.query(RoleRecord).filter(RoleRecord.name == payload.role).first() is not None
            if not role_exists:
                raise HTTPException(status_code=400, detail=f"Role '{payload.role}' does not exist.")
            changes.append(f"role from '{user.role}' to '{payload.role}'")
            user.role = payload.role
            
        if payload.is_active is not None and payload.is_active != user.is_active:
            changes.append(f"is_active from '{user.is_active}' to '{payload.is_active}'")
            user.is_active = payload.is_active
            
        if changes:
            session.commit()
            
        user_data = {
            "id": user.id,
            "email": user_email,
            "role": user.role,
            "is_active": user.is_active
        }
            
    if changes:
        log_auth_audit(
            event_type="USER_UPDATED",
            user_id=current_user["id"],
            details=f"Admin {current_user['email']} updated user {user_email}: {', '.join(changes)}"
        )
        
    return {
        "message": "User updated successfully.",
        "user": user_data
    }

@router.get("/roles")
def get_roles(current_user: dict = Depends(PermissionChecker("roles:read"))):
    with get_db_session() as session:
        roles = session.query(RoleRecord).all()
        result = []
        for r in roles:
            perms = session.query(PermissionRecord).join(
                RolePermissionRecord, RolePermissionRecord.permission_id == PermissionRecord.id
            ).filter(RolePermissionRecord.role_id == r.id).all()
            
            result.append({
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "created_at": r.created_at,
                "permissions": [p.name for p in perms]
            })
        return result

@router.get("/permissions")
def get_permissions(current_user: dict = Depends(PermissionChecker("roles:read"))):
    with get_db_session() as session:
        perms = session.query(PermissionRecord).all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description
            }
            for p in perms
        ]

@router.post("/roles/{role_id}/permissions")
def update_role_permissions(
    role_id: str,
    payload: RolePermissionsUpdateSchema,
    current_user: dict = Depends(PermissionChecker("roles:write"))
):
    with get_db_session() as session:
        role = session.query(RoleRecord).filter(RoleRecord.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found.")
            
        role_name = role.name
        
        db_perms = session.query(PermissionRecord).filter(PermissionRecord.name.in_(payload.permission_names)).all()
        if len(db_perms) != len(payload.permission_names):
            raise HTTPException(status_code=400, detail="One or more permissions are invalid.")
            
        session.query(RolePermissionRecord).filter(RolePermissionRecord.role_id == role.id).delete()
        
        for p in db_perms:
            session.add(RolePermissionRecord(role_id=role.id, permission_id=p.id))
            
        session.commit()
        
    log_auth_audit(
        event_type="ROLE_PERMISSIONS_UPDATED",
        user_id=current_user["id"],
        details=f"Admin {current_user['email']} updated permissions for role '{role_name}' to: {payload.permission_names}"
    )
    return {"message": f"Permissions updated successfully for role '{role_name}'."}

@router.get("/audit-logs")
def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(PermissionChecker("audit:read"))
):
    with get_db_session() as session:
        logs = session.query(AuthAuditLogRecord).order_by(AuthAuditLogRecord.timestamp.desc()).limit(limit).offset(offset).all()
        return [
            {
                "id": log.id,
                "event_type": log.event_type,
                "user_id": log.user_id,
                "details": log.details,
                "timestamp": log.timestamp
            }
            for log in logs
        ]
