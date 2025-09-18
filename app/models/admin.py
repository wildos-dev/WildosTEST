from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import ConfigDict, BaseModel

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/admins/token"
)  # Admin view url


class Token(BaseModel):
    access_token: str
    is_sudo: bool
    token_type: str = "bearer"


class Admin(BaseModel):
    id: int | None = None
    username: str
    is_sudo: bool
    enabled: bool = True
    all_services_access: bool = False
    modify_users_access: bool = True
    service_ids: list = []
    subscription_url_prefix: str = ""
    model_config = ConfigDict(from_attributes=True)


class AdminCreate(Admin):
    username: str
    password: str

    @property
    def hashed_password(self):
        return pwd_context.hash(self.password)


class AdminResponse(BaseModel):
    id: int
    username: str
    is_sudo: bool
    enabled: bool = True
    all_services_access: bool = False
    modify_users_access: bool = True
    service_ids: list = []
    subscription_url_prefix: str = ""
    users_data_usage: int
    model_config = ConfigDict(from_attributes=True)


class AdminModify(Admin):
    password: str
    is_sudo: bool

    @property
    def hashed_password(self):
        return (
            pwd_context.hash(self.password)
            if self.password is not None
            else None
        )


class AdminPartialModify(BaseModel):
    """Partial admin modification model with all optional fields"""
    
    id: int | None = None
    username: str | None = None
    password: str | None = None
    is_sudo: bool | None = None
    enabled: bool | None = None
    all_services_access: bool | None = None
    modify_users_access: bool | None = None
    service_ids: list | None = None
    subscription_url_prefix: str | None = None
    
    @property
    def hashed_password(self):
        return (
            pwd_context.hash(self.password)
            if self.password is not None
            else None
        )
    
    model_config = ConfigDict(from_attributes=True)


class AdminInDB(Admin):
    username: str
    hashed_password: str

    def verify_password(self, plain_password):
        return pwd_context.verify(plain_password, self.hashed_password)
