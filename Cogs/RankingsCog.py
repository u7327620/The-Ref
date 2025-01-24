import logging
from typing import Optional
import sqlite3
from discord.ext import commands

INITIAL_ELO = 1500

class RankingsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.connection = create_connection("rankings.db")
        self.cursor = self.connection.cursor()

    @commands.hybrid_command(name="elo_lookup", description="Enter player name, discord id, or leave blank for self!")
    async def elo_lookup(self, ctx: commands.Context, name_or_id: Optional[str]):
        try:
            if name_or_id is not None:
                if name_or_id.isnumeric():
                    self.cursor.execute("SELECT elo FROM players WHERE discord_id like ?", (name_or_id,))
                else:
                    self.cursor.execute("SELECT elo FROM players WHERE name like ?", (name_or_id,))
                ret_elo = str(self.cursor.fetchone())
                if ret_elo[1:-2] == 'o':
                    await ctx.send(f"{name_or_id} isn't in the database.")
                    return 0
                else:
                    await ctx.send(f"{name_or_id}'s elo is: {ret_elo[1:-2]}")
                    return int(ret_elo[1:-2])
            else:
                self.cursor.execute("SELECT elo FROM players WHERE discord_id like ?", (ctx.author.id,))
                await ctx.send(f"your elo is: {str(self.cursor.fetchone())[1:-2]}")
        except sqlite3.OperationalError:
            await ctx.send("No matches found. Have you linked your discord account yet?")

    @commands.hybrid_command(name="link", description="Links a discord account to a (presently, it also creates a new) player")
    async def link(self, ctx: commands.Context, *, name: str, discord_id: Optional[str]):
        try:
            # INSERT INTO players (discord_id, name, elo)
            if discord_id is not None:
                self.cursor.execute("INSERT INTO players (discord_id, name, elo) VALUES (?, ?, ?)",
                                    (discord_id, name.lower(), INITIAL_ELO))
                logging.log(logging.DEBUG, f"Attempted add of user: {discord_id}")
            else:
                self.cursor.execute("INSERT INTO players (discord_id, name, elo) VALUES (?, ?, ?)",
                                (ctx.author.id, name.lower(), INITIAL_ELO))
                logging.log(logging.DEBUG, f"Attempted add of user: {ctx.author.name}")
            self.connection.commit()
            await ctx.send("Successful linkage!")
        except sqlite3.IntegrityError as e:
            logging.log(logging.ERROR, e)
            await ctx.send("Likely already linked! Ask Lostmail for further help!")

def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
        logging.log(logging.DEBUG, f"Connection to {path} successful")
    except Exception as error:
        logging.log(logging.ERROR, error)
    return connection

async def setup(bot):
    await bot.add_cog(RankingsCog(bot))