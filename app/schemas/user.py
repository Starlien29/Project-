from pydantic import BaseModel
from app.models.user import UserRole


class UserCreate(BaseModel):
    email: str
    university_id: str
    password: str


class UserLogin(BaseModel):
    email: str | None = None
    university_id: str | None = None
    password: str

    def get_identifier(self) -> str | None:
        return self.email or self.university_id


class UserResponse(BaseModel):
    id: int
    email: str
    university_id: str
    role: UserRole
    created_at: str | None = None

    class Config:
        from_attributes = True


class UserRoleUpdate(BaseModel):
    role: UserRole
