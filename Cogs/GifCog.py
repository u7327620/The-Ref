import logging
import os, discord.interactions
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
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def _is_filtered_url(url: str | None) -> bool:
        if not url:
            return False
        url_lower = url.lower()
        return "tenor" in url_lower or "giphy" in url_lower

    def _embed_has_filtered_url(self, embed: discord.Embed) -> bool:
        if self._is_filtered_url(embed.url):
            return True
        if embed.video and self._is_filtered_url(embed.video.url):
            return True
        if embed.thumbnail and self._is_filtered_url(embed.thumbnail.url):
            return True
        if embed.image and self._is_filtered_url(embed.image.url):
            return True
        return False

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != submission_id:
            return
        elif message.author.bot:
            return
        for attachment in message.attachments:
            if self._is_filtered_url(attachment.url) or self._is_filtered_url(attachment.proxy_url) or self._is_filtered_url(str(attachment)):
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
