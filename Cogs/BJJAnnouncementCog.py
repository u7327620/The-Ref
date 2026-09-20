import json
import logging
from contextlib import closing
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

import discord
from discord.ext import commands, tasks


CHANNEL_ID = 674790073316671488
AEST = timezone(timedelta(hours=10), "AEST")
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = PROJECT_ROOT / ".bjj-announcement.json"
IMAGE_FILE = PROJECT_ROOT / "assets" / "bjj-announcement.png"
logger = logging.getLogger("discord.bjj_announcement")

ANNOUNCEMENT = """<@&239051720582234123> <@&691006314947805365> <@&759244559254421554>

BJJ Nights officially kicks off in <t:{start}:R>. To participate in this event all you have to do is simply ping the <@&759244559254421554> Role or ping someone of your choosing that’s it. No sign ups. No commitment. This is free to everyone but please do everyone a favor by taking a quick look at the rules in https://discord.com/channels/193574406507724800/1544507455034097804

Remember that this event is submissions only so don’t go posting your rpls unless you got a submission.

This event ends <t:{end}:R>  after it starts.

Have fun and remember <:realmoves:321015862964518913> only!"""


class BJJAnnouncementCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        try:
            self.enabled = json.loads(STATE_FILE.read_text(encoding="utf-8"))["enabled"] is True
        except (OSError, ValueError, KeyError, TypeError):
            self.enabled = False
        self.announce.start()

    def cog_unload(self):
        self.announce.cancel()

    @commands.hybrid_command(name="toggle-bjj-announcement", description="Toggle Friday BJJ announcements")
    @commands.check(lambda ctx: ctx.guild is not None and ctx.guild.id == 193574406507724800)
    async def toggle_bjj_announcement(self, ctx: commands.Context):
        if ctx.guild is None or not ctx.author.guild_permissions.ban_members:
            return await ctx.send("You need Ban Members permission to use this command.", ephemeral=True)
        enabled = not self.enabled
        STATE_FILE.write_text(json.dumps({"enabled": enabled}), encoding="utf-8")
        self.enabled = enabled
        await ctx.send(f"BJJ announcements {'enabled' if enabled else 'disabled'}.", ephemeral=True)
        return None

    @tasks.loop(time=time(hour=14, minute=5, tzinfo=AEST))
    async def announce(self):
        now = datetime.now(AEST)
        if not self.enabled or now.weekday() != 4:
            return
        start = now.replace(hour=17, minute=3, second=0, microsecond=0)
        end = start + timedelta(days=1)
        try:
            channel = self.bot.get_channel(CHANNEL_ID) or await self.bot.fetch_channel(CHANNEL_ID)
            with closing(discord.File(IMAGE_FILE, filename="bjj-announcement.png")) as image:
                await channel.send(
                    ANNOUNCEMENT.format(start=int(start.timestamp()), end=int(end.timestamp())),
                    file=image,
                    allowed_mentions=discord.AllowedMentions(
                        everyone=False, users=False, roles=True, replied_user=False,
                    ),
                )
        except (discord.HTTPException, OSError):
            logger.exception("Failed to send BJJ announcement to channel %s", CHANNEL_ID)

    @announce.before_loop
    async def before_announce(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(BJJAnnouncementCog(bot))
