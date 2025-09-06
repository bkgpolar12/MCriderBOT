import discord
from discord.ext import commands
from discord import app_commands
from settings import *
import gspread
import random
import requests
from functools import lru_cache
import re
import time
from dotenv import load_dotenv
import os, ast
import Paginator
import asyncio
from packaging import version as v
import aiohttp
from mojang import *

normal_engines = [
    "X", "V1", "EX", "JIU", "NEW", "Z7", "PRO", "A2", "1.0", "RALLY"
]
dummy_engines = [
    "N1", "KEY", "MK", "BOAT", "GEAR"
]

json_key_path = os.environ.get('REACT_JSON_KEY_PATH')
gc = gspread.service_account(filename=json_key_path)
sheet_url = os.environ.get('REACT_SHEET_URL')
doc = gc.open_by_url(sheet_url)
sheet = doc.worksheet("포레스트 통나무")
track_sheets = doc.worksheets()
not_track_sheets = ast.literal_eval(os.getenv("REACT_NOTTRACK_SHEET"))
tracks = [worksheet.title for worksheet in track_sheets if worksheet.title not in not_track_sheets]
lpeng_image = discord.File("image/L_Peng.png", filename="L_Peng.png")

load_dotenv()

def get_uiddata_from_sheet(uid):
    temp_sheet = doc.worksheet("RecordApplicationData")
    try:
        cell = temp_sheet.find(str(uid))
        row = temp_sheet.row_values(cell.row)
        return {
            "uid": row[0],
            "username_id": row[1],
            "mcname": row[2],
            "track": row[3],
            "record": row[4],
            "kart": row[5],
            "engine": row[6],
            "youtubevideo": row[7],
            "timestamp": row[8],
            "mode_num": row[9] if row[9] else ["0", "0", "0", "0"],
            "mode": row[10] if len(row) > 10 else "기본",
        }
    except Exception:
        return None

