from fastapi import APIRouter, HTTPException, status
from typing import List
import shortuuid
from datetime import datetime

from ..database import get_database
from ..models.guardian import (
    GuardianInvite,
    Guardian,
    GuardianJoin,
    GuardianUpdate,
    GuardianResponse,
    GuardianStatus,
)
from ..models.vault import Vault

router = APIRouter()


def generate_invitation_code() -> str:
    """Generate a unique invitation code"""
    return f"INVITE-{shortuuid.ShortUUID().random(length=12).upper()}"


@router.post("/invite", response_model=GuardianResponse, status_code=status.HTTP_201_CREATED)
async def invite_guardian(invite: GuardianInvite):
    """Invite a new guardian to a vault"""
    db = get_database()

    # Check vault exists
    vault_doc = await db.vaults.find_one({"vault_id": invite.vault_id})
    if not vault_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vault {invite.vault_id} not found",
        )

    vault = Vault(**vault_doc)

    # Check if vault is full
    if vault.guardians_joined >= vault.total_guardians:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vault already has maximum guardians ({vault.total_guardians})",
        )

    # Generate guardian ID and invitation code
    guardian_id = f"guard_{shortuuid.uuid()[:12]}"
    invitation_code = generate_invitation_code()

    # Determine share_id (next available)
    share_id = vault.guardians_joined + 1

    # Create guardian
    guardian = Guardian(
        guardian_id=guardian_id,
        vault_id=invite.vault_id,
        name=invite.name,
        email=invite.email,
        role=invite.role,
        invitation_code=invitation_code,
        status=GuardianStatus.INVITED,
        share_id=share_id,
    )

    # Insert guardian
    await db.guardians.insert_one(guardian.model_dump())

    # Update vault guardian count
    await db.vaults.update_one(
        {"vault_id": invite.vault_id},
        {
            "$inc": {"guardians_joined": 1},
            "$push": {"guardian_ids": guardian_id},
            "$set": {"updated_at": datetime.utcnow()},
        },
    )

    return GuardianResponse.from_guardian(guardian)


@router.post("/join", response_model=GuardianResponse)
async def join_as_guardian(join: GuardianJoin):
    """Guardian joins with invitation code"""
    db = get_database()

    # Find guardian by invitation code
    guardian_doc = await db.guardians.find_one(
        {"invitation_code": join.invitation_code}
    )
    if not guardian_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invitation code",
        )

    guardian = Guardian(**guardian_doc)

    # Check if already joined
    if guardian.status == GuardianStatus.ACTIVE:
        return GuardianResponse.from_guardian(guardian)

    # Update guardian status
    await db.guardians.update_one(
        {"guardian_id": guardian.guardian_id},
        {
            "$set": {
                "status": GuardianStatus.ACTIVE,
                "invitation_accepted_at": datetime.utcnow(),
                "last_active_at": datetime.utcnow(),
                "has_share": True,  # Assume share setup complete
                "updated_at": datetime.utcnow(),
            }
        },
    )

    # Fetch updated guardian
    updated = await db.guardians.find_one({"guardian_id": guardian.guardian_id})
    guardian = Guardian(**updated)

    return GuardianResponse.from_guardian(guardian)


@router.get("/", response_model=List[GuardianResponse])
async def list_guardians(
    vault_id: str | None = None,
    status: GuardianStatus | None = None,
    skip: int = 0,
    limit: int = 100,
):
    """List guardians with optional filters"""
    db = get_database()

    # Build query
    query = {}
    if vault_id:
        query["vault_id"] = vault_id
    if status:
        query["status"] = status

    # Fetch guardians
    cursor = db.guardians.find(query).skip(skip).limit(limit).sort("created_at", -1)
    guardians = await cursor.to_list(length=limit)

    return [GuardianResponse.from_guardian(Guardian(**g)) for g in guardians]


@router.get("/{guardian_id}", response_model=GuardianResponse)
async def get_guardian(guardian_id: str):
    """Get guardian by ID"""
    db = get_database()

    guardian_doc = await db.guardians.find_one({"guardian_id": guardian_id})
    if not guardian_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guardian {guardian_id} not found",
        )

    guardian = Guardian(**guardian_doc)
    return GuardianResponse.from_guardian(guardian)


@router.patch("/{guardian_id}", response_model=GuardianResponse)
async def update_guardian(guardian_id: str, update: GuardianUpdate):
    """Update guardian details"""
    db = get_database()

    # Check guardian exists
    existing = await db.guardians.find_one({"guardian_id": guardian_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guardian {guardian_id} not found",
        )

    # Build update document
    update_data = update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    update_data["updated_at"] = datetime.utcnow()

    # Update guardian
    await db.guardians.update_one(
        {"guardian_id": guardian_id},
        {"$set": update_data},
    )

    # Fetch updated guardian
    updated = await db.guardians.find_one({"guardian_id": guardian_id})
    guardian = Guardian(**updated)
    return GuardianResponse.from_guardian(guardian)


@router.delete("/{guardian_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_guardian(guardian_id: str):
    """Remove a guardian (marks as removed)"""
    db = get_database()

    # Check guardian exists
    existing = await db.guardians.find_one({"guardian_id": guardian_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guardian {guardian_id} not found",
        )

    # Mark as removed
    await db.guardians.update_one(
        {"guardian_id": guardian_id},
        {
            "$set": {
                "status": GuardianStatus.REMOVED,
                "updated_at": datetime.utcnow(),
            }
        },
    )


@router.get("/{guardian_id}/stats")
async def get_guardian_stats(guardian_id: str):
    """Get guardian statistics"""
    db = get_database()

    guardian_doc = await db.guardians.find_one({"guardian_id": guardian_id})
    if not guardian_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guardian {guardian_id} not found",
        )

    guardian = Guardian(**guardian_doc)

    # Get vault info
    vault_doc = await db.vaults.find_one({"vault_id": guardian.vault_id})
    vault = Vault(**vault_doc) if vault_doc else None

    # Get signature count from transactions
    signed_txs = await db.transactions.count_documents(
        {
            "vault_id": guardian.vault_id,
            "guardian_signatures.guardian_id": guardian_id,
        }
    )

    return {
        "guardian_id": guardian_id,
        "name": guardian.name,
        "status": guardian.status,
        "vault": {
            "vault_id": guardian.vault_id,
            "name": vault.name if vault else "Unknown",
        },
        "signatures": {
            "total": signed_txs,
            "last_signed_at": guardian.last_signature_at,
        },
        "activity": {
            "last_active_at": guardian.last_active_at,
            "joined_at": guardian.invitation_accepted_at,
        },
    }
