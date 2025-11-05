# GuardianVault Examples

This directory contains example scripts demonstrating how to use the GuardianVault library.

## Available Examples

### `complete_mpc_workflow.py`
Complete MPC workflow demonstration showing the full lifecycle:
- Setup and key generation
- Address generation
- Transaction signing

**Key Feature:** Private key is NEVER reconstructed at any point!

**Usage:**
```bash
python examples/complete_mpc_workflow.py
```

### `mpc_cli.py`
Command-line interface for MPC cryptocurrency key management.

**Usage:**
```bash
# Generate and split master seed
python examples/mpc_cli.py generate --num-shares 5 --threshold 3

# Derive BIP32 keys
python examples/mpc_cli.py derive --shares share1.json share2.json share3.json

# Sign a transaction
python examples/mpc_cli.py sign --shares share1.json share2.json share3.json --message "tx_hash"
```

### `mpc_workflow_example.py`
Practical MPC workflow simulation showing a realistic scenario:
- Company managing crypto treasury with 3-of-5 multisig
- Demonstrates party interactions
- Shows secure share management

**Usage:**
```bash
python examples/mpc_workflow_example.py
```

## Prerequisites

Make sure you have installed all dependencies:

```bash
pip install -r requirements.txt
```

## Important Notes

- These examples are for **demonstration purposes**
- In production, key shares should be stored securely and never in plain text
- Network communication should be encrypted and authenticated
- Consider using hardware security modules (HSMs) for storing shares
- Implement proper access controls and audit logging

## Related Documentation

- See `guardianvault/README.md` for library documentation
- See `docs/` for architecture and protocol details
- See `tests/test_coordination_server.py` for integration testing example
