import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import aiomysql

from src.settings import get_settings

logger = logging.getLogger(__name__)

_connection_pool = None


async def _safe_rollback(conn, source: str = "unknown") -> None:
    """Rollback only when possible; never mask the original exception."""
    if not conn or getattr(conn, "closed", True):
        return
    try:
        await conn.rollback()
    except aiomysql.Error as rollback_error:
        logger.warning(f"[DB] Rollback skipped ({source}): {rollback_error}")


async def init_db_pool():
    global _connection_pool
    settings = get_settings()
    POOL_SIZE = 16
    if _connection_pool is None:
        _connection_pool = await aiomysql.create_pool(minsize=1, maxsize=POOL_SIZE, **settings.db_config)
        logger.info("Database pool created")
    return _connection_pool


async def get_connection_from_pool():
    """
    Context manager that safely checks out a connection from the pool,
    and returns it afterward (even if errors happen).
    Automatically rebuilds the pool if it breaks.
    """
    global _connection_pool
    conn = None
    if _connection_pool is None:
        raise RuntimeError("Database pool is not initialized")

    try:
        conn = await _connection_pool.acquire()
        await conn.ping(reconnect=True)
        logger.debug("[DB] Got connection from pool: id=%s", id(conn))
    except Exception as e:
        logger.warning(f"[DB CONNECTION] Failed to get healthy pooled connection: {e}")
        if conn:
            conn.close()
            _connection_pool.release(conn)
        raise
    return conn


@asynccontextmanager
async def get_db_connection():
    """
    Context manager for safely acquiring and releasing a DB connection.
    Rolls back on error when possible and always releases the connection.
    """
    conn = None
    try:
        conn = await get_connection_from_pool()
        # Test connection quickly (cheap ping)
        # conn.ping(reconnect=True, attempts=1, delay=0)

        yield conn  # hand off to the calling code

    except aiomysql.Error as e:
        await _safe_rollback(conn, source="get_db_connection")
        logger.error("[DB ERROR] %s", e)
        raise  # propagate error up to cog

    finally:
        if conn:
            _connection_pool.release(conn)  # release_connection(conn)


async def execute_query(conn, query, params=None, fetch="all", isProc: bool = False):
    """
    Safely executes an SQL query with rollback on error.
    :conn: DB connection object
    :query: SQL query string
    :params: Optional tuple/list of parameters
    :fetch: "all", "one", or None (for INSERT/UPDATE/DELETE)
    :return: Query result or None if no result
    """
    async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
            if isProc:
                await cursor.callproc(query, params or ())
            else:
                await cursor.execute(query, params or ())

            if fetch == "all":
                result = await cursor.fetchall()
            elif fetch == "one":
                result = await cursor.fetchone()
            else:
                result = None

            await conn.commit()
            return result

        except Exception as e:
            await _safe_rollback(conn, source="execute_query")
            logger.error(f"[DB QUERY ERROR]: {e}\nQuery: {query}\nParams: {params}")
            raise


async def get_event_types(db):
    """Get event types and ids of recurring events from 'events' table"""
    sql_gettypes = "SELECT id, name FROM events"  # WHERE recurring = 1"
    eventtypes = await execute_query(db, sql_gettypes, fetch="all")

    return eventtypes  # [{'id': 7, 'name': 'Weekly Classic Mini'} . . .


async def get_user_id(db, discord_id: str):
    """Given a discord user id (discord_id), returns the database
    id of that user
    """
    sql_getuser = "SELECT id from users WHERE discord_user_id = %s"
    user = await execute_query(db, sql_getuser, params=(discord_id,), fetch="one")
    if user:
        return user["id"]
    else:
        return None


async def add_new_user(db, discord_username, display_name=None) -> None:
    """Adds new user to the database"""

    # Assuming "discord_display_name" isn't required
    sql_newuser = "INSERT INTO users (tag, discord_user_id) VALUES (%s, %s);"

    if display_name is None:  # Defaults to user's server display name
        display_name = discord_username.nick[0:10]
    await execute_query(db, sql_newuser, params=(display_name, discord_username.name), fetch=None)


async def modify_user_display_name(db, db_user_id, display_name) -> None:
    """Modifies an existing user's display name in the database"""
    sql_modifyuser = "UPDATE users SET tag = %s WHERE id = %s;"
    await execute_query(db, sql_modifyuser, params=(display_name, db_user_id), fetch=None)


