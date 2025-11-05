from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class CoinType(str, Enum):
    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum"


class VaultStatus(str, Enum):
    SETUP = "setup"  # Initial setup, not all guardians joined
    ACTIVE = "active"  # All guardians joined, ready for transactions
    SUSPENDED = "suspended"  # Temporarily suspended
    ARCHIVED = "archived"  # No longer in use


class VaultCreate(BaseModel):
    """Request model for creating a new vault"""
    name: str = Field(..., min_length=1, max_length=100)
    coin_type: CoinType
    threshold: int = Field(..., ge=2, le=10)
    total_guardians: int = Field(..., ge=2, le=15)
    account_index: int = Field(default=0, ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Company Treasury",
                "coin_type": "bitcoin",
                "threshold": 3,
                "total_guardians": 5,
                "account_index": 0
            }
        }


class Vault(BaseModel):
    """Vault model"""
    vault_id: str
    name: str
    coin_type: CoinType
    threshold: int
    total_guardians: int
    account_index: int
    status: VaultStatus = VaultStatus.SETUP

    # Extended public key (xpub) - set after guardian setup
    xpub: Optional[str] = None
    xpub_chain_code: Optional[str] = None

    # Guardian tracking
    guardians_joined: int = 0
    guardian_ids: List[str] = []

    # Statistics
    total_transactions: int = 0
    total_addresses_generated: int = 0

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "vault_id": "vault_abc123",
                "name": "Company Treasury",
                "coin_type": "bitcoin",
                "threshold": 3,
                "total_guardians": 5,
                "account_index": 0,
                "status": "active",
                "guardians_joined": 5,
                "guardian_ids": ["guard_1", "guard_2", "guard_3", "guard_4", "guard_5"],
                "total_transactions": 42,
                "total_addresses_generated": 150
            }
        }


class VaultUpdate(BaseModel):
    """Update vault details"""
    name: Optional[str] = None
    status: Optional[VaultStatus] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Treasury Name",
                "status": "active"
            }
        }


class VaultResponse(Vault):
    """Response model for vault (includes computed fields)"""
    is_setup_complete: bool = False

    @classmethod
    def from_vault(cls, vault: Vault):
        data = vault.model_dump()
        data["is_setup_complete"] = vault.guardians_joined >= vault.total_guardians
        return cls(**data)
