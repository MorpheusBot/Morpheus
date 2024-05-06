import discord

from .messages import NasaMess


def create_nasa_embed(response: dict) -> tuple[discord.Embed, str | None]:
    """
    Create embed for NASA API response
    """
    embed = discord.Embed(title=response["title"], url=NasaMess.nasa_url, color=discord.Color.blurple())
    url = response["hdurl"] if response.get("hdurl", None) else response["url"]
    if response.get("media_type", None) != "video":
        embed.set_image(url=url)
    embed.add_field(name="Explanation", value=response["explanation"], inline=False)
    return embed, url
