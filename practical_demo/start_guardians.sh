#!/bin/bash
# Helper script to start guardian clients
# Run this in 3 separate terminals

VAULT_ID="vault_hHnn9VMkv7TX"
SERVER="http://localhost:8000"
CONFIG="clovr_output/vault_config.json"
PYTHON="/Users/ivan/projects/personal/GuardianVault/practical_demo/venv/bin/python"

# Check which guardian to start
if [ "$1" == "" ]; then
    echo "Usage: ./start_guardians.sh [1|2|3]"
    echo ""
    echo "Start each guardian in a separate terminal:"
    echo "  Terminal 1: ./start_guardians.sh 1"
    echo "  Terminal 2: ./start_guardians.sh 2"
    echo "  Terminal 3: ./start_guardians.sh 3"
    exit 1
fi

GUARDIAN_ID=$1
SHARE_FILE="clovr_output/guardian_${GUARDIAN_ID}_share.json"

echo "Starting Guardian $GUARDIAN_ID..."
echo "Vault ID: $VAULT_ID"
echo "Share file: $SHARE_FILE"
echo ""

$PYTHON cli_guardian_client.py \
  --server $SERVER \
  --vault-id $VAULT_ID \
  --guardian-id $GUARDIAN_ID \
  --share-file $SHARE_FILE \
  --vault-config $CONFIG
