from discord import ClientException
from discord.ext import commands, tasks
from Cogs.RankingsCog import RankingsCog

INITIAL_WIDTH = 100


async def match_made_helper(player: tuple, opponent: tuple):
    assert player[0] != opponent[0]  # ids are not the same
    player_elo = player[1][0]
    opponent_elo = opponent[1][0]
    search = min(player[1][1], opponent[1][1]) # always check with minimum width
    return player_elo <= opponent_elo + search or player_elo >= opponent_elo - search

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
                if len(self.playerQueue) == 0:
                    self.matchmaking_loop.start(ctx)
                self.playerQueue[ctx.author.id] = [elo, INITIAL_WIDTH]
                elo = self.playerQueue[ctx.author.id][0]
                await ctx.send(f"Name: {ctx.author.name}, Elo: {elo} added to queue!")
            else:
                await ctx.send(f"{ctx.author.name} is already in queue!")
        except ClientException:
            await ctx.send(f"{ctx.author.name} couldn't be added to queue! Perchance they're unlinked?")

    async def match_players(self, ctx: commands.Context):
        for index, player in enumerate(self.playerQueue.items()):
            for _, opponent in enumerate(self.playerQueue.items(), start=index+1):
                if player[0] == opponent[0]:
                    pass
                elif await match_made_helper(player, opponent):
                    await ctx.send(f"Match made for @{player[0]} ({player[1][0]}) and @{opponent[0]} ({opponent[1][0]})!")
                    self.playerQueue.pop(opponent[0])
                    self.playerQueue.pop(player[0])
                    if len(self.playerQueue) == 0:
                        self.matchmaking_loop.stop()
                    return

    async def increase_search_range(self):
        for player in self.playerQueue:
            self.playerQueue[player][1] += 15

    @tasks.loop(seconds=15)
    async def matchmaking_loop(self, ctx: commands.Context):
        print(self.playerQueue)
        await self.increase_search_range()
        await self.match_players(ctx)

    @commands.hybrid_command(name="test_queue", description="Adds Nazzern to the queue")
    async def test_join_queue(self, ctx: commands.Context):
        if ctx.author.id == 312158176126566401:
            self.playerQueue[1211615230820360203] = [1500, INITIAL_WIDTH]
            elo = self.playerQueue[1211615230820360203][0]
            await ctx.send(f"Name: {ctx.author.name}, Elo: {elo} added to queue!")

async def setup(bot: commands.Bot):
    # If Ranking cog not preloaded, could be goofy!
    await bot.add_cog(MatchmakingCog(bot))
