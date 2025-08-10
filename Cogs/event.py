import discord
from discord.ext import commands
from discord import app_commands
from typing import Union
from settings import *
import traceback
from datetime import datetime

def traceback_maker(error):
    try:
        return f"{''.join(traceback.format_tb(error.__traceback__))}\n{type(error).__name__}: {error}"
    except:
        return error

async def setup(bot):
    await bot.add_cog(Event(bot))


class Event(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.client.tree.on_error = self.on_command_error
        

    @commands.Cog.listener()
    async def on_command_error(self, msg: Union[discord.Interaction, commands.Context], error):
        # Command Errors
        if isinstance(error, commands.errors.CheckFailure):
            return
        if isinstance(error, commands.errors.CommandNotFound):
            return
        if isinstance(error, commands.errors.NotOwner):
            return await msg.reply(
                embed=discord.Embed(
                    title=":x: 오류",
                    description="> 관리자만 사용할 수 있습니다."),
                    color=EmbedColor.RED
                )

        # App Command Errors
        if isinstance(error, app_commands.errors.CommandOnCooldown):
            return await msg.response.send_message(
                embed=discord.Embed(
                    title=":clock: 쿨타임",
                    description=f"`{round(error.retry_after)}`초 뒤에 다시 실행해 주세요.",
                    color=EmbedColor.RED,
                ),    
                ephemeral=True,
            )
        if isinstance(error, app_commands.errors.CheckFailure):
            return

        # Unhandled Errors
        if not msg.message:
            commandData = f"/{msg.command.qualified_name}"
        else:
            commandData = msg.message.content[:100] + (
                f"...(총 {len(msg.message.content)}자)"
                if len(msg.message.content) >= 100
                else ""
            )
        if hasattr(error, "original"):
            error = traceback_maker(error.original)
        await msg.channel.send(
            embed=discord.Embed(
                title=":warning: 오류가 발생하였습니다.",
                description=f"```\n[ Command ] {commandData}```\n```\n{error}```",
                timestamp=datetime.utcnow(),
                color=EmbedColor.RED,
            ),
        )