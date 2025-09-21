from typing import Optional, Annotated

import sqlalchemy
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter, Request
from fastapi import Depends, status

from ..exceptions import (
    admin_not_found_error, admin_already_exists_error,
    ConflictError, ValidationError, ServerError,
    UnauthorizedError, ForbiddenError
)
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate

from app.db import Session, crud
from app.db.models import Admin as DBAdmin, Service, User
from app.dependencies import AdminDep, SudoAdminDep, DBDep
from app.wildosnode.operations import update_user
from app.models.admin import (
    Admin,
    AdminCreate,
    AdminInDB,
    Token,
    AdminPartialModify,
    AdminResponse,
)
from app.models.service import ServiceResponse
from app.models.user import UserResponse
from app.utils.auth import create_admin_token
from app.security.guards import RequireSudoAdmin, security_guard
from app.middleware.validation import StrictAdminCreateRequest
from app.middleware.proxy_headers import get_client_ip
from app.security.security_logger import SecurityEventType, security_logger

router = APIRouter(tags=["Admin"], prefix="/admins")


def authenticate_admin(
    db: Session, username: str, password: str
) -> Optional[Admin]:
    dbadmin = crud.get_admin(db, username)
    if not dbadmin:
        return None

    return (
        dbadmin
        if AdminInDB.model_validate(dbadmin).verify_password(password)
        else None
    )


@router.get("", response_model=Page[AdminResponse])
def get_admins(db: DBDep, admin: SudoAdminDep, username: str | None = None):
    query = select(DBAdmin)
    if username:
        query = query.where(DBAdmin.username.ilike(f"%{username}%"))
    return paginate(db, query)


@router.post("", response_model=Admin)
def create_admin(
    new_admin: StrictAdminCreateRequest, 
    db: DBDep, 
    admin: Annotated[Admin, RequireSudoAdmin("create", "admin")],
    request: Request
):
    """Create a new admin with enhanced security validation"""
    client_ip = get_client_ip(request)
    
    # Log admin creation attempt
    security_logger.log_security_event(
        event_type=SecurityEventType.AUTHENTICATION_SUCCESS,
        details={
            "operation": "create_admin",
            "target_username": new_admin.username,
            "created_by": admin.username,
            "is_sudo_creation": new_admin.is_sudo
        },
        severity="INFO" if not new_admin.is_sudo else "WARNING",
        ip_address=client_ip,
        user_id=admin.id
    )
    
    try:
        # Convert strict request to AdminCreate model
        admin_create = AdminCreate(
            username=new_admin.username,
            password=new_admin.password,
            is_sudo=new_admin.is_sudo,
            enabled=new_admin.enabled,
            service_ids=new_admin.service_ids
        )
        
        dbadmin = crud.create_admin(db, admin_create)
        
        # Log successful creation
        security_logger.log_security_event(
            event_type=SecurityEventType.AUTHENTICATION_SUCCESS,
            details={
                "operation": "admin_created",
                "new_admin_id": dbadmin.id,
                "new_username": dbadmin.username,
                "created_by": admin.username
            },
            severity="INFO",
            ip_address=client_ip,
            user_id=admin.id
        )
        
        return dbadmin
        
    except IntegrityError:
        db.rollback()
        
        # Log failed creation attempt
        security_logger.log_security_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            details={
                "operation": "admin_creation_failed",
                "reason": "Admin already exists",
                "attempted_username": new_admin.username,
                "created_by": admin.username
            },
            severity="WARNING",
            ip_address=client_ip,
            user_id=admin.id
        )
        
        raise admin_already_exists_error()


@router.get("/current", response_model=Admin)
def get_current_admin(admin: AdminDep):
    return admin


@router.get("/current/token")
def get_current_admin_token(admin: AdminDep):
    """Get current admin's access token"""
    token = create_admin_token(admin.username, is_sudo=admin.is_sudo)
    return {"token": token}


@router.post("/token", response_model=Token)
def admin_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DBDep
):
    if dbadmin := authenticate_admin(
        db, form_data.username, form_data.password
    ):
        return Token(
            is_sudo=dbadmin.is_sudo,
            access_token=create_admin_token(
                form_data.username, is_sudo=dbadmin.is_sudo
            ),
        )

    raise UnauthorizedError(
        "Incorrect username or password", 
        "INVALID_CREDENTIALS"
    )


