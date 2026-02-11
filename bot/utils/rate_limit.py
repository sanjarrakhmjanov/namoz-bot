import asyncio


async def rate_limit_send(delay_sec: float) -> None:
    await asyncio.sleep(delay_sec)
