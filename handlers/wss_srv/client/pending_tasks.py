import asyncio
import logging


async def cancel_pending_tasks_for_client(connection):
    """Cancel all pending tasks for a misbehaving WebSocket client."""
    current_task = asyncio.current_task()
    all_tasks = {t for t in asyncio.all_tasks() if t is not current_task}

    for task in all_tasks:
        if not task.done():
            task.cancel()

    warn = f"❌ Canceled all tasks for misbehaving client: {connection.remote_address}"
    logging.warning(warn)

    await connection.close()
