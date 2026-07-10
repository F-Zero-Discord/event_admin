from typing import Literal
import discord
from discord import app_commands
from discord.ext import commands
from src.settings import get_settings
from src.utils.event_class import Event
from src.views.step_one_views import StepOneView
from src.views.step_two_views import StepTwoView
from src.views.step_three_views import StepThreeView


class EventMgr(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Commands
    @app_commands.command(
        name="new_event", description="Create a new event (database safe)"
    )
    async def new_event(self, interaction: discord.Interaction):
        # Initialize database variable object
        event = Event()
        
        # # Present the first step menu to user
        # view = StepOneView()
        thumb = discord.File(fp="images/container1.png",filename="container1.png")
        # await interaction.response.send_message(view=view, file=thumb)
        # timed_out = await view.wait()
    
        # # Check why we stopped waiting
        # if timed_out:
        #     await interaction.followup.send("Selection timed out. Please try again.", ephemeral=True)
        #     return
        
        # # Populate event variables into Event object instance
        # event.event_name = view.name
        # event.description = view.description
        # event.mode = view.mode
        # event.scoring = view.scoring
        # event.machine_required = view.machine_required
        
        event.event_name = "Big Test Event"
        # # Present the second step menu to user
        # view = StepTwoView(event.event_name)
        # await interaction.edit_original_response(view=view)
        # timed_out = await view.wait()
    
        # # Check why we stopped waiting
        # if timed_out:
        #     await interaction.followup.send("Selection timed out. Please try again.", ephemeral=True)
        #     return
        
        # # Populate event variables into Event object instance
        # event.start_time = view.start_time
        # event.start_time = view.end_time

        # Present the third step menu to user
        view = StepThreeView(event.event_name)
        await interaction.response.send_message(view=view, file=thumb)
        # await interaction.edit_original_response(view=view, file=thumb)
        timed_out = await view.wait()
    
        # Check why we stopped waiting
        if timed_out:
            await interaction.followup.send("Selection timed out. Please try again.", ephemeral=True)
            return



async def setup(bot: commands.Bot):
    server_id = get_settings().server_id
    GUILD_ID = discord.Object(id=server_id)
    await bot.add_cog(EventMgr(bot), guild=GUILD_ID)