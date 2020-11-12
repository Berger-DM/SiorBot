import os
import ssl
import discord
import asyncio
import asyncpg
from discord.ext import commands
from dotenv import load_dotenv, find_dotenv

intents = discord.Intents.all()
client = commands.Bot(command_prefix="!", intents=intents)
extensions = ['cogs.events', 'cogs.characters', 'cogs.goals', 'cogs.award',
              'cogs.server', 'cogs.players', 'cogs.quests']
load_dotenv(find_dotenv())

if __name__ == "__main__":
    for extension in extensions:
        client.load_extension(extension)

try:
    heroku_url = os.getenv("DATABASE_URL")
    ssl_obj = ssl.create_default_context(cafile='./rds-combined-ca-bundle.pem')
    ssl_obj.check_hostname = False
    ssl_obj.verify_mode = ssl.CERT_NONE
    loop = asyncio.get_event_loop()
    client.pool = loop.run_until_complete(asyncpg.create_pool(dsn=heroku_url,
                                                              ssl=ssl_obj))
except asyncpg.exceptions.InvalidPasswordError:
    import smtplib

    email = os.getenv("GMAIL_EMAIL")
    smtp = smtplib.SMTP("smtp.gmail.com", 587)
    smtp.starttls()
    smtp.login(email, os.getenv("GMAIL_PASSW"))
    de = email
    para = [email]
    msg = """From: %s\nTo: %s\nSubject: Database Error in SiorBot\n
    O SiorBot teve um problema para acessar seu banco de dados.\n
    Por favor verifique as credenciais e atualize o .env do SiorBot.\n
    Atenciosamente,\n
    SiorBot.\n
    """ % (de, ', '.join(para))
    smtp.sendmail(de, para, msg)
    smtp.quit()

    exit(1)

client.run(os.getenv("TOKEN"), bot='true')
