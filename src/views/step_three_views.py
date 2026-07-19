from typing import Literal
import discord
from discord import ui
from src.utils.event_class import Event, Division, Team, group_list
from src.utils.view_utils import (
    set_step_info,
    highlight_step
)

#####################################
# Modal classes
#####################################

class AddModal(ui.Modal):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        match self.parent_view.div_team:
            case "divisions":
                placeholder = "division"
                default_name = None
                default_altname = None
            case "teams":
                placeholder = "team"
                default_name = None
                default_altname = None
            case _:
                raise ValueError(f"Unexpected div_team value of {self.parent_view.div_team}.")
        super().__init__(title=f"Provide new {placeholder} information")

        preamble = ui.TextDisplay(content="Limit for each: 40 characters")
        self.name_input = ui.Label(
            text=f"{placeholder.capitalize()} Name",
            component=ui.TextInput(
                default=default_name,
                style=discord.TextStyle.short,
                max_length=40,
                required=True,
            )
        )
        self.add_item(preamble)
        self.add_item(self.name_input)

        self.altname_input = ui.Label(
            text=f"{placeholder.capitalize()} Alternate Name",
            component=ui.TextInput(
                default=default_altname,
                style=discord.TextStyle.short,
                max_length=40,
                required=False,
            )
        )
        self.add_item(self.altname_input)

        self.emote_input = ui.Label(text=f"{placeholder.capitalize()} Emote",
            component=ui.TextInput(
                default=None,
                style=discord.TextStyle.short,
                max_length=40,
                required=False,
            )
        )
        self.add_item(self.emote_input)

        self.capacity_input = ui.Label(
            text=f"{placeholder.capitalize()} Capacity",
            component=ui.TextInput(
                default=None,
                style=discord.TextStyle.short,
                max_length=3,
                required=False,
            )
        )
        self.add_item(self.capacity_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Check for valid input
        # - None implemented

        # Save the edited text back to the parent view
        match self.parent_view.div_team:
            case "divisions":
                d = Division()
                d.name = self.name_input.component.value
                d.alt_name = self.altname_input.component.value
                d.emote = self.emote_input.component.value
                d.capacity = self.capacity_input.component.value
                self.parent_view.divisions.append(d)
                # Add select option for dropdowns
                self.parent_view.division_options.append(discord.SelectOption(
                    label=d.name, 
                    value=d.name
                    )
                )
            case "teams":
                t = Team()
                t.name = self.name_input.component.value
                t.alt_name = self.altname_input.component.value
                t.emote = self.emote_input.component.value
                t.capacity = self.capacity_input.component.value
                self.parent_view.teams.append(t)
                # Add select option for dropdowns
                self.parent_view.team_options.append(discord.SelectOption(
                    label=t.name, 
                    value=t.name
                    )
                )
            case _: 
                raise ValueError(f"Unexpected div_team value of {self.parent_view.div_team}.")

        self.parent_view.component_status_manager()
    
        # self.parent_view.completed()
        await interaction.response.edit_message(view=self.parent_view)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        # This prints the error straight to your terminal console
        print(f"Error in modal {self.title}: {error}")
        
        # It is highly recommended to notify the user as well
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "Something went wrong while processing your request.", 
                ephemeral=True
            )


