import time
import asyncio
import discord
from discord import app_commands, ui
from discord.ext import commands
from src.settings import get_settings
from src.fzd_db import (
    get_db_connection, 
    get_registration_events
)
from src.utils.event_class import Event, UserRegistrations
from src.utils.db_utils import refresh_event_list, registration_update_db
from src.views.register_views import (
    CancelView,
    LoadView,
    RegisterMenuView,
    DivTeamView,
    DivTeamEditView,
    ConfirmView,
    ConfirmWithdrawlView,
    ExitView
)

#############################################
# Functions for loading tasks
#############################################

async def loading_menu(interaction: discord.Interaction) -> None:
    """ Loading menu task to seek interaction from user while 
        database loading and view creation occur in the background.
    """
    load_view = LoadView()
    await interaction.response.send_message(view=load_view, ephemeral=True)
    await load_view.wait()


async def get_event_information() -> list[Event]:
    """
    """
    events: list[Event] = []

    async with get_db_connection() as db:
        reg_event_dict_list = await get_registration_events(db)
        event_name_list = [event['event_name'] for event in reg_event_dict_list if 'event_name' in event]
        event_id_list = [event['scheduled_event_id'] for event in reg_event_dict_list if 'scheduled_event_id' in event]

    # for event_id in event_id_list:
    #     event = await Event.load_event_from_database(scheduled_event_id=event_id)
    #     events.append(event)
    async with asyncio.TaskGroup() as eg:
        tasks = [eg.create_task(
            Event.load_event_from_database(scheduled_event_id=event_id)) for event_id in event_id_list]
    events = [task.result() for task in tasks]

    return events


async def get_user_reg_information(interaction: discord.Interaction) -> UserRegistrations:
    """
    """
    user = UserRegistrations(interaction)
    await user.get_user_info(interaction)
    return user


async def startup_tasks(interaction: discord.Interaction
        ) -> tuple[list[Event], UserRegistrations, ui.LayoutView]:
    """ Performs database retrievals and view creation while the user is 
        made to do the unthinkable: read text.
    """
    start = time.perf_counter()
    # Create task group for loading from the database
    async with asyncio.TaskGroup() as dlg:
        task1 = dlg.create_task(get_event_information())
        task2 = dlg.create_task(get_user_reg_information(interaction))

    events = task1.result()
    user = task2.result()

    database_load_time = time.perf_counter() - start
    print(f"Initial database calls complete: {database_load_time:.4f} seconds")

    start = time.perf_counter()
    # Create relevant views
    menu_view = RegisterMenuView(events, user)

    view_creation_time = time.perf_counter() - start
    print(f"Views created: {view_creation_time:.4f} seconds")

    return events, user, menu_view



#############################################
# Slash Commands
#############################################

