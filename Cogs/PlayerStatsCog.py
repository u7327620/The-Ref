from discord.ext import commands
import requests

class PlayerStatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="get_stats", alias=["get"], description="Retrieves TFC fighter profile")
    async def get_stats(self, ctx: commands.Context, name: str):
        response = requests.get(f"https://github.com/u7327620/TMA_Records/raw/refs/heads/main/Data/Fighters/{name.lower()}_Database.txt")
        if response.status_code == 404:
            return await ctx.send(f"No TFC fighter \"{name}\" found")
        elif response.status_code != 200:
            return await ctx.send(f"error {response.status_code} looking up {name}")
        else:
            return await ctx.send(response.text)

async def setup(bot: commands.Bot):
    await bot.add_cog(PlayerStatsCog(bot))