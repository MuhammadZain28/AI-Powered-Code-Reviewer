import asyncpg
from app.utils.logger import get_logger
from dotenv import load_dotenv
import os

load_dotenv()

class Database:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance
    def __init__(self):
        if hasattr(self, 'initialized') and self.initialized:
            return
        self.dsn = os.getenv("DATABASE_URL")
        self.pool = None
        self.logger = get_logger("Database")
        self.initialized = True

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(
                dsn=self.dsn,
                min_size=1,
                max_size=10
            )

            self.logger.info("Database connection established")

        except Exception as e:
            self.logger.error(f"Error connecting to database: {e}")
            raise

    async def disconnect(self):
        try:
            if self.pool:
                await self.pool.close()

            self.logger.info("Database connection closed")

        except Exception as e:
            self.logger.error(f"Error closing database connection: {e}")
            raise

    async def execute(self, query: str, *args):
        if not self.pool:
            self.logger.warning("Database connection not established. Attempting to connect...")
            self.pool = await asyncpg.create_pool(dsn=self.dsn)
        async with self.pool.acquire() as connection:
            try:
                return await connection.execute(query, *args)

            except Exception as e:
                self.logger.error(f"Error executing query: {e}")
                raise

    async def fetch(self, query: str, *args):
        if not self.pool:
            self.logger.warning("Database connection not established. Attempting to connect...")
            self.pool = await asyncpg.create_pool(dsn=self.dsn)
        async with self.pool.acquire() as connection:
            try:
                return await connection.fetch(query, *args)

            except Exception as e:
                self.logger.error(f"Error fetching data: {e}")
                raise

    async def fetchrow(self, query: str, *args):
        if not self.pool:
            self.logger.warning("Database connection not established. Attempting to connect...")
            self.pool = await asyncpg.create_pool(dsn=self.dsn)
        async with self.pool.acquire() as connection:
            try:
                return await connection.fetchrow(query, *args)

            except Exception as e:
                self.logger.error(f"Error fetching row: {e}")
                raise