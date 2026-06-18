import logging
import os, discord.interactions
from urllib.parse import urlparse
from discord.ext import commands
from discord.ext.commands import Cog

gif_formats = ["video", "video/mp4", "video/quicktime", "video/mov", "image/gif", "gifv"]
submission_id = int(os.getenv("CLIP_SUBMISSION_CHANNEL"))
approval_id = int(os.getenv("CLIP_APPROVAL_CHANNEL"))
display_id = int(os.getenv("CLIP_DISPLAY_CHANNEL"))

class GifView(discord.ui.View):
    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green, emoji="✅") #type: ignore
    async def approve_button_callback(self, ctx: discord.Interaction, button: discord.ui.Button):
        await ctx.client.get_channel(display_id).send(ctx.message.content)
        try:
            await ctx.message.delete()
        except Exception as e:
            logging.log(logging.ERROR, f"Failed to delete message via button, error: {e}")
            await ctx.response.send_message("Couldn't delete the message :man_shrugging:", ephemeral=True)


    @discord.ui.button(label="NOT WORTHY", style=discord.ButtonStyle.red, emoji="❌") #type: ignore
    async def disapprove_button_callback(self, ctx: discord.Interaction, button: discord.ui.Button):
        try:
            await ctx.message.delete()
        except Exception as e:
            logging.log(logging.ERROR, f"Failed to delete message via button, error: {e}")
            await ctx.response.send_message("Couldn't delete the message :man_shrugging:", ephemeral=True)

class GifCog(commands.Cog):
    FILTERED_GIF_DOMAINS = ("tenor.com", "giphy.com")

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def _is_filtered_url(url: str | None) -> bool:
        if not url:
            return False
        hostname = urlparse(url).hostname
        if not hostname:
            return False
        hostname = hostname.lower()
        return any(hostname == domain or hostname.endswith(f".{domain}") for domain in GifCog.FILTERED_GIF_DOMAINS)

    def _media_has_filtered_url(self, media: object | None) -> bool:
        if not media:
            return False
        return self._is_filtered_url(getattr(media, "url", None)) or self._is_filtered_url(getattr(media, "proxy_url", None))

    def _embed_has_filtered_url(self, embed: discord.Embed) -> bool:
        return self._is_filtered_url(embed.url) or self._media_has_filtered_url(embed.video) or self._media_has_filtered_url(embed.thumbnail) or self._media_has_filtered_url(embed.image)

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != submission_id:
            return
        elif message.author.bot:
            return
        for attachment in message.attachments:
            if self._is_filtered_url(attachment.url) or self._is_filtered_url(attachment.proxy_url):
                continue
            if attachment.content_type in gif_formats:
                await self.request_approval(f"{attachment.proxy_url}, {message.jump_url} by {message.author}")
        for embed in message.embeds:
            if self._embed_has_filtered_url(embed):
                continue
            if embed.type in gif_formats:
                await self.request_approval(f"{embed.url}, {message.jump_url} by {message.author}")

    async def request_approval(self, text:str):
        await self.bot.get_channel(approval_id).send(text, view=GifView(timeout=None))

async def setup(bot: commands.Bot):
    await bot.add_cog(GifCog(bot))
