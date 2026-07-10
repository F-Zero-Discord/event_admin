from datetime import datetime, timedelta
import discord
from discord import ui
from src.utils.view_utils import (
    time_string_to_datetime,
    discord_timestamp,
    set_step_info,
    highlight_step
)

#####################################
# Modal classes
#####################################

class StartModal(ui.Modal):
    def __init__(self, parent_view):
        super().__init__(title=f"Enter the event start time")
        self.parent_view = parent_view

        preamble = ui.TextDisplay(
             "Time must be in _YYYY-MM-DD HH:SS_ format, UTC"
        )
        self.text_input = ui.TextInput(
            label="Name",
            style=discord.TextStyle.short,
            default=self.parent_view.text_time,
            max_length=16
        )
        self.add_item(preamble)
        self.add_item(self.text_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Set default text with whatever was entered
        self.parent_view.text_time = self.text_input.value
        # Check for valid input
        time_dt = time_string_to_datetime(self.text_input.value)
        if time_dt:
             # Save the edited text back to the parent view
            self.parent_view.start_time = time_dt
            start_ts = discord_timestamp(dt=time_dt, format_type="long")
        else:
             raise ValueError(f"{self.text_input.value} is not in YYYY-MM-DD HH:SS format.")

        # Update the TextDisplay elements that say the event name
        self.parent_view.completed()
        self.parent_view.dynamic_start.content = f"  **{start_ts if start_ts is not None else ''} **"
        await interaction.response.edit_message(view=self.parent_view)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        """
        Catches errors raised inside on_submit or during modal processing.
        Sends a clean, custom error message back to the user privately.
        """
        # Distinguish your validation errors from unexpected backend bugs
        if isinstance(error, ValueError):
            error_message = f"❌ **Error:** {error}"
        else:
            error_message = "❌ **An unexpected error occurred.** Please try again later."

        # Send the custom error message to the user ephemerally
        await interaction.response.send_message(error_message, ephemeral=True)


class DurationModal(ui.Modal):
    def __init__(self, parent_view):
        super().__init__(title=f"Event's scoreboard duration? (minutes)")
        self.parent_view = parent_view

        preamble = ui.TextDisplay(
             "This determines how long the scoreboard is open. Limit: 3 characters, or 999 minutes"
        )
        self.text_input = ui.TextInput(
            label="Description",
            placeholder="e.g. 120, or 3 hours",
            style=discord.TextStyle.short,
            default=self.parent_view.text_duration,
            max_length=3
        )
        self.add_item(preamble)
        self.add_item(self.text_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Save the edited text back to the parent view
        self.parent_view.text_duration = self.text_input.value

        # Confirm time string is a nunber
        try:
            duration_int = int(self.text_input.value)
        except ValueError as e:
            print(f"{self.text_input.value} is not an integer.")
            raise

        # Turn duration integer into a timedelta, and add to start time
        if self.parent_view.start_time:
            self.parent_view.end_time = self.parent_view.start_time + timedelta(minutes=duration_int)
            duration_num = self.parent_view.end_time
            duration_num = discord_timestamp(dt=self.parent_view.end_time, format_type="long")
        else:
            self.parent_view.duration = timedelta(minutes=duration_int)
            duration_num = duration_int

        # Update the TextDisplay elements that say the event name
        self.parent_view.completed()
        self.parent_view.dynamic_duration.content = f"  **{duration_num if duration_num is not None else ''} **"
        await interaction.response.edit_message(view=self.parent_view)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        """
        Catches errors raised inside on_submit or during modal processing.
        Sends a clean, custom error message back to the user privately.
        """
        # Distinguish your validation errors from unexpected backend bugs
        if isinstance(error, ValueError):
            error_message = f"❌ **Error:** {error}"
        else:
            error_message = "❌ **An unexpected error occurred.** Please try again later."

        # Send the custom error message to the user ephemerally
        await interaction.response.send_message(error_message, ephemeral=True)


#####################################
# LayoutView classes for each step
#####################################

class StepTwoView(ui.LayoutView):
    def __init__(self, event_name: str):
        super().__init__(timeout=300)
        # Internal variables
        self.step_info: list[str] = set_step_info()
        self.current_step: int = 1
        self.text_time: str | None = None # time in string format for display in modal for default
        self.text_duration: str | None = None # text user input of duration modal

        # User choices
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self.duration: datetime | None = None

        # Set layout components
        dynamic_title = ui.TextDisplay(
             content=f"## New Event: {event_name}",
             id=101)
        section_top_image = ui.Thumbnail(
             "attachment://container1.png"
            )
        section_top = ui.Section(
            ui.TextDisplay(highlight_step(self.step_info, self.current_step)),
            accessory=section_top_image
            )

        container_top = ui.Container()
        container_top.add_item(dynamic_title)
        container_top.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container_top.add_item(section_top)
        container_top.accent_color = discord.Colour.dark_purple()

        #######################
        # TextInput
        #######################
        start_time_section = ui.Section(
            ui.TextDisplay(content="Press button to set event start time"), 
            accessory=self.start_time_button(self),
            id=301
            )
        self.dynamic_start = ui.TextDisplay(
            f"  **{self.start_time if self.start_time is not None else ''} **",
            id=302)
        duration_section = ui.Section(
            ui.TextDisplay("Press button to set event duration (minutes)"),
            accessory=self.duration_button(self))
        self.dynamic_duration = ui.TextDisplay(
            f"  **{self.end_time if self.end_time is not None else ''} **",
            id=303)
        
        container_bottom = ui.Container()
        container_bottom.add_item(start_time_section)
        container_bottom.add_item(self.dynamic_start)
        container_bottom.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container_bottom.add_item(duration_section)
        container_bottom.add_item(self.dynamic_duration)
        
        container_bottom.accent_color = discord.Colour.dark_red()

        self.add_item(container_top)
        self.add_item(container_bottom)


    #################################
    # Button classes
    #################################
    class start_time_button(ui.Button):
        def __init__(self, parent_view: ui.LayoutView):
              self.parent_view = parent_view
              super().__init__(label="Set Start Time", 
                               style=discord.ButtonStyle.green,
                               id=401)

        async def callback(self, interaction: discord.Interaction):
            # open modal
            # await interaction.response.edit_message(view=self.parent_view)
            await interaction.response.send_modal(StartModal(self.parent_view))


    class duration_button(ui.Button):
        def __init__(self, parent_view: ui.LayoutView):
              self.parent_view = parent_view
              super().__init__(label="Set Event Duration", style=discord.ButtonStyle.green)

        async def callback(self, interaction: discord.Interaction):
            # open modal
            # await interaction.response.edit_message(view=self.parent_view)
            await interaction.response.send_modal(DurationModal(self.parent_view))


    class next_step_button(ui.Button):
        def __init__(self, parent_view: ui.LayoutView):
              self.parent_view = parent_view
              super().__init__(label="Proceed to Next Step", 
                               style=discord.ButtonStyle.green,
                               disabled=False)

        async def callback(self, interaction: discord.Interaction):
            # Debug output
            # if not self.parent_view.end_time:
            #     self.parent_view.end_time = self.parent_view.start_time + self.parent_view.duration
            # output = f"""start time: {self.parent_view.start_time}\n\
            #     end_time: {self.parent_view.end_time}"""

            # await interaction.response.send_message(content=output)
            self.parent_view.stop() # This finally releases the view.wait() in calling method

    #################################
    # Class utility methods
    #################################

    def completed(self) -> None:
        if self.start_time and (self.end_time or self.duration):
            try:
                self.container_subbottom
            except:
                next_button_section = ui.Section(
                    ui.TextDisplay(content="When you have made your selections..."),
                    accessory=self.next_step_button(self),
                    id=304
                )
                self.container_subbottom = ui.Container(next_button_section)
                self.add_item(self.container_subbottom)