import json
import emoji
import discord
from discord.ext import commands


# NO NEED TO IMPORT FROM OTHER COGS

class QuestsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    # -----------------------
    # QUEST-RELATED COMMANDS
    # -----------------------

    # ALLOWS USERS TO PROPOSE QUESTS TO THE GROUP
    @commands.command()
    async def quest(self, ctx, serial_no, date, time):
        with open("sior.json", "r", encoding="utf-8") as json_file:
            server_info = json.load(json_file)
        author = ctx.message.author
        current_ch = ctx.message.channel
        current_ct = current_ch.category
        cur_ct_nfo = server_info[current_ct.name]
        print(cur_ct_nfo)
        mentions = ctx.message.mentions
        if mentions:
            author = mentions[0]
        try:
            correct_ch = self.bot.get_channel(
                cur_ct_nfo["propostas-de-expedição"])
            if current_ch.id == correct_ch.id:
                try:
                    mage_emoji = emoji.emojize(":mage:", use_aliases=True)
                    map_emoji = "U+1F5FA"
                    print(map_emoji)
                    rumour_no = serial_no
                    exped_dat = date
                    exped_tim = time
                    rumour_ch = self.bot.get_channel(cur_ct_nfo["rumores"])
                    c_history = await rumour_ch.history().flatten()
                    try:
                        correct_rumour = [x for x in c_history
                                          if x.content.startswith(mage_emoji+" #"+rumour_no)][0]
                        rumour_reactions = correct_rumour.reactions
                        if map_emoji in rumour_reactions:
                            await ctx.send(f'Rumor #{str(serial_no)} está com '
                                           f'proposta de expedição atualmente'
                                           f' ativa! Dê uma olhada no canal '
                                           f'#propostas-de-expedição e procure'
                                           f'por ela lá.')
                            return
                        embed_txt = correct_rumour.content.split(f'{mage_emoji} ')[1]
                        print(embed_txt)
                        embed = discord.Embed(
                            # TODO: criar tabela de nomes:id no BD, colocar nome aq
                            title=f'{author.name} PROPÕE UMA '
                                  f'EXPEDIÇÃO!',
                            description=embed_txt)
                        embed.add_field(name="Dia", value=exped_dat, inline=True)
                        embed.add_field(name="Horário", value=exped_tim,
                                        inline=True)
                        embed.set_footer(
                            text=f'Clique no {mage_emoji} para se \
                                        juntar a esta expedição!')
                        embed_msg = await ctx.send("@everyone", embed=embed)
                        await embed_msg.add_reaction(mage_emoji)
                        await correct_rumour.add_reaction(
                            chr(int(map_emoji[2:], 16)))
                        return
                    except IndexError:
                        await ctx.send("Rumor com este \'#\' não existe.")
                        return
                except Exception as e:
                    print(e)
                    return
            else:
                await ctx.send(f'Por favor, envie propostas de expedição apenas'
                               f'nos canais "proposta-de-expedição" das bases de'
                               f' operação.')
                await ctx.message.delete(delay=5)
                return
        except KeyError:
            await ctx.send(f'Por favor, envie propostas de expedição apenas'
                           f'nos canais "proposta-de-expedição" das bases de'
                           f' operação.')
            await ctx.message.delete(delay=5)
            return

    # CANCELS QUEST THAT WAS TRULY CANCELLED BY PLAYERS OR TIMED OUT
    @commands.has_role('Narrador')
    @commands.command()
    async def cancel_quest(self, ctx, msg_id):
        map_emoji = chr(int("U+1F5FA"[2:], 16))
        message = await ctx.fetch_message(int(msg_id))
        url = message.jump_url
        await message.clear_reaction(map_emoji)
        await ctx.send(f'A proposta de expedição do link\n\n{url}\n\n'
                       f'foi cancelada.')
        await ctx.message.delete()
        return


def setup(bot):
    bot.add_cog(QuestsCog(bot))
