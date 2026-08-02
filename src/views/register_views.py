import traceback
from typing import Literal
import asyncio
import discord
from discord import ui
from src.utils.event_class import Event, Division, Team, UserRegistrations
from src.utils.view_utils import discord_timestamp
from src.utils.status_policies import user_event_status


#################################
# Button classes
#################################

class WithdrawButton(ui.Button):
    def __init__(self, parent_view: ui.LayoutView, label: str):
        self.parent_view = parent_view
        super().__init__(label=label, 
                            style=discord.ButtonStyle.red)

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.output_mode = "withdraw"

        await interaction.response.edit_message(view=self.parent_view)
        self.parent_view.stop()
        

class CancelButton(ui.Button):
    def __init__(self, parent_view: ui.LayoutView, label: str, message: str):
        self.parent_view = parent_view
        self.message = message
        super().__init__(label=label, 
                            style=discord.ButtonStyle.red)

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.output_mode = "cancel"
        cancel_message = CancelView("No action taken. Come back anytime.")
        await interaction.response.edit_message(view=cancel_message)
        self.parent_view.stop()


class AffirmButton(ui.Button):
    def __init__(self, parent_view: ui.LayoutView):
        self.parent_view = parent_view
        super().__init__(label="Continue", 
                            style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=self.parent_view)
        self.parent_view.stop()


class EditButton(ui.Button):
    def __init__(self, parent_view: ui.LayoutView):
        self.parent_view = parent_view
        super().__init__(label="Edit", 
                            style=discord.ButtonStyle.blurple)

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.output_mode = "edit"

        await interaction.response.edit_message(view=self.parent_view)
        self.parent_view.stop()



class ChoiceButton(ui.Button):
    def __init__(self, parent_view: ui.LayoutView,
                 scheduled_event_id: int,
                 button_label: str, 
                 button_color: discord.ButtonStyle, 
                 button_disabled: bool):
        self.scheduled_event_id = scheduled_event_id
        self.parent_view = parent_view
        super().__init__(label=button_label, style=button_color, disabled=button_disabled)

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.choice = self.scheduled_event_id
        if self.label == "Edit":
            self.parent_view.output_mode = "edit"
        else:
            self.parent_view.output_mode = "choice"

        self.disabled = True
        await interaction.response.edit_message(view=self.parent_view)
        self.parent_view.stop()

    async def on_error(self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction) -> None:
        # Print the traceback to your console for debugging
        traceback.print_exception(type(error), error, error.__traceback__)
        
        # Inform the user safely via interaction response or followup
        message = "An unexpected error occurred while processing your click."
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


#################################
# LayoutView classes
#################################

class CancelView(ui.LayoutView):
    def __init__(self, message: str):
        super().__init__(timeout=300)
        container = ui.Container()

        container.add_item(ui.TextDisplay(content=message))
        self.add_item(container)


class LoadView(ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=300)
        self.output_mode: Literal["cancel", "edit", "choice", "withdraw"] | None = None

        loading_screen_text = """Welcome to your portal to sign up for FZD events! If we have a pending event ready for your signup, you'll find it here.

For events with divisions or teams, we will endeavor to place you in your requested division or team, but we may need to make changes to account for capacity and balance.

Please press continue below to start!"""

        container = ui.Container()
        container.add_item(ui.TextDisplay(content="# Register for an Event"))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(ui.TextDisplay(content=loading_screen_text))
        
        container.add_item(ui.ActionRow(
            AffirmButton(self),
            CancelButton(self, label="Leave", message="No registration actions taken.")
            ))
        self.add_item(container)


class RegisterMenuView(ui.LayoutView):
    def __init__(self, events: list[Event], user: UserRegistrations):
        super().__init__(timeout=300)
        self.choice: int | None = None
        self.output_mode: Literal["cancel", "edit", "choice", "withdraw"] | None = None

        container = ui.Container()
        container.add_item(ui.TextDisplay(content="# Register for an Event"))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Build sections for each event in events
        section_text: list[ui.TextDisplay] = []
        section_button: list[ChoiceButton] = []
        section: list[ui.Section] = []
        for i, event in enumerate(events):
            status = user_event_status(event, user)
            section_text.append(ui.TextDisplay(
                content=f"### {event.event_name}\n\t{discord_timestamp(event.start_time, "long")}\n\t{status["label"]}"))
            section_button.append(ChoiceButton(self, event.scheduled_event_id, 
                                          status["button_label"], status["button_color"], 
                                          status["button_disabled"]))
            section.append(ui.Section(section_text[i], accessory=section_button[i]))
            container.add_item(section[i])

        # Build the Cancel button section
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(ui.ActionRow(
            CancelButton(self, label="Leave", message="No registration actions taken.")))

        self.add_item(container)