@router.get("/{username}", response_model=AdminResponse)
def get_admin(
    username: str,
    db: DBDep,
    admin: SudoAdminDep,
):
    dbadmin = crud.get_admin(db, username)
    if not dbadmin:
        raise admin_not_found_error()
    return dbadmin


@router.put("/{username}", response_model=AdminResponse)
def modify_admin(
    username: str,
    modified_admin: AdminPartialModify,
    db: DBDep,
    admin: SudoAdminDep,
):
    dbadmin = crud.get_admin(db, username)
    if not dbadmin:
        raise admin_not_found_error()

    # If a sudoer admin wants to edit another sudoer
    if username != admin.username and bool(getattr(dbadmin, 'is_sudo', False)):
        raise ForbiddenError(
            "You're not allowed to edit another sudoers account. Use wildosvpn-cli instead.",
            "CANNOT_EDIT_SUDO_ADMIN"
        )

    dbadmin = crud.update_admin(db, dbadmin, modified_admin)
    return dbadmin


@router.get("/{username}/services", response_model=Page[ServiceResponse])
def get_admin_services(username: str, db: DBDep, admin: SudoAdminDep):
    """
    Get user services
    """
    db_admin = crud.get_admin(db, username)
    if not db_admin:
        raise admin_not_found_error()

    if bool(getattr(db_admin, 'is_sudo', False)) or bool(getattr(db_admin, 'all_services_access', False)):
        query = select(Service)
    else:
        query = (
            select(Service)
            .join(Service.admins)
            .where(DBAdmin.id == db_admin.id)
        )

    return paginate(db, query)


@router.get("/{username}/users", response_model=Page[UserResponse])
def get_admin_users(username: str, db: DBDep, admin: SudoAdminDep):
    """
    Get user services
    """
    db_admin = crud.get_admin(db, username)
    if not db_admin:
        raise admin_not_found_error()

    query = select(User).where(User.admin_id == db_admin.id)

    return paginate(db, query)


@router.post("/{username}/disable_users", response_model=AdminResponse)
async def disable_users(username: str, db: DBDep, admin: SudoAdminDep):
    db_admin = crud.get_admin(db, username)
    if not db_admin:
        raise admin_not_found_error()

    if bool(getattr(db_admin, 'is_sudo', False)) and getattr(db_admin, 'username', '') != admin.username:
        raise ForbiddenError(
            "You're not allowed.",
            "ACCESS_DENIED"
        )

    for user in crud.get_users(db, admin=db_admin, enabled=True):
        if bool(getattr(user, 'activated', False)):
            update_user(user, remove=True)
        setattr(user, 'enabled', False)
        setattr(user, 'activated', False)
    db.commit()

    return db_admin


@router.post("/{username}/enable_users", response_model=AdminResponse)
async def enable_users(username: str, db: DBDep, admin: SudoAdminDep):
    db_admin = crud.get_admin(db, username)
    if not db_admin:
        raise admin_not_found_error()

    if bool(getattr(db_admin, 'is_sudo', False)) and getattr(db_admin, 'username', '') != admin.username:
        raise ForbiddenError(
            "You're not allowed.",
            "ACCESS_DENIED"
        )

    for user in crud.get_users(db, admin=db_admin, enabled=False):
        setattr(user, 'enabled', True)
        if bool(getattr(user, 'is_active', False)):
            update_user(user)
            setattr(user, 'activated', True)
    db.commit()

    return db_admin


@router.delete("/{username}")
def remove_admin(username: str, db: DBDep, admin: SudoAdminDep):
    dbadmin = crud.get_admin(db, username)
    if not dbadmin:
        raise admin_not_found_error()

    if bool(getattr(dbadmin, 'is_sudo', False)):
        raise ForbiddenError(
            "You're not allowed to delete sudoers accounts. Use wildosvpn-cli instead.",
            "CANNOT_DELETE_SUDO_ADMIN"
        )

    crud.remove_admin(db, dbadmin)
    return {}
