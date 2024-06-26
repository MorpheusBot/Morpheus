from __future__ import annotations

import asyncio
import io
import urllib
from typing import TYPE_CHECKING

import aiohttp
import discord
from discord.ext import commands

from cogs.base import Base
from custom.cooldowns import default_cooldown
from custom.custom_errors import ApiError

if TYPE_CHECKING:
    from morpheus import Morpheus

PNG_HEADER = b"\x89PNG\r\n\x1a\n"


class Latex(Base, commands.Cog):
    def __init__(self, bot: Morpheus):
        super().__init__()
        self.bot = bot

    @default_cooldown()
    @commands.command()
    async def latex(self, ctx, *, equation):
        async with ctx.typing():
            eq = urllib.parse.quote(equation)
            imgURL = f"http://www.sciweavers.org/tex2img.php?eq={eq}&fc=White&im=png&fs=25&edit=0"

            try:
                async with self.bot.morpheus_session.get(imgURL) as resp:
                    if resp.status != 200:
                        return await ctx.send("Could not get image.")
                    data = await resp.read()
                    if not data.startswith(PNG_HEADER):
                        return await ctx.send("Could not get image.")

                    datastream = io.BytesIO(data)
                    await ctx.send(file=discord.File(datastream, "latex.png"))
            except (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError) as error:
                raise ApiError(error=str(error))
