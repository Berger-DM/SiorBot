from discord.ext import commands


# NO NEED TO IMPORT FROM OTHER COGS

class PlayersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    # ------------------------
    # PLAYER-RELATED COMMANDS
    # ------------------------

    # REGISTERS PLAYERS TO DATABASE
    @commands.has_role('Narrador')
    @commands.command()
    async def register_player(self, ctx, player_handle):
        member_to_register = ctx.message.mentions[0]
        member_id = str(member_to_register.id)
        statement_tuple = (member_id, player_handle)
        print(statement_tuple)
        try:
            async with self.bot.pool.acquire() as connection:
                async with connection.transaction():
                    await connection.execute(f'INSERT INTO players VALUES '
                                             f'{statement_tuple}')
            await ctx.send(f'{member_to_register.mention} registrado com o'
                           f' SiorBot como {player_handle}!')
            await ctx.message.delete()
        except Exception as e:
            print(e)
            await ctx.message.delete()
            return
        return

    # SHOWS ACTIVE CHARACTERS OF COMMAND CALLER OR MENTIONED PLAYER
    @commands.command(aliases=["my_chars"])
    async def show_characters(self, ctx):
        message = ctx.message
        mentions = message.mentions
        if mentions:
            player_id = str(mentions[0].id)
        else:
            player_id = str(ctx.author.id)
        try:
            async with self.bot.pool.acquire() as connection:
                async with connection.transaction():
                    players_characters = await connection.fetch("""SELECT
                                            char_name, char_gold, char_exp
                                            FROM characters
                                            WHERE char_player = $1 AND
                                            alive = 'true'""",
                                                                player_id)
            if players_characters:
                base_message = (f'<@!{player_id}>, seus personagens ativos são:'
                                f'\n\n')
                for character in players_characters:
                    character_name = character["char_name"]
                    character_xp = character["char_exp"]
                    character_gold = character["char_gold"]
                    base_message += (f'{str(character_name)}'
                                     f' -> EXP: {str(character_xp)}, '
                                     f'GOLD: {str(character_gold)}\n')
                await ctx.send(base_message)
            else:
                await ctx.send(f'<@!{player_id}>, você não tem personagens '
                               f'ativos no momento.')
            await ctx.message.delete()
        except Exception as e:
            print(e)
            await ctx.message.delete()
            return
        return


def setup(bot):
    bot.add_cog(PlayersCog(bot))