class AddRecordOptionRow(discord.ui.View):
    def __init__(self, author_interaction: discord.Interaction, uid: int):
        super().__init__(timeout=None)
        self.author_interaction = author_interaction
        self.uid = uid
        self.options = [
            ["톡톡이 모드", False],
            ["팀전 모드", False],
            ["무한 부스터 모드", False],
            ["벽 충돌 페널티 모드", False]
        ]
        for idx, (name, value) in enumerate(self.options):
            button = discord.ui.Button(
                style=discord.ButtonStyle.success if value else discord.ButtonStyle.secondary,
                label=f"{name} : {'⭕' if value else '❌'}",
                custom_id=f"{idx}"
            )
            button.callback = self.update_option
            self.add_item(button)

        submit_button = discord.ui.Button(
            label="제출",
            style=discord.ButtonStyle.primary,
        )
        submit_button.callback = self.submit_option
        self.add_item(submit_button)

    async def submit_option(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            mode_num = ["1" if option[1] else "0" for option in self.options]
            if all(num == "0" for num in mode_num):
                mode = "기본"
            else:
                mode = ", ".join(
                    filter(
                        None, 
                        [
                            "톡톡이 모드" if mode_num[0] == "1" else "",
                            "팀전 모드" if mode_num[1] == "1" else "",
                            "무한 부스터 모드" if mode_num[2] == "1" else "",
                            "벽 충돌 페널티 모드" if mode_num[3] == "1" else "",
                        ]
                    )
                )
            temp_sheet = doc.worksheet("RecordApplicationData")
            cell = temp_sheet.find(str(self.uid))
            row = cell.row
            temp_sheet.update_acell(f"J{row}", str(mode_num))
            temp_sheet.update_acell(f"K{row}", mode)

            verifychannel = os.environ.get('REACT_VERIFYCHANNEL')
            if not verifychannel or int(verifychannel) == 0:
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ 신청 실패",
                        description="관리자가 기록 등록 메시지가 전송될 채널을 지정하지 않았습니다. 이 문제를 해결하기 위해 관리자에게 문의하세요.",
                        color=EmbedColor.RED,
                    ),
                    ephemeral=True
                )

            channel = interaction.client.get_channel(int(verifychannel))
            if not channel:
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ 신청 실패",
                        description="지정된 채널을 찾을 수 없습니다.",
                        color=EmbedColor.RED,
                    ),
                    ephemeral=True,
                )
            # 관리자용 버튼 View
            admin_view = discord.ui.View(timeout=None)
            admin_view.add_item(
                discord.ui.Button(
                    custom_id=CustomID.make_deny_record(self.uid),
                    style=discord.ButtonStyle.danger,
                    label="거절",
                )
            )
            admin_view.add_item(
                discord.ui.Button(
                    custom_id=CustomID.make_verify_record(self.uid),
                    style=discord.ButtonStyle.success,
                    label="등록",
                )
            )
            uiddata = get_uiddata_from_sheet(self.uid)
            user_obj = self.author_interaction.user
            embed = discord.Embed(
                title=f"🔔 기록 등록 신청 - `#{self.uid}`",
                description=(
                    f"- **신청자** : {user_obj.display_name} ({user_obj.name})\n"
                    f"- **마크 닉네임** : {uiddata['mcname']}\n"
                    f"- **트랙명** : {uiddata['track']}\n"
                    f"- **기록** : {uiddata['record']}\n"
                    f"- **탑승 카트** : {uiddata['kart']}\n"
                    f"- **엔진** : {uiddata['engine']}\n"
                    f"- **모드** : {uiddata['mode']}\n"
                    f"- **영상** : {uiddata['youtubevideo']}"
                ),
                color=EmbedColor.YELLOW,
            )
            embed.set_thumbnail(url=get_player_head_url(uiddata['mcname']))
            await channel.send(
                embed=embed,
                view=admin_view,
                mention_author=False
            )
            await self.author_interaction.edit_original_response(
                embed=discord.Embed(
                    title="✅ 신청 완료",
                    description="관리자에게 요청이 전송되었습니다.",
                    color=EmbedColor.GREEN,
                ),
                view=None
            )
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ 예외 발생",
                    description=f"오류가 발생했습니다: `{type(e).__name__}`\n{str(e)}",
                    color=EmbedColor.RED,
                ),
                ephemeral=True,
            )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_interaction.user.id:
            await interaction.response.send_message(
                embed=discord.Embed(title="❌ 오류", description="명령어 사용자만 누를 수 있습니다.", color=EmbedColor.RED),
                ephemeral=True,
            )
            return False
        return True

    async def update_option(self, interaction: discord.Interaction):
        idx = int(interaction.data['custom_id'])
        self.options[idx][1] = not self.options[idx][1]
        button = self.children[idx]
        button.style = discord.ButtonStyle.success if self.options[idx][1] else discord.ButtonStyle.secondary
        button.label = f"{self.options[idx][0]} : {'⭕' if self.options[idx][1] else '❌'}"
        await interaction.response.edit_message(view=self)

