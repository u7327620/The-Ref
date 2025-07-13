from discord.ext import commands

class CoreCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="sync", description="syncs guild commands")
    async def sync(self, ctx: commands.Context):
        """Adds commands to the application interface (/ commands)"""
        if ctx.author.id == 312158176126566401:
            await self.bot.tree.sync(guild=ctx.guild)
            await ctx.send(f"Successfully synced guild commands")
        else:
            await ctx.send(f"Only LostMail can execute this command")

    @commands.hybrid_command(name="ping")
    async def ping(self, ctx: commands.Context):
        """PONG!"""
        await ctx.send(f":moyai:")

async def setup(bot: commands.Bot):
    await bot.add_cog(CoreCog(bot))