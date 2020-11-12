import itertools
import pprint
from collections import OrderedDict
import PyPDF2
import discord
import pypdftk
from PyPDF2.generic import BooleanObject, NameObject, IndirectObject
from discord.ext import commands

# NO NEED TO IMPORT FROM OTHER COGS

# DEFINITIONS NEEDED FOR EXTRACTING AND RETRIEVING CHARACTER SHEETS
prof_list = ["prof" + str(x) for x in range(1, 8)]
checkprof_list = ["checkprof" + str(x) for x in range(1, 8)]
ld_list = ["ld" + str(x) for x in range(1, 19)]
desc_list = ["desc" + str(x) for x in range(1, 19)]
sup_list = ["sup" + str(x) for x in range(1, 19)]
dur_list = ["dur" + str(x) for x in range(1, 19)]
inv_list = ["inventory" + str(x) for x in range(1, 19)]  # condensed ld,desc,sup,dur
attributes = ["str", "dex", "con", "int", "wis", "cha"]
attrib_profcheck_list = [x + "profcheck" for x in attributes]
scores_list = [x + "score" for x in attributes]
other_fields_list = ["player", "name", "origin", "class", "archetype", "exp",
                     "maxhp", "curac", "weaponsdmg", "spellsfeatures"]
field_list = list(itertools.chain(prof_list, checkprof_list, ld_list, desc_list,
                                  sup_list, dur_list, attrib_profcheck_list,
                                  scores_list, other_fields_list))


# print(field_list)

def getfields(pdffile, tree=None, retval=None, outfile=None):
    fieldattributes = {'/FT': 'Field Type', '/Parent': 'Parent',
                       '/T': 'Field Name', '/TU': 'Alternate Field Name',
                       '/TM': 'Mapping Name', '/Ff': 'Field Flags',
                       '/V': 'Value', '/DV': 'Default Value'}
    if retval is None:
        retval = OrderedDict()
        catalog = pdffile.trailer["/Root"]
        if "/AcroForm" in catalog:
            tree = catalog["/AcroForm"]
        else:
            return None
    if tree is None:
        return retval

    pdffile._checkKids(tree, retval, outfile)
    for attr in fieldattributes:
        if attr in tree:
            pdffile._buildField(tree, retval, outfile, fieldattributes)
            break

    if "/Fields" in tree:
        fields = tree["/Fields"]
        for f in fields:
            field = f.getObject()
            pdffile._buildField(field, retval, outfile, fieldattributes)

    return retval


def get_form_fields(infile):
    infile = PyPDF2.PdfFileReader(open(infile, 'rb'))
    fields = getfields(infile)
    return OrderedDict((k, v.get('/V', '')) for k, v in fields.items())


def str_check(val):
    if not isinstance(val, str):
        return str(val, "utf-8", "ignore")
    else:
        return val


def set_need_appearances_writer(writer):
    # basically used to ensured there are not
    # overlapping form fields, which makes printing hard
    try:
        catalog = writer._root_object
        # get the AcroForm tree and add "/NeedAppearances attribute
        if "/AcroForm" not in catalog:
            writer._root_object.update({
                NameObject("/AcroForm"): IndirectObject(len(writer._objects),
                                                        0, writer)})

        need_appearances = NameObject("/NeedAppearances")
        writer._root_object["/AcroForm"][need_appearances] = BooleanObject(True)

    except Exception as e:
        print('set_need_appearances_writer() catch : ', repr(e))

    return writer


class CharactersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    # ---------------------------------
    # AUXILIARY FUNCTIONS TO COMMMANDS
    # ---------------------------------

    # GETS ID FROM PREVIOUSLY ESTABLISHED NAME IN DATABASE
    async def get_id_from_db(self, name):
        async with self.bot.pool.acquire() as connection:
            async with connection.transaction():
                return await connection.fetchval("""SELECT discord_id FROM
                                                players WHERE
                                                player_name = $1""", name)

    # GETS NAME FROM PREVIOUSLY ESTABLISHED ID IN DATABASE
    async def get_name_from_db(self, id):
        async with self.bot.pool.acquire() as connection:
            async with connection.transaction():
                return await connection.fetchval("""SELECT player_name FROM
                                                players WHERE
                                                discord_id = $1""", id)

    # CHECKS NUMBER OF CHARACTERS THE PLAYER HAS THAT ARE ALIVE
    async def check_number_of_characters(self, id):
        async with self.bot.pool.acquire() as connection:
            async with connection.transaction():
                num = await connection.fetchval("""SELECT no_characters FROM
                                                players WHERE
                                                discord_id = $1 AND
                                                alive = 'true'""", id)
                if num < 2:
                    return True
                else:
                    return False

    # ---------------------------
    # CHARACTER-RELATED COMMANDS
    # ---------------------------

    # EXTRACTS CHARACTER INFO FROM PDF FILLABLE CHARACTER SHEET: CREATE/UPDATE
    @commands.command(aliases=["char"])
    async def extract_character_sheet(self, ctx, func):
        std_filename = "char_sheet.pdf"
        forbidden_prefixes = ["ld", "desc", "sup", "dur"]
        message = ctx.message
        author = message.author
        statement = ''
        end_message = ''
        msg_attachments = [x for x in message.attachments
                           if x.filename.endswith(".pdf")]
        for attachment in msg_attachments:
            filename = attachment.filename
            await attachment.save(std_filename)
            char_sheet_fields = get_form_fields(std_filename)
            important_fields = {k: str_check(v) for (k, v) in
                                char_sheet_fields.items() if k in field_list}
            new_char = {"char_" + x: y for (x, y) in important_fields.items()
                        if not x.startswith(tuple(forbidden_prefixes))}
            raw_inv = {x: y for (x, y) in important_fields.items()
                       if x.startswith(tuple(forbidden_prefixes))}
            inventory = {"char_inventory" + str(x):
                             '-'.join([raw_inv["ld" + str(x)],
                                       raw_inv["desc" + str(x)], raw_inv["sup" + str(x)],
                                       raw_inv["dur" + str(x)]])
                         for x in range(1, 19)}
            new_char.update(inventory)
            pprint.pprint(new_char)
            char_player = new_char["char_player"]
            char_player_id = await self.get_id_from_db(char_player)
            if char_player_id:
                char_player_id = str_check(char_player_id)
                if await self.check_number_of_characters(char_player_id):
                    name_to_id = {"char_player": char_player_id}
                    new_char.update(name_to_id)
                    pprint.pprint(new_char)
                    db_entries = [(k, v) for k, v in new_char.items()]
                    if func == "new":
                        db_columns = ', '.join([e[0] for e in db_entries])
                        db_values = tuple([e[1] for e in db_entries])
                        print(db_columns)
                        print(db_values)
                        statement = (f'INSERT INTO characters ({db_columns})'
                                     f' VALUES {db_values};'
                                     f'\nUPDATE players '
                                     f'SET no_characters = no_characters + 1 '
                                     f'WHERE discord_id = \'{char_player_id}\';')
                        end_message = (f'<@{new_char["char_player"]}>, seu '
                                       f'personagem **{new_char["char_name"]}** '
                                       f'foi adicionado às fileiras dos corajosos'
                                       f' aventureiros!')
                    elif func == "update":
                        db_update = ', \n'.join(" = ".join([e[0], "'" + e[1] + "'"])
                                                for e in db_entries)
                        print(db_update)
                        statement = (f'UPDATE characters SET {db_update}\n'
                                     f' WHERE char_player = \''
                                     f'{char_player_id}\' AND char_name = \''
                                     f'{new_char["char_name"]}\';')
                        end_message = (f'<@{new_char["char_player"]}>, seu '
                                       f'personagem **{new_char["char_name"]}** '
                                       f'foi atualizado de acordo com a nova '
                                       f'ficha enviada!')
                    try:
                        print("Entering insert or update")
                        async with self.bot.pool.acquire() as connection:
                            async with connection.transaction():
                                await connection.execute(statement)
                        await ctx.send(end_message)
                        await ctx.message.delete()
                        return
                    except Exception as e:
                        await ctx.send(
                            f'ERRO ao extrair personagem de {filename}:\n\n'
                            f'{e}')
                        print(e)
                        await ctx.message.delete()
                        return
                else:
                    await ctx.send(
                        f'<@{char_player_id}>, você já tem dois '
                        f'personagens vivos registrados no banco de '
                        f'dados. Caso um destes tenha morrido em uma '
                        f'expedição, peça ao Narrador para que seja '
                        f'oficializada a baixa.')
                    await ctx.message.delete()
                    return
            else:
                await ctx.send("""Jogador ou Jogadora ainda não está nos
                                registros do servidor. Por favor informe ao
                                Narrador que designação quer utilizar para
                                que possa entrar nos registros.""")
                await ctx.message.delete()
                return

    # RETRIEVES CHARACTER SHEET FROM DATABASE AND OUTPUTS IT IN PDF FILE
    @commands.command(aliases=["get_char"])
    async def retrieve_character_sheet(self, ctx, name):
        try:
            async with self.bot.pool.acquire() as connection:
                async with connection.transaction():
                    char = await connection.fetchrow("""SELECT * FROM characters
                                                WHERE char_name = $1""", name)
            char = dict(char)
            out_char = {k[len("char_"):]: v for k, v in char.items()
                        if not k.startswith("char_inventory")}
            out_inv = {k: v for k, v in char.items()
                       if k.startswith("char_inven")}
            separated_inventory = dict()
            for k, v in out_inv.items():
                order = k[len("char_inventory"):]
                temp_list = v.split("-")
                separated_inventory['ld' + order] = temp_list.pop(0)
                separated_inventory['dur' + order] = temp_list.pop()
                separated_inventory['sup' + order] = temp_list.pop()
                separated_inventory['desc' + order] = '-'.join(temp_list)
            separated_inventory["player"] = await self.get_name_from_db(
                out_char["player"])
            out_char.update(separated_inventory)
            pprint.pprint(out_char)

            finalpdf = pypdftk.fill_form("Base_Sheet.pdf", out_char,
                                         f'{"_".join(name.split(" "))}.pdf', flatten=False)
            print(finalpdf)
            with open(finalpdf, 'rb') as file:
                file_to_send = discord.File(file, finalpdf)
                await ctx.send(f'{ctx.author.mention}, aqui está o personagem'
                               f' requisitado, **{name}**:\n',
                               file=file_to_send)
            await ctx.message.delete()
        except Exception as e:
            print(e)
            await ctx.message.delete()
            return
        return

    # DECOMISSIONS CHARACTERS EITHER THROUGH DEATH OR RETIREMENT
    @commands.has_role('Narrador')
    @commands.command(aliases=["goodbye_char"])
    async def decomission_character(self, ctx, name, player, reason=''):
        player_id = player.strip("<>!@")
        print(name)
        print(reason)
        try:
            async with self.bot.pool.acquire() as connection:
                async with connection.transaction():
                    await connection.execute("""UPDATE characters set
                                            alive = FALSE
                                            WHERE char_name = $1 AND
                                            char_player = $2""",
                                             name, player_id)
            if len(reason) > 0:
                await ctx.send(f'**{name}** não está mais entre os corajosos '
                               f'aventureiros dos Exilados de Sìor. Seu '
                               f'destino: {reason}.')
            else:
                await ctx.send(f'**{name}** não está mais entre os corajosos '
                               f'aventureiros dos Exilados de Sìor.')
            await ctx.message.delete()
            return
        except Exception as e:
            print(e)
            await ctx.message.delete()
            return


def setup(bot):
    bot.add_cog(CharactersCog(bot))
