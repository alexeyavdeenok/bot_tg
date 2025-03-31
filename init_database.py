from database2 import db

async def init_db():
    await db.connect()