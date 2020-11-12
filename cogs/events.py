import json
import emoji as tags
from discord.utils import get
from discord.ext import commands


class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.Cog.listener()
    async def on_ready(self):
        print("bot is ready.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        emoji = payload.emoji
        mage_emoji = tags.emojize(":mage:")
        print(emoji)
        with open('sior.json', 'r') as json_file:
            server_info = json.load(json_file)
        print(server_info)
        channel = self.bot.get_channel(payload.channel_id)
        category_channel = self.bot.get_channel(channel.category_id)
        message = payload.message_id
        categ = server_info[category_channel.name]
        member = payload.member
        if channel.name in categ and categ[channel.name] == channel.id:
            channel_history = await channel.history().flatten()
            correct_msg = [x for x in channel_history if x.id == message][0]
        else:
            print(f'{channel.name} não está nas categs ou id não bate... ')
            return
        # SWITCH BLOCK
        # Reaction for agreeing to take part in an expedition
        if str(emoji) == mage_emoji:
            reaction = get(correct_msg.reactions, emoji=str(emoji))
            if reaction:
                reaction_count = reaction.count
                if not member.bot:
                    await channel.send(f'{member.mention} aceitou participar '
                                       f'desta expedição! Até o momento, '
                                       f'{str(reaction_count)} jogadores '
                                       f'aceitaram participar da expedição.')
                if reaction_count == 3:
                    await channel.send(f'Com 3 jogadores tendo aceitado '
                                       f'participar, a expedição está confirmada!'
                                       f' <@&768723622080151592>, faça os preparativos'
                                       f' necessários!')
                return


def setup(bot):
    bot.add_cog(EventsCog(bot))
