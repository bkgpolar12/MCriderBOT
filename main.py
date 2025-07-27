import discord
import asyncio
from discord import app_commands
from discord.ext import commands
from settings import *
import gspread
import random
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.all()
client = commands.Bot(
    command_prefix="/",
    intents=intents,
    owner_ids=[int(os.environ.get('REACT_BKG')), int(os.environ.get('REACT_HEXX'))],
)


async def ready_cogs():
    cog_files = [
        file[:-3]
        for file in os.listdir(f"{os.path.dirname(os.path.abspath(__file__))}/Cogs")
        if file.endswith(".py")
    ]
    loaded_extensions = [name[5:] for name in list(client.extensions.keys())]
    work_failed = []
    work_success = []

    if "ku" in loaded_extensions:  # jishaku 제외
        loaded_extensions.remove("ku")

    for file in filter(lambda name: not name in cog_files, loaded_extensions):
        try:
            await client.unload_extension(f"Cogs.{file}")
            work_success.append(["Unload", file])
        except Exception as e:
            work_failed.append(["Unload", file, e])

    for file in filter(lambda name: name in cog_files, loaded_extensions):
        try:
            await client.reload_extension(f"Cogs.{file}")
            work_success.append(["Reload", file])
        except Exception as e:
            work_failed.append(["Reload", file, e])

    for file in filter(lambda name: not name in loaded_extensions, cog_files):
        try:
            await client.load_extension(f"Cogs.{file}")
            work_success.append(["Load", file])
        except Exception as e:
            work_failed.append(["Load", file, e])

    return [work_success, work_failed, cog_files]


@client.command(name="싱크", aliases=["sync", "ㅅㅋ", "tz"])
@commands.is_owner()
@commands.has_role("관리자")
async def setup(interaction: discord.Interaction):
    try:
        synced = await client.tree.sync()
        client.tree.copy_global_to(guild=discord.Object(id=f"{os.environ.get('REACT_GUILD_ID')}"))
        passed = True
    except Exception as e:
        passed = False
        error = e
    await interaction.message.reply(
        embed=discord.Embed(
            title=f"Slash Command Setup ({len(synced) if passed else 0}/{len(client.tree.get_commands())})",
            description="success" if passed else f"failed\n{error}",
            colour=0x00FF00 if passed else 0xFF0000,
        ),
        mention_author=False,
    )


@client.command(aliases=["리로드", "ㄹㄹㄷ", "ffe"])
@commands.has_role("관리자")
async def reload(interaction: discord.Interaction):
    LoadResult = await ready_cogs()
    success = "".join([f"```\n[ {i[0]:^6} ] {i[1]}```" for i in LoadResult[0]])
    failed = "".join([f"```\n[ {i[0]:^6} ] {i[1]}\n{i[2]}```" for i in LoadResult[1]])
    await interaction.message.reply(
        embed=discord.Embed(
            title=f"Cogs Reload ({len(client.cogs)-1}/{len(LoadResult[2])})",
            description=(f"**Success**{success}" if success else "")
            + ("\n" if success and failed else "")
            + (f"**Failed**{failed}" if failed else ""),
        ),
        mention_author=False,
    )


@client.event
async def on_ready():
    print(f"✅ 로그인: {client.user.name} ({client.user.id})")


# ✅ 안정적으로 봇 시작 (jishaku 포함) - 가장 중요!
async def main():
    async with client:
        try:
            await client.load_extension("jishaku")
            print("✅ jishaku loaded successfully")
        except Exception as e:
            print(f"❌ jishaku load failed: {e}")

        await ready_cogs()
        await client.start(os.environ.get("REACT_BOT_TOKEN"))


if __name__ == "__main__":
    asyncio.run(main())
