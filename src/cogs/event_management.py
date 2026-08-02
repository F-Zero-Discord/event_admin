from typing import Literal
import discord
from discord import app_commands
from discord.ext import commands
from discord import ui
from src.settings import get_settings
from src.utils.event_class import Event, test_event
from src.utils.db_utils import refresh_event_list
from src.views.step_one_views import StepOneView
from src.views.step_two_views import StepTwoView
from src.views.step_three_views import StepThreeView
from src.views.step_four_views import StepFourView
from src.views.step_five_views import StepFiveView
from src.views.confirm_view import ConfirmView, SimpleMessageView


class EventMgr(commands.Cog):
    def __init__(self, bot: commands.Bot, event_list: list[str]) -> None:
        self.bot: commands.Bot = bot
        self.event_list: list[str] | None = event_list

    
    ''' Autocomplete methods '''
    async def event_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        options = [event for event in self.event_list if current.lower() in event.lower()]

        # Return up to 25 results (25=discord limit)
        return [app_commands.Choice(name=event, value=f"{event}") for event in options[:25]]
    

    """ Commands """
    @app_commands.command(
        name="event_create_update", description="Create a new event (database safe)"
    )
    async def event_create_update(self, interaction: discord.Interaction, event_choice: str | None = None):
        """
        """
        self.event_list = await refresh_event_list()

        # Initialize database variable object
        if event_choice:
            # Load event info
            event = await Event.load_event_from_database(scheduled_event_name=event_choice)
        else:
            event = Event()
        
        # Present the first step menu to user
        view = StepOneView(event=event)
        thumb = discord.File(fp="images/container1.png",filename="container1.png")
        await interaction.response.send_message(view=view, file=thumb)
        timed_out = await view.wait()
    
        # Check why we stopped waiting
        if timed_out:
            await interaction.followup.send("Selection timed out. Please try again.", ephemeral=True)
            return
        
        # Populate event variables into Event object instance
        event.event_name = view.name
        event.description = view.description
        event.mode = view.mode
        event.scoring = view.scoring
        event.machine_required = view.machine_required
        view.clear_items()
        
        # event.event_name = "Big Test Event"
        # Present the second step menu to user
        view = StepTwoView(event=event)
        await interaction.edit_original_response(view=view)
        timed_out = await view.wait()
    
        # Check why we stopped waiting
        if timed_out:
            await interaction.followup.send("Selection timed out. Please try again.", ephemeral=True)
            return
        
        # Populate event variables into Event object instance
        event.start_time = view.start_time
        event.end_time = view.end_time
        view.clear_items()

        # Present the third step menu to user
        view = StepThreeView(event=event)
        # await interaction.response.send_message(view=view, file=thumb)
        await interaction.edit_original_response(view=view)
        timed_out = await view.wait()
    
        # Check why we stopped waiting
        if timed_out:
            await interaction.followup.send("Selection timed out. Please try again.", ephemeral=True)
            return
        
        # Populate event variables into Event object instance
        event.divisions = view.divisions
        event.teams = view.teams
        view.clear_items()

        view = StepFourView(event=event)
        await interaction.edit_original_response(view=view)
        timed_out = await view.wait()
    
        # Check why we stopped waiting
        if timed_out:
            await interaction.followup.send("Selection timed out. Please try again.", ephemeral=True)
            return
        
        # Populate event variables into Event object instance
        event.reg_open = view.start_time
        event.reg_close = view.end_time
        view.clear_items()

        view = StepFiveView(event=event)
        # await interaction.response.send_message(view=view, file=thumb)
        await interaction.edit_original_response(view=view)
        timed_out = await view.wait()
    
        # Check why we stopped waiting
        if timed_out:
            await interaction.followup.send("Selection timed out. Please try again.", ephemeral=True)
            return
        
        view.clear_items()
        
        # Post final results before committing to database
        view = ConfirmView(event=event)
        await interaction.edit_original_response(view=view)
        timed_out = await view.wait()
    
        # Check why we stopped waiting
        if timed_out:
            await interaction.followup.send("Selection timed out. Please try again.", ephemeral=True)
            return
        
        if view.confirmed:
            # Save to database
            await event.send_event_to_database()
            # Print result
            view = SimpleMessageView(f"Event added to database\n{event:detail}")
            await interaction.edit_original_response(view=view)
        else:
            # Print no event created.
            # await interaction.edit_original_response(content="No event created",view=None)
            view = SimpleMessageView(f"No event created.")
            await interaction.edit_original_response(view=view)

        # # Testing
        # event = test_event()
        # # Save to database
        # print(event)
        # await event.send_event_to_database()
        # # Print result interaction.response.edit_message
        # # await interaction.response.send_message(content=f"Event added to database\n{event:detail}", view=None)
        # await interaction.edit_original_response(content=f"Event added to database\n{event:detail}", view=None)


    async def cog_load(self):
        self.event_create_update.autocomplete("event_choice")(self.event_autocomplete)


async def setup(bot: commands.Bot):
    server_id = get_settings().server_id
    GUILD_ID = discord.Object(id=server_id)
    # Get initial event list. To be refreshed upon /event_create_update calls
    event_list = await refresh_event_list()
    await bot.add_cog(EventMgr(bot, event_list), guild=GUILD_ID)