from typing import Callable, Optional
import discord.interactions
import sqlite3
from discord import app_commands
from discord.app_commands import default_permissions
from discord.ext import commands

PAGE_LENGTH = 10

class Pagination(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, get_page: Callable):
        super().__init__(timeout=120)
        self.interaction = interaction
        self.get_page = get_page
        self.total_pages: Optional[int] = None
        self.index = 1

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.interaction.user:
            return True
        else:
            emb = discord.Embed(
                description=f"Only the author of the command can perform this action.",
                color=16711680
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
            return False

    async def navigate(self):
        emb, self.total_pages = await self.get_page(self.index)
        if self.total_pages == 1:
            await self.interaction.response.send_message(embed=emb)
        elif self.total_pages > 1:
            self.update_buttons()
            await self.interaction.response.send_message(embed=emb, view=self)

    async def edit_page(self, interaction: discord.Interaction):
        emb, self.total_pages = await self.get_page(self.index)
        self.update_buttons()
        await interaction.response.edit_message(embed=emb, view=self)

    def update_buttons(self):
        if self.index > self.total_pages // 2:
            self.children[2].emoji = "⏮️"
        else:
            self.children[2].emoji = "⏭️"
        self.children[0].disabled = self.index == 1
        self.children[1].disabled = self.index == self.total_pages

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction, button: discord.Button):
        self.index -= 1
        await self.edit_page(interaction)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: discord.Button):
        self.index += 1
        await self.edit_page(interaction)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.blurple)
    async def end(self, interaction: discord.Interaction, button: discord.Button):
        if self.index <= self.total_pages//2:
            self.index = self.total_pages
        else:
            self.index = 1
        await self.edit_page(interaction)

    async def on_timeout(self):
        # remove buttons on timeout
        message = await self.interaction.original_response()
        await message.edit(view=None)

    @staticmethod
    def compute_total_pages(total_results: int, results_per_page: int) -> int:
        return ((total_results - 1) // results_per_page) + 1

class BetCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bets = sqlite3.connect("database/bets.db")

    @app_commands.command(name="calculate_payouts", description="calculates all bets needing to be payed out")
    @default_permissions(ban_members=True)
    async def calculate_payouts(self, ctx: discord.Interaction):
        """Calculates all bets needing to be payed out"""
        # 1. Get all correct bets on finished matches which are not yet paid out
        cursor = self.bets.cursor()
        correct_unpaid_bets = cursor.execute("SELECT * FROM bets WHERE match_id IN (SELECT id FROM matches WHERE victor IS bets.fighter) AND bet_received = 1 AND payed_out = 0").fetchall()

        # 2. Calculate for each bet
        out = []
        for bet in correct_unpaid_bets:
            f_name = bet[0]
            bet_amt = bet[2]
            punter = bet[3]
            f_total = cursor.execute("SELECT SUM(amount) FROM bets WHERE match_id = ? AND fighter = ?", (bet[4], f_name)).fetchone()[0]
            match_total = cursor.execute("SELECT SUM(amount) FROM bets WHERE match_id = ?", (bet[4],)).fetchone()[0]
            opp_total = match_total - f_total
            payout = int(bet_amt + 0.85 * (bet_amt / f_total) * opp_total)
            out.append(f"({bet[1]}) {punter} won ${payout:,} on {f_name} in ({bet[4]}) with a bet of ${bet_amt:,}")
        return await ctx.response.send_message("\n".join(out) if out else "No payouts to calculate", ephemeral=True)

    # ----------------- matches ----------------- #
    @app_commands.command(name="get_matches", description="lists all matches")
    async def get_matches(self, ctx: discord.Interaction):
        async def get_page(page: int):
            cursor = self.bets.cursor()
            all_bets = cursor.execute("SELECT fighter, SUM(amount), match_id FROM bets GROUP BY match_id, fighter").fetchall()
            cursor.execute("SELECT * FROM matches order by id desc")
            rows = cursor.fetchmany(50)
            emb = discord.Embed(title="Matches", color=0xff0000)
            for row in rows:
                f1 = row[1]
                f2 = row[2]
                total_f1 = total_f2 = 0
                for f, bet, match in all_bets:
                    if f == f1 and match == row[0]:
                        total_f1 = bet
                    elif f == f2 and match == row[0]:
                        total_f2 = bet

                name = f"{f1} vs {f2}"
                if row[3] is not None:
                    name += f" - {row[3]} won"
                name += f" {row[0]}"
                emb.add_field(name=name, value=f"${total_f1:,} vs ${total_f2:,}",
                              inline=False)
            emb.set_author(name=f"Requested by {ctx.user}", icon_url=ctx.user.display_avatar.url)
            total_pages = Pagination.compute_total_pages(len(rows), PAGE_LENGTH)
            emb.set_footer(text=f"Page {page}/{total_pages}")
            return emb, total_pages
        await Pagination(ctx, get_page).navigate()

    @app_commands.command(name="add_match", description="adds a match to the database")
    @default_permissions(ban_members=True)
    async def add_match(self, ctx: discord.Interaction, fighter1: str, fighter2: str):
        """Adds a match to the database"""
        cursor = self.bets.cursor()
        try:
            cursor.execute("INSERT INTO matches (fighter_1, fighter_2) VALUES (?, ?)", (fighter1.lower(), fighter2.lower()))
            self.bets.commit()
            return await ctx.response.send_message(f"Added match {fighter1} vs {fighter2}", ephemeral=True)
        except sqlite3.Error:
            return await ctx.response.send_message(f"Error trying to add match, try again", ephemeral=True)

    @app_commands.command(name="remove_match", description="removes a match from the database")
    @default_permissions(ban_members=True)
    async def remove_match(self, ctx: discord.Interaction, match_id: int):
        """Removes a match from the database"""
        try:
            match, cursor = await self._get_thing("matches", match_id)
            cursor.execute("DELETE FROM matches WHERE id = ?", (match_id,))
            cursor.execute("DELETE FROM bets WHERE match_id = ?", (match_id,))
            self.bets.commit()
            return await ctx.response.send_message(f"Removed match {match_id} ({match[1]} vs {match[2]}) and any associated bets", ephemeral=True)
        except sqlite3.Error:
            return await ctx.response.send_message(f"Error trying to remove match, try again", ephemeral=True)
        except commands.CommandError as e:
            return await ctx.response.send_message(str(e), ephemeral=True)

    # ----------------- bets ----------------- #
    @app_commands.command(name="get_bets", description="retrieves a list of all the bets")
    async def get_bets(self, ctx: discord.Interaction, match_id: Optional[int] = None):
        async def get_page(page: int):
            offset = (page - 1) * PAGE_LENGTH
            cursor = self.bets.cursor()
            if match_id:
                emb = discord.Embed(title=f"Bets on {match_id}", color=0xff0f00)
                cursor.execute(
                    "SELECT * FROM bets JOIN matches ON bets.match_id = matches.id WHERE matches.id = ? order by bets.id desc",
                    (match_id,))
            else:
                emb = discord.Embed(title="Recent Bets", color=0xff0000)
                cursor.execute("SELECT * FROM bets JOIN matches ON bets.match_id = matches.id order by bets.id desc")
            rows = cursor.fetchmany(50)
            for row in rows[offset:offset + PAGE_LENGTH]:
                temp_value = ""
                if row[5] == 1:  # Approved bets
                    temp_name = f"${row[2]:,} on {row[0]} by {row[3]} - PAID ({row[1]})"
                else:
                    temp_name = f"${row[2]:,} on {row[0]} by {row[3]} ({row[1]})"
                if not match_id:
                    temp_value = f"{row[8]} vs {row[9]}"
                emb.add_field(name=temp_name, value=temp_value, inline=False)
            emb.set_author(name=f"Requested by {ctx.user}", icon_url=ctx.user.display_avatar.url)
            total_pages = Pagination.compute_total_pages(len(rows), PAGE_LENGTH)
            emb.set_footer(text=f"Page {page}/{total_pages}")
            return emb, total_pages

        await Pagination(ctx, get_page).navigate()

    @app_commands.command(name="add_bet", description="adds a bet to the database")
    async def add_bet(self, ctx: discord.Interaction, match_id: int, fighter: str, amount: int):
        """Adds a bet to the database"""
        try:
            match, cursor = await self._get_thing("matches", match_id)
            if match[3] is not None:
                return await ctx.response.send_message(f"Match {match_id} already has a victor ({match[3]}), no more bets allowed", ephemeral=True)
            cursor.execute("INSERT INTO bets (fighter, amount, punter, match_id) VALUES (?, ?, ?, ?)",
                           (fighter.lower(), amount, str(ctx.user), match_id))
            self.bets.commit()
            return await ctx.response.send_message(f"Added bet of ${amount:,} on {fighter} for match {match_id} ({match[1]} vs {match[2]})",ephemeral=True)
        except sqlite3.IntegrityError:
            return await ctx.response.send_message(f"Bet must be greater than 0", ephemeral=True)
        except sqlite3.Error:
            return await ctx.response.send_message(f"Error trying to add bet, try again", ephemeral=True)
        except commands.commandError as e:
            return await ctx.response.send_message(str(e), ephemeral=True)

    @app_commands.command(name="remove_bet", description="removes a bet from the database")
    async def remove_bet(self, ctx: discord.Interaction, bet_id: int):
        """Removes a bet from the database"""
        try:
            bet, cursor = await self._get_thing("bets", bet_id)
            if ctx.user.name != bet[3] and not ctx.user.guild_permissions.ban_members:
                return await ctx.response.send_message(f"Only the punter ({bet[3]}) or a moderator can remove this bet", ephemeral=True)
            cursor.execute("DELETE FROM bets WHERE id = ?", (bet_id,))
            self.bets.commit()
            return await ctx.response.send_message(f"Removed bet {bet_id} (${bet[2]:,} on {bet[0]} by {bet[3]})", ephemeral=True)
        except sqlite3.Error:
            return await ctx.response.send_message(f"Error trying to remove bet, try again", ephemeral=True)
        except commands.CommandError as e:
            return await ctx.response.send_message(str(e), ephemeral=True)

    @app_commands.command(name="approve_bet", description="approves a bet as paid")
    @default_permissions(ban_members=True)
    async def approve_bet(self, ctx: discord.Interaction, bet_id: int):
        """Approves a bet as paid"""
        try:
            bet, cursor = await self._get_thing("bets", bet_id)
            if bet[5] == 1:
                return await ctx.response.send_message(f"Bet {bet_id} is already approved", ephemeral=True)
            cursor.execute("UPDATE bets SET bet_received = 1 WHERE id = ?", (bet_id,))
            self.bets.commit()
            return await ctx.response.send_message(f"Approved bet {bet_id} (${bet[2]:,} on {bet[0]} by {bet[3]}) as paid", ephemeral=True)
        except sqlite3.Error:
            return await ctx.response.send_message(f"Error trying to approve bet, try again", ephemeral=True)
        except commands.CommandError as e:
            return await ctx.response.send_message(str(e), ephemeral=True)

    @app_commands.command(name="pay_bet", description="marks a bet as payed out")
    @default_permissions(ban_members=True)
    async def pay_bet(self, ctx: discord.Interaction, bet_id: int):
        """Marks a bet as payed out"""
        try:
            bet, cursor = await self._get_thing("bets", bet_id)
            if bet[6] == 1:
                return await ctx.response.send_message(f"Bet {bet_id} is already payed out", ephemeral=True)
            cursor.execute("UPDATE bets SET payed_out = 1 WHERE id = ?", (bet_id,))
            self.bets.commit()
            return await ctx.response.send_message(f"Marked bet {bet_id} (${bet[2]:,} on {bet[0]} by {bet[3]}) as payed out", ephemeral=True)
        except sqlite3.Error:
            return await ctx.response.send_message(f"Error trying to mark bet as payed out, try again", ephemeral=True)
        except commands.CommandError as e:
            return await ctx.response.send_message(str(e), ephemeral=True)

    # ----------------- other ----------------- #
    @app_commands.command(name="set_victory", description="sets the victor of a match")
    @default_permissions(ban_members=True)
    async def set_victor(self, ctx: discord.Interaction, match_id: int, fighter_name: str):
        """Sets the victor of a match"""
        try:
            match, cursor = await self._get_thing("matches", match_id, fighter_name)
            cursor.execute("UPDATE matches SET victor = ? WHERE id = ?", (fighter_name.lower(), match_id))
            self.bets.commit()
            return await ctx.response.send_message(f"Set victor of match {match_id} to {fighter_name}", ephemeral=True)
        except sqlite3.Error:
            return await ctx.response.send_message(f"Error trying to set victor, try again", ephemeral=True)
        except commands.CommandError as e:
            return await ctx.response.send_message(str(e), ephemeral=True)

    # ----------------- helper ----------------- #
    async def _get_thing(self, table: str, id: int, fighter: str=None) -> tuple:
        """Intentionally sql injection vulnerable for internal use only"""
        cursor = self.bets.cursor()
        match = cursor.execute(f"SELECT * FROM {table.lower()} WHERE id = {id}").fetchone()
        if not match:
            raise commands.CommandError(f"No {table} with id {id} found")
        if fighter and table.lower() == "matches":
            if fighter.lower() not in (match[1], match[2]):
                raise commands.CommandError(f"{fighter} is not in match {id} ({match[1]} vs {match[2]})")
        return match, cursor

async def setup(bot: commands.Bot):
    await bot.add_cog(BetCog(bot))
