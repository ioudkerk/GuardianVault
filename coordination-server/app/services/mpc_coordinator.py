"""
MPC Coordinator - Orchestrates the 4-round threshold ECDSA signing protocol
"""
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import logging

# Add parent directory to path to import threshold crypto modules
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from threshold_signing import ThresholdSigner
from threshold_mpc_keymanager import EllipticCurvePoint, SECP256K1_N

logger = logging.getLogger(__name__)


class MPCCoordinator:
    """Coordinates the 4-round MPC signing protocol"""

    def __init__(self, database):
        self.db = database

    async def start_signing_round1(self, transaction_id: str):
        """Initialize Round 1 - Nonce generation"""
        logger.info(f"Starting Round 1 for transaction {transaction_id}")

        # Update transaction status
        await self.db.transactions.update_one(
            {"transaction_id": transaction_id},
            {
                "$set": {
                    "status": "signing_round1",
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        return {"success": True, "message": "Round 1 started"}

    async def submit_round1_data(
        self, transaction_id: str, guardian_id: str, nonce_share: str, r_point: str
    ) -> Dict:
        """Submit Round 1 data (nonce share and R point) from a guardian"""
        logger.info(f"Guardian {guardian_id} submitting Round 1 data for {transaction_id}")

        # Get transaction
        tx_doc = await self.db.transactions.find_one({"transaction_id": transaction_id})
        if not tx_doc:
            return {"success": False, "error": "Transaction not found"}

        # Store Round 1 data
        await self.db.transactions.update_one(
            {"transaction_id": transaction_id},
            {
                "$set": {
                    f"round1_data.{guardian_id}": {
                        "nonce_share": nonce_share,
                        "r_point": r_point,
                        "submitted_at": datetime.utcnow().isoformat(),
                    },
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        # Check if all guardians submitted
        tx_doc = await self.db.transactions.find_one({"transaction_id": transaction_id})
        round1_count = len(tx_doc.get("round1_data", {}))
        required = tx_doc["signatures_required"]

        logger.info(f"Round 1 progress: {round1_count}/{required}")

        # If all guardians submitted, proceed to Round 2
        if round1_count >= required:
            await self.execute_round2(transaction_id)

        return {
            "success": True,
            "round1_count": round1_count,
            "required": required,
            "round2_ready": round1_count >= required,
        }

    async def execute_round2(self, transaction_id: str):
        """
        Execute Round 2 - Server combines all R points
        This is done by the server, guardians wait for result
        """
        logger.info(f"Executing Round 2 for transaction {transaction_id}")

        try:
            # Get transaction with all Round 1 data
            tx_doc = await self.db.transactions.find_one({"transaction_id": transaction_id})
            if not tx_doc:
                raise ValueError("Transaction not found")

            round1_data = tx_doc.get("round1_data", {})

            # Extract all R points
            r_points_hex = []
            nonce_shares_hex = []
            for guardian_id, data in round1_data.items():
                r_points_hex.append(data["r_point"])
                nonce_shares_hex.append(data["nonce_share"])

            # Combine R points: R = R_1 + R_2 + R_3
            combined_r_point = None
            for r_hex in r_points_hex:
                r_point = EllipticCurvePoint.from_bytes(bytes.fromhex(r_hex))
                if combined_r_point is None:
                    combined_r_point = r_point
                else:
                    combined_r_point = combined_r_point + r_point

            # Get r coordinate (x-coordinate mod n)
            r = combined_r_point.x % SECP256K1_N

            # Calculate k_total (sum of all nonce shares)
            k_total = 0
            for nonce_hex in nonce_shares_hex:
                nonce_value = int.from_bytes(bytes.fromhex(nonce_hex), "big")
                k_total = (k_total + nonce_value) % SECP256K1_N

            # Store Round 2 result (convert large ints to strings for MongoDB)
            round2_data = {
                "kTotal": str(k_total),  # Store as string - too large for MongoDB int
                "r": str(r),  # Store as string - too large for MongoDB int
                "R_combined": combined_r_point.to_bytes(compressed=True).hex(),
                "computed_at": datetime.utcnow().isoformat(),
            }

            await self.db.transactions.update_one(
                {"transaction_id": transaction_id},
                {
                    "$set": {
                        "round2_data": round2_data,
                        "status": "signing_round2",
                        "updated_at": datetime.utcnow(),
                    }
                },
            )

            logger.info(f"Round 2 complete for {transaction_id}: r={r}")

            # Proceed to Round 3
            await self.start_signing_round3(transaction_id)

            return {"success": True, "round2_data": round2_data}

        except Exception as e:
            logger.error(f"Round 2 failed for {transaction_id}: {e}")
            await self.db.transactions.update_one(
                {"transaction_id": transaction_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": f"Round 2 failed: {str(e)}",
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            return {"success": False, "error": str(e)}

    async def start_signing_round3(self, transaction_id: str):
        """Initialize Round 3 - Signature share computation"""
        logger.info(f"Starting Round 3 for transaction {transaction_id}")

        await self.db.transactions.update_one(
            {"transaction_id": transaction_id},
            {
                "$set": {
                    "status": "signing_round3",
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        return {"success": True, "message": "Round 3 started"}

    async def submit_round3_data(
        self, transaction_id: str, guardian_id: str, signature_share: int
    ) -> Dict:
        """Submit Round 3 data (signature share) from a guardian"""
        logger.info(f"Guardian {guardian_id} submitting Round 3 data for {transaction_id}")

        # Get transaction
        tx_doc = await self.db.transactions.find_one({"transaction_id": transaction_id})
        if not tx_doc:
            return {"success": False, "error": "Transaction not found"}

        # Store Round 3 data (convert large int to string for MongoDB)
        await self.db.transactions.update_one(
            {"transaction_id": transaction_id},
            {
                "$set": {
                    f"round3_data.{guardian_id}": {
                        "signature_share": str(signature_share),  # Store as string - too large for MongoDB int
                        "submitted_at": datetime.utcnow().isoformat(),
                    },
                    "updated_at": datetime.utcnow(),
                },
                "$inc": {"signatures_received": 1},
            },
        )

        # Check if all guardians submitted
        tx_doc = await self.db.transactions.find_one({"transaction_id": transaction_id})
        round3_count = len(tx_doc.get("round3_data", {}))
        required = tx_doc["signatures_required"]

        logger.info(f"Round 3 progress: {round3_count}/{required}")

        # If all guardians submitted, proceed to Round 4
        if round3_count >= required:
            await self.execute_round4(transaction_id)

        return {
            "success": True,
            "round3_count": round3_count,
            "required": required,
            "round4_ready": round3_count >= required,
        }

    async def execute_round4(self, transaction_id: str):
        """
        Execute Round 4 - Server combines all signature shares
        Final signature: s = s_1 + s_2 + s_3
        """
        logger.info(f"Executing Round 4 for transaction {transaction_id}")

        try:
            # Get transaction with all Round 3 data
            tx_doc = await self.db.transactions.find_one({"transaction_id": transaction_id})
            if not tx_doc:
                raise ValueError("Transaction not found")

            round2_data = tx_doc.get("round2_data", {})
            round3_data = tx_doc.get("round3_data", {})

            # Convert r from string back to int
            r = int(round2_data["r"])

            # Combine all signature shares: s = s_1 + s_2 + s_3 mod n
            s_combined = 0
            for guardian_id, data in round3_data.items():
                # Convert signature share from string back to int
                s_i = int(data["signature_share"])
                s_combined = (s_combined + s_i) % SECP256K1_N

            # Ensure s is in lower half of curve order (BIP62)
            if s_combined > SECP256K1_N // 2:
                s_combined = SECP256K1_N - s_combined

            # Create final signature (store large ints as strings for MongoDB)
            final_signature = {
                "r": str(r),  # Store as string - too large for MongoDB int
                "s": str(s_combined),  # Store as string - too large for MongoDB int
                "rHex": r.to_bytes(32, 'big').hex(),
                "sHex": s_combined.to_bytes(32, 'big').hex(),
                "created_at": datetime.utcnow().isoformat(),
            }

            # TODO: Create DER encoding
            # final_signature["der"] = create_der_signature(r, s_combined)

            # Update transaction as completed
            await self.db.transactions.update_one(
                {"transaction_id": transaction_id},
                {
                    "$set": {
                        "final_signature": final_signature,
                        "status": "completed",
                        "completed_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                },
            )

            logger.info(f"Round 4 complete - Transaction {transaction_id} signed successfully!")

            return {"success": True, "signature": final_signature}

        except Exception as e:
            logger.error(f"Round 4 failed for {transaction_id}: {e}")
            await self.db.transactions.update_one(
                {"transaction_id": transaction_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": f"Round 4 failed: {str(e)}",
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            return {"success": False, "error": str(e)}

    async def get_round2_data(self, transaction_id: str) -> Dict:
        """Get Round 2 data for guardians to use in Round 3"""
        tx_doc = await self.db.transactions.find_one({"transaction_id": transaction_id})
        if not tx_doc:
            return {"success": False, "error": "Transaction not found"}

        round2_data = tx_doc.get("round2_data")
        if not round2_data:
            return {"success": False, "error": "Round 2 not complete yet"}

        # Convert strings back to integers (stored as strings for MongoDB compatibility)
        return {
            "success": True,
            "data": {
                "k_total": int(round2_data["kTotal"]),
                "r": int(round2_data["r"]),
                "num_parties": tx_doc["signatures_required"],
            },
        }

    async def get_final_signature(self, transaction_id: str) -> Dict:
        """Get final signature after Round 4"""
        tx_doc = await self.db.transactions.find_one({"transaction_id": transaction_id})
        if not tx_doc:
            return {"success": False, "error": "Transaction not found"}

        if tx_doc["status"] != "completed":
            return {
                "success": False,
                "error": f"Transaction not completed yet (status: {tx_doc['status']})",
            }

        final_signature = tx_doc.get("final_signature")
        if not final_signature:
            return {"success": False, "error": "Signature not found"}

        return {"success": True, "signature": final_signature}
