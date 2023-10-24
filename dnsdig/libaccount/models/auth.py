from enum import Enum
from typing import List, Any, Dict

from pydantic import BaseModel, constr

from dnsdig.libshared.models import BaseRequestResponse


class Permissions(str, Enum):
    ReadResolver = "read:resolver"
    WriteResolver = "write:resolver"


class Roles(str, Enum):
    Resolver = "resolver"
    Admin = "admin"


class RoleAndPermissions(BaseModel):
    role: Roles
    permissions: List[Permissions]


resolver_role = RoleAndPermissions(role=Roles.Resolver, permissions=[Permissions.ReadResolver])
admin_role = RoleAndPermissions(role=Roles.Admin, permissions=[Permissions.ReadResolver, Permissions.WriteResolver])


class LoginUrlRequest(BaseRequestResponse):
    state: constr(min_length=8) | None = None
    store: Dict[str, Any] | None = None


class CreateApplicationRequest(BaseRequestResponse):
    name: str
    description: str | None = None
    website: str | None = None


class ClientCredentialsRequest(BaseRequestResponse):
    client_id: str
    client_secret: str
    grant_type: str = "client_credentials"
