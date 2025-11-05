from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Global MongoDB client and database
mongodb_client: AsyncIOMotorClient | None = None
mongodb: AsyncIOMotorDatabase | None = None


async def connect_to_mongodb():
    """Connect to MongoDB"""
    global mongodb_client, mongodb

    try:
        logger.info(f"Connecting to MongoDB at {settings.mongodb_url}")
        mongodb_client = AsyncIOMotorClient(settings.mongodb_url)
        mongodb = mongodb_client[settings.mongodb_db_name]

        # Test connection
        await mongodb.command("ping")
        logger.info(f"Successfully connected to MongoDB database: {settings.mongodb_db_name}")

        # Create indexes
        await create_indexes()

    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongodb_connection():
    """Close MongoDB connection"""
    global mongodb_client

    if mongodb_client is not None:
        logger.info("Closing MongoDB connection")
        mongodb_client.close()


async def create_indexes():
    """Create database indexes for better performance"""
    if mongodb is None:
        return

    # Vaults indexes
    await mongodb.vaults.create_index("vault_id", unique=True)

    # Guardians indexes
    await mongodb.guardians.create_index("guardian_id", unique=True)
    await mongodb.guardians.create_index("vault_id")
    await mongodb.guardians.create_index("invitation_code", unique=True, sparse=True)

    # Transactions indexes
    await mongodb.transactions.create_index("transaction_id", unique=True)
    await mongodb.transactions.create_index("vault_id")
    await mongodb.transactions.create_index([("vault_id", 1), ("status", 1)])
    await mongodb.transactions.create_index("created_at")

    # Signing rounds indexes
    await mongodb.signing_rounds.create_index("transaction_id")
    await mongodb.signing_rounds.create_index([("transaction_id", 1), ("round", 1)])

    logger.info("Database indexes created successfully")


def get_database() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance"""
    if mongodb is None:
        raise RuntimeError("MongoDB not connected. Call connect_to_mongodb() first.")
    return mongodb
