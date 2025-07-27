from discord.ext import commands
from discord import app_commands, Interaction
import requests


class PlayerStatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="get_stats", description="Retrieves TFC fighter profile")
    async def get_stats(self, ctx: Interaction, name: str):
        response = requests.get(f"https://github.com/u7327620/TMA_Records/raw/refs/heads/main/Data/Fighters/{name.lower()}_Database.txt")
        if response.status_code == 404:
            return await ctx.response.send_message(f"No TFC fighter \"{name}\" found", ephemeral=True)
        elif response.status_code != 200:
            return await ctx.response.send_message(f"error {response.status_code} looking up {name}", ephemeral=True)
        else:
            return await ctx.response.send_message(response.text, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(PlayerStatsCog(bot))