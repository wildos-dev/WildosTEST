import sqlalchemy
from fastapi import APIRouter, Query, Request
from ..exceptions import BadRequestError, ForbiddenError, ConflictError
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination.links import Page

from app import wildosnode
from app.db import crud
from app.db.models import Service, User, Inbound
from app.dependencies import DBDep, AdminDep, SudoAdminDep, ServiceDep
from app.models.proxy import Inbound as InboundResponse
from app.models.service import ServiceCreate, ServiceModify, ServiceResponse
from app.models.user import UserResponse
from app.middleware.validation import StrictServiceCreateRequest
from app.middleware.proxy_headers import get_client_ip
from app.security.security_logger import SecurityEventType, security_logger

router = APIRouter(prefix="/services", tags=["Service"])


@router.get("", response_model=Page[ServiceResponse])
def get_services(db: DBDep, admin: AdminDep, name: str = Query(None)):
    query = db.query(Service)

    if name:
        query = query.filter(Service.name.ilike(f"%{name}%"))

    if not admin.is_sudo and not admin.all_services_access:
        query = query.filter(Service.id.in_(admin.service_ids))

    return paginate(query)


@router.post("", response_model=ServiceResponse)
def add_service(
    new_service: StrictServiceCreateRequest, 
    db: DBDep, 
    admin: SudoAdminDep,
    request: Request
):
    """
    Add a new service with enhanced security validation

    - **name** service name
    - **inbounds** list of inbound configurations
    """
    client_ip = get_client_ip(request)
    
    # Log service creation attempt
    security_logger.log_security_event(
        event_type=SecurityEventType.AUTHENTICATION_SUCCESS,
        details={
            "operation": "create_service",
            "target_service": new_service.name,
            "created_by": admin.username,
            "inbounds_count": len(new_service.inbounds) if new_service.inbounds else 0
        },
        severity="INFO",
        ip_address=client_ip,
        user_id=admin.id
    )
    
    try:
        # Extract inbound IDs from inbound dictionaries with validation
        inbound_ids = []
        for i, inbound in enumerate(new_service.inbounds):
            if 'id' not in inbound:
                # Log security event for invalid payload
                security_logger.log_security_event(
                    event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                    details={
                        "operation": "service_creation_invalid_payload",
                        "reason": f"Inbound at index {i} missing required 'id' field",
                        "service_name": new_service.name,
                        "created_by": admin.username,
                        "inbound_data": str(inbound)[:200]  # Truncated for security
                    },
                    severity="WARNING",
                    ip_address=client_ip,
                    user_id=admin.id
                )
                raise BadRequestError(
                    f"Inbound at index {i} missing required 'id' field",
                    "MISSING_INBOUND_ID"
                )
            
            try:
                inbound_id = int(inbound['id'])
                if inbound_id <= 0:
                    raise ValueError("ID must be positive")
                inbound_ids.append(inbound_id)
            except (ValueError, TypeError) as e:
                # Log security event for invalid ID format
                security_logger.log_security_event(
                    event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                    details={
                        "operation": "service_creation_invalid_id",
                        "reason": f"Invalid inbound ID at index {i}: {str(e)}",
                        "service_name": new_service.name,
                        "created_by": admin.username,
                        "invalid_id": str(inbound.get('id', 'missing'))[:50]
                    },
                    severity="WARNING",
                    ip_address=client_ip,
                    user_id=admin.id
                )
                raise BadRequestError(
                    f"Invalid inbound ID at index {i}: must be a positive integer",
                    "INVALID_INBOUND_ID"
                )
        
        # Convert strict request to ServiceCreate model
        service_create = ServiceCreate(
            name=new_service.name,
            inbound_ids=inbound_ids
        )
        
        service = crud.create_service(db, service_create)
        
        # Log successful creation
        security_logger.log_security_event(
            event_type=SecurityEventType.AUTHENTICATION_SUCCESS,
            details={
                "operation": "service_created",
                "new_service_id": service.id,
                "new_service_name": service.name,
                "created_by": admin.username
            },
            severity="INFO",
            ip_address=client_ip,
            user_id=admin.id
        )
        
        return service
        
    except sqlalchemy.exc.IntegrityError:
        db.rollback()
        
        # Log failed creation attempt
        security_logger.log_security_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            details={
                "operation": "service_creation_failed",
                "reason": "Service already exists",
                "attempted_name": new_service.name,
                "created_by": admin.username
            },
            severity="WARNING",
            ip_address=client_ip,
            user_id=admin.id
        )
        
        raise ConflictError(
            "Service by this name already exists",
            "SERVICE_NAME_EXISTS"
        )


@router.get("/{id}", response_model=ServiceResponse)
def get_service(service: ServiceDep, db: DBDep, admin: AdminDep):
    """
    Get Service information with id
    """
    if not (
        admin.is_sudo or admin.all_services_access or service.id in admin.service_ids
    ):
        raise ForbiddenError(
            "You're not allowed",
            "ACCESS_DENIED"
        )

    return service


@router.get("/{id}/users", response_model=Page[UserResponse])
def get_service_users(service: ServiceDep, db: DBDep, admin: SudoAdminDep):
    """
    Get service users
    """
    query = (
        db.query(User)
        .join(User.services)
        .where(Service.id == service.id)
        .filter(User.removed != True)
    )

    return paginate(query)


@router.get("/{id}/inbounds", response_model=Page[InboundResponse])
def get_service_inbounds(service: ServiceDep, db: DBDep, admin: SudoAdminDep):
    """
    Get service inbounds
    """
    query = (
        db.query(Inbound)
        .join(Service.inbounds)
        .where(Service.id == service.id)
    )

    return paginate(query)


@router.put("/{id}", response_model=ServiceResponse)
async def modify_service(
    service: ServiceDep,
    modification: ServiceModify,
    db: DBDep,
    admin: SudoAdminDep,
):
    """
    Modify Service

    - **name** can be up to 64 characters
    - **inbounds** list of inbound ids. if not specified no change will be applied;
    in case of an empty list all inbounds would be removed.
    """
    old_inbounds = {(i.node_id, i.protocol, i.tag) for i in service.inbounds}
    try:
        response = crud.update_service(db, service, modification)
    except sqlalchemy.exc.IntegrityError:
        db.rollback()
        raise ConflictError(
            "Problem updating the service",
            "SERVICE_UPDATE_ERROR"
        )
    else:
        for user in response.users:
            if user.activated:
                wildosnode.operations.update_user(
                    user, old_inbounds=old_inbounds
                )
        return response


@router.delete("/{id}")
def remove_service(service: ServiceDep, db: DBDep, admin: SudoAdminDep):
    crud.remove_service(db, service)
    return dict()
