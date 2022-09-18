from disnake.ext import commands

import disnake
import random
import re
import json
import requests
import time
import keys
import os
from config.messages import Messages


class ManageMessages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.has_permissions(manage_messages=True)
    @commands.slash_command(name="purge", description="Delete number of messages")
    async def purge(ctx, number_of_messages: int):
        await ctx.channel.purge(limit=number_of_messages)
        await ctx.send("Poof", delete_after=5)

    @commands.slash_command(name="addreply", description="Add autoreply")
    async def addreply(self, inter: disnake.ApplicationCommandInteraction, key, reply):
        with open(f"servers/{inter.guild.name}/replies.json", 'r+', encoding='utf-8') as f:
            dict = json.load(f)
            if key.lower() in dict.keys():
                await inter.response.send_message(f"hláška {key} již existuje")
            else:
                add = {f"{key.lower()}": reply}
                dict.update(add)
                with open(f"servers/{inter.guild.name}/replies.json", 'w', encoding='utf-8') as f:
                    json.dump(dict, f, ensure_ascii=False, indent=4)
                await inter.response.send_message(f"reply {key} byla přidána")

    @commands.slash_command(name="remreply", description="Remove autoreply")
    async def remreply(self, inter: disnake.ApplicationCommandInteraction, key):
        with open(f"servers/{inter.guild.name}/replies.json", 'r+', encoding='utf-8') as f:
            dict = json.load(f)
            if key.lower() in dict.keys():
                dict.pop(key.lower())
                with open(f"servers/{inter.guild.name}/replies.json", 'w', encoding='utf-8') as f:
                    json.dump(dict, f, ensure_ascii=False, indent=4)
                await inter.response.send_message(f"hláška {key} byla odstraněna")
            else:
                await inter.response.send_message("takovou hlášku jsem nenašel")

    @commands.Cog.listener("on_message")
    async def reply(self, message):
        """sends messages to users depending on the content"""

        if message.guild is None:
            return

        with open(f"servers/{message.guild.name}/replies.json", 'r') as f:
            replies = json.load(f)

        if message.author.bot:
            return
        elif "uh oh" in message.content:
            await message.channel.send("uh oh")
        elif f"<@!{self.bot.user.id}>" in message.content or f"<@{self.bot.user.id}>" in message.content:
            await message.channel.send(random.choice(Messages.Morpheus))
        else:
            for key, value in replies.items():
                if re.search(fr"^{key.lower()}$", message.content.lower()):
                    await message.channel.send(value)

    @commands.has_permissions(administrator=True)
    @commands.command(name="count", description="Count all messages from everyone")
    async def message_count(self, ctx):
        member_ids = [member.id for member in ctx.guild.members]
        messages_count = {}
        headers = {
                    'authorization': keys.authorization
                    }
        for ids in member_ids:
            r = requests.get(f'https://discord.com/api/v9/guilds/{ctx.guild.id}/messages/search?author_id={ids}&include_nsfw=true', headers=headers)  # noqa: E501
            data = json.loads(r.text)
            username = ctx.guild.get_member(ids)

            messages_count.update({ids: data['total_results']})
            await ctx.send(f"**Jméno**= {username}; **ID**= {ids}; **počet zpráv**= {data['total_results']}")
            # prevent rate limit
            time.sleep(2)

        with open(f"servers/{ctx.guild.name}/messages.json", 'w', encoding='utf-8') as f:
            json.dump(messages_count, f, ensure_ascii=False, indent=4)

    @commands.has_permissions(administrator=True)
    @commands.slash_command(name="history", description=Messages.channel_history_brief)
    async def channel_history(
            self,
            inter,
            channel: disnake.TextChannel,
            old_to_new: bool = commands.Param(default=True, description="Sort messages chronologically"),
            limit: int = commands.Param(default=None, description="Number of messages to retrieve")
            ):
        await inter.response.defer()
        messages = await channel.history(limit=limit, oldest_first=old_to_new).flatten()
        name_lenght = 0
        for message in messages:
            if name_lenght < len(message.author.name):
                name_lenght = len(message.author.name)
        with open(f"{channel}_history.txt", "w") as file:
            for message in messages:
                time = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
                content = message.content.replace("\n", " ")
                author = message.author.name.ljust(name_lenght, " ")
                file.write(f"{time} | {author} | {content}\n")
        await inter.author.send(file=disnake.File(f"{channel}_history.txt"))
        await inter.edit_original_message(Messages.channel_history_success.format(channel))

        if os.path.exists(f"{channel}_history.txt"):
            os.remove(f"{channel}_history.txt")


def setup(bot):
    bot.add_cog(ManageMessages(bot))
