from typing import Literal
import discord
from discord import ui
from src.utils.view_utils import (
    set_step_info,
    highlight_step,
    group_list
)
from src.utils.event_class import Division, Team

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
        super().__init__(title=f"Provide new {placeholder} information", custom_id=str(self.parent_view.custom_id))
        self.parent_view.custom_id += self.parent_view.custom_id

        preamble = ui.TextDisplay(content="Limit for each: 40 characters")
        self.name_input = ui.TextInput(
            label=f"{placeholder.capitalize()} Name",
            default=default_name,
            style=discord.TextStyle.short,
            max_length=40,
            required=True,
            custom_id=str(self.parent_view.custom_id)
        )
        self.parent_view.custom_id += self.parent_view.custom_id
        self.add_item(preamble)
        self.add_item(self.name_input)

        self.altname_input = ui.TextInput(
            label=f"{placeholder.capitalize()} Alternate Name",
            default=default_altname,
            style=discord.TextStyle.short,
            max_length=40,
            required=False,
            custom_id=str(self.parent_view.custom_id)
        )
        self.parent_view.custom_id += self.parent_view.custom_id
        self.add_item(self.altname_input)

        self.emote_input = ui.TextInput(
            label=f"{placeholder.capitalize()} Emote",
            default=None,
            style=discord.TextStyle.short,
            max_length=40,
            required=False,
            custom_id=str(self.parent_view.custom_id)
        )
        self.parent_view.custom_id += self.parent_view.custom_id
        self.add_item(self.emote_input)

        self.capacity_input = ui.TextInput(
            label=f"{placeholder.capitalize()} Capacity",
            default=None,
            style=discord.TextStyle.short,
            max_length=3,
            required=False,
            custom_id=str(self.parent_view.custom_id)
        )
        self.parent_view.custom_id += self.parent_view.custom_id
        self.add_item(self.capacity_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Check for valid input
        # - None implemented

        # Save the edited text back to the parent view
        match self.parent_view.div_team:
            case "divisions":
                d = Division()
                d.name = self.name_input.value
                d.alt_name = self.altname_input.value
                d.emote = self.emote_input.value
                d.capacity = self.capacity_input.value
                self.parent_view.divisions.append(d)
            case "teams":
                t = Team()
                t.name = self.name_input.value
                t.alt_name = self.altname_input.value
                t.emote = self.emote_input.value
                t.capacity = self.capacity_input.value
                self.parent_view.teams.append(t)
            case _: 
                raise ValueError(f"Unexpected div_team value of {self.parent_view.div_team}.")

        self.parent_view.div_team_container()
    
        # self.parent_view.completed()
        await interaction.response.edit_message(view=self.parent_view)


class EditDivTeamModal(ui.Modal):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        self.index = self.parent_view.edit_option
        match self.parent_view.div_team:
            case "divisions":
                placeholder = "division"
                default_name = self.parent_view.divisions[self.index].name
                default_altname = self.parent_view.divisions[self.index].altname
                default_emote = self.parent_view.divisions[self.index].emote
                default_capacity = self.parent_view.divisions[self.index].capacity
            case "teams":
                placeholder = "team"
                default_name = self.parent_view.teams[self.index].name
                default_altname = self.parent_view.teams[self.index].altname
                default_emote = self.parent_view.teams[self.index].emote
                default_capacity = self.parent_view.teams[self.index].capacity
            case _:
                raise ValueError(f"Unexpected div_team value of {self.parent_view.div_team}.")
        super().__init__(title=f"Provide new {placeholder} information", custom_id=str(self.parent_view.custom_id))
        self.parent_view.custom_id += self.parent_view.custom_id

        preamble = ui.TextDisplay(content="Limit for each: 40 characters")
        self.name_input = ui.TextInput(
            label=f"{placeholder.capitalize()} Name",
            default=default_name,
            style=discord.TextStyle.short,
            max_length=40,
            required=True,
            custom_id=str(self.parent_view.custom_id)
        )
        self.parent_view.custom_id += self.parent_view.custom_id
        self.add_item(preamble)
        self.add_item(self.name_input)

        self.altname_input = ui.TextInput(
            label=f"{placeholder.capitalize()} Alternate Name",
            default=default_altname,
            style=discord.TextStyle.short,
            max_length=40,
            required=False,
            custom_id=str(self.parent_view.custom_id)
        )
        self.parent_view.custom_id += self.parent_view.custom_id
        self.add_item(self.altname_input)

        self.emote_input = ui.TextInput(
            label=f"{placeholder.capitalize()} Emote",
            default=default_emote,
            style=discord.TextStyle.short,
            max_length=40,
            required=False,
            custom_id=str(self.parent_view.custom_id)
        )
        self.parent_view.custom_id += self.parent_view.custom_id
        self.add_item(self.emote_input)

        self.capacity_input = ui.TextInput(
            label=f"{placeholder.capitalize()} Capacity",
            default=default_capacity,
            style=discord.TextStyle.short,
            max_length=3,
            required=False,
            custom_id=str(self.parent_view.custom_id)
        )
        self.parent_view.custom_id += self.parent_view.custom_id
        self.add_item(self.capacity_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Check for valid input
        # - None implemented

        # Save the edited text back to the parent view
        match self.parent_view.div_team:
            case "divisions":
                self.parent_view.divisions[self.index].name = self.name_input.value
                self.parent_view.divisions[self.index].alt_name = self.altname_input.value
                self.parent_view.divisions[self.index].emote = self.emote_input.value
                self.parent_view.divisions[self.index].capacity = self.capacity_input.value
            case "teams":
                self.parent_view.teams[self.index].name = self.name_input.value
                self.parent_view.teams[self.index].alt_name = self.altname_input.value
                self.parent_view.teams[self.index].emote = self.emote_input.value
                self.parent_view.teams[self.index].capacity = self.capacity_input.value
            case _: 
                raise ValueError(f"Unexpected div_team value of {self.parent_view.div_team}.")

        self.parent_view.div_team_container()
    
        # self.parent_view.completed()
        await interaction.response.edit_message(view=self.parent_view)


class EditNeitherModal(ui.Modal):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        match self.parent_view.div_team:
            case "neither":
                default_name = self.parent_view.divisions[0].name
                default_capacity = self.parent_view.divisions[0].capacity
            case _:
                raise ValueError(f"Unexpected div_team value of {self.parent_view.div_team}.")
        super().__init__(title=f"Edit Event Detailss", custom_id=str(self.parent_view.custom_id))
        self.parent_view.custom_id += self.parent_view.custom_id

        name = ui.TextDisplay(f"Event Name\n    {default_name}\n\n")
        preamble = ui.TextDisplay("Limit 3 characters")
        self.capacity_input = ui.TextInput(
            label=f"Event Capacity",
            default=default_capacity,
            style=discord.TextStyle.short,
            max_length=3,
            required=False,
            custom_id=str(self.parent_view.custom_id)
        )
        self.parent_view.custom_id += self.parent_view.custom_id
        self.add_item(name)
        self.add_item(preamble)
        self.add_item(self.capacity_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Check for valid input
        # - None implemented

        # Save the edited text back to the parent view
        match self.parent_view.div_team:
            case "neither":
                self.parent_view.neither[0].capacity = self.capacity_input.value
            case _: 
                raise ValueError(f"Unexpected div_team value of {self.parent_view.div_team}.")

        self.parent_view.div_team_container()
    
        # self.parent_view.completed()
        await interaction.response.edit_message(view=self.parent_view)

# Note: Must update to account for dropdown outside of modal.
#   Probably just a "confirm remove" button
class RemoveModal(ui.Modal):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        super().__init__(
            title=f"Remove a {self.parent_view.div_team.rstrip("s")}",
            custom_id=str(self.parent_view.custom_id))
        self.parent_view.custom_id += self.parent_view.custom_id

        # Set options
        match self.parent_view.div_team:
            case "divisions":
                options = []
                for division in self.parent_view.divisions:
                    options.append(
                        discord.SelectOption(label=division.name, value=division.name)
                    )
            case "teams":
                options = []
                for team in self.parent_view.teams:
                    options.append(
                        discord.SelectOption(label=team.name, value=team.name)
                    )
            case _:
                raise ValueError(f"Unexpected div_team value of {self.parent_view.div_team}.")

        remove_select = ui.Select(options=options, required=True)

        preamble = ui.TextDisplay(
             content=f"Select a {self.parent_view.div_team.rstrip("s")} to remove")
        
        self.add_item(preamble)
        self.add_item(remove_select)

    async def on_submit(self, interaction: discord.Interaction):
        # Check for valid input
        # - None implemented


        # # Remove selected item
        # match self.parent_view.div_team:
        #     case "divisions":
        #         # Remove selected item from divisions
        #         self.parent_view.divisions = [
        #             d for d in self.parent_view.divisions if d.get("name") != self.remove_select.value
        #             ]
        #         # Update menu
        #         self.parent_view.dynamic_group.content = (
        #             f"**Divisions:**\n{group_list(self.parent_view.divisions) if self.parent_view.divisions is not None else ''}"
        #             )
        #         # Disable remove button if no more divisions
        #         if self.parent_view.divisions:
        #             self.parent_view.button_remove.disabled = False
        #         else:
        #             self.parent_view.button_remove.disabled = True
        #     case "teams":
        #         # Remove selected item from teams
        #         self.parent_view.teams = [
        #             t for t in self.parent_view.teams if t.get("name") != self.remove_select.value
        #             ]
        #         # Update Menu
        #         self.parent_view.dynamic_group.content = (
        #             f"**Teams:**\n{group_list(self.parent_view.teams) if self.parent_view.teams is not None else ''}"
        #             )
        #         # Disable remove button if no more teams
        #         if self.parent_view.teams:
        #             self.parent_view.button_remove.disabled = False
        #         else:
        #             self.parent_view.button_remove.disabled = True
        #     case _:
        #         raise ValueError(f"Unexpected div_team value of {self.parent_view.div_team}.")

        
        # self.parent_view.container_bottom2.clear_items()
        # self.parent_view.container_bottom2.add_item(self.parent_view.dynamic_group)

        await interaction.response.edit_message(view=self.parent_view)


#####################################
# LayoutView classes for each step
#####################################

class StepThreeView(ui.LayoutView):
    def __init__(self, event_name: str):
        super().__init__(timeout=300)
        # Internal variables
        self.event_name: str = event_name
        self.step_info: list[str] = set_step_info()
        self.current_step: int = 2
        self.edit_option: int | None = None
        self.custom_id: int = 0

        # Import input event information
            # Not yet implemented

        # User choices
        self.div_team: Literal["divisions", "teams", "neither"] = "neither"
        self.divisions: list[Division] = []
        self.teams: list[Team] = []
        self.neither: list[Division] = []

        # Create no-division division
        self.neither.append(Division())
        self.neither[0].name = event_name
        self.neither[0].alt_name = event_name

        # Assign division info to neither if division a silent division
        if (len(self.divisions) == 1) and (self.event_name == self.division[0].name):
            self.neither = self.divisions
            self.divisions = None 

        # Set layout components
        # Top container
        dynamic_title = ui.TextDisplay(
             content=f"## New Event: {event_name}"
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
        div_team_select = self.div_team_selection(self)
        div_team_row = ui.ActionRow()
        div_team_row.add_item(div_team_select)

        self.button_add = self.add_button(self)
        self.button_editdivteam = self.edit_div_team_button(self)
        self.button_remove = self.remove_button(self)
        button_row = ui.ActionRow()
        button_row.add_item(self.button_add)
        button_row.add_item(self.button_editdivteam)
        button_row.add_item(self.button_remove)

        self.edit_remove_select = self.edit_remove_selection(self)
        edit_remove_row = ui.ActionRow()
        edit_remove_row.add_item(edit_remove_row)

        container_middle = ui.Container()
        container_middle.add_item(
            ui.TextDisplay(
                content="Is this a team event, an event with multiple divisions, or neither?"
                ))
        container_middle.add_item(div_team_row)
        container_middle.add_item(button_row)
        container_middle.add_item(edit_remove_row)

        # Set labels and active/inactive of middle (action) container
        self.div_team_container()

        # Team/Div text container
        dynamic_container = ui.Container()
        self.dynamic_text = self.div_team_listing()
        dynamic_container.add_item(self.dynamic_text)

        # Next Step Container
        self.next_button = self.next_step_button(self)
        next_button_section = ui.Section(
                    ui.TextDisplay(content="When you have made your selections..."),
                    accessory=self.next_button,
                    id=304
                )
        container_bottom = ui.Container()
        container_bottom.add_item(container_bottom)

        # Add containers to LayoutView
        self.add_item(container_top)
        self.add_item(container_middle)
        self.add_item(self.dynamic_container)
        self.add_item(container_bottom)
        container_top.accent_color = discord.Colour.dark_purple()
        container_bottom.accent_color = discord.Colour.dark_red()
        self.dynamic_container.accent_color = discord.Colour.dark_red()


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
                                 default=False),
            discord.SelectOption(label="teams", 
                                 description="Create a team event", 
                                 value="teams",
                                 default=False),
            discord.SelectOption(label="neither", 
                                 description="Just one set of races", 
                                 value="neither",
                                 default=True)
            ]
            super().__init__(options=div_team_options, custom_id=str(self.parent_view.custom_id))
            self.parent_view.custom_id += self.parent_view.custom_id

        async def callback(self, interaction: discord.Interaction):
            # Assign output to class variable
            self.parent_view.div_team = self.values[0]

            # Set default dropdown option to user's selection
            for option in self.options:
                option.default = (option.value == self.values[0])
            
            self.parent_view.div_team_container()
            await interaction.response.edit_message(view=self.parent_view)


    class edit_remove_selection(ui.Select):
        def __init__(self, parent_view: ui.LayoutView):
            self.parent_view = parent_view

            options = []
            match self.parent_view.div_team:
                case "divisions":
                    if self.parent_view.divisions:
                        options.append(
                            discord.SelectOption(label="N/A", value=0))
                    else: 
                        for i, division in self.parent_view.divisions:
                            options.append(
                                discord.SelectOption(label=division.name, value=i))
                case "teams":
                    if self.parent_view.teams:
                        options.append(
                            discord.SelectOption(label="N/A", value=0))
                    else: 
                        for i, team in enumerate(self.parent_view.teams):
                            options.append(
                                discord.SelectOption(label=team.name, value=i))
                case "neither":
                    options.append(
                        discord.SelectOption(label="N/A", value=0))
                case _:
                    options.append(
                        discord.SelectOption(label="N/A", value=0))
            
            super().__init__(options=options)

        async def callback(self, interaction: discord.Interaction):
            # Assign output to class variable
            self.parent_view.edit_option = self.values[0]

            # Set default dropdown option to user's selection
            for option in self.options:
                option.default = (option.value == self.values[0])
            
            self.parent_view.div_team_container()
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
                               custom_id=str(self.parent_view.custom_id))
              self.parent_view.custom_id += self.parent_view.custom_id

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
                               custom_id=str(self.parent_view.custom_id))
              self.parent_view.custom_id += self.parent_view.custom_id

        async def callback(self, interaction: discord.Interaction):
            # open modal
            # await interaction.response.edit_message(view=self.parent_view)
            
            # Send to different modal depending on if "neither" is selected.
            match self.div_team:
                case "neither":
                    await interaction.response.send_modal(EditNeitherModal(self.parent_view))
                case _:
                    await interaction.response.send_modal(EditDivTeamModal(self.parent_view))

    
    # class edit_neither_button(ui.Button):
    #     def __init__(self, parent_view: ui.LayoutView):
    #           self.parent_view = parent_view
    #           super().__init__(label="Edit Capacity", 
    #                            style=discord.ButtonStyle.danger,
    #                            disabled=True,
    #                            custom_id=str(self.parent_view.custom_id))
    #           self.parent_view.custom_id += self.parent_view.custom_id

    #     async def callback(self, interaction: discord.Interaction):
    #         # open modal
    #         # await interaction.response.edit_message(view=self.parent_view)
    #         await interaction.response.send_modal(EditNeitherModal(self.parent_view))


    class remove_button(ui.Button):
        def __init__(self, parent_view: ui.LayoutView):
              self.parent_view = parent_view
              super().__init__(label="Remove", 
                               style=discord.ButtonStyle.danger,
                               disabled=True,
                               custom_id=str(self.parent_view.custom_id))
              self.parent_view.custom_id += self.parent_view.custom_id

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
                               custom_id=str(self.parent_view.custom_id))
              self.parent_view.custom_id += self.parent_view.custom_id

        async def callback(self, interaction: discord.Interaction):
            # Debug output
            # if not self.parent_view.end_time:
            #     self.parent_view.end_time = self.parent_view.start_time + self.parent_view.duration
            # output = f"""start time: {self.parent_view.start_time}\n\
            #     end_time: {self.parent_view.end_time}"""

            # await interaction.response.send_message(content=output)

            # If "neither", create a division with the name and alt name of 
            #   the event.
            if div_team == "neither":
                self.parent_view.divisions = self.parent_view.neither

            self.parent_view.stop() # This finally releases the view.wait() in calling method


    #################################
    # Class utility methods
    #################################

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
    

    def div_team_container(self):
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
                self.edit_remove_select.disabled = False
                if self.divisions:
                    self.button_editdivteam.disabled = False
                    self.button_remove.disabled = False
                    self.next_button.disabled = False
                else:
                    self.button_editdivteam.disabled = True
                    self.button_remove.disabled = True
                    self.next_button.disabled = True
            case "teams":
                self.button_add.disabled = False
                self.button_add.label = "Add Team"
                self.button_editdivteam.label = "Edit Team"
                self.button_remove.label = "Remove Team"
                self.edit_remove_select.disabled = False
                if self.teams:
                    self.button_editdivteam.disabled = False
                    self.button_remove.disabled = False
                    self.next_button.disabled = False
                else:
                    self.button_editdivteam.disabled = True
                    self.button_remove.disabled = True
                    self.next_button.disabled = True
            case "neither":
                # Create one division with event_name
                self.button_add.disabled = True
                self.button_remove.disabled = True
                self.button_add.label = "-----"
                self.button_remove.label = "-----"
                self.button_editdivteam.label = "Edit Details"
                self.edit_remove_select.disabled = True
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

        # # Organize container contents
        # self.dynamic_container.clear_items()
        # self.dynamic_selectrow.clear_items()
        # self.dynamic_buttonrow.clear_items()
        # self.dynamic_selectrow.add_item(self.edit_remove_select)
        # match self.div_team:
        #     case "divisions":
        #         self.dynamic_buttonrow.add_item(self.button_editdivteam)
        #         self.dynamic_buttonrow.add_item(self.button_remove)
        #     case "teams":
        #         self.dynamic_buttonrow.add_item(self.button_editdivteam)
        #         self.dynamic_buttonrow.add_item(self.button_remove)
        #     case "neither":
        #         self.dynamic_buttonrow.add_item(self.button_editneither)
        #     case None:
        #         self.dynamic_buttonrow.add_item(self.button_editneither)
        #     case _:
        #         raise ValueError(f"Unexpected div_team value of {self.div_team}.")

        # self.dynamic_container.add_item(self.div_team_listing())
        # self.dynamic_container.add_item(self.dynamic_selectrow)
        # self.dynamic_container.add_item(self.dynamic_buttonrow)