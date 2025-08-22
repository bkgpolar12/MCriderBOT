import discord
import asyncio
from discord.ext import commands
from discord.ext import tasks
from settings import *
import os
from dotenv import load_dotenv
from packaging import version as v
import aiohttp

load_dotenv()

intents = discord.Intents.all()
client = commands.Bot(
    command_prefix="/",
    intents=intents,
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

async def fetch_latest_version() -> str | None:
    """깃허브 최신 릴리스 버전 가져오기"""
    async with aiohttp.ClientSession() as session:
        async with session.get(BotInfo.GITHUB_API) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("tag_name")  # ex) "v1.2.0"
        return None
    

    
@tasks.loop(hours=Option.latest_version_check_interval)
async def check_github_release():
    if Option.latest_version_check == True:
        print("\n\nGitHub 릴리즈 상황 가져오는 중...")
        latest = await fetch_latest_version()
        print(f"최신 버전: {latest},  적용된 버전: {BotInfo.VERSION}")
        if not latest:
            print("최신 버전을 가져오지 못했습니다. (latest is None)")
        return

    if Option.latest_version_check == True:
        if v.parse(latest.lstrip("v")) > v.parse(BotInfo.VERSION.lstrip("v")):
                try:
                    channel = client.get_channel(int(os.environ.get('REACT_VERIFYCHANNEL')))
                    if channel:
                        await channel.send(
                            f":bell: **새로운 GitHub 릴리스가 감지되었습니다!**\n\n"
                            f"저장소: {BotInfo.GITHUB_URL}\n"
                            f"버전: `{BotInfo.VERSION}`\n"
                            f"최신 버전: `{latest}`"
                        )
                    else:
                        print("채널을 찾을 수 없습니다. CHANNEL_ID 확인 필요")
                except Exception as e:
                    print("채널 알림 전송 실패:", e)


@client.event
async def on_ready():
    print(f"✅ 로그인: {client.user.name} ({client.user.id})")
    check_github_release.start()


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