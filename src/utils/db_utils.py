from src.fzd_db import get_db_connection, get_registration_events


async def refresh_event_list() -> list[str]:
    async with get_db_connection() as db:
        reg_event_dict = await get_registration_events(db)
    return [event['event_name'] for event in reg_event_dict if 'event_name' in event]