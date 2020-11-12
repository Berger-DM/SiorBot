from discord.ext import commands


# NO NEED TO IMPORT FROM OTHER COGS

class AwardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    # --------------------------------
    # AUXILIARY FUNCTIONS TO COMMANDS
    # --------------------------------

    # CHECKS NUMBER OF CHARACTERS THE PLAYER HAS THAT ARE ALIVE
    async def check_exp(self, name):
        async with self.bot.pool.acquire() as connection:
            async with connection.transaction():
                num = await connection.fetchval("""SELECT char_exp FROM
                                                characters WHERE
                                                char_name = $1""", name)
                if num == "":
                    num = 0
                return num

    # CHECKS NUMBER OF CHARACTERS THE PLAYER HAS THAT ARE ALIVE
    async def check_gold(self, name):
        async with self.bot.pool.acquire() as connection:
            async with connection.transaction():
                num = await connection.fetchval("""SELECT char_gold FROM
                                                characters WHERE
                                                char_name = $1""", name)
                return num

    # RETURNS BOTH GOLD AND EXP FOR THE CHARACTER
    async def check_gold_xp(self, name):
        gold = str(await self.check_gold(name))
        xp = str(await self.check_exp(name))
        return gold, xp

    # SERVES TO AWARD ANYTHING NEEDED TO CHARACTERS (GOLD, XP)
    async def award(self, player, name, what, amount):
        try:
            async with self.bot.pool.acquire() as connection:
                async with connection.transaction():
                    if what == "char_gold":
                        amount = str(amount)
                    else:
                        amount = "'" + str(amount) + "'"
                    await connection.execute(f'UPDATE characters SET '
                                             f'{what} = {amount}'
                                             f' WHERE char_player = '
                                             f'\'{player}\' AND '
                                             f'char_name = \'{name}\';')
            return
        except Exception as e:
            print(e)
            return

    # ------------------------
    # REWARD-RELATED COMMANDS
    # ------------------------

    # REWARDS PARTY IN GOLD AND EXP FOR THEIR LATEST EXPEDITION
    @commands.has_role('Narrador')
    @commands.command()
    async def reward_party(self, ctx, gold, exp):
        wink_emoji = chr(int("U+1F609"[2:], 16))
        await ctx.send(f'@Narrador, liste os pares personagem/jogador,'
                       f'em ordem, no formato <personagem> <jogador>, '
                       f'separados por vírgula, por favor. '
                       f'Vai lá, eu espero {wink_emoji}')

        def check(author):
            def inner_check(msg):
                if msg.author != author:
                    return False
                else:
                    return True

            return inner_check

        message = await self.bot.wait_for('message', check=check)
        content = message.content
        print(content)
        split_content = content.split(" , ")
        print(split_content)
        characters = [x.split(" <")[0] for x in split_content]
        print(characters)
        mentions = [x.strip("<@!>") for x in content.split(' ')
                    if x.startswith("<")]
        print(mentions)
        for i in range(len(characters)):
            char_gold, char_xp = await self.check_gold_xp(characters[i])
            await self.award(mentions[i], characters[i], 'char_gold',
                             int(char_gold) + int(gold))
            await self.award(mentions[i], characters[i], 'char_exp',
                             int(char_xp) + int(exp))
        prep_char_string = ", e ".join(", ".join(characters).rsplit(", ", 1))
        await ctx.send(f'{prep_char_string} recebem {gold} GP em tesouros '
                       f'e recursos, e {exp} EXP por sua mais recente '
                       f'expedição e salvo retorno!')
        await ctx.message.delete()
        return


def setup(bot):
    bot.add_cog(AwardCog(bot))