class DivTeamView(ui.LayoutView):
    def __init__(self, event: Event):
        super().__init__(timeout=300)
        self.output_mode: Literal["cancel", "edit", "choice", "withdraw"] | None = None
        self.choice: int | None = None
        self.event: Event = event
        self.div_team_string: Literal["division", "team"] | None = None

        if self.event.divisions:
            self.div_team_string = "division"
            div_team_list = self.event.divisions
        elif self.event.teams:
            self.div_team_string = "team"
            div_team_list = self.event.teams
        else:
            raise ValueError("To create a DivTeamView there need to be divisions (plural) or teams.")

        container = ui.Container()
        container.add_item(ui.TextDisplay(
            f"# Chooose a {self.div_team_string.capitalize()}"))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Build sections for each event in events
        container.add_item(ui.ActionRow(self.div_team_selection(self, div_team_list)))
        self.status_text = ui.TextDisplay(content="-")
        container.add_item(self.status_text)

        # Build the Continue button section
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        self.continue_button = AffirmButton(self)
        container.add_item(ui.ActionRow(self.continue_button))

        self.add_item(container)

        self.set_status()

    #################################
    # Drowdown subclass
    #################################
    class div_team_selection(ui.Select):
        def __init__(self, parent_view: ui.LayoutView, div_team_list: list[Division] | list[Team]):
            self.parent_view = parent_view

            options = []
            for div_team in div_team_list:
                options.append(discord.SelectOption(label=div_team.name, 
                                        description=None, 
                                        value=div_team.id
                ))
            super().__init__(options=options)

        async def callback(self, interaction: discord.Interaction):
            # Assign output to class variable
            self.parent_view.choice = int(self.values[0])

            # Set default dropdown option to user's selection
            for option in self.options:
                option.default = (int(option.value) == int(self.values[0]))

            self.parent_view.set_status()
            await interaction.response.edit_message(view=self.parent_view)


    ###########################
    # Class methods
    ###########################

    def set_status(self) -> None:
        """ Enable/disable Continue button and set status textbox.
        """
        # Find div_team with dropdown choice id
        if not self.choice:
            self.continue_button.disabled = True
            self.status_text.content = "-"
            return

        # Get div_team object selected
        match self.div_team_string:
            case "division":
                div_team = [dt for dt in self.event.divisions if dt.id == self.choice][0]
            case "team":
                div_team = [dt for dt in self.event.teams if dt.id == self.choice][0]
            case _:
                raise ValueError(f"Self.div_team must be 'division' or 'team', not {div_team}")

        # Set statuses
        if div_team.at_capacity:
            self.continue_button.disabled = True
            print(f"{self.div_team_string.capitalize()} {div_team.name} full!")
            self.status_text.content = f"{self.div_team_string.capitalize()} {div_team.name} full!"
        else:
            self.continue_button.disabled = False
            # self.status_text = ui.TextDisplay(content=f"{div_team.capacity - div_team.num_registered} spots available!")
            self.status_text.content = f"{div_team.capacity - div_team.num_registered} spots available!"


class DivTeamEditView(ui.LayoutView):
    def __init__(self, event: Event, existing_div_team_id: int):
        super().__init__(timeout=300)
        self.choice: int | None = existing_div_team_id
        self.event: Event = event
        self.existing_div_team_id: int = existing_div_team_id
        self.div_team_string: Literal["division", "team"] | None = None
        self.output_mode: Literal["cancel", "edit", "choice", "withdraw"] | None = None
        
        if self.event.divisions:
            self.div_team_string = "division"
            div_team_list = self.event.divisions
        elif self.event.teams:
            self.div_team_string = "team"
            div_team_list = self.event.teams
        else:
            raise ValueError("To create a DivTeamView there need to be divisions (plural) or teams.")

        container = ui.Container()
        container.add_item(ui.TextDisplay(
            f"# Edit Your Registration"))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Build dropdown part of container
        container.add_item(ui.ActionRow(self.div_team_selection(self, div_team_list)))
        self.status_text = ui.TextDisplay(content="-")
        container.add_item(self.status_text)

        # Build the button ActionRow
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        # Buttons need to be "Withdraw", "Modify", "Cancel"
        self.edit_button = EditButton(self)
        self.edit_button.style = discord.ButtonStyle.blurple
        self.withdraw_button = WithdrawButton(self, label="Withdraw from Event")
        self.withdraw_button.style = discord.ButtonStyle.red
        self.cancel_button = CancelButton(self, 
                    label="Cancel", message="No registration actions taken.")
        self.cancel_button.style = discord.ButtonStyle.gray
        container.add_item(ui.ActionRow(
            self.edit_button, 
            self.withdraw_button, 
            self.cancel_button)
            )

        self.add_item(container)

        self.set_status()


    #################################
    # Drowdown subclass
    #################################
    class div_team_selection(ui.Select):
        def __init__(self, parent_view: ui.LayoutView, div_team_list: list[Division] | list[Team]):
            self.parent_view = parent_view

            options = []
            for div_team in div_team_list:
                if div_team.id == self.parent_view.existing_div_team_id:
                    label = f"{div_team.name} (current)"
                else:
                    label = f"{div_team.name}"
                options.append(discord.SelectOption(label=label, 
                                        description=None, 
                                        value=div_team.id
                ))
            super().__init__(options=options)

        async def callback(self, interaction: discord.Interaction):
            # Assign output to class variable
            self.parent_view.choice = int(self.values[0])

            # Set default dropdown option to user's selection
            for option in self.options:
                option.default = (int(option.value) == int(self.values[0]))

            self.parent_view.set_status()
            await interaction.response.edit_message(view=self.parent_view)


    ###########################
    # Class methods
    ###########################

    def set_status(self) -> None:
        """ Enable/disable Continue button and set status textbox.
        """
        # Find div_team with dropdown choice id
        if not self.choice:
            self.continue_button.disabled = True
            self.status_text.content = "-"
            return

        # Get div_team object selected
        match self.div_team_string:
            case "division":
                div_team = [d for d in self.event.divisions if d.id == self.choice][0]
            case "team":
                div_team = [t for t in self.event.teams if t.id == self.choice][0]
            case _:
                raise ValueError(f"Self.div_team must be 'division' or 'team', not {div_team}")

        # Set statuses
        if div_team.at_capacity:
            self.edit_button.disabled = True
            print(f"{self.div_team_string.capitalize()} {div_team.name} full!")
            self.status_text.content = f"{self.div_team_string.capitalize()} {div_team.name} full!"
        else:
            self.edit_button.disabled = False
            # self.status_text = ui.TextDisplay(content=f"{div_team.capacity - div_team.num_registered} spots available!")
            self.status_text.content = f"{div_team.capacity - div_team.num_registered} spots available!"


