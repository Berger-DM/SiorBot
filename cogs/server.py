import json
import discord
from discord.ext import commands


# NO NEED TO IMPORT FROM OTHER COGS

class ServerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    # ------------------------
    # SERVER-RELATED COMMANDS
    # ------------------------

    # SWEEPS SERVER FOR ALL CATEGORIES AND TEXT CHANNELS
    @commands.has_role('Narrador')
    @commands.command()
    async def sweep_server_for_ids(self, ctx):
        server_channels = dict()
        guild = ctx.guild
        server_channels['guild_nm'] = guild.name
        server_channels['guild_id'] = guild.id
        catchnls = [x for x in guild.channels if
                    x.type == discord.ChannelType.category]
        for category in catchnls:
            category_channels = dict()
            category_channels['category_nm'] = category.name
            category_channels['category_id'] = category.id
            cat_text_channels = category.text_channels
            for text_channel in cat_text_channels:
                category_channels[text_channel.name] = text_channel.id
            server_channels[category.name] = category_channels
        # TODO: TROCAR DE ARQUIVO LOCAL PARA ENTRADA NO BD?
        with open('sior.json', 'w') as json_file:
            json.dump(server_channels, json_file, indent=4)


def setup(bot):
    bot.add_cog(ServerCog(bot))
