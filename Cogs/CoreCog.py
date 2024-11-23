import discord
from discord.ext import commands

class CoreCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="sync", description="syncs global commands")
    async def sync(self, ctx: commands.Context):
        """Adds commands to the application interface (/ commands)"""
        if ctx.author.id == 312158176126566401:
            await self.bot.tree.sync(guild=None)
            await ctx.send(f"Successfully synced global commands")
        else:
            await ctx.send(f"Only LostMail can execute this command")

async def setup(bot: commands.Bot):
    await bot.add_cog(CoreCog(bot))