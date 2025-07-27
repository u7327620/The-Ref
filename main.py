import asyncio, logging, sys, os
from dotenv import load_dotenv
from discord.ext import commands
from discord import Intents

# Put bot keys in a .env file in same-directory as main.py
load_dotenv(f"{os.getcwd()}/config.env")
token = os.getenv("TOKEN")

# All intents bar presences and members
intents = Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="gimme ", intents=intents)

# Logging errors
logger = logging.getLogger("discord")
logger.setLevel(logging.ERROR)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# discord.py v2 async startup
async def load_cogs():
    for file in os.listdir("./Cogs"):
        if file.endswith(".py"):
            await client.load_extension(f"Cogs.{file[:-3]}")
    logging.log(logging.DEBUG, client.all_commands)

async def main():
    async with client:
        await load_cogs()
        await client.start(token)

asyncio.run(main())