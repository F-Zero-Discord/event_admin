from typing import Literal
from datetime import datetime, timedelta
import discord
from discord import ui
from src.utils.view_utils import (
    set_step_info,
    highlight_step
)

#####################################
# Modal classes
#####################################

class NameModal(ui.Modal):
    def __init__(self, parent_view):
        super().__init__(title=f"Give your event a name")
        self.parent_view = parent_view

        preamble = ui.TextDisplay(
             "Limit: 40 characters"
        )
        self.text_input = ui.TextInput(
            label="Name",
            style=discord.TextStyle.short,
            default=self.parent_view.name,
            max_length=40
        )
        self.add_item(preamble)
        self.add_item(self.text_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Save the edited text back to the parent view
        self.parent_view.name = self.text_input.value

        # Check for valid input
        # - None implemented
        # - Should check db for whether the same name is already in it
    
        self.parent_view.completed()
        self.parent_view.dynamic_title.content = f"## New Event: {self.parent_view.name if self.parent_view.name is not None else ''}"
        self.parent_view.dynamic_name.content = f"  **{self.parent_view.name if self.parent_view.name is not None else ''} **"

        await interaction.response.edit_message(view=self.parent_view)


class DescriptionModal(ui.Modal):
    def __init__(self, parent_view):
        super().__init__(title=f"Give your event a description")
        self.parent_view = parent_view

        preamble = ui.TextDisplay(
             "Limit: 100 characters"
        )
        self.text_input = ui.TextInput(
            label="Description",
            style=discord.TextStyle.long,
            default=self.parent_view.description,
            max_length=100
        )
        self.add_item(preamble)
        self.add_item(self.text_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Save the edited text back to the parent view
        self.parent_view.description = self.text_input.value

        self.parent_view.completed()
        self.parent_view.dynamic_description.content = f"  **{self.parent_view.description if self.parent_view.description is not None else ''} **"

        await interaction.response.edit_message(view=self.parent_view)

#####################################
# LayoutView classes for each step
#####################################

class StepOneView(ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=300)
        # Internal variables
        self.step_info: list[str] = set_step_info()
        self.current_step: int = 0

        # User choices
        self.name: str | None = None
        self.description: str | None = None
        self.mode: Literal["99", "classic"] = "99"
        self.scoring: Literal["points", "placement"] = "points"
        self.machine_required: bool = False

        # Set layout components
        self.dynamic_title = ui.TextDisplay(
             content="## New Event",
             id=101)
        section_top_image = ui.Thumbnail(
             "attachment://container1.png"
            )
        section_top = ui.Section(
            ui.TextDisplay(highlight_step(self.step_info, self.current_step)),
            accessory=section_top_image
            )

        container_top = ui.Container()
        container_top.add_item(self.dynamic_title)
        container_top.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container_top.add_item(section_top)
        container_top.accent_color = discord.Colour.dark_purple()

        #######################
        # TextInput
        #######################
        event_name_section = ui.Section(
            ui.TextDisplay(content="Press button to set event name"), 
            accessory=self.name_button(self),
            id=301
            )
        self.dynamic_name = ui.TextDisplay(
            f"  **{self.name if self.name is not None else ''} **",
            id=302)
        event_description_section = ui.Section(
            ui.TextDisplay("Press button to set event description"),
            accessory=self.description_button(self))
        self.dynamic_description = ui.TextDisplay(
            f"  **{self.name if self.name is not None else ''} **",
            id=303)

        #######################
        # Select Menus
        #######################
        mode_options = [
            discord.SelectOption(label="99", 
                                 description="good ole 99s", 
                                 value="99",
                                 default=True),
            discord.SelectOption(label="classic", 
                                 description="for a more refined event", 
                                 value="classic",
                                 default=False)
        ]
        mode_row = ui.ActionRow()
        mode_select = self.mode_selection(self, mode_options=mode_options)

        scoring_options = [
            discord.SelectOption(label="points", 
                                 description="for the normies", 
                                 value="points",
                                 default=True),
            discord.SelectOption(label="placement", 
                                 description="for kingmaker-type events", 
                                 value="placement",
                                 default=False)
        ]
        scoring_row = ui.ActionRow()
        scoring_select = self.scoring_selection(self, scoring_options=scoring_options)

        machine_options = [
            discord.SelectOption(label="No", 
                                 description="users need not id machines with scores", 
                                 value="No",
                                 default=True),
            discord.SelectOption(label="Yes", 
                                 description="users must id machines with scores", 
                                 value="Yes",
                                 default=False)
        ]
        machine_row = ui.ActionRow()
        machine_select = self.machine_selection(self, machine_options=machine_options)

        mode_row.add_item(mode_select)
        scoring_row.add_item(scoring_select)
        machine_row.add_item(machine_select)

        

        container_bottom = ui.Container()
        container_bottom.add_item(event_name_section)
        container_bottom.add_item(self.dynamic_name)
        container_bottom.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container_bottom.add_item(event_description_section)
        container_bottom.add_item(self.dynamic_description)
        container_bottom.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container_bottom.add_item(ui.TextDisplay("Select the event mode:"))
        container_bottom.add_item(mode_row)
        container_bottom.add_item(ui.TextDisplay("Select the scoring method:"))
        container_bottom.add_item(scoring_row)
        container_bottom.add_item(ui.TextDisplay("Should users be required to enter machine used with score?"))
        container_bottom.add_item(machine_row)
        
        container_bottom.accent_color = discord.Colour.dark_red()

        self.add_item(container_top)
        self.add_item(container_bottom)

    #################################
    # Button classes
    #################################
    class name_button(ui.Button):
        def __init__(self, parent_view: ui.LayoutView):
              self.parent_view = parent_view
              super().__init__(label="Set Name", 
                               style=discord.ButtonStyle.green,
                               id=401)

        async def callback(self, interaction: discord.Interaction):
            # open modal
            await interaction.response.send_modal(NameModal(self.parent_view))


    class description_button(ui.Button):
        def __init__(self, parent_view: ui.LayoutView):
              self.parent_view = parent_view
              super().__init__(label="Set Description", style=discord.ButtonStyle.green)

        async def callback(self, interaction: discord.Interaction):
            # open modal
            await interaction.response.send_modal(DescriptionModal(self.parent_view))


    class next_step_button(ui.Button):
        def __init__(self, parent_view: ui.LayoutView):
              self.parent_view = parent_view
              super().__init__(label="Proceed to Next Step", 
                               style=discord.ButtonStyle.green,
                               disabled=False)

        async def callback(self, interaction: discord.Interaction):
            
            # # Debud output
            # output = f"""name: {self.parent_view.name}\n\
            #     description: {self.parent_view.description}\n\
            #     mode: {self.parent_view.mode}\n\
            #     scoring: {self.parent_view.scoring}\n\
            #     machine input with score: {self.parent_view.machine_required}"""

            # await interaction.response.send_message(content=output)
            self.parent_view.stop() # This finally releases the view.wait() in calling method

    #################################
    # Drowdown classes
    #################################
    class mode_selection(ui.Select):
        def __init__(self, parent_view: ui.LayoutView, mode_options: list[discord.SelectOption]):
            self.parent_view = parent_view
            super().__init__(options=mode_options)

        async def callback(self, interaction: discord.Interaction):
            # Assign output to class variable
            self.parent_view.mode = self.values[0]

            # Set default dropdown option to user's selection
            for option in self.options:
                option.default = (option.value == self.values[0])

            # Check to see if proceed button can be displayed
            self.parent_view.completed()

            # refresh message view
            await interaction.response.edit_message(view=self.parent_view)
    

    class scoring_selection(ui.Select):
        def __init__(self, parent_view: ui.LayoutView, scoring_options: list[discord.SelectOption]):
            self.parent_view = parent_view
            super().__init__(options=scoring_options)

        async def callback(self, interaction: discord.Interaction):
            # Assign output to class variable
            self.parent_view.scoring = self.values[0]

            # Set default dropdown option to user's selection
            for option in self.options:
                option.default = (option.value == self.values[0])
            
            # Check to see if proceed button can be displayed
            self.parent_view.completed()

            # refresh message view
            await interaction.response.edit_message(view=self.parent_view)


    class machine_selection(ui.Select):
        def __init__(self, parent_view: ui.LayoutView, machine_options: list[discord.SelectOption]):
            self.parent_view = parent_view
            super().__init__(options=machine_options)

        async def callback(self, interaction: discord.Interaction):
            # Assign output to class variable
            if self.values[0] == "No":
                self.parent_view.machine_required = False
            else:
                self.parent_view.machine_required = True
            
            # Set default dropdown option to user's selection
            for option in self.options:
                option.default = (option.value == self.values[0])

            # Check to see if proceed button can be displayed
            self.parent_view.completed()

            # refresh message view
            await interaction.response.edit_message(view=self.parent_view)


    #################################
    # Class utility methods
    #################################

    def completed(self) -> None:
        if self.name and self.description:
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