async def create_event(db, event, duration: int = 2) -> None:
    """Inserts new event into the 'events_scheduled' database
    duration is optional variable to set how long the event window is (2 hours by default)
    """
    now = datetime.now(timezone.utc)  # now.strftime('%Y-%m-%d %H:%M:%S')
    endtime = now + timedelta(hours=duration)
    tformat = "%Y-%m-%d %H:%M:%S"
    sql_addevent = "INSERT INTO events_scheduled (event_id, utc_start_dt, utc_end_dt) VALUES (%s, %s, %s);"
    await execute_query(
        db, sql_addevent, params=(event["id"], now.strftime(tformat), endtime.strftime(tformat)), fetch=None
    )


async def check_for_active_event(db, hours_from_now: int = 0):
    """Checks database event times start and end times to see if
    event is active right now, returns dict with name and id
    """
    active_event = {"name": "NULL", "id": 0, "is_machine_input_required": False}  # Assume no match
    sql_getevent = """SELECT es.id, e.name, es.utc_start_dt, es.utc_end_dt, es.scoring_method, es.is_machine_input_required
                    FROM events_scheduled es
                    JOIN events e ON e.id = es.event_id
                    WHERE DATE_ADD(UTC_TIMESTAMP(), INTERVAL %s HOUR) 
                          BETWEEN utc_start_dt AND utc_end_dt;"""
    eventmatch = await execute_query(db, sql_getevent, params=(hours_from_now,), fetch="one")
    if eventmatch:
        active_event["name"] = eventmatch["name"]
        active_event["id"] = eventmatch["id"]
        active_event["scoring_method"] = eventmatch["scoring_method"]
        raw_machine_flag = eventmatch.get("is_machine_input_required")
        if isinstance(raw_machine_flag, (bytes, bytearray)):
            active_event["is_machine_input_required"] = int.from_bytes(raw_machine_flag, byteorder="big") == 1
        else:
            active_event["is_machine_input_required"] = bool(raw_machine_flag)

    return active_event


async def submit_score(db, dataentry) -> int:
    """Executes sql query command to insert data to database
    db = database connection object
    dataentry = [ user_id, scheduled_event_id, score ] - all integers
    """
    sql_newrow = "sp_insert_score"
    dataentry.append("NULL")  # fifth argument is what will be returned...handled by "fetch" in python
    score = await execute_query(db, sql_newrow, params=dataentry, fetch="one", isProc=True)
    return int(score["@sp_output_score"])


async def edit_score(db, dataentry) -> None:
    """Executes sql query command to insert data to database
    db = database connection object
    dataentry = [ newscore, id ] for modifying score,
                all integer values
    """
    sql_updaterow = "UPDATE event_result_points SET score = %s WHERE id = %s;"
    await execute_query(db, sql_updaterow, params=dataentry, fetch=None)


async def delete_score(db, dataentry) -> None:
    """Executes sql query command to insert data to database
    db = database connection object
    dataentry = [ id ] for deleting score
                all integer values
    """
    sql_deleterow = "DELETE FROM event_result_points WHERE id = %s;"
    await execute_query(db, sql_deleterow, params=dataentry, fetch=None)


async def get_user_scores(db, user_name, check_for_score_method=False) -> list[dict[str, str]]:
    """Query the database for scores of active event of a given user
    Returns all values as strings for autocomplete bot feature
    """
    active_event = await check_for_active_event(db)
    if active_event["name"] == "NULL":
        return [{"score": "NO CURRENT EVENT", "id": "-999"}]
    elif check_for_score_method and active_event["scoring_method"] == "placement":
        return [{"score": "DISABLED FOR THIS EVENT", "id": "-888"}]
    db_user_id = await get_user_id(db, user_name)

    sql_getscores = """SELECT CAST(score AS CHAR) AS score, 
                              CAST(id AS CHAR) AS id
                       FROM event_result_points 
                       WHERE user_id = %s AND scheduled_event_id = %s 
                       ORDER BY id ASC;"""
    scoresdict = await execute_query(db, sql_getscores, params=(db_user_id, active_event["id"]), fetch="all")

    if not scoresdict:
        return [{"score": "NO USER SCORES FOUND", "id": "-999"}]

    return scoresdict


