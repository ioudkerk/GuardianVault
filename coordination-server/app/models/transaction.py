from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class TransactionStatus(str, Enum):
    PENDING = "pending"  # Created, waiting for signatures
    SIGNING_ROUND1 = "signing_round1"  # Round 1 in progress
    SIGNING_ROUND2 = "signing_round2"  # Round 2 (server combining)
    SIGNING_ROUND3 = "signing_round3"  # Round 3 in progress
    COMPLETED = "completed"  # All signatures received, transaction signed
    FAILED = "failed"  # Signing failed (timeout, error, etc.)
    CANCELLED = "cancelled"  # Manually cancelled


class TransactionType(str, Enum):
    SEND = "send"  # Send funds
    CONSOLIDATE = "consolidate"  # Consolidate UTXOs
    SWEEP = "sweep"  # Emergency sweep


class TransactionCreate(BaseModel):
    """Request model for creating a new transaction"""
    vault_id: str
    type: TransactionType = TransactionType.SEND
    coin_type: str  # bitcoin or ethereum
    amount: str  # String to preserve precision
    recipient: str
    fee: Optional[str] = None
    memo: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "vault_id": "vault_abc123",
                "type": "send",
                "coin_type": "bitcoin",
                "amount": "0.5",
                "recipient": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                "fee": "0.0001",
                "memo": "Payment for services"
            }
        }


class SignatureShare(BaseModel):
    """Signature share from a guardian"""
    guardian_id: str
    submitted_at: datetime
    round: int
    data: Dict  # Flexible dict for round-specific data


class Transaction(BaseModel):
    """Transaction model"""
    transaction_id: str
    vault_id: str
    type: TransactionType
    coin_type: str

    # Transaction details
    amount: str
    recipient: str
    fee: Optional[str] = None
    memo: Optional[str] = None

    # Message to sign (transaction hash)
    message_hash: str

    # Status tracking
    status: TransactionStatus = TransactionStatus.PENDING
    error_message: Optional[str] = None

    # Signature tracking
    signatures_required: int
    signatures_received: int = 0
    guardian_signatures: List[SignatureShare] = []

    # MPC Protocol data
    round1_data: Dict = {}  # {guardian_id: {nonce_share, R_point}}
    round2_data: Dict = {}  # {k_total, r, R_combined}
    round3_data: Dict = {}  # {guardian_id: signature_share}
    final_signature: Optional[Dict] = None  # {r, s, der}

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Timeout tracking
    timeout_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "tx_abc123",
                "vault_id": "vault_abc123",
                "type": "send",
                "coin_type": "bitcoin",
                "amount": "0.5",
                "recipient": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                "fee": "0.0001",
                "message_hash": "9c12cfdc04c74584d787ac3d23772132c18524bc7ab28dec4219b8fc5b425f70",
                "status": "signing_round1",
                "signatures_required": 3,
                "signatures_received": 2
            }
        }


class TransactionUpdate(BaseModel):
    """Update transaction"""
    status: Optional[TransactionStatus] = None
    error_message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed"
            }
        }


class TransactionResponse(Transaction):
    """Response model for transaction with computed fields"""
    progress_percentage: int = 0
    is_complete: bool = False
    is_expired: bool = False

    @classmethod
    def from_transaction(cls, tx: Transaction):
        data = tx.model_dump()
        if tx.signatures_required > 0:
            data["progress_percentage"] = int(
                (tx.signatures_received / tx.signatures_required) * 100
            )
        data["is_complete"] = tx.status == TransactionStatus.COMPLETED
        data["is_expired"] = (
            tx.timeout_at is not None and datetime.utcnow() > tx.timeout_at
        )
        return cls(**data)


# WebSocket event models

class SigningRound1Submit(BaseModel):
    """Round 1 submission from guardian"""
    transaction_id: str
    guardian_id: str
    nonce_share: str  # Hex string
    r_point: str  # Hex string (compressed public key)


class SigningRound3Submit(BaseModel):
    """Round 3 submission from guardian"""
    transaction_id: str
    guardian_id: str
    signature_share: int  # Signature share s_i
