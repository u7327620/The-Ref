from discord.permissions import Permissions
from discord.ext import commands


class CoreCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="sync", description="syncs guild commands", default_permissions=Permissions(administrator=True))
    async def sync(self, ctx: commands.Context):
        """Adds commands to the application interface (/ commands)"""
        if ctx.author.id == 312158176126566401:
            await self.bot.tree.sync(guild=ctx.guild)
            out = ", ".join([x for x in self.bot.all_commands])
            await ctx.send(f"Successfully synced: {", ".join(out)}")
        else:
            await ctx.send(f"Only LostMail can execute this command")

    @commands.hybrid_command(name="ping")
    async def ping(self, ctx: commands.Context):
        """PONG!"""
        await ctx.send(f":moyai:")

async def setup(bot: commands.Bot):
    await bot.add_cog(CoreCog(bot))