async def get_latest_event(db, event_id=None):
    """Get most recent event, return a dict containing the unique id,
    name of event, and start date of the event
    OPTIONAL: event_id to find latest of a specific event
              event)subid if an event_id has multiple sub0events (i.e. GGP)
              NOTE only ONE is allowed to be set when called!
    """

    sql_getevent = """SELECT es.id, e.name, es.utc_start_dt, es.utc_end_dt, es.event_id
                    FROM events_scheduled es
                    JOIN events e ON e.id = es.event_id
                    WHERE utc_start_dt =
                        (SELECT MAX(utc_start_dt) FROM events_scheduled 
                         WHERE utc_start_dt < UTC_TIMESTAMP())"""
    params = None
    if event_id is not None:
        sql_getevent = sql_getevent.replace("())", "() AND event_id = %s)")
        params = (event_id,)

    selectedevent = await execute_query(db, sql_getevent, params=params, fetch="one")

    return selectedevent


async def get_event_scoreboard(db, db_user_id: int, event_type=None):
    """Query the FZD database for all scores of a given event,
    defined by scheduled_event_id.

    Returns an ordered list of dicts with 'player': str and 'score': Decimal
    as well as the eventinfo (from get_latest_event function)
    """
    sql_getscoreboard = "sp_show_scoreboard"

    if event_type is None:
        eventinfo = await get_latest_event(db)
    else:
        eventinfo = await get_latest_event(db, event_id=int(event_type))

    # Check there's an event to display
    if not eventinfo:
        return None, None

    allscores = await execute_query(db, sql_getscoreboard, params=(eventinfo["id"], db_user_id), isProc=True)

    # print(allscores)
    # strip off is_qualified results if we're not viewing a qualifier event
    valid_qual_events = [8, 9, 10, 11, 12, 13]  # MM, Thu FZD, Fri FZD, EAD, CC, APAC
    if eventinfo["event_id"] not in valid_qual_events:
        for d in allscores:
            d.pop("is_qualified", None)

    return eventinfo, allscores


async def get_event_schedule(db):
    """Executes sql process query to get scheduled events in future"""
    sql_events = "SELECT event, utc_start, utc_end FROM vw_list_scheduled_events"
    events = await execute_query(db, sql_events, params=None, fetch="all", isProc=False)
    # print(events)
    # print(type(events))
    return events


async def get_machines(db):
    sql_getmachines = "SELECT CAST(id AS CHAR) AS id, CAST(name AS CHAR) AS name FROM machines;"
    machines_dict = await execute_query(db, sql_getmachines)
    return machines_dict


###################################################################
# Database calls for event registration
###################################################################

async def get_registration_events(db):
    """ Gets event information from database.
    """
    sql_getregevents = ("""SELECT CAST(id AS CHAR) AS id,
                        SELECT CAST(event_id AS CHAR) AS event_id,
                        utc_start_dt,
                        CAST(display_name AS CHAR) AS event_name,
                        CAST(capacity AS CHAR) AS capacity 
                        FROM events_scheduled 
                        WHERE is_registration_event = 1;"""
                       )
    reg_event_dict = await execute_query(db, sql_getregevents)
    # Turn numbers back into numbers
    if reg_event_dict:
        for event in reg_event_dict:
            event.id = int(event.id)
            event.event_id = int(event.event_id)
            event.capacity = int(event.capacity)
    return reg_event_dict


async def get_user_registrations(db, discord_user_id):
    # This version gets info from the event_registration_log table, which is likely not 
    # consistent with how the log will be implemented
    # sql_getuserevents = ("""SELECT CAST(A.id AS CHAR) AS id, 
    #                      A.utc_start_dt, 
    #                      CAST(A.display_name AS CHAR) AS event_name
    #                      FROM events_scheduled A
    #                      INNER JOIN event_registration_log B
    #                      ON B.event_scheduled_id = A.id
    #                      WHERE B.user_id = %s;"""
    #                    )
    """ Gets event information where user is registered for either a team or division
        associated with an event. Note that this function, unlike 
        get_registration_events, does not get the event capacity.
    """
    # sql_getuserevents = ("""SELECT CAST(A.scheduled_event_id AS CHAR) AS id, 
    #                         C.utc_start_dt, 
    #                         CAST(C.display_name AS CHAR) AS event_name
    #                         FROM divisions A, events_scheduled C
    #                         INNER JOIN user_divisions B 
    #                         WHERE A.id = B.division_id AND B.user_id = %s AND A.scheduled_event_id = C.id
    #                         UNION
    #                         SELECT CAST(A.scheduled_event_id AS CHAR) AS id, 
    #                         C.utc_start_dt, 
    #                         CAST(C.display_name AS CHAR) AS event_name
    #                         FROM teams A, events_scheduled C
    #                         INNER JOIN user_teams B 
    #                         WHERE A.id = B.team_id AND B.user_id = %s AND A.scheduled_event_id = C.id      
    #                      """)
    """ Output is:
        'scheduled_event_id': int
        'type': char (enum['division', 'team'])
        'div_team_id': int
    """
    sql_getuserevents = ("""SELECT CAST(divisions.scheduled_event_id AS CHAR) AS scheduled_event_id,
                            CAST("division" AS CHAR) AS type,
                            CAST(user_divisions.division_id AS CHAR) AS div_team_id
                            FROM user_divisions
                            INNER JOIN divisions
                            ON user_divisions.division_id = divisions.id AND user_divisions.user_id = %s

                            UNION

                            SELECT CAST(teams.scheduled_event_id AS CHAR) AS scheduled_event_id,
                                    CAST("team" AS CHAR) AS type,
                                    CAST(user_teams.team_id AS CHAR) AS div_team_id
                            FROM user_teams
                            INNER JOIN teams
                            ON user_teams.team_id = teams.id AND user_teams.user_id = %s
                         """
                        )
    user_event_dict = await execute_query(
                                        db, 
                                        sql_getuserevents, 
                                        params=(str(discord_user_id), str(discord_user_id),)
                                        )
    if user_event_dict:
        for thing in user_event_dict:
            thing.scheduled_event_id = int(thing.scheduled_event_id)
            thing.div_team_id = int(thing.div_team_id)
    return user_event_dict