class Admin(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.verifychannel = int(os.environ.get('REACT_VERIFYCHANNEL'))
        self.verifierrole = int(os.environ.get('REACT_VERIFIER_ROLD_ID'))
        self.maxranking = Option.maxranking
        self.verify_log = Option.verify_log
        self.deny_dm  = Option.deny_dm
        self.verify_dm = Option.verify_dm

    @lru_cache(maxsize=128)
    def get_uuid(self, username):
        try:
            response = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{username}", timeout=5)
            if response.status_code == 200:
                return response.json()["name"]
        except requests.RequestException:
            pass
        return None

    # 이펭귄
    @app_commands.command(name="이펭귄")
    @app_commands.checks.cooldown(1, 5)
    async def penguin(self, interaction: discord.Interaction):
        """이펭귄에 대한 모든 유저들의 생각"""
        await interaction.response.send_message(
            view=discord.ui.LayoutView()
                .add_item(discord.ui.Section(accessory=discord.ui.Thumbnail(lpeng_image))
                    .add_item("# 흉물")
                ),
            ephemeral=True,
            file=lpeng_image
        )


    # 봇 정보 명령어            
    @app_commands.command(name="info")
    @app_commands.checks.cooldown(1, 5)
    async def credit(self, interaction: discord.Interaction):
        """봇 정보를 표시합니다."""

        async def get_latest_version() -> str | None:
            """깃허브 최신 릴리스 버전 가져오기"""
            async with aiohttp.ClientSession() as session:
                async with session.get(BotInfo.GITHUB_API) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("tag_name") # "tag_name": "v0.0.0",
            return None
        
        latest = await get_latest_version()
        updatenoti = f"\n:warning: 새로운 업데이트가 있습니다!\n적용된 버전 : `{BotInfo.VERSION}`\n최신 버전 `{latest}`" if latest and v.parse(latest.lstrip("v")) > v.parse((BotInfo.VERSION).lstrip("v")) else "\n:white_check_mark: 최신 버전입니다."
        await interaction.response.send_message(
            content=f'''## {BotInfo.NAME}
### 버전 : {BotInfo.VERSION} {updatenoti}

개발 : {BotInfo.AUTHOR}

사이트 : {BotInfo.GITHUB_URL}''',
            ephemeral=True
        )

    # 트랙 자동완성
    async def track_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
        app_commands.Choice(name=track, value=track)
        for track in tracks if current.lower() in track.lower()
        ][:25]

    # 트랙 순위 명령어
    @app_commands.command(name="showranking")
    @app_commands.checks.cooldown(1, 5)
    @app_commands.autocomplete(track_name=track_autocomplete)
    @app_commands.rename(track_name="트랙이름", numb="페이지", kartengine="엔진", toktoki="톡톡이모드", team="팀전모드", infinity="무한부스터모드", crash="벽충돌페널티모드")
    @app_commands.choices(toktoki=[
        app_commands.Choice(name="활성화", value="1"),
        app_commands.Choice(name="비활성화", value="0"),
    ])
    @app_commands.choices(team=[
        app_commands.Choice(name="활성화", value="1"),
        app_commands.Choice(name="비활성화", value="0"),
    ])
    @app_commands.choices(infinity=[
        app_commands.Choice(name="활성화", value="1"),
        app_commands.Choice(name="비활성화", value="0"),
    ])
    @app_commands.choices(crash=[
        app_commands.Choice(name="활성화", value="1"),
        app_commands.Choice(name="비활성화", value="0"),
    ])
    @app_commands.choices(
    kartengine=[
        app_commands.Choice(name="전체", value="전체"),
        *[app_commands.Choice(name=name, value=name) for name in normal_engines],
        *[app_commands.Choice(name=f"(더미) {name}", value=name) for name in dummy_engines],
    ]
)
    async def show_rank(self, interaction: discord.Interaction, track_name: str, kartengine: app_commands.Choice[str], toktoki: app_commands.Choice[str],
        team: app_commands.Choice[str], infinity: app_commands.Choice[str], crash: app_commands.Choice[str], numb: discord.app_commands.Range[int, 1] = 1):
        mode_num = [
            "1" if toktoki.value == "1" else "0",
            "1" if team.value == "1" else "0",
            "1" if infinity.value == "1" else "0",
            "1" if crash.value == "1" else "0"
        ]
        mode = "기본" if all(num == "0" for num in mode_num) else ", ".join(filter(None, [
            "톡톡이 모드" if mode_num[0] == "1" else "",
            "팀전 모드" if mode_num[1] == "1" else "",
            "무한 부스터 모드" if mode_num[2] == "1" else "",
            "벽 충돌 페널티 모드" if mode_num[3] == "1" else "",
        ]))
        await interaction.response.defer(ephemeral=True)
        if track_name not in tracks:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ 오류",
                    description="존재하지 않는 트랙입니다.",
                    color=EmbedColor.RED,
                ),
                ephemeral=True,
            )
        try:
            sheet = doc.worksheet(track_name)
            all_data = sheet.get_all_values()
            mode_num_str = str(mode_num)
            count = 0
            x = 0
            containers: list[discord.ui.Container] = []
            sections: list[discord.ui.Section] = []
            for row_idx in range(1, len(all_data)):
                row = all_data[row_idx]
                if len(row) < 6:
                    continue
                if row[0] and row[4] == mode_num_str and (row[3] == kartengine.value or kartengine.value == "전체"):
                    count += 1

                    sections.append(
                        discord.ui.Section(accessory=discord.ui.Thumbnail(get_player_head_url(row[0])))
                            .add_item(f'''
- **순위** : {count}등 
- **닉네임** : {row[0]}
- **기록** : {row[1]}
- **탑승 카트** : {row[2]} 
- **엔진** : {row[3]}
- **모드** : {mode}
- **영상** : {row[5]}\n\n''')
                    )
                if count % 5 == 0 and sections:
                    container = discord.ui.Container(accent_color=EmbedColor.BLUE)
                    container.add_item(discord.ui.TextDisplay(f"### 🕐 {track_name} 순위 ({count - 4}등 ~ {count}등)"))

                    for section in sections:
                        container.add_item(section)
                        container.add_item(discord.ui.Separator())

                    x = count + 1
                    containers.append(container)
                    sections = []

            if len(sections):
                # 0등이라 뜨는 더 방지
                if x == 0:
                    x += 1

                container = discord.ui.Container(accent_color=EmbedColor.BLUE)
                container.add_item(discord.ui.TextDisplay(f"### 🕐 {track_name} 순위 ({x}등 ~ {count}등)"))

                for section in sections:
                    container.add_item(section)
                    container.add_item(discord.ui.Separator())

                x = count + 1
                containers.append(container)

            if not containers:
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title=f"🕐 {track_name} 순위",
                        description="⚠️ 표시할 데이터가 없습니다.",
                        color=EmbedColor.BLUE,
                    )
                )
            if numb > len(containers):
                numb = len(containers)
            await Paginator.Simple(InitialPage=numb-1).start(interaction, pages=containers)
        except Exception as e:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ 예외 발생",
                    description=f"오류가 발생했습니다: `{type(e).__name__}`\n{str(e)}",
                    color=EmbedColor.RED,
                ),
                ephemeral=True,
            )


    # 등록 명령어
    @app_commands.command(name="addrecord")
    @app_commands.autocomplete(track_name=track_autocomplete)
    @app_commands.choices(
        kartengine=[
            *[app_commands.Choice(name=name, value=name) for name in normal_engines],
            *[app_commands.Choice(name=f"(더미) {name}", value=name) for name in dummy_engines],
        ]
    )
    @app_commands.rename(
        mcname="마크닉네임",
        track_name="트랙명",
        record="기록",
        kartbody="탑승카트",
        kartengine="엔진",
        youtubevideo="영상"
    )
    async def add_record(
        self,
        interaction: discord.Interaction,
        mcname: str, 
        track_name: str,
        record: str, 
        kartbody: str, 
        kartengine: app_commands.Choice[str], 
        youtubevideo: str,
    ):
        await interaction.response.defer(ephemeral=True)
        def validate_input():
            if not re.match(r'^https?://(?:www\.)?(youtube\.com|youtu\.be)', youtubevideo):
                return "유효한 유튜브 링크를 입력해주세요."
            if not re.match(r'^\d{1,2}:[0-5][0-9]\.\d{3}$', record):
                return "기록은 `00:00.000` 형식으로 입력해주세요 (예: 01:23.456)."
            if len(kartbody) > 20:
                return "탑승 카트 이름은 20글자 이하여야 합니다."
            if track_name not in tracks:
                return "존재하지 않은 트랙이거나 트랙 이름이 올바르지 않습니다."
            if not self.get_uuid(mcname):
                return "이 이름을 가진 마인크래프트 유저를 찾을 수 없습니다."
            return None
        validation_error = validate_input()
        if validation_error:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ 입력 오류",
                    description=validation_error,
                    color=EmbedColor.RED,
                ),
                ephemeral=True,
            )
        uid = random.randint(1, 100000000)
        embed = discord.Embed(
            title="🔔 새 기록 등록",
            description=(
                f":bust_in_silhouette: **마크 닉네임** - `{mcname}`\n"
                f":map: **트랙명** - `{track_name}`\n"
                f":stopwatch: **기록** - `{record}`\n"
                f":red_car: **카트** - `{kartbody} {kartengine.value}`\n"
                f":arrow_forward: **유튜브 링크** - {youtubevideo}"
            ),
            color=EmbedColor.YELLOW,
        )
        embed.set_thumbnail(url=get_player_head_url(mcname))
        row = AddRecordOptionRow(
            author_interaction=interaction,
            uid=uid
        )
        temp_sheet = doc.worksheet("RecordApplicationData")
        temp_sheet.append_row([
            uid,
            str(interaction.user.id),
            mcname,
            track_name,
            record,
            kartbody,
            kartengine.value,
            youtubevideo,
            time.time(),
            "",  # mode_num
            ""   # mode
        ])
        await interaction.followup.send(
            embed=embed,
            view=row,
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.data.get("component_type") != 2:
            return
        DELAY_TO_DELETE = 5
        custom_id = interaction.data.get("custom_id")
        def escape_formula(value: str) -> str:
            if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
                return "'" + value
            return value
        def time_str_to_seconds(time_str: str) -> float:
            minutes, sec_ms = time_str.split(":")
            seconds, ms = sec_ms.split(".")
            return int(minutes) * 60 + int(seconds) + int(ms) / 1000
        async def send_fail_dm(username_obj, request_id, mcname, track_name, record, old_record, kartbody, kartengine, mode, youtubevideo):
            ch = await username_obj.create_dm()
            await ch.send(
                embed=discord.Embed(
                    title=f"❌ 등록 실패 - `#{request_id}`",
                    description=f"""
- **닉네임** : {mcname}
- **트랙명** : {track_name}
- **기록** : {record} | (기존 기록 : {old_record})
- **탑승 카트** : {kartbody}
- **엔진** : {kartengine}
- **모드**: {mode}
- **영상** : {youtubevideo}""",
                    color=EmbedColor.RED,
                ).set_footer(
                    text="기존 기록이 신청한 기록보다 빠르거나 같습니다."
                )
            )
        class DenyModal(discord.ui.Modal):
            def __init__(self, request_id, uiddata, deny_dm, verify_log, client):
                super().__init__(title=f"등록 거절 - #{request_id}")
                self.request_id = request_id
                self.uiddata = uiddata
                self.deny_dm = deny_dm
                self.verify_log = verify_log
                self.client = client
                self.reason = discord.ui.TextInput(label="사유")
                self.add_item(self.reason)
            async def on_submit(self, interaction: discord.Interaction):
                await interaction.response.defer()
                user = interaction.user
                data = self.uiddata
                track_name = data["track"]
                mcname = data["mcname"]
                record = data["record"]
                kartbody = data["kart"]
                kartengine = data["engine"]
                youtubevideo = data["youtubevideo"]
                request_user_id = int(data["username_id"])
                mode = data["mode"]
                request_user_obj = interaction.guild.get_member(request_user_id)
                if self.deny_dm and request_user_obj:
                    ch = await request_user_obj.create_dm()
                    await ch.send(
                        embed=discord.Embed(
                            title=f"❌ 등록 거부됨 - `#{self.request_id}`",
                            description=f"""
- **닉네임** : {mcname}
- **트랙명** : {track_name}
- **기록** : {record}
- **탑승 카트** : {kartbody}
- **엔진** : {kartengine}
- **모드** : {mode}
- **영상** : {youtubevideo}
- **사유** : {self.reason.value}""",
                            color=EmbedColor.RED,
                        ).set_footer(
                            text="등록 조건에 맞춰 제출하시기 바랍니다."
                        ),
                    )
                if self.verify_log:
                    ch = self.client.get_channel(int(os.environ.get('REACT_VERIFYLOGCHANNEL')))
                    await ch.send(
                        embed=discord.Embed(
                            title=f"❌ 등록 거부 - `#{self.request_id}`",
                            description=f"""
- **담당자** : {user.display_name} ({user.name})
- **닉네임** : {mcname}
- **트랙명** : {track_name}
- **기록** : {record}
- **탑승 카트** : {kartbody}
- **엔진** : {kartengine}
- **모드**: {mode}
- **영상** : {youtubevideo}
- **사유** : {self.reason.value}""",
                            color=EmbedColor.BLUE,
                        ).set_footer(
                            text="관리자 전용 메시지입니다. 유출하지 마십시오."
                        ),
                    )
                temp_sheet = doc.worksheet("RecordApplicationData")
                try:
                    cell = temp_sheet.find(str(self.request_id))
                    temp_sheet.delete_rows(cell.row)
                except Exception:
                    pass
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="✅ 거절 완료",
                        description=f"요청 `#{self.request_id}`을 거절하였습니다.",
                        color=EmbedColor.GREEN,
                    ),
                    ephemeral=True,
                )
                await asyncio.sleep(DELAY_TO_DELETE)
                await interaction.delete_original_response()
        if custom_id.startswith(CustomID.VERIFY_RECORD):
            if not any(role.id == int(self.verifierrole) for role in interaction.user.roles):
                return await interaction.response.send_message("❌ 당신은 이 버튼을 누를 권한이 없습니다.", ephemeral=True)
            request_id = CustomID.get_verify_record_uid(custom_id)
            user = interaction.user
            await interaction.response.defer()
            try:
                uiddata = get_uiddata_from_sheet(request_id)
                if not uiddata:
                    return await interaction.followup.send(
                        embed=discord.Embed(
                            title="❌ 등록 실패",
                            description="존재하지 않는 ID입니다.",
                            color=EmbedColor.RED,
                        ),
                        ephemeral=True,
                    )
                track_name = uiddata["track"]
                mcname = uiddata["mcname"]
                record = uiddata["record"]
                kartbody = uiddata["kart"]
                kartengine = uiddata["engine"]
                youtubevideo = uiddata["youtubevideo"]
                username_id = int(uiddata["username_id"])
                mode_num = uiddata["mode_num"]
                mode = uiddata["mode"]
                username_obj = interaction.guild.get_member(username_id)
                if track_name in tracks:
                    sheet = doc.worksheet(track_name)
                    all_rows = sheet.get_all_values()
                    columns = ("A", "B", "C", "D", "E", "F")
                    values = [mcname, record, kartbody, kartengine, str(mode_num), youtubevideo]
                    for i in range(2, self.maxranking+1):
                        if i-1 >= len(all_rows):
                            cell_mcname = None
                            cell_engine = None
                            cell_mode = None
                            cell_record = None
                        else:
                            row = all_rows[i-1]
                            cell_mcname = row[0] if len(row) > 0 else None
                            cell_record = row[1] if len(row) > 1 else None
                            cell_engine = row[3] if len(row) > 3 else None
                            cell_mode = row[4] if len(row) > 4 else None
                        if cell_engine == kartengine and cell_mode == str(mode_num) and cell_mcname == mcname:
                            if time_str_to_seconds(cell_record) > time_str_to_seconds(record):
                                await self.send_dm_and_log(interaction, user, username_obj, request_id, mcname, track_name, record, kartbody, kartengine, youtubevideo, mode)
                                for col, value in zip(columns, values):
                                    sheet.update_acell(f"{col}{i}", escape_formula(value))
                                sort_range = f"{columns[0]}2:{columns[-1]}{self.maxranking}"
                                sheet.sort((2, "asc"), range=sort_range)
                                temp_sheet = doc.worksheet("RecordApplicationData")
                                try:
                                    cell = temp_sheet.find(str(request_id))
                                    temp_sheet.delete_rows(cell.row)
                                except Exception:
                                    pass
                                await interaction.followup.send(
                                    embed=discord.Embed(
                                        title="✅ 등록 완료",
                                        description=f"요청 `#{request_id}`을 등록하였습니다.",
                                        color=EmbedColor.GREEN,
                                    ),
                                    ephemeral=True,
                                )
                                await asyncio.sleep(DELAY_TO_DELETE)
                                await interaction.delete_original_response()
                                break
                            else:
                                await interaction.followup.send(
                                    embed=discord.Embed(
                                        title=f"❌ 등록 실패 - `#{request_id}`",
                                        description=f"""
- **닉네임** : {mcname}
- **트랙명** : {track_name}
- **기록** : {record} | (기존 기록 : {cell_record})
- **탑승 카트** : {kartbody}
- **엔진** : {kartengine}
- **모드**: {mode}
- **영상** : {youtubevideo}""",
                                        color=EmbedColor.RED,
                                    ).set_footer(
                                        text="기존 기록이 신청한 기록보다 빠르거나 같습니다."
                                    ),
                                    view=discord.ui.View(),
                                )
                                if self.verify_dm and username_obj:
                                    await send_fail_dm(username_obj, request_id, mcname, track_name, record, cell_record, kartbody, kartengine, mode, youtubevideo)
                                    await asyncio.sleep(DELAY_TO_DELETE)
                                    await interaction.delete_original_response()
                                    temp_sheet = doc.worksheet("RecordApplicationData")
                                    try:
                                        cell = temp_sheet.find(str(request_id))
                                        temp_sheet.delete_rows(cell.row)
                                    except Exception:
                                        pass
                                break
                        elif cell_mcname is None:
                            await self.send_dm_and_log(interaction, user, username_obj, request_id, mcname, track_name, record, kartbody, kartengine, youtubevideo, mode)
                            for col, value in zip(columns, values):
                                sheet.update_acell(f"{col}{i}", escape_formula(value))
                            sort_range = f"{columns[0]}2:{columns[-1]}{self.maxranking}"
                            sheet.sort((2, "asc"), range=sort_range)
                            temp_sheet = doc.worksheet("RecordApplicationData")
                            try:
                                cell = temp_sheet.find(str(request_id))
                                temp_sheet.delete_rows(cell.row)
                            except Exception:
                                pass
                            await interaction.followup.send(
                                embed=discord.Embed(
                                    title="✅ 등록 완료",
                                    description=f"요청 `#{request_id}`을 등록하였습니다.",
                                    color=EmbedColor.GREEN,
                                ),
                                ephemeral=True,
                            )
                            await asyncio.sleep(DELAY_TO_DELETE)
                            await interaction.delete_original_response()
                            break
                else:
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title="❌ 등록 실패",
                            description="존재하지 않는 트랙입니다.",
                            color=EmbedColor.RED,
                        ),
                        ephemeral=True,
                    )
            except Exception as e:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ 예외 발생",
                        description=f"오류가 발생했습니다: `{type(e).__name__}`\n{str(e)}",
                        color=EmbedColor.RED,
                    ),
                    ephemeral=True,
                )
        elif custom_id.startswith(CustomID.DENY_RECORD):
            if not any(role.id == int(self.verifierrole) for role in interaction.user.roles):
                return await interaction.response.send_message("❌ 당신은 이 버튼을 누를 권한이 없습니다.", ephemeral=True)
            request_id = CustomID.get_deny_record_uid(custom_id)
            uiddata = get_uiddata_from_sheet(request_id)
            if not uiddata:
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ 등록 실패",
                        description="존재하지 않는 ID입니다.",
                        color=EmbedColor.RED,
                    ),
                    ephemeral=True,
                )
            await interaction.response.send_modal(
                DenyModal(request_id, uiddata, self.deny_dm, self.verify_log, self.client)
            )

    async def send_dm_and_log(self, interaction, user, username_obj, request_id, mcname, track_name, record, kartbody, kartengine, youtubevideo, mode):
        if self.verify_dm and username_obj:
            ch = await username_obj.create_dm()
            await ch.send(
                embed=discord.Embed(
                    title=f"✅ 등록 완료! - `#{request_id}`",
                    description=f"""
- **닉네임** : {mcname}
- **트랙명** : {track_name}
- **기록** : {record}
- **탑승 카트** : {kartbody}
- **엔진** : {kartengine}
- **모드**: {mode}
- **영상** : {youtubevideo}""",
                    color=EmbedColor.YELLOW,
                ).set_footer(
                    text="축하합니다! 이제 더 빠른 기록을 도전하는 것은 어떨까요?"
                )
            )
        if self.verify_log:
            ch = self.client.get_channel(int(os.environ.get('REACT_VERIFYLOGCHANNEL')))
            await ch.send(
                embed=discord.Embed(
                    title=f"✅ 등록 완료! - `#{request_id}`",
                    description=f"""
- **담당자** : {user.display_name} ({user.name})
- **닉네임** : {mcname}
- **트랙명** : {track_name}
- **기록** : {record}
- **탑승 카트** : {kartbody}
- **엔진** : {kartengine}
- **모드**: {mode}
- **영상** : {youtubevideo}""",
                    color=EmbedColor.BLUE,
                ).set_footer(
                    text="관리자 전용 메시지입니다. 유출하지 마십시오."
                )
            )

async def setup(bot):
    await bot.add_cog(Admin(bot))