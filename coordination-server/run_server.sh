#!/bin/bash
# Run GuardianVault Coordination Server with Socket.IO support

echo "Starting GuardianVault Coordination Server..."
echo "Server will be available at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""

# Run with socket_app (includes Socket.IO)
poetry run uvicorn app.main:socket_app --reload --host 0.0.0.0 --port 8000
