import discord
import git
from discord import app_commands
from discord.ext import commands

import utils.utils as utils
from cogs.base import Base
from custom.permission_check import is_bot_admin

from .buttons import CogSelect, SystemView
from .features import split_cogs
from .messages import SystemMess


class Git:
    def __init__(self):
        self.repo = git.Repo(search_parent_directories=True)
        self.cmd = self.repo.git

    async def pull(self):
        return self.cmd.pull()

    def short_hash(self):
        return self.repo.head.object.hexsha[:7]


class System(Base, commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.git = Git()

        self.unloadable_cogs = ["system"]

    git_group = app_commands.Group(name="git", description=SystemMess.git_brief)

    @is_bot_admin()
    @git_group.command(name="pull", description=SystemMess.git_pull_brief)
    async def pull(self, inter: discord.Interaction):
        message: discord.Message = await inter.response.send_message("Pulling")

        pull_result = await self.git.pull()
        pull_parts = utils.cut_string(pull_result, 1900)

        await message.edit(content=f"```{pull_parts[0]}```")

        for part in pull_parts[1:]:
            await inter.followup.send(inter, f"```{part}```")

    @is_bot_admin()
    @app_commands.command(name="shutdown", description=SystemMess.shutdown_brief)
    async def shutdown(self, inter: discord.Interaction):
        await inter.response.send_message("shutting down")
        exit(0)

    @is_bot_admin()
    @app_commands.command(name="cogs", description=SystemMess.cogs_brief)
    async def cogs(self, inter: discord.Interaction):
        """
        Creates embed with button and select(s) to load/unload/reload cogs.

        Max number of cogs can be 100 (4x25).
        """
        await inter.response.defer()
        cogs = await split_cogs()
        view = SystemView(self.bot, len(cogs), cogs)
        embed = CogSelect.create_embed(self, inter.user.colour)
        message = await inter.followup.send(embed=embed, view=view)

        # pass message object to classes
        view.message = message
        for i, _ in enumerate(cogs):
            view.selects[i].message = message

    @cogs.error
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error.__cause__, commands.errors.ExtensionNotLoaded):
            await ctx.send(SystemMess.not_loaded.format(error.__cause__.name))
            return True