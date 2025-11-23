"""
WebSocket handlers for MPC signing protocol
"""
import logging
from datetime import datetime

from ..database import get_database
from ..services.mpc_coordinator import MPCCoordinator

logger = logging.getLogger(__name__)


def register_handlers(sio):
    """Register all WebSocket event handlers for signing protocol"""

    @sio.event
    async def signing_submit_round1(sid, data):
        """
        Guardian submits Round 1 data (nonce share and R point)

        Expected data:
        {
            "transactionId": "tx_...",
            "guardianId": "guard_...",
            "nonceShare": "hex string",
            "rPoint": "hex string (compressed public key)"
        }
        """
        try:
            # Extract data
            transaction_id = data.get("transactionId")
            guardian_id = data.get("guardianId")
            nonce_share = data.get("nonceShare")
            r_point = data.get("rPoint")

            # Validate
            if not all([transaction_id, guardian_id, nonce_share, r_point]):
                return {"success": False, "error": "Missing required fields"}

            # Verify guardian is in session
            async with sio.session(sid) as session:
                session_guardian_id = session.get("guardian_id")
                if session_guardian_id != guardian_id:
                    return {"success": False, "error": "Guardian ID mismatch"}

            logger.info(f"Received Round 1 from {guardian_id} for {transaction_id}")

            # Submit to MPC coordinator
            db = get_database()
            coordinator = MPCCoordinator(db)
            result = await coordinator.submit_round1_data(
                transaction_id, guardian_id, nonce_share, r_point
            )

            # If Round 1 complete, notify all guardians in vault
            if result.get("round2_ready"):
                # Get vault_id from transaction
                tx_doc = await db.transactions.find_one({"transaction_id": transaction_id})
                vault_id = tx_doc["vault_id"]

                # Notify guardians that Round 2 is ready
                await sio.emit(
                    "signing:round2_ready",
                    {
                        "transaction_id": transaction_id,
                        "message": "All guardians submitted Round 1. Round 2 in progress.",
                    },
                    room=f"vault_{vault_id}",
                )

            return result

        except Exception as e:
            logger.error(f"Error in signing_submit_round1: {e}")
            return {"success": False, "error": str(e)}

    @sio.event
    async def signing_get_round2_data(sid, data):
        """
        Guardian requests Round 2 data for computing signature share

        Expected data:
        {
            "transactionId": "tx_...",
            "guardianId": "guard_..."
        }

        Returns:
        {
            "success": true,
            "data": {
                "kTotal": number,
                "r": number,
                "numParties": number,
                "messageHash": string
            }
        }
        """
        try:
            transaction_id = data.get("transactionId")
            guardian_id = data.get("guardianId")

            if not transaction_id:
                return {"success": False, "error": "Missing transactionId"}

            # Verify guardian
            async with sio.session(sid) as session:
                session_guardian_id = session.get("guardian_id")
                if session_guardian_id != guardian_id:
                    return {"success": False, "error": "Guardian ID mismatch"}

            logger.info(f"Guardian {guardian_id} requesting Round 2 data for {transaction_id}")

            # Get Round 2 data from coordinator
            db = get_database()
            coordinator = MPCCoordinator(db)
            result = await coordinator.get_round2_data(transaction_id)

            if result.get("success"):
                # Convert to camelCase for JavaScript
                data_dict = result["data"]
                return {
                    "success": True,
                    "data": {
                        "kTotal": data_dict["k_total"],
                        "r": data_dict["r"],
                        "numParties": data_dict["num_parties"],
                        "messageHash": data_dict["message_hash"],
                    },
                }
            else:
                return result

        except Exception as e:
            logger.error(f"Error in signing_get_round2_data: {e}")
            return {"success": False, "error": str(e)}

    @sio.event
    async def signing_submit_round3(sid, data):
        """
        Guardian submits Round 3 data (signature share)

        Expected data:
        {
            "transactionId": "tx_...",
            "guardianId": "guard_...",
            "signatureShare": number
        }
        """
        try:
            transaction_id = data.get("transactionId")
            guardian_id = data.get("guardianId")
            signature_share = data.get("signatureShare")

            # Validate
            if not all([transaction_id, guardian_id, signature_share is not None]):
                return {"success": False, "error": "Missing required fields"}

            # Verify guardian
            async with sio.session(sid) as session:
                session_guardian_id = session.get("guardian_id")
                if session_guardian_id != guardian_id:
                    return {"success": False, "error": "Guardian ID mismatch"}

            logger.info(f"Received Round 3 from {guardian_id} for {transaction_id}")

            # Submit to MPC coordinator
            db = get_database()
            coordinator = MPCCoordinator(db)
            result = await coordinator.submit_round3_data(
                transaction_id, guardian_id, signature_share
            )

            # If Round 3 complete (signature ready), notify all guardians
            if result.get("round4_ready"):
                # Get vault_id from transaction
                tx_doc = await db.transactions.find_one({"transaction_id": transaction_id})
                vault_id = tx_doc["vault_id"]

                # Notify guardians that signature is complete
                await sio.emit(
                    "signing:complete",
                    {
                        "transaction_id": transaction_id,
                        "message": "Transaction signed successfully!",
                        "status": "completed",
                    },
                    room=f"vault_{vault_id}",
                )

                # Update guardian stats
                for gid in tx_doc.get("round3_data", {}).keys():
                    await db.guardians.update_one(
                        {"guardian_id": gid},
                        {
                            "$inc": {"total_signatures": 1},
                            "$set": {
                                "last_signature_at": datetime.utcnow(),
                                "last_active_at": datetime.utcnow(),
                            },
                        },
                    )

            return result

        except Exception as e:
            logger.error(f"Error in signing_submit_round3: {e}")
            return {"success": False, "error": str(e)}

    @sio.event
    async def signing_get_final_signature(sid, data):
        """
        Guardian requests final signature after Round 4

        Expected data:
        {
            "transactionId": "tx_...",
            "guardianId": "guard_..."
        }

        Returns:
        {
            "success": true,
            "signature": {
                "r": number,
                "s": number,
                "rHex": "hex string",
                "sHex": "hex string",
                "der": "hex string" (optional)
            }
        }
        """
        try:
            transaction_id = data.get("transactionId")
            guardian_id = data.get("guardianId")

            if not transaction_id:
                return {"success": False, "error": "Missing transactionId"}

            # Verify guardian
            async with sio.session(sid) as session:
                session_guardian_id = session.get("guardian_id")
                if session_guardian_id != guardian_id:
                    return {"success": False, "error": "Guardian ID mismatch"}

            logger.info(f"Guardian {guardian_id} requesting final signature for {transaction_id}")

            # Get final signature from coordinator
            db = get_database()
            coordinator = MPCCoordinator(db)
            result = await coordinator.get_final_signature(transaction_id)

            if result.get("success"):
                # Convert to camelCase for JavaScript
                sig = result["signature"]
                return {
                    "success": True,
                    "signature": {
                        "r": sig["r"],
                        "s": sig["s"],
                        "rHex": sig["r_hex"],
                        "sHex": sig["s_hex"],
                        "der": sig.get("der"),
                    },
                }
            else:
                return result

        except Exception as e:
            logger.error(f"Error in signing_get_final_signature: {e}")
            return {"success": False, "error": str(e)}

    @sio.event
    async def transactions_get_pending(sid, data):
        """
        Get pending transactions for a vault

        Expected data:
        {
            "vaultId": "vault_..."
        }
        """
        try:
            vault_id = data.get("vaultId")

            if not vault_id:
                return {"success": False, "error": "Missing vaultId"}

            # Verify guardian has access to this vault
            async with sio.session(sid) as session:
                session_vault_id = session.get("vault_id")
                if session_vault_id != vault_id:
                    return {"success": False, "error": "Vault ID mismatch"}

            logger.info(f"Fetching pending transactions for vault {vault_id}")

            # Get pending transactions
            db = get_database()
            cursor = db.transactions.find(
                {
                    "vault_id": vault_id,
                    "status": {
                        "$in": [
                            "pending",
                            "signing_round1",
                            "signing_round2",
                            "signing_round3",
                        ]
                    },
                }
            ).sort("created_at", -1)

            transactions = await cursor.to_list(length=100)

            # Convert to camelCase
            tx_list = []
            for tx in transactions:
                tx_list.append(
                    {
                        "id": tx["transaction_id"],
                        "vaultId": tx["vault_id"],
                        "type": tx["coin_type"],
                        "amount": tx["amount"],
                        "recipient": tx["recipient"],
                        "messageHash": tx["message_hash"],
                        "status": tx["status"],
                        "signaturesRequired": tx["signatures_required"],
                        "signaturesReceived": tx["signatures_received"],
                        "createdAt": tx["created_at"].isoformat(),
                        "fee": tx.get("fee"),
                    }
                )

            return {"success": True, "transactions": tx_list}

        except Exception as e:
            logger.error(f"Error in transactions_get_pending: {e}")
            return {"success": False, "error": str(e)}

    @sio.event
    async def transactions_get(sid, data):
        """
        Get single transaction details

        Expected data:
        {
            "transactionId": "tx_..."
        }
        """
        try:
            transaction_id = data.get("transactionId")

            if not transaction_id:
                return {"success": False, "error": "Missing transactionId"}

            # Get transaction
            db = get_database()
            tx_doc = await db.transactions.find_one({"transaction_id": transaction_id})

            if not tx_doc:
                return {"success": False, "error": "Transaction not found"}

            # Verify guardian has access to this vault
            async with sio.session(sid) as session:
                session_vault_id = session.get("vault_id")
                if session_vault_id != tx_doc["vault_id"]:
                    return {"success": False, "error": "Access denied"}

            # Convert to camelCase
            transaction = {
                "id": tx_doc["transaction_id"],
                "vaultId": tx_doc["vault_id"],
                "type": tx_doc["coin_type"],
                "amount": tx_doc["amount"],
                "recipient": tx_doc["recipient"],
                "messageHash": tx_doc["message_hash"],
                "status": tx_doc["status"],
                "signaturesRequired": tx_doc["signatures_required"],
                "signaturesReceived": tx_doc["signatures_received"],
                "createdAt": tx_doc["created_at"].isoformat(),
                "fee": tx_doc.get("fee"),
            }

            return {"success": True, "transaction": transaction}

        except Exception as e:
            logger.error(f"Error in transactions_get: {e}")
            return {"success": False, "error": str(e)}

    logger.info("WebSocket signing protocol handlers registered")