class EditDivTeamModal(ui.Modal):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        
        match self.parent_view.div_team:
            case "divisions":
                placeholder = "division"
                self.index = next((i for i, item in enumerate(self.parent_view.divisions) if item.name == self.parent_view.edit_option))
                default_name = self.parent_view.divisions[self.index].name
                default_altname = self.parent_view.divisions[self.index].alt_name
                default_emote = self.parent_view.divisions[self.index].emote
                default_capacity = self.parent_view.divisions[self.index].capacity
            case "teams":
                placeholder = "team"
                self.index = next((i for i, item in enumerate(self.parent_view.teams) if item.name == self.parent_view.edit_option))
                default_name = self.parent_view.teams[self.index].name
                default_altname = self.parent_view.teams[self.index].alt_name
                default_emote = self.parent_view.teams[self.index].emote
                default_capacity = self.parent_view.teams[self.index].capacity
            case _:
                raise ValueError(f"Unexpected div_team value of {self.parent_view.div_team}.")
        super().__init__(title=f"Provide new {placeholder} information")

        preamble = ui.TextDisplay(content="Limit for each: 40 characters")
        self.name_input = ui.Label(
            text=f"{placeholder.capitalize()} Name",
            component=ui.TextInput(
                default=default_name,
                style=discord.TextStyle.short,
                max_length=40,
                required=True,
            )
        )
        self.add_item(preamble)
        self.add_item(self.name_input)

        self.altname_input = ui.Label(
            text=f"{placeholder.capitalize()} Alternate Name",
            component=ui.TextInput(
                default=default_altname,
                style=discord.TextStyle.short,
                max_length=40,
                required=False,
            )
        )
        self.add_item(self.altname_input)

        self.emote_input = ui.Label(
            text=f"{placeholder.capitalize()} Emote",
            component=ui.TextInput(
                default=default_emote,
                style=discord.TextStyle.short,
                max_length=40,
                required=False,
            )
        )
        self.add_item(self.emote_input)

        self.capacity_input = ui.Label(
            text=f"{placeholder.capitalize()} Capacity",
            component=ui.TextInput(
                default=default_capacity,
                style=discord.TextStyle.short,
                max_length=3,
                required=False,
            )
        )
        self.add_item(self.capacity_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Check for valid input
        # - None implemented

        # Save the edited text back to the parent view
        match self.parent_view.div_team:
            case "divisions":
                self.parent_view.divisions[self.index].name = self.name_input.component.value
                self.parent_view.divisions[self.index].alt_name = self.altname_input.component.value
                self.parent_view.divisions[self.index].emote = self.emote_input.component.value
                self.parent_view.divisions[self.index].capacity = self.capacity_input.component.value
            case "teams":
                self.parent_view.teams[self.index].name = self.name_input.component.value
                self.parent_view.teams[self.index].alt_name = self.altname_input.component.value
                self.parent_view.teams[self.index].emote = self.emote_input.component.value
                self.parent_view.teams[self.index].capacity = self.capacity_input.component.value
            case _: 
                raise ValueError(f"Unexpected div_team value of {self.parent_view.div_team}.")

        # Update statuses and tracking variables in advance of refresh
        self.parent_view.refresh_divteam_options()
        self.parent_view.component_status_manager()
    
        # self.parent_view.completed()
        await interaction.response.edit_message(view=self.parent_view)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        # This prints the error straight to your terminal console
        print(f"Error in modal {self.title}: {error}")
        
        # It is highly recommended to notify the user as well
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "Something went wrong while processing your request.", 
                ephemeral=True
            )


class EditNeitherModal(ui.Modal):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        match self.parent_view.div_team:
            case "neither":
                default_name = self.parent_view.neither[0].name
                default_capacity = self.parent_view.neither[0].capacity
            case _:
                raise ValueError(f"Unexpected div_team value of {self.parent_view.div_team}.")
        super().__init__(title=f"Edit Event Details")

        name = ui.TextDisplay(f"Event Name\n    {default_name}\n\n")
        preamble = ui.TextDisplay("Limit 3 characters")
        self.capacity_input = ui.Label(
            text=f"Event Capacity",
                component=ui.TextInput(
                default=default_capacity,
                style=discord.TextStyle.short,
                max_length=3,
                required=False,
                )
        )
        self.add_item(name)
        self.add_item(preamble)
        self.add_item(self.capacity_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Check for valid input
        # - None implemented

        # Save the edited text back to the parent view
        match self.parent_view.div_team:
            case "neither":
                self.parent_view.neither[0].capacity = self.capacity_input.component.value
            case _: 
                raise ValueError(f"Unexpected div_team value of {self.parent_view.div_team}.")

        self.parent_view.component_status_manager()
    
        # self.parent_view.completed()
        await interaction.response.edit_message(view=self.parent_view)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        # This prints the error straight to your terminal console
        print(f"Error in modal {self.title}: {error}")
        
        # It is highly recommended to notify the user as well
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "Something went wrong while processing your request.", 
                ephemeral=True
            )


