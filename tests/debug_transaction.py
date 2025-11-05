#!/Users/ivan/.virtualenvs/claude-mcp/bin/python
"""
Debug script to check transaction status in MongoDB
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import json

async def check_transaction():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.guardianvault

    # Get the most recent transaction
    transactions = await db.transactions.find().sort("created_at", -1).limit(1).to_list(1)

    if not transactions:
        print("No transactions found in database")
        return

    tx = transactions[0]

    print("=" * 80)
    print("MOST RECENT TRANSACTION")
    print("=" * 80)
    print(f"\nTransaction ID: {tx.get('transaction_id')}")
    print(f"Status: {tx.get('status')}")
    print(f"Error: {tx.get('error_message', 'None')}")
    print(f"\nSignatures required: {tx.get('signatures_required')}")
    print(f"Signatures received: {tx.get('signatures_received')}")

    print(f"\n--- Round 1 Data ---")
    round1 = tx.get('round1_data', {})
    print(f"Guardians submitted: {len(round1)}")
    for guardian_id in round1.keys():
        print(f"  - {guardian_id}")

    print(f"\n--- Round 2 Data ---")
    round2 = tx.get('round2_data')
    if round2:
        print(f"k_total: {round2.get('k_total')}")
        print(f"r: {round2.get('r')}")
        print(f"R_combined: {round2.get('R_combined', '')[:64]}...")
    else:
        print("No Round 2 data")

    print(f"\n--- Round 3 Data ---")
    round3 = tx.get('round3_data', {})
    print(f"Guardians submitted: {len(round3)}")
    for guardian_id, data in round3.items():
        print(f"  - {guardian_id}: {data.get('signature_share')}")

    print(f"\n--- Final Signature ---")
    sig = tx.get('final_signature')
    if sig:
        print(f"r: {sig.get('r')}")
        print(f"s: {sig.get('s')}")
        print(f"rHex: {sig.get('rHex')}")
        print(f"sHex: {sig.get('sHex')}")
    else:
        print("No final signature")

    print(f"\n--- Full Transaction Document ---")
    # Remove the _id field for cleaner output
    tx.pop('_id', None)
    print(json.dumps(tx, indent=2, default=str))

    client.close()

if __name__ == "__main__":
    asyncio.run(check_transaction())
