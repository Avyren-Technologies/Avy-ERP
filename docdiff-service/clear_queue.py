import asyncio
from redis.asyncio import Redis

async def clear_redis():
    r = Redis.from_url("redis://:admin123@localhost:6379/2")
    await r.flushdb()
    print("Database 2 cleared!")

asyncio.run(clear_redis())
