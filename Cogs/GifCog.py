import logging
import os, discord.interactions
from discord.ext import commands
from discord.ext.commands import Cog
from dotenv import load_dotenv

# Put bot keys in a .env file in same-directory as main.py
load_dotenv(f"{os.getcwd()}/config.env")
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

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != submission_id:
            return
        elif message.author.bot:
            return
        for attachment in message.attachments:
            if attachment.content_type in gif_formats:
                await self.request_approval(f"{attachment.proxy_url}, {message.jump_url} by {message.author}")
        for embed in message.embeds:
            if embed.type in gif_formats:
                await self.request_approval(f"{embed.url}, {message.jump_url} by {message.author}")

    async def request_approval(self, text:str):
        await self.bot.get_channel(approval_id).send(text, view=GifView())

async def setup(bot: commands.Bot):
    await bot.add_cog(GifCog(bot))