# Note: Must update to account for dropdown outside of modal.
#   Probably just a "confirm remove" button
class RemoveModal(ui.Modal):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        super().__init__(
            title=f"Remove {self.parent_view.div_team.rstrip("s")}"
            )
        
        self.add_item(ui.TextDisplay(
            f"Remove {self.parent_view.div_team.rstrip("s")} {self.parent_view.edit_option} from the event?"
            ))

    async def on_submit(self, interaction: discord.Interaction):
        # Check for valid input
        # - Below are checks to prevent division/team removal if already in the database.
        #   Could be improved upon to 
        #       1) create a function to remove a division/team
        #       2) develop a function to check if the division/team has registrants

        # Remove selected item
        match self.parent_view.div_team:
            case "divisions":
                # Check to see if has a database id: if so, don't allow removal
                for division in self.parent_view.divisions:
                    if division.name == self.parent_view.edit_option:
                        if division.id: # ids are assigned in the database
                            await interaction.response.send_message(
                                "This division is already in the database and cannot be removed using this interface. Contact lurch, Taco, or Nightmare to remove.", 
                                ephemeral=True)
                            return
                # Remove selected item from divisions
                self.parent_view.divisions = [
                    d for d in self.parent_view.divisions if d.name != self.parent_view.edit_option
                    ]
                # Remove option from division_options and reset selection
                self.parent_view.division_options = [
                    option for option in self.parent_view.division_options if option.label != self.parent_view.edit_option
                    ]
                self.parent_view.edit_option = None
            case "teams":
                # Check to see if has a database id: if so, don't allow removal
                for team in self.parent_view.teams:
                    if team.name == self.parent_view.edit_option:
                        if team.id: # ids are assigned in the database
                            await interaction.response.send_message(
                                "This team is already in the database and cannot be removed using this interface. Contact lurch, Taco, or Nightmare to remove.", 
                                ephemeral=True)
                            return
                # Remove selected item from teams
                self.parent_view.teams = [
                    t for t in self.parent_view.teams if t.name != self.parent_view.edit_option
                    ]
                # Remove option from team_options and reset selection
                self.parent_view.team_options = [
                    option for option in self.parent_view.team_options if option.label != self.parent_view.edit_option
                    ]
                self.parent_view.edit_option = None
            case _:
                raise ValueError(f"Unexpected div_team value of {self.parent_view.div_team}.")

        # Update statuses and tracking variables in advance of refresh
        self.parent_view.refresh_divteam_options()
        self.parent_view.component_status_manager()

        await interaction.response.edit_message(view=self.parent_view)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        # This prints the error straight to your terminal console
        print(f"Error in modal {self.title}: {error}")
        
        # It is highly recommended to notify the user as well
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "Something went wrong while processing your request.", 
                ephemeral=True
            )



#####################################
# LayoutView classes for each step
#####################################

