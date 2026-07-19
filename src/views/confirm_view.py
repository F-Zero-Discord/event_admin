import discord
from discord import ui
from src.utils.event_class import Event


class ConfirmView(ui.LayoutView):
    def __init__(self, event: Event):
        super().__init__(timeout=300)
        self.confirmed: bool = False

        section_top = ui.Section(
            ui.TextDisplay(content=f"## New Event: {event.event_name}"),
            accessory=ui.Thumbnail("attachment://container1.png")
        )
        container_top = ui.Container()
        container_top.add_item(section_top)

        container_middle = ui.Container()
        container_middle.add_item(ui.TextDisplay(content=f"{event:detail}"))

        # Next Step Container
        button_confirm = self.confirm_button(self)
        button_cancel = self.cancel_button(self)
        button_row = ui.ActionRow(button_confirm, button_cancel)

        container_bottom = ui.Container()
        container_bottom.add_item(
             ui.TextDisplay(content="Confirm to save event information to database, or cancel to exit without saving")
        )
        container_bottom.add_item(button_row)

        self.add_item(container_top)
        self.add_item(container_middle)
        self.add_item(container_bottom)
        container_top.accent_color = discord.Colour.dark_purple()
        container_middle.accent_color = discord.Colour.dark_red()
        container_bottom.accent_color = discord.Colour.dark_red()


    #################################
    # Button classes
    #################################
    class confirm_button(ui.Button):
        def __init__(self, parent_view: ui.LayoutView):
              self.parent_view = parent_view
              super().__init__(label="Confirm", 
                               style=discord.ButtonStyle.green,
                               disabled=False)

        async def callback(self, interaction: discord.Interaction):
            self.parent_view.confirmed = True
            self.parent_view.stop() # Releases the view.wait() in calling method

    
    class cancel_button(ui.Button):
        def __init__(self, parent_view: ui.LayoutView):
              self.parent_view = parent_view
              super().__init__(label="Cancel", 
                               style=discord.ButtonStyle.danger,
                               disabled=False)

        async def callback(self, interaction: discord.Interaction):
            self.parent_view.confirmed = False
            self.parent_view.stop() # Releases the view.wait() in calling method


class SimpleMessageView(ui.LayoutView):
    def __init__(self,message: str):
        super().__init__(timeout=300)
        self.add_item(ui.TextDisplay(content=message))