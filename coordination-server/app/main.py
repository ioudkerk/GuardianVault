import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .config import settings
from .database import connect_to_mongodb, close_mongodb_connection
from .routers import vaults, guardians, transactions
from .websocket import signing_protocol

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting GuardianVault Coordination Server...")
    await connect_to_mongodb()
    logger.info("Server started successfully")
    yield
    # Shutdown
    logger.info("Shutting down server...")
    await close_mongodb_connection()
    logger.info("Server shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="GuardianVault Coordination Server",
    description="Multi-Party Computation coordination server for cryptocurrency custody",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["*"],  # Allow all in dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST API routers
app.include_router(vaults.router, prefix="/api/vaults", tags=["vaults"])
app.include_router(guardians.router, prefix="/api/guardians", tags=["guardians"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "guardianvault-coordination-server",
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "GuardianVault Coordination Server",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# ==============================================================================
# Socket.IO Setup for WebSocket MPC Coordination
# ==============================================================================

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.cors_origins + ["*"],
    logger=settings.debug,
    engineio_logger=settings.debug,
)

# Wrap FastAPI app with Socket.IO
socket_app = socketio.ASGIApp(
    socketio_server=sio,
    other_asgi_app=app,
)

# Inject Socket.IO server into routers for WebSocket notifications
transactions.sio = sio


# ==============================================================================
# Socket.IO Event Handlers
# ==============================================================================

@sio.event
async def connect(sid, environ, auth):
    """Handle guardian connection"""
    logger.info(f"Guardian connecting: {sid}")

    # Extract auth data
    vault_id = auth.get("vaultId") if auth else None
    guardian_id = auth.get("guardianId") if auth else None

    if not vault_id or not guardian_id:
        logger.warning(f"Connection rejected: missing auth data")
        return False  # Reject connection

    # Store session data
    async with sio.session(sid) as session:
        session["vault_id"] = vault_id
        session["guardian_id"] = guardian_id

    # Join vault room
    await sio.enter_room(sid, f"vault_{vault_id}")

    logger.info(f"Guardian {guardian_id} connected to vault {vault_id}")

    # Notify other guardians in the vault
    await sio.emit(
        "guardian:connected",
        {"guardian_id": guardian_id},
        room=f"vault_{vault_id}",
        skip_sid=sid,
    )

    return True  # Accept connection


@sio.event
async def disconnect(sid):
    """Handle guardian disconnection"""
    try:
        async with sio.session(sid) as session:
            vault_id = session.get("vault_id")
            guardian_id = session.get("guardian_id")

        if vault_id and guardian_id:
            logger.info(f"Guardian {guardian_id} disconnected from vault {vault_id}")

            # Notify other guardians
            await sio.emit(
                "guardian:disconnected",
                {"guardian_id": guardian_id},
                room=f"vault_{vault_id}",
            )
    except Exception as e:
        logger.error(f"Error handling disconnect: {e}")


@sio.event
async def ping(sid, data):
    """Ping/pong for testing connection"""
    return {"success": True, "pong": True}


# Register signing protocol handlers
signing_protocol.register_handlers(sio)


# ==============================================================================
# Run Server
# ==============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:socket_app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning",
    )
