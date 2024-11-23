import logging
from discord import ClientException
from discord.ext import commands
from Cogs.RankingsCog import RankingsCog

INITIAL_WIDTH = 100

class MatchmakingCog(commands.Cog):
    """Relies on RankingsCog"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.playerQueue = {} # dict(playerID: int -> [elo: int, searchWidth: int]

    @commands.hybrid_command(name="queue", aliases=["q"], description="Adds a player to the queue")
    async def join_queue(self, ctx: commands.Context):
        if ctx.author.id not in self.playerQueue:
            rc = self.bot.get_cog("RankingsCog")
            self.playerQueue[ctx.author.id] = [rc.lookup(ctx), INITIAL_WIDTH]
            await ctx.send(f"Name: {ctx.author.name}, Elo: {self.playerQueue[ctx.author.id][0]} added to queue!")
        else:
            await ctx.send(f"{ctx.author.name} is already in queue!")

async def setup(bot: commands.Bot):
    # If Ranking cog not preloaded, could be goofy!
    await bot.add_cog(MatchmakingCog(bot))