async def get_event_divisions(db, event_id):
    sql_geteventdivisions = ("""SELECT CAST(A.id AS CHAR) as id, 
                             CAST(A.name AS CHAR) AS name,
                             CAST(A.capacity AS CHAR) AS capacity, 
                             CAST(A.emote AS CHAR) AS emote
                             FROM divisions A
                             INNER JOIN events_scheduled B
                             ON B.id = A.scheduled_event_id
                             WHERE A.scheduled_event_id = %s"""
                             )
    divisions_dict = await execute_query(db, sql_geteventdivisions, params=(str(event_id),))
    # Recast numbers as numbers
    if divisions_dict:
        for division in divisions_dict:
            division.id = int(division.id)
            division.capacity = int(division.capacity)
    return divisions_dict


async def get_event_teams(db, event_id):
    sql_geteventteams = ("""SELECT CAST(A.id AS CHAR) AS id, 
                         CAST(A.name AS CHAR) AS name,
                         CAST(A.capacity AS CHAR) AS capacity,
                         CAST(A.emote AS CHAR) AS emote
                         FROM teams A
                         INNER JOIN events_scheduled B
                         ON B.id = A.scheduled_event_id
                         WHERE A.scheduled_event_id = %s"""
                         )
    teams_dict = await execute_query(db, sql_geteventteams, params=(str(event_id),))
    # Recast numbers as numbers
    if teams_dict:
        for team in teams_dict:
            team.id = int(team.id)
            team.capacity = int(team.capacity)
    return teams_dict


async def add_user_to_division(db, dataentry):
    """ Executes sql query command to insert data to database
        db = database connection object
        dataentry = [ user_id, division_id ] - all integers
    """
    sql_newrow="sp_assign_user_to_division"
    await execute_query(db, sql_newrow, params=dataentry, fetch=None, isProc=True)


async def add_user_to_team(db, dataentry):
    """ Executes sql query command to insert data to database
        db = database connection object
        dataentry = [ user_id, team_id ] - all integers
    """
    sql_newrow="sp_assign_user_to_team"
    await execute_query(db, sql_newrow, params=dataentry, fetch=None, isProc=True)


async def remove_user_from_division(db, db_user_id, event_id):
    """ Executes sql query command to delete data in the user_divisions database table
        db = database connection object
        dataentry = [ user_id, event_id ] - all integers
    """
    sql_remove_from_division = ("""DELETE A
                                FROM user_divisions A
                                INNER JOIN divisions B
                                ON A.division_id = B.id
                                WHERE B.scheduled_event_id = %s AND user_id = %s"""
                                )
    await execute_query(db, sql_remove_from_division, params=(event_id, db_user_id,))


async def remove_user_from_team(db, db_user_id, event_id):
    """ Executes sql query command to delete data in the user_teams database table
        db = database connection object
        dataentry = [ user_id, event_id ] - all integers
    """
    sql_remove_from_team = ("""DELETE A
                            FROM user_teams A
                            INNER JOIN teams B
                            ON A.team_id = B.id
                            WHERE B.scheduled_event_id = %s AND user_id = %s"""
                            )
    await execute_query(db, sql_remove_from_team, params=(event_id, db_user_id,))
