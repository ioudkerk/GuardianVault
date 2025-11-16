#!/bin/bash
# Convenience script to run Bitcoin regtest integration test

set -e

echo "=================================="
echo "Bitcoin Regtest Integration Test"
echo "=================================="
echo ""

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "   Please start Docker Desktop first."
    exit 1
fi

echo "Step 1: Start Bitcoin regtest stack"
echo "----------------------------------"
echo "Starting:"
echo "  - Bitcoin Core (regtest)"
echo "  - Mempool Explorer (UI)"
echo "  - MariaDB (for Mempool)"
echo ""
docker compose -f docker-compose.regtest.yml up -d
echo "✓ All services started"
echo ""

echo "Waiting for services to be ready..."
sleep 5

# Wait for Bitcoin node to be healthy
echo "Checking Bitcoin node health..."
for i in {1..30}; do
    if docker exec guardianvault-bitcoin-regtest bitcoin-cli -regtest -rpcuser=regtest -rpcpassword=regtest getblockchaininfo > /dev/null 2>&1; then
        echo "✓ Bitcoin node is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Bitcoin node failed to start"
        exit 1
    fi
    echo "  Waiting... ($i/30)"
    sleep 2
done
echo ""

# Wait a bit more for Mempool to initialize
echo "Waiting for Mempool to initialize..."
sleep 10
echo "✓ Mempool should be ready"
echo ""

echo "=================================="
echo "🌐 Mempool Explorer UI:"
echo "   http://localhost:8080"
echo ""
echo "   You can view blocks, transactions,"
echo "   and the mempool in real-time!"
echo "=================================="
echo ""

echo "Step 2: Run integration test"
echo "----------------------------------"
python3 examples/bitcoin_regtest_test.py

echo ""
echo "=================================="
echo "🌐 View results in Mempool:"
echo "   http://localhost:8080"
echo ""
echo "Useful commands:"
echo ""
echo "Stop all services:"
echo "  docker compose -f docker-compose.regtest.yml down"
echo ""
echo "Stop and delete data:"
echo "  docker compose -f docker-compose.regtest.yml down -v"
echo ""
echo "View logs:"
echo "  docker compose -f docker-compose.regtest.yml logs -f"
echo ""
echo "View specific service logs:"
echo "  docker compose -f docker-compose.regtest.yml logs -f bitcoin-regtest"
echo "  docker compose -f docker-compose.regtest.yml logs -f mempool-backend"
echo ""
echo "Interact with bitcoin-cli:"
echo "  docker exec -it guardianvault-bitcoin-regtest bitcoin-cli -regtest -rpcuser=regtest -rpcpassword=regtest <command>"
echo "=================================="
