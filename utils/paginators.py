"""
Paginators for commands.
Copyright (C) 2021 avizum

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from utils.view import AvimetryView
import discord
from utils.context import AvimetryContext
from discord.ext.menus.views import ViewMenuPages
from discord.ext.menus import button, Position, PageSource


class AvimetryPages(AvimetryView):
    def __init__(self, source: PageSource, *, ctx: AvimetryContext, message: discord.Message = None, timeout: int = 180,
                 disable_view_after: bool = False, remove_view_after: bool = False, delete_message_after: bool = False):
        self.source = source
        self.ctx = ctx
        self.disable_view_after = disable_view_after
        self.remove_view_after = remove_view_after
        self.delete_message_after = delete_message_after
        self.current_page = 0
        self.message = message
        super().__init__(timeout=timeout, member=ctx.author)
        self.clear_items()
        self.add_items()

    def add_items(self):
        if self.source.is_paginating():
            max_pages = self.source.get_max_pages()
            if max_pages <= 1:
                pass
            elif max_pages > 2:
                self.add_item(self.skip_to_first)
                self.add_item(self.go_back_one)
                self.add_item(self.show_page_number)
                self.add_item(self.go_forward_one)
                self.add_item(self.skip_to_last)
            else:
                self.add_item(self.go_back_one)
                self.add_item(self.show_page_number)
                self.add_item(self.go_forward_one)

            self.add_item(self.stop_view)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user and interaction.user.id in (*self.ctx.bot.owner_ids, self.ctx.author.id):
            return True
        await interaction.response.send_message(
            f"This menu can only be used by {self.ctx.author}, not you.", ephemeral=True)
        return False

    def _update(self, page: int):
        self.go_forward_one.disabled = False
        self.go_back_one.disabled = False
        self.skip_to_last.disabled = False
        self.skip_to_first.disabled = False

        if self.show_page_number.emoji:
            self.show_page_number.emoji = None
        current = self.current_page + 1
        most = self.source.get_max_pages()
        self.show_page_number.label = f"{current}/{most}"

        self.skip_to_first.label = "1"
        self.skip_to_last.label = str(most)

        if page + 1 == most:
            self.go_forward_one.disabled = True
            self.skip_to_last.disabled = True
        if page == 0:
            self.go_back_one.disabled = True
            self.skip_to_first.disabled = True

    async def show_page(self, interaction: discord.Interaction, page_num: int):
        page = await self.source.get_page(page_num)
        self.current_page = page_num
        self._update(page_num)
        kwargs = await self.get_page_kwargs(page)

        if interaction.response.is_done():
            if self.message:
                await self.message.edit(**kwargs, view=self)
        else:
            await interaction.response.edit_message(**kwargs, view=self)

    async def show_checked_page(self, interaction: discord.Interaction, page_num: int):
        max_pages = self.source.get_max_pages()
        try:
            if max_pages is None or max_pages > page_num >= 0:
                await self.show_page(interaction, page_num)
        except IndexError:
            pass

    async def get_page_kwargs(self, page: int):
        value = await discord.utils.maybe_coroutine(self.source.format_page, self, page)
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            return {'content': value, 'embed': None}
        elif isinstance(value, discord.Embed):
            return {'embed': value, 'content': None}
        else:
            return {}

    async def on_timeout(self):
        if self.message:
            if self.disable_view_after:
                for item in self.children:
                    item.disabled = True
                await self.message.edit(view=self)
            elif self.remove_view_after:
                await self.message.edit(view=None)
            elif self.delete_message_after:
                await self.message.delete()
            await self.ctx.message.add_reaction(self.ctx.bot.emoji_dictionary["green_tick"])

    async def start(self):
        await self.source._prepare_once()
        page = await self.source.get_page(0)
        kwargs = await self.get_page_kwargs(page)
        self._update(0)
        self.message = await self.ctx.send(**kwargs, view=self)

    @discord.ui.button(emoji="\U000023ee\U0000fe0f")
    async def skip_to_first(self, button: discord.ui.Button, interaction: discord.Interaction):
        """
        Skips to the first page.
        """
        await self.show_page(interaction, 0)

    @discord.ui.button(emoji="\U000025c0\U0000fe0f")
    async def go_back_one(self, button: discord.ui.Button, interaction: discord.Interaction):
        """
        Goes back one page.
        """
        await self.show_checked_page(interaction, self.current_page - 1)

    @discord.ui.button(emoji="<:avimetry:877445146709463081>", disabled=True, style=discord.ButtonStyle.blurple)
    async def show_page_number(self, button: discord.ui.Button, interaction: discord.Interaction):
        pass

    @discord.ui.button(emoji="\U000025b6\U0000fe0f")
    async def go_forward_one(self, button: discord.ui.Button, interaction: discord.Interaction):
        """
        Goes to the next page.
        """
        await self.show_checked_page(interaction, self.current_page + 1)

    @discord.ui.button(emoji="\U000023ed\U0000fe0f")
    async def skip_to_last(self, button: discord.ui.Button, interaction: discord.Interaction):
        """
        Skips to the last page.
        """
        await self.show_page(interaction, self.source.get_max_pages() - 1)

    @discord.ui.button(emoji="\U000023f9\U0000fe0f", label="Stop", style=discord.ButtonStyle.red, row=2)
    async def stop_view(self, button: discord.ui.Button, interaction: discord.Interaction):
        """
        Stops the paginator and view.
        """
        if self.disable_view_after:
            for item in self.children:
                item.disabled = True
            button.label = "Disabled"
            await interaction.response.edit_message(view=self)
        elif self.remove_view_after:
            await interaction.response.edit_message(view=None)
        elif self.delete_message_after:
            await interaction.delete_original_message()
        await self.ctx.message.add_reaction(self.ctx.bot.emoji_dictionary["green_tick"])
        self.stop()


class OldAvimetryPages(ViewMenuPages):
    def __init__(self, source, **kwargs):
        super().__init__(source=source, clear_reactions_after=True, **kwargs)

    async def send_initial_message(self, ctx, channel, interaction=None):
        page = await self._source.get_page(0)
        kwargs = await self.get_page_kwargs(page)
        if interaction:
            return await interaction.response.edit_message(**kwargs, view=self.build_view())
        return await self.send_with_view(ctx, **kwargs)

    def _skip_double_triangle_buttons(self):
        max_pages = self._source.get_max_pages()
        if max_pages is None:
            return True
        return max_pages <= 2

    @button('\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f', position=Position(0),
            skip_if=_skip_double_triangle_buttons)
    async def go_to_first_page(self, payload):
        """go to the first page"""
        await self.show_page(0)

    @button('\N{BLACK LEFT-POINTING TRIANGLE}\ufe0f', position=Position(1))
    async def go_to_previous_page(self, payload):
        """go to the previous page"""
        await self.show_checked_page(self.current_page - 1)

    @button('\N{BLACK SQUARE FOR STOP}\ufe0f', position=Position(2))
    async def stop_pages(self, payload):
        """stops the pagination session."""
        self.stop()

    @button('\N{BLACK RIGHT-POINTING TRIANGLE}\ufe0f', position=Position(3))
    async def go_to_next_page(self, payload):
        """go to the next page"""
        await self.show_checked_page(self.current_page + 1)

    @button('\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f', position=Position(4),
            skip_if=_skip_double_triangle_buttons)
    async def go_to_last_page(self, payload):
        """go to the last page"""
        # The call here is safe because it's guarded by skip_if
        await self.show_page(self._source.get_max_pages() - 1)

    async def _internal_loop(self):
        try:
            self.__timed_out = await self.view.wait()
        except Exception as e:
            print(e)
        finally:
            self._event.set()

            try:
                await self.finalize(self.__timed_out)
            except Exception:
                pass
            finally:
                self.__timed_out = False

            if self.bot.is_closed():
                return

            try:
                if self.delete_message_after:
                    return await self.message.delete()

                if self.clear_reactions_after:
                    for i in self.view.children:
                        i.disabled = True
                    return await self.message.edit(view=self.view)
            except Exception:
                pass
