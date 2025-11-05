from fastapi import APIRouter, HTTPException, status
from typing import List
import shortuuid
from datetime import datetime, timedelta
import hashlib

from ..database import get_database
from ..models.transaction import (
    TransactionCreate,
    Transaction,
    TransactionUpdate,
    TransactionResponse,
    TransactionStatus,
)
from ..models.vault import Vault
from ..config import settings

router = APIRouter()


def compute_message_hash(transaction_data: dict) -> str:
    """Compute message hash for transaction"""
    # In production, this should create proper Bitcoin/Ethereum transaction hash
    # For now, create a simple hash of transaction data
    data_str = f"{transaction_data['amount']}{transaction_data['recipient']}{transaction_data['vault_id']}"
    return hashlib.sha256(data_str.encode()).hexdigest()


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(tx_create: TransactionCreate):
    """Create a new transaction for signing"""
    db = get_database()

    # Check vault exists
    vault_doc = await db.vaults.find_one({"vault_id": tx_create.vault_id})
    if not vault_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vault {tx_create.vault_id} not found",
        )

    vault = Vault(**vault_doc)

    # Check vault is active
    if vault.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vault status is {vault.status}, must be active",
        )

    # Verify coin type matches
    if tx_create.coin_type != vault.coin_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Coin type mismatch: vault is {vault.coin_type}",
        )

    # Generate transaction ID
    transaction_id = f"tx_{shortuuid.uuid()[:12]}"

    # Compute message hash
    message_hash = compute_message_hash(tx_create.model_dump())

    # Calculate timeout
    timeout_at = datetime.utcnow() + timedelta(seconds=settings.transaction_timeout)

    # Create transaction
    transaction = Transaction(
        transaction_id=transaction_id,
        vault_id=tx_create.vault_id,
        type=tx_create.type,
        coin_type=tx_create.coin_type,
        amount=tx_create.amount,
        recipient=tx_create.recipient,
        fee=tx_create.fee,
        memo=tx_create.memo,
        message_hash=message_hash,
        status=TransactionStatus.PENDING,
        signatures_required=vault.threshold,
        timeout_at=timeout_at,
    )

    # Insert transaction
    await db.transactions.insert_one(transaction.model_dump())

    # Update vault stats
    await db.vaults.update_one(
        {"vault_id": tx_create.vault_id},
        {
            "$inc": {"total_transactions": 1},
            "$set": {"updated_at": datetime.utcnow()},
        },
    )

    return TransactionResponse.from_transaction(transaction)


@router.get("/", response_model=List[TransactionResponse])
async def list_transactions(
    vault_id: str | None = None,
    status: TransactionStatus | None = None,
    skip: int = 0,
    limit: int = 100,
):
    """List transactions with optional filters"""
    db = get_database()

    # Build query
    query = {}
    if vault_id:
        query["vault_id"] = vault_id
    if status:
        query["status"] = status

    # Fetch transactions
    cursor = db.transactions.find(query).skip(skip).limit(limit).sort("created_at", -1)
    transactions = await cursor.to_list(length=limit)

    return [TransactionResponse.from_transaction(Transaction(**tx)) for tx in transactions]


@router.get("/pending", response_model=List[TransactionResponse])
async def get_pending_transactions(vault_id: str):
    """Get all pending transactions for a vault"""
    db = get_database()

    # Fetch pending transactions
    cursor = db.transactions.find(
        {"vault_id": vault_id, "status": {"$in": ["pending", "signing_round1", "signing_round2", "signing_round3"]}}
    ).sort("created_at", -1)

    transactions = await cursor.to_list(length=100)

    return [TransactionResponse.from_transaction(Transaction(**tx)) for tx in transactions]


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: str):
    """Get transaction by ID"""
    db = get_database()

    tx_doc = await db.transactions.find_one({"transaction_id": transaction_id})
    if not tx_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found",
        )

    transaction = Transaction(**tx_doc)
    return TransactionResponse.from_transaction(transaction)


@router.patch("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(transaction_id: str, update: TransactionUpdate):
    """Update transaction status"""
    db = get_database()

    # Check transaction exists
    existing = await db.transactions.find_one({"transaction_id": transaction_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found",
        )

    # Build update document
    update_data = update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    update_data["updated_at"] = datetime.utcnow()

    # If completed, set completed_at
    if update.status == TransactionStatus.COMPLETED:
        update_data["completed_at"] = datetime.utcnow()

    # Update transaction
    await db.transactions.update_one(
        {"transaction_id": transaction_id},
        {"$set": update_data},
    )

    # Fetch updated transaction
    updated = await db.transactions.find_one({"transaction_id": transaction_id})
    transaction = Transaction(**updated)
    return TransactionResponse.from_transaction(transaction)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_transaction(transaction_id: str):
    """Cancel a transaction"""
    db = get_database()

    # Check transaction exists
    existing = await db.transactions.find_one({"transaction_id": transaction_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found",
        )

    tx = Transaction(**existing)

    # Can only cancel pending transactions
    if tx.status not in [TransactionStatus.PENDING, TransactionStatus.SIGNING_ROUND1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel transaction with status {tx.status}",
        )

    # Mark as cancelled
    await db.transactions.update_one(
        {"transaction_id": transaction_id},
        {
            "$set": {
                "status": TransactionStatus.CANCELLED,
                "updated_at": datetime.utcnow(),
            }
        },
    )


@router.get("/{transaction_id}/status")
async def get_transaction_status(transaction_id: str):
    """Get detailed transaction status"""
    db = get_database()

    tx_doc = await db.transactions.find_one({"transaction_id": transaction_id})
    if not tx_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found",
        )

    tx = Transaction(**tx_doc)

    # Get guardian signatures status
    signatures_by_guardian = {}
    for sig in tx.guardian_signatures:
        signatures_by_guardian[sig.guardian_id] = {
            "round": sig.round,
            "submitted_at": sig.submitted_at.isoformat(),
        }

    return {
        "transaction_id": transaction_id,
        "status": tx.status,
        "progress": {
            "signatures_received": tx.signatures_received,
            "signatures_required": tx.signatures_required,
            "percentage": int((tx.signatures_received / tx.signatures_required) * 100) if tx.signatures_required > 0 else 0,
        },
        "rounds": {
            "round1": {
                "complete": len(tx.round1_data) >= tx.signatures_required,
                "submissions": len(tx.round1_data),
            },
            "round2": {
                "complete": bool(tx.round2_data),
                "data": tx.round2_data if tx.round2_data else None,
            },
            "round3": {
                "complete": len(tx.round3_data) >= tx.signatures_required,
                "submissions": len(tx.round3_data),
            },
            "final_signature": tx.final_signature,
        },
        "guardians": signatures_by_guardian,
        "is_expired": tx.timeout_at and datetime.utcnow() > tx.timeout_at,
    }
