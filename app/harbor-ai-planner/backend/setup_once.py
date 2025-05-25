import asyncio
from main import async_session, create_harbor_layout


async def setup():
    async with async_session() as db:
        result = await create_harbor_layout(db)
        print(result)

if __name__ == "__main__":
    asyncio.run(setup())
