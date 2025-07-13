from discord.ext import commands
from database import DatabaseManager

class PlayerStatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()

    @commands.hybrid_command(name="add_player", alias=["add"], description="Adds a player to the database")
    async def add_player(self, ctx: commands.Context, discord_id: int, name: str):
        if await self.db.set_player(discord_id, name.lower()):
            await ctx.send(f":moyai:")
        else:
            await ctx.send(f":no_entry:")

async def setup(bot: commands.Bot):
    await bot.add_cog(PlayerStatsCog(bot))