class StepThreeView(ui.LayoutView):
    def __init__(self, event: Event):
        super().__init__(timeout=300)
        # Internal variables
        self.event_name: str = event.event_name
        self.step_info: list[str] = set_step_info()
        self.current_step: int = 2
        self.edit_option: int | None = None

        # Import input event information
            # Not yet implemented

        # User choices
        self.div_team: Literal["divisions", "teams", "neither"] = "neither"
        self.divisions: list[Division] = []
        self.teams: list[Team] = event.teams
        self.neither: list[Division] = []
        self.neither.append(Division())
        self.neither[0].name = event.event_name
        self.neither[0].alt_name = event.event_name
        if event.divisions:
            if (len(event.divisions) == 1) and (event.divisions[0].name == event.event_name):
                self.div_team = "neither"
                self.neither: list[Division] = event.divisions
            else:
                self.div_team = "divisions"
                self.divisions: list[Division] = event.divisions
        if event.teams:
            self.div_team = "teams"
        
        # self.neither: list[Division] = []
        # self.divisions: list[Division] = []
        # self.teams: list[Team] = []
        # self.neither: list[Division] = []

        # # Assign division info to neither if division a silent division
        # if (len(self.divisions) == 1) and (self.event_name == self.division[0].name):
        #     self.neither = self.divisions
        #     self.divisions = None 

        # Start division/team option list
        self.neither_option: list[discord.SelectOption] = [discord.SelectOption(label="N/A", value=0)]
        self.refresh_divteam_options()

        # Set layout components
        # Top container
        dynamic_title = ui.TextDisplay(
            content=f"## Event: {event.event_name if event.event_name is not None else ''}",
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

        # Middle container
        self.div_team_select = self.div_team_selection(self)
        div_team_row = ui.ActionRow()
        div_team_row.add_item(self.div_team_select)

        self.button_add = self.add_button(self)
        self.button_editdivteam = self.edit_div_team_button(self)
        self.button_remove = self.remove_button(self)
        button_row = ui.ActionRow()
        button_row.add_item(self.button_add)
        button_row.add_item(self.button_editdivteam)
        button_row.add_item(self.button_remove)

        self.edit_remove_select = self.edit_remove_selection(self)
        edit_remove_row = ui.ActionRow()
        edit_remove_row.add_item(self.edit_remove_select)

        container_middle = ui.Container()
        container_middle.add_item(
            ui.TextDisplay(
                content="Is this a team event, an event with multiple divisions, or neither?"
                ))
        container_middle.add_item(div_team_row)
        container_middle.add_item(button_row)
        container_middle.add_item(
            ui.TextDisplay(
                content="Use this dropdown to select a division or team to edit or remove."
                ))
        container_middle.add_item(edit_remove_row)

        # Team/Div text container
        self.dynamic_container = ui.Container()
        self.dynamic_text = self.div_team_listing()
        self.dynamic_container.add_item(self.dynamic_text)

        # Next Step Container
        self.next_button = self.next_step_button(self)
        next_button_section = ui.Section(
                    ui.TextDisplay(content="When you have made your selections..."),
                    accessory=self.next_button,
                    id=304
                )
        container_bottom = ui.Container()
        container_bottom.add_item(next_button_section)

        # Set labels and active/inactive of middle (action) container and next button
        self.component_status_manager()

        # Add containers to LayoutView
        self.add_item(container_top)
        self.add_item(container_middle)
        self.add_item(self.dynamic_container)
        self.add_item(container_bottom)
        container_top.accent_color = discord.Colour.dark_purple()
        container_middle.accent_color = discord.Colour.dark_red()
        self.dynamic_container.accent_color = discord.Colour.dark_red()
        container_bottom.accent_color = discord.Colour.dark_red()
        


    #################################
    # Drowdown classes
    #################################
    class div_team_selection(ui.Select):
        def __init__(self, parent_view: ui.LayoutView):
            self.parent_view = parent_view
            div_team_options = [
            discord.SelectOption(label="divisions", 
                                 description="Run the event with multiple divisions", 
                                 value="divisions",
                                 default=self.parent_view.div_team == "divisions"),
            discord.SelectOption(label="teams", 
                                 description="Create a team event", 
                                 value="teams",
                                 default=self.parent_view.div_team == "teams"),
            discord.SelectOption(label="neither", 
                                 description="Just one set of races", 
                                 value="neither",
                                 default=self.parent_view.div_team == "neither")
            ]
            super().__init__(options=div_team_options)

        async def callback(self, interaction: discord.Interaction):
            # Assign output to class variable
            self.parent_view.div_team = self.values[0]

            # Set default dropdown option to user's selection
            for option in self.options:
                option.default = (option.value == self.values[0])
            
            self.parent_view.component_status_manager()
            await interaction.response.edit_message(view=self.parent_view)


    class edit_remove_selection(ui.Select):
        def __init__(self, parent_view: ui.LayoutView):
            self.parent_view = parent_view

            match self.parent_view.div_team:
                case "divisions":
                    if self.parent_view.divisions:
                        options = self.parent_view.division_options
                    else: 
                        options = self.parent_view.neither_option
                case "teams":
                    if self.parent_view.teams:
                        options = self.parent_view.team_options
                    else: 
                        options = self.parent_view.neither_option
                case "neither":
                    options = self.parent_view.neither_option
                case _:
                    raise ValueError(f"Unexpected div_team value of {self.div_team}")
            
            super().__init__(options=options)

        async def callback(self, interaction: discord.Interaction):
            # Assign output to class variable
            self.parent_view.edit_option = self.values[0]

            # Set default dropdown option to user's selection
            for option in self.options:
                option.default = (option.value == self.values[0])
            
            self.parent_view.component_status_manager()
            await interaction.response.edit_message(view=self.parent_view)
                

    #################################
    # Button classes
    #################################

    class add_button(ui.Button):
        def __init__(self, parent_view: ui.LayoutView):
              self.parent_view = parent_view
              super().__init__(label="Add", 
                               style=discord.ButtonStyle.success,
                               disabled=True,
                               )

        async def callback(self, interaction: discord.Interaction):
            # open modal
            # await interaction.response.edit_message(view=self.parent_view)
            await interaction.response.send_modal(AddModal(self.parent_view))


    class edit_div_team_button(ui.Button):
        def __init__(self, parent_view: ui.LayoutView):
              self.parent_view = parent_view
              super().__init__(label="Edit", 
                               style=discord.ButtonStyle.danger,
                               disabled=True,
                            )

        async def callback(self, interaction: discord.Interaction):
            # open modal
            # await interaction.response.edit_message(view=self.parent_view)
            
            # Send to different modal depending on if "neither" is selected.
            match self.parent_view.div_team:
                case "neither":
                    await interaction.response.send_modal(EditNeitherModal(self.parent_view))
                case _:
                    await interaction.response.send_modal(EditDivTeamModal(self.parent_view))


    class remove_button(ui.Button):
        def __init__(self, parent_view: ui.LayoutView):
              self.parent_view = parent_view
              super().__init__(label="Remove", 
                               style=discord.ButtonStyle.danger,
                               disabled=True,
                            )

        async def callback(self, interaction: discord.Interaction):
            # open modal
            # await interaction.response.edit_message(view=self.parent_view)
            await interaction.response.send_modal(RemoveModal(self.parent_view))


    class next_step_button(ui.Button):
        def __init__(self, parent_view: ui.LayoutView):
              self.parent_view = parent_view
              super().__init__(label="Proceed to Next Step", 
                               style=discord.ButtonStyle.green,
                               disabled=False,
                            )

        async def callback(self, interaction: discord.Interaction):
            # Debug output
            # if not self.parent_view.end_time:
            #     self.parent_view.end_time = self.parent_view.start_time + self.parent_view.duration
            # output = f"""start time: {self.parent_view.start_time}\n\
            #     end_time: {self.parent_view.end_time}"""

            # await interaction.response.send_message(content=output)

            # If "neither", create a division with the name and alt name of 
            #   the event.
            if self.parent_view.div_team == "neither":
                self.parent_view.divisions = self.parent_view.neither

            self.parent_view.stop() # This finally releases the view.wait() in calling method


    #################################
    # Class utility methods
    #################################

    def refresh_divteam_options(self):
        self.division_options: list[discord.SelectOption] = []
        if self.divisions:
            for division in self.divisions:
                self.division_options.append(discord.SelectOption(
                    label=division.name, 
                    value=division.name
                    )
                )

        self.team_options: list[discord.SelectOption] = []
        if self.teams:
            for team in self.teams:
                self.team_options.append(discord.SelectOption(
                    label=team.name, 
                    value=team.name
                    )
                )


    
    def div_team_listing(self) -> ui.TextDisplay:
        """ Create the TextDisplay that lists the created divisions/teams.
        """
        match self.div_team:
            case "divisions":
                dynamic_group = ui.TextDisplay(
                    content=f"**Divisions:**\n{group_list(self.divisions) if self.divisions is not None else ''}"
                    )
            case "teams":
                dynamic_group = ui.TextDisplay(
                    content=f"**Teams:**\n{group_list(self.teams) if self.teams is not None else ''}"
                    )
            case "neither" | None:
                dynamic_group = ui.TextDisplay(content="-")
            case None:
                # triggered on LayoutView creation where div_team initialized to None
                dynamic_group = ui.TextDisplay(content="-")
            case _:
                raise ValueError(f"Unexpected div_team value of {self.div_team}")
        return dynamic_group
    

    def component_status_manager(self):
        """ Post-action method to change what is in container displaying 
            team and division in information. The following actions must 
            be taken:
                - If there is NO division/team, 
                    make edit and remove buttons inactive
                    change labels of add/edit/remove buttons to reflect team/division
                    make div/team dropdown inactive
                - If there is a division/team, 
                    make edit and remove buttons active
                    change labels of add/edit/remove buttons to reflect team/division
                    make div/team dropdown active
                - If 'neither' selected,
                    make add and remove buttons inactive
                    change label of edit button to "edit details"
                    make div/team dropdown inactive

        """
        # Manage labels and active status
        match self.div_team:
            case "divisions":
                self.button_add.disabled = False
                self.button_add.label = "Add Division"
                self.button_editdivteam.label = "Edit Division"
                self.button_remove.label = "Remove Divison"
                if self.divisions:
                    self.button_editdivteam.disabled = False
                    self.button_remove.disabled = False
                    self.next_button.disabled = False
                    self.edit_remove_select.disabled = False
                    self.edit_remove_select.options = self.division_options
                else:
                    self.button_editdivteam.disabled = True
                    self.button_remove.disabled = True
                    self.next_button.disabled = True
                    self.edit_remove_select.disabled = True
                    self.edit_remove_select.options = self.neither_option
            case "teams":
                self.button_add.disabled = False
                self.button_add.label = "Add Team"
                self.button_editdivteam.label = "Edit Team"
                self.button_remove.label = "Remove Team"
                self.edit_remove_select.options = self.team_options
                if self.teams:
                    self.button_editdivteam.disabled = False
                    self.button_remove.disabled = False
                    self.next_button.disabled = False
                    self.edit_remove_select.disabled = False
                    self.edit_remove_select.options = self.team_options
                else:
                    self.button_editdivteam.disabled = True
                    self.button_remove.disabled = True
                    self.next_button.disabled = True
                    self.edit_remove_select.disabled = True
                    self.edit_remove_select.options = self.neither_option
            case "neither":
                # Create one division with event_name
                self.button_add.disabled = True
                self.button_remove.disabled = True
                self.button_add.label = "-----"
                self.button_remove.label = "-----"
                self.button_editdivteam.label = "Edit Details"
                self.edit_remove_select.options = self.neither_option
                self.edit_remove_select.disabled = False
                self.button_editdivteam.disabled = False
                self.next_button.disabled = False
            case None: # Note: default now neither. this shouldnt occur.
                # Create one division with event_name
                self.button_add.disabled = True
                self.button_remove.disabled = True
                self.button_add.label = "-----"
                self.button_remove.label = "-----"
                self.edit_remove_select.disabled = True
                self.button_editdivteam.disabled = True
            case _:
                raise ValueError(f"Unexpected div_team value of {self.div_team}.")
        # Don't allow edit/removal of item if no item is in dropdown
        if not self.edit_option:
            self.button_editdivteam.disabled = True
            self.button_remove.disabled = True

        # Check to see if there are team or division database ids, and if so, lock
        #   out edit_remove_select and button_remove.
        if self.divisions:
            if self.divisions[0].id:
                self.div_team_select.disabled = True
        if self.teams:
            if self.teams[0].id:
                self.div_team_select.disabled = True
            
        self.dynamic_container.clear_items()
        self.dynamic_container.add_item(self.div_team_listing())