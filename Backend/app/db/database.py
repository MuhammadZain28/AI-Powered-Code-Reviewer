import asyncpg
from app.utils.logger import get_logger
from dotenv import load_dotenv
import os
import asyncio
load_dotenv()

class Database:
    def __init__(self):
        self.dsn = os.getenv("DATABASE_URL")
        self.pool = None
        self.logger = get_logger("Database")

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(self.dsn)
            self.logger.info("Database connection established")
        except Exception as e:
            self.logger.error(f"Error connecting to database: {e}")
            raise

    async def disconnect(self):
        try:
            await self.pool.close()
            self.logger.info("Database connection closed")
        except Exception as e:
            self.logger.error(f"Error closing database connection: {e}")
            raise
