import asyncio, logging, sys, os
import sqlite3
from dotenv import load_dotenv
from discord.ext import commands
from discord import Intents
from database import DatabaseManager

# Put bot keys in a .env file in same-directory as main.py
load_dotenv()
token = os.getenv("API_KEY")

# All intents bar presences and members
intents = Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="gimme ", intents=intents)

# Logging errors
root = logging.getLogger()
root.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

# discord.py v2 async startup
async def load_cogs():
    for file in os.listdir("./Cogs"):
        if file.endswith(".py"):
            await client.load_extension(f"Cogs.{file[:-3]}")

async def load_database():
    client.database = DatabaseManager(connection=sqlite3.connect(
        f"{os.path.realpath(os.path.dirname(__file__))}/database/rankings.db"))

async def main():
    async with client:
        await load_database()
        await load_cogs()
        await client.start(token)

asyncio.run(main())