from fastapi import APIRouter, HTTPException, status
from typing import List
import shortuuid
from datetime import datetime

from ..database import get_database
from ..models.vault import (
    VaultCreate,
    Vault,
    VaultUpdate,
    VaultResponse,
    VaultStatus,
)

router = APIRouter()


@router.post("", response_model=VaultResponse, status_code=status.HTTP_201_CREATED)
async def create_vault(vault_create: VaultCreate):
    """Create a new vault"""
    db = get_database()

    # Validate threshold
    if vault_create.threshold > vault_create.total_guardians:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Threshold cannot exceed total guardians",
        )

    # Generate vault ID
    vault_id = f"vault_{shortuuid.uuid()[:12]}"

    # Create vault document
    vault = Vault(
        vault_id=vault_id,
        name=vault_create.name,
        coin_type=vault_create.coin_type,
        threshold=vault_create.threshold,
        total_guardians=vault_create.total_guardians,
        account_index=vault_create.account_index,
        status=VaultStatus.SETUP,
    )

    # Insert into database
    await db.vaults.insert_one(vault.model_dump())

    return VaultResponse.from_vault(vault)


@router.get("", response_model=List[VaultResponse])
async def list_vaults(
    status: VaultStatus | None = None,
    coin_type: str | None = None,
    skip: int = 0,
    limit: int = 100,
):
    """List all vaults with optional filters"""
    db = get_database()

    # Build query
    query = {}
    if status:
        query["status"] = status
    if coin_type:
        query["coin_type"] = coin_type

    # Fetch vaults
    cursor = db.vaults.find(query).skip(skip).limit(limit).sort("created_at", -1)
    vaults = await cursor.to_list(length=limit)

    return [VaultResponse.from_vault(Vault(**v)) for v in vaults]


@router.get("/{vault_id}", response_model=VaultResponse)
async def get_vault(vault_id: str):
    """Get vault by ID"""
    db = get_database()

    vault_doc = await db.vaults.find_one({"vault_id": vault_id})
    if not vault_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vault {vault_id} not found",
        )

    vault = Vault(**vault_doc)
    return VaultResponse.from_vault(vault)


@router.patch("/{vault_id}", response_model=VaultResponse)
async def update_vault(vault_id: str, vault_update: VaultUpdate):
    """Update vault details"""
    db = get_database()

    # Check vault exists
    existing = await db.vaults.find_one({"vault_id": vault_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vault {vault_id} not found",
        )

    # Build update document
    update_data = vault_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    update_data["updated_at"] = datetime.utcnow()

    # Update vault
    await db.vaults.update_one(
        {"vault_id": vault_id},
        {"$set": update_data},
    )

    # Fetch updated vault
    updated = await db.vaults.find_one({"vault_id": vault_id})
    vault = Vault(**updated)
    return VaultResponse.from_vault(vault)


@router.delete("/{vault_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vault(vault_id: str):
    """Delete a vault (archives it)"""
    db = get_database()

    # Check vault exists
    existing = await db.vaults.find_one({"vault_id": vault_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vault {vault_id} not found",
        )

    # Archive instead of delete
    await db.vaults.update_one(
        {"vault_id": vault_id},
        {
            "$set": {
                "status": VaultStatus.ARCHIVED,
                "updated_at": datetime.utcnow(),
            }
        },
    )


@router.post("/{vault_id}/activate", response_model=VaultResponse)
async def activate_vault(vault_id: str):
    """Activate a vault (after all guardians joined)"""
    db = get_database()

    vault_doc = await db.vaults.find_one({"vault_id": vault_id})
    if not vault_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vault {vault_id} not found",
        )

    vault = Vault(**vault_doc)

    # Check if all guardians joined
    if vault.guardians_joined < vault.total_guardians:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot activate: {vault.guardians_joined}/{vault.total_guardians} guardians joined",
        )

    # Activate vault
    await db.vaults.update_one(
        {"vault_id": vault_id},
        {
            "$set": {
                "status": VaultStatus.ACTIVE,
                "updated_at": datetime.utcnow(),
            }
        },
    )

    # Fetch updated vault
    updated = await db.vaults.find_one({"vault_id": vault_id})
    vault = Vault(**updated)
    return VaultResponse.from_vault(vault)


@router.get("/{vault_id}/stats")
async def get_vault_stats(vault_id: str):
    """Get vault statistics"""
    db = get_database()

    # Check vault exists
    vault_doc = await db.vaults.find_one({"vault_id": vault_id})
    if not vault_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vault {vault_id} not found",
        )

    # Get guardians count
    guardians_count = await db.guardians.count_documents({"vault_id": vault_id})
    active_guardians = await db.guardians.count_documents(
        {"vault_id": vault_id, "status": "active"}
    )

    # Get transactions stats
    total_txs = await db.transactions.count_documents({"vault_id": vault_id})
    pending_txs = await db.transactions.count_documents(
        {"vault_id": vault_id, "status": "pending"}
    )
    completed_txs = await db.transactions.count_documents(
        {"vault_id": vault_id, "status": "completed"}
    )

    return {
        "vault_id": vault_id,
        "guardians": {
            "total": guardians_count,
            "active": active_guardians,
            "required": vault_doc["threshold"],
        },
        "transactions": {
            "total": total_txs,
            "pending": pending_txs,
            "completed": completed_txs,
            "failed": total_txs - pending_txs - completed_txs,
        },
    }