class ConfirmView(ui.LayoutView):
    def __init__(self, event: Event, div_team_id: int):
        super().__init__(timeout=300)
        self.output_mode: Literal["cancel", "edit", "choice", "withdraw"] | None = None

        div_team_str = event.div_or_team()

        # get division/team name
        match div_team_str:
            case "division":
                if len(event.divisions) == 1:
                    div_team_str = ""
                    div_team_name = ""
                div_team_name = [d.name for d in event.divisions if d.id == div_team_id][0]
            case "team":
                div_team_name = [t.name for t in event.teams if t.id == div_team_id][0]
            case _:
                raise ValueError(f"Self.div_team must be 'division' or 'team', not {div_team_str}")

        choice_text = f"### {event.event_name}\n\t{discord_timestamp(event.start_time, "long")}\n**{div_team_str.capitalize()}**\n\t{div_team_name}"
        confirm_text = f"### Are you ready! Confirm below."

        container = ui.Container()
        container.add_item(ui.TextDisplay(content="# Confirm Your Choice"))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(ui.TextDisplay(content=f"{choice_text}\n\n\n\n{confirm_text}"))

        affirm_button = AffirmButton(self)
        affirm_button.label = "Let's Go!"
        container.add_item(ui.ActionRow(
            affirm_button,
            CancelButton(self, label="Cancel", message="No registration actions taken.")
            ))
        self.add_item(container)


class ConfirmWithdrawlView(ui.LayoutView):
    def __init__(self, event: Event, div_team_id: int):
        super().__init__(timeout=300)
        self.output_mode: Literal["cancel", "edit", "choice", "withdraw"] | None = None

        div_team_str = event.div_or_team()

        # get division/team name
        match div_team_str:
            case "division":
                if len(event.divisions) == 1:
                    div_team_str = ""
                    div_team_name = ""
                div_team_name = [d.name for d in event.divisions if d.id == div_team_id][0]
            case "team":
                div_team_name = [t.name for t in event.teams if t.id == div_team_id][0]
            case _:
                raise ValueError(f"Self.div_team must be 'division' or 'team', not {div_team_str}")

        choice_text = f"### {event.event_name}\n\t{discord_timestamp(event.start_time, "long")}\n**{div_team_str.capitalize()}**\n\t{div_team_name}"
        confirm_text = f"### Are you sure you want to withdraw your registration?"

        container = ui.Container()
        container.add_item(ui.TextDisplay(content="# Withdraw Your Registration?"))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(ui.TextDisplay(content=f"{choice_text}\n\n\n\n{confirm_text}"))

        affirm_button = AffirmButton(self)
        cancel_button = CancelButton(self, label="Cancel", message="No registration actions taken.")
        affirm_button.label = "Withdraw"
        affirm_button.style = discord.ButtonStyle.danger
        cancel_button.style = discord.ButtonStyle.blurple
        container.add_item(ui.ActionRow(
            affirm_button,
            cancel_button)
            )
        self.add_item(container)

class ExitView(ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=300)

        self.add_item(ui.Container(ui.TextDisplay("Thank you!")))