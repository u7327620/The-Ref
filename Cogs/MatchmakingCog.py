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
        try:
            lookup_cmd = self.bot.get_command("elo_lookup")
            if ctx.author.id not in self.playerQueue:
                elo = await lookup_cmd.__call__(ctx, name_or_id=str(ctx.author.id))
                self.playerQueue[ctx.author.id] = [elo, INITIAL_WIDTH]
                elo = self.playerQueue[ctx.author.id][0]
                await ctx.send(f"Name: {ctx.author.name}, Elo: {elo} added to queue!")
            else:
                await ctx.send(f"{ctx.author.name} is already in queue!")
        except ClientException:
            await ctx.send(f"{ctx.author.name} couldn't be added to queue! Perchance they're unlinked?")

async def setup(bot: commands.Bot):
    # If Ranking cog not preloaded, could be goofy!
    await bot.add_cog(MatchmakingCog(bot))
