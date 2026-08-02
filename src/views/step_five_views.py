import discord
from discord import ui
from src.utils.event_class import Event
from src.utils.view_utils import (
    set_step_info,
    highlight_step
)

#####################################
# LayoutView classes for each step
#####################################

class StepFiveView(ui.LayoutView):
    def __init__(self, event: Event):
        super().__init__(timeout=300)
        # Internal variables
        self.step_info: list[str] = set_step_info()
        self.current_step: int = 4


        # Set layout components
        dynamic_title = ui.TextDisplay(
             content=f"## New Event: {event.event_name}",
             )
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

        # Middle Container
        container_middle = ui.Container()
        container_middle.add_item(ui.TextDisplay(
            content="Channel info not yet implemented. Move along. Move along."
            ))

        # Next Step Container
        next_button = self.next_step_button(self)
        next_button_section = ui.Section(
                    ui.TextDisplay(content="When you have made your selections...\n(NOTE: Ignore the intial 'didn't respond in time' error)"),
                    accessory=next_button
                )
        container_bottom = ui.Container()
        container_bottom.add_item(next_button_section)

        self.add_item(container_top)
        self.add_item(container_middle)
        self.add_item(container_bottom)
        container_top.accent_color = discord.Colour.dark_purple()
        container_middle.accent_color = discord.Colour.dark_red()
        container_bottom.accent_color = discord.Colour.dark_red()

    #################################
    # Button classes
    #################################
    class next_step_button(ui.Button):
        def __init__(self, parent_view: ui.LayoutView):
              self.parent_view = parent_view
              super().__init__(label="Finish", 
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

        async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
            # This prints the error straight to your terminal console
            print(f"Error in modal {self.title}: {error}")
            
            # It is highly recommended to notify the user as well
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Something went wrong while processing your request.", 
                    ephemeral=True
            )