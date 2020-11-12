from discord.ext import commands


# IMPORTS FROM AwardCog "check_gold_xp", "award"

class GoalsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    # --------------------------------
    # AUXILIARY FUNCTIONS TO COMMANDS
    # --------------------------------

    # CHECKS CURRENT PROGRESS TOWARDS GOAL
    async def check_goal(self, goal, base, cur_or_am="cur"):
        async with self.bot.pool.acquire() as connection:
            if cur_or_am == "cur":
                what_goal = "goal_current"
            elif cur_or_am == "am":
                what_goal = "goal_amount"
            else:
                return False
            async with connection.transaction():
                num = await connection.fetchrow(
                    """SELECT * FROM
                                        goals WHERE goal = $1 AND
                                        base = $2""", goal, base)

                return num[what_goal]

    # SERVES TO COUNT PROGRESS TOWARDS GOALS
    async def build_towards_goal(self, goal, base, amount):
        try:
            async with self.bot.pool.acquire() as connection:
                async with connection.transaction():
                    await connection.execute(f'UPDATE goals SET '
                                             f'goal_current = {amount}'
                                             f' WHERE goal = '
                                             f'\'{goal}\' AND '
                                             f'base = \'{base}\';')
            return
        except Exception as e:
            print(e)
            return

    # ----------------------
    # GOAL-RELATED COMMANDS
    # ----------------------

    # ALLOW GM TO SET GOALS FOR THE PLAYERS TO INVEST IN
    @commands.has_role("Narrador")
    @commands.command()
    async def set_goal(self, ctx, goal, amount, comment=""):
        base = ctx.channel.category.name
        try:
            async with self.bot.pool.acquire() as connection:
                async with connection.transaction():
                    await connection.execute("""INSERT INTO goals
                                            (base, goal, goal_amount, comment)
                                            VALUES
                                            ($1, $2, $3, $4)""",
                                             base, goal, int(amount), comment)
            if comment == "":
                await ctx.send(f'Os Exilados de Sìor tem um novo possível '
                               f'objetivo:\n\n**{goal}**\n'
                               f'**Recursos necessários:** *{amount} GP*\n\n'
                               f'Fica à sua escolha quanto e quando se devotar'
                               f' a este projeto.')
            else:
                await ctx.send(f'Os Exilados de Sìor tem um novo possível '
                               f'objetivo:\n\n**{goal}**\n'
                               f'**Recursos necessários:** *{amount} GP*\n'
                               f'**Comentários adicionais:** *{comment}*\n\n'
                               f'Fica à sua escolha quanto e quando se devotar'
                               f' a este projeto.')
            await ctx.message.delete()
            return
        except Exception as e:
            print(e)
            await ctx.message.delete()
            return

    # ALLOWS PLAYERS TO SEE ALL GOALS FOR THE BASE THE COMMAND IS CALLED ON
    @commands.command()
    async def goals(self, ctx):
        base = ctx.channel.category.name
        try:
            async with self.bot.pool.acquire() as connection:
                async with connection.transaction():
                    goals = await connection.fetch("""SELECT * FROM goals
                                            WHERE base = $1""",
                                                   base)
            if goals:
                start_of_msg = f'**Objetivos Ativos de {base}:**\n'
                full_msg = start_of_msg
                for goal in goals:
                    goal_reason = goal["goal"]
                    amount = goal["goal_amount"]
                    current = goal["goal_current"]
                    goal_comment = goal["comment"]
                    full_msg += f'\n**{goal_reason}:** **{current}/{amount}**\n'
                    if goal_comment != "":
                        full_msg += f'Comentário adicional: *{goal_comment}*\n'
                await ctx.send(full_msg)
                await ctx.message.delete()
            return
        except Exception as e:
            print(e)
            await ctx.message.delete()
            return

    # ALLOWS INVESTMENT OF FUNDS ON BASES AND AWARDS XP AS PER RULES
    @commands.command()
    async def invest(self, ctx, amount, character, goal):
        award = self.bot.get_cog('AwardCog')
        if award is None:
            print('Erro para conseguir AwardCog')
            return
        print("amount = ", amount)
        print("character = ", character)
        print("comment = ", goal)
        author = ctx.author
        category = ctx.channel.category
        author_id = str(author.id)
        mentions = ctx.message.mentions
        char_gold, char_exp = (await award.check_gold_xp(character)).split(" ")
        current_goal = await self.check_goal(goal, category.name, "cur")
        print(current_goal)
        goal_amount = await self.check_goal(goal, category.name, "am")
        print(goal_amount)
        new_current_goal = int(current_goal) + int(amount)
        if int(current_goal) + int(amount) >= int(goal_amount):
            end_of_msg = ("\nCom este investimento, caso não existam outras \
                            circunstâncias que impeçam, este objetivo está \
                            pronto para ser concluído!")
        else:
            end_of_msg = (f'\n\nProgresso atual em direção a este objetivo:\n'
                          f'\t\t\t{new_current_goal}/{goal_amount}')
        print(char_gold, char_exp)

        if int(amount) > int(char_gold):
            print("Personagem caloteiro")
            await ctx.send(f'{character} não tem os fundos para fazer este '
                           f'investimento no momento.')
            return
        if mentions:
            author_id = str(ctx.message.mentions[0].id)
        try:
            await award.award(author_id, character, 'char_gold',
                              int(char_gold) - int(amount))
            await award.award(author_id, character, 'char_exp',
                              int(char_exp) + int(amount))
            await self.build_towards_goal(goal, category.name, new_current_goal)
            await ctx.send(f'{character} investiu {amount} GP em recursos '
                           f'em {category.name} para {goal}, e por isso'
                           f' recebeu a mesma quantia em EXP!' + end_of_msg)
            await ctx.message.delete()
        except Exception as e:
            print(e)
            await ctx.message.delete()
            return
        return


def setup(bot):
    bot.add_cog(GoalsCog(bot))
