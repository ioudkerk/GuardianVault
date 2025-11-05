from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class GuardianStatus(str, Enum):
    INVITED = "invited"  # Invitation sent, not yet joined
    ACTIVE = "active"  # Joined and active
    INACTIVE = "inactive"  # Temporarily inactive
    REMOVED = "removed"  # Removed from vault


class GuardianInvite(BaseModel):
    """Request model for inviting a guardian"""
    vault_id: str
    name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[str] = "Guardian"

    class Config:
        json_schema_extra = {
            "example": {
                "vault_id": "vault_abc123",
                "name": "John Smith",
                "email": "john@company.com",
                "role": "CFO"
            }
        }


class Guardian(BaseModel):
    """Guardian model"""
    guardian_id: str
    vault_id: str
    name: str
    email: Optional[EmailStr] = None
    role: Optional[str] = "Guardian"

    # Invitation
    invitation_code: str
    invitation_sent_at: datetime = Field(default_factory=datetime.utcnow)
    invitation_accepted_at: Optional[datetime] = None

    # Status
    status: GuardianStatus = GuardianStatus.INVITED

    # Share information (NEVER store actual share, only metadata)
    has_share: bool = False
    share_id: Optional[int] = None  # Which share number (1, 2, 3, etc.)

    # Statistics
    total_signatures: int = 0
    last_signature_at: Optional[datetime] = None
    last_active_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "guardian_id": "guard_abc123",
                "vault_id": "vault_abc123",
                "name": "John Smith",
                "email": "john@company.com",
                "role": "CFO",
                "invitation_code": "INVITE-ABC-123-XYZ",
                "status": "active",
                "has_share": True,
                "share_id": 1,
                "total_signatures": 15
            }
        }


class GuardianJoin(BaseModel):
    """Request model for guardian joining with invitation code"""
    invitation_code: str
    device_info: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "invitation_code": "INVITE-ABC-123-XYZ",
                "device_info": "MacBook Pro - Chrome"
            }
        }


class GuardianUpdate(BaseModel):
    """Update guardian details"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    status: Optional[GuardianStatus] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Smith",
                "role": "CFO",
                "status": "active"
            }
        }


class GuardianResponse(Guardian):
    """Response model for guardian"""
    is_setup_complete: bool = False

    @classmethod
    def from_guardian(cls, guardian: Guardian):
        data = guardian.model_dump()
        data["is_setup_complete"] = guardian.status == GuardianStatus.ACTIVE and guardian.has_share
        return cls(**data)