class EventRegister(commands.Cog):
    def __init__(self, bot: commands.Bot, event_list: list[str]) -> None:
        self.bot: commands.Bot = bot
        self.event_list: list[str] | None = event_list

    """ Commands """
    @app_commands.command(
        name="event_register", description="Register for an event"
    )
    async def event_register(self, interaction: discord.Interaction):
        """
        """
        # Set up concurrent tasks to load info and create views while user reading
        # loading screen.
        async with asyncio.TaskGroup() as tg:
            task1 = tg.create_task(startup_tasks(interaction))
            task2 = tg.create_task(loading_menu(interaction))

        events, user, menu_view = task1.result()

        # End loop if no events are available to register for.
        if not events:
            no_events_message = CancelView("No events are currently available to register. Keep an eye out for new announcements and check in later")
            await interaction.edit_original_response(view=no_events_message)
            return
        
        # Send register menu message
        start = time.perf_counter()
        await interaction.edit_original_response(view=menu_view)
        print(f"Menu View await time: {(time.perf_counter() - start):.4f} seconds")
        timed_out = await menu_view.wait()

        # Check why we stopped waiting
        if timed_out:
            await interaction.followup.send("Selection timed out. Please try again.", ephemeral=True)
            return

        if menu_view.output_mode == "cancel":
            return
        # Grab selected event
        selected_event = [event for event in events if event.scheduled_event_id == menu_view.choice][0]
        # String to identify if the event supports divisions or teams.
        div_team_str = selected_event.div_or_team()

        match menu_view.output_mode:
            # Add a registration
            case "choice":
                # Check to see if event has only one division/team; if so, go straight to confirmation
                if selected_event.has_solo_division:
                    div_team_id = selected_event.divisions[0].id
                else:
                    div_team_view = DivTeamView(selected_event)
                    await interaction.edit_original_response(view=div_team_view)
                    timed_out = await div_team_view.wait()
                    
                    # Check why we stopped waiting
                    if timed_out:
                        await interaction.followup.send("Selection timed out. Please try again.", ephemeral=True)
                        return

                    div_team_id = div_team_view.choice

                # Go to confirmation view
                confirmation_view = ConfirmView(selected_event, div_team_id)
                await interaction.edit_original_response(view=confirmation_view)
                timed_out = await confirmation_view.wait()
                
                # Check why we stopped waiting
                if timed_out:
                    await interaction.followup.send("Selection timed out. Please try again.", ephemeral=True)
                    return

                # If not Cancel, add to database
                if confirmation_view.output_mode == "cancel":
                    # Make no changes
                    return
                else:
                    # Add user to event division/team
                    await registration_update_db(db_user_id=user.db_id,
                                           div_team_str=div_team_str,
                                            add_div_team_id=div_team_id)
                    exit_view = ExitView()
                    await interaction.edit_original_response(view=exit_view)
                
            # Edit or remove a registration
            case "edit":
                div_team_id = [user_reg["div_team_id"] for user_reg in user.registrations if user_reg["scheduled_event_id"] == selected_event.scheduled_event_id][0]
                # Check to see if event has only one division/team; if so, go straight to confirmation
                if selected_event.has_solo_division:
                    withdraw_view = ConfirmWithdrawlView(selected_event, div_team_id)
                    timed_out = await withdraw_view.wait()
                    
                    # Check why we stopped waiting
                    if timed_out:
                        await interaction.followup.send("Selection timed out. Please try again.", ephemeral=True)
                        return

                    if withdraw_view.output_mode == "cancel":
                        # Make no changes
                        cancel_message = CancelView("No registration actions taken.")
                        await interaction.edit_original_response(view=cancel_message)
                        return
                    else:
                        # Update database to remove user from division/team.
                        await registration_update_db(db_user_id=user.db_id, 
                                                div_team_str=div_team_str,
                                                rm_div_team_id=div_team_id)
                        exit_view = ExitView()
                        await interaction.edit_original_response(view=exit_view)
                else:
                    div_team_edit_view = DivTeamEditView(event=selected_event, 
                                                         existing_div_team_id=div_team_id)
                    await interaction.edit_original_response(view=div_team_edit_view)
                    timed_out = await div_team_edit_view.wait()
                    
                    # Check why we stopped waiting
                    if timed_out:
                        await interaction.followup.send("Selection timed out. Please try again.", ephemeral=True)
                        return

                    match div_team_edit_view.output_mode:
                        case "cancel":
                            # Make no changes
                            return

                        case "edit":
                            # Change the div_team in the event
                            new_div_team_id = div_team_edit_view.choice

                            # Go to confirmation view
                            confirmation_view = ConfirmView(selected_event, new_div_team_id)
                            await interaction.edit_original_response(view=confirmation_view)
                            timed_out = await confirmation_view.wait()
                                                
                            # Check why we stopped waiting
                            if timed_out:
                                await interaction.followup.send("Selection timed out. Please try again.", ephemeral=True)
                                return

                            if confirmation_view.output_mode == "cancel":
                                # Make no changes
                                return
                            else:
                                # Update database to change user's division/team.
                                await registration_update_db(db_user_id=user.db_id, 
                                                       div_team_str=div_team_str,
                                                       add_div_team_id=new_div_team_id, 
                                                       rm_div_team_id=div_team_id)
                                exit_view = ExitView()
                                await interaction.edit_original_response(view=exit_view)

                        case "withdraw":
                            withdraw_view = ConfirmWithdrawlView(selected_event, div_team_id)
                            await interaction.edit_original_response(view=withdraw_view)
                            timed_out = await withdraw_view.wait()
                                                
                            # Check why we stopped waiting
                            if timed_out:
                                await interaction.followup.send("Selection timed out. Please try again.", ephemeral=True)
                                return
                            
                            if withdraw_view.output_mode == "cancel":
                                # Make no changes
                                return
                            else:
                                # Update database to remove user from division/team.
                                await registration_update_db(db_user_id=user.db_id, 
                                                        div_team_str=div_team_str,
                                                        rm_div_team_id=div_team_id)
                                exit_view = ExitView()
                                await interaction.edit_original_response(view=exit_view)
                        case _:
                            raise ValueError(
        f"'output_mode' must be 'cancel', 'edit', 'withdraw', not {div_team_edit_view.output_mode}."
                                    )



async def setup(bot: commands.Bot):
    server_id = get_settings().server_id
    GUILD_ID = discord.Object(id=server_id)
    # Get initial event list. To be refreshed upon /event_create_update calls
    event_list = await refresh_event_list()
    await bot.add_cog(EventRegister(bot, event_list), guild=GUILD_ID)