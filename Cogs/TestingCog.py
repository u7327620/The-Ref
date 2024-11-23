from discord.ext import commands

class TestingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="ping")
    async def ping(self, ctx: commands.Context):
        """PONG!"""
        await ctx.send(f"PONG! YA STINKY GIT")

async def setup(bot: commands.Bot):
    await bot.add_cog(TestingCog(bot))