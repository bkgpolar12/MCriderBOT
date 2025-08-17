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
import os
import asyncio
import Paginator

engine_names = [
    "X", "V1", "EX", "JIU", "NEW", "Z7", "PRO", "A2", "1.0",
    "N1", "KEY", "MK", "BOAT", "GEAR"
]
json_key_path = os.environ.get('REACT_JSON_KEY_PATH')
gc = gspread.service_account(filename=json_key_path) # 서비스 계정의 키
sheet_url = os.environ.get('REACT_SHEET_URL') #스프레드시트 url
doc = gc.open_by_url(sheet_url)
sheet = doc.worksheet("포레스트 통나무") #시트 기본값
track_sheets = doc.worksheets()
tracks = [worksheet.title for worksheet in track_sheets]

load_dotenv()

class AddRecordOptionView(discord.ui.View):
    def __init__(self, author_interaction: discord.Interaction, uid, uiddata, parent):
        self.author_interaction = author_interaction  # Interaction 객체
        self.uid = uid  # UID 값
        self.uiddata = uiddata  # UID 데이터
        self.parent = parent
        super().__init__(timeout=None)
        self.options = [
            ["톡톡이 모드", False],
            ["팀전 모드", False],
            ["무한 부스터 모드", False],
            ["벽 충돌 페널티 모드", False]
        ]
        # 각 옵션에 대해 토글 버튼 추가
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
            self.uiddata['mode_num'] = mode_num
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
            self.uiddata['mode'] = mode
            self.parent.uiddata[self.uid] = self.uiddata

            # 채널 확인 및 메시지 전송
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

            channel = self.parent.client.get_channel(int(verifychannel))
            if not channel:
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ 신청 실패",
                        description="지정된 채널을 찾을 수 없습니다.",
                        color=EmbedColor.RED,
                    ),
                    ephemeral=True,
                )

                    # 채널에 기록 신청 전송
            try:
                view = discord.ui.View().add_item(
                    discord.ui.Button(
                        custom_id=CustomID.make_deny_record(self.uid),
                        style=discord.ButtonStyle.danger,
                        label="거절",
                    ),
                ).add_item(
                    discord.ui.Button(
                        custom_id=CustomID.make_verify_record(self.uid),
                        style=discord.ButtonStyle.success,
                        label="등록",
                    ),
                )
            except Exception as e:
                print("VIEW ERROR:", type(e), e)
                view = None  # view 생성에 실패하면 None으로 설정

            await channel.send(
                embed=discord.Embed(
                    title=f"🔔 기록 등록 신청 - `#{self.uid}`",
                    description=f"""
- **신청자** : {self.parent.uiddata[self.uid]['username'].display_name} ({self.parent.uiddata[self.uid]['username'].name})
- **마크 닉네임** : {self.parent.uiddata[self.uid]['mcname']}
- **트랙명** : {self.parent.uiddata[self.uid]['track']}
- **기록** : {self.parent.uiddata[self.uid]['record']}
- **탑승 카트** : {self.parent.uiddata[self.uid]['kart']}
- **엔진** : {self.parent.uiddata[self.uid]['engine']}
- **모드** : {self.parent.uiddata[self.uid]['mode']}
- **영상** : {self.parent.uiddata[self.uid]['youtubevideo']}""",
                    color=EmbedColor.YELLOW,
                ),
                view=view,          # 위에서 에러가 발생하면 None (버튼 없이 전송됨)
                mention_author=False,
            )

            # 사용자에게 신청 완료 메시지 전송
            await self.author_interaction.followup.send(
                embed=discord.Embed(
                    title="✅ 신청 완료",
                    description="관리자에게 요청이 전송되었습니다.",
                    color=EmbedColor.GREEN,
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

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_interaction.user.id:
            await interaction.response.send_message(
                embed=discord.Embed(title="❌ 오류", description="명령어 사용자만 누를 수 있습니다.", color=EmbedColor.RED),
                ephemeral=True,
            )
            return False
        return True

    async def update_option(self, interaction: discord.Interaction):
        # interaction에서 누른 버튼 custiom_id 추출
        idx = int(interaction.data['custom_id'])
        self.options[idx][1] = not self.options[idx][1]  # 토글 값 변경
        button = self.children[idx]
        button.style = discord.ButtonStyle.success if self.options[idx][1] else discord.ButtonStyle.secondary
        button.label = f"{self.options[idx][0]} : {'⭕' if self.options[idx][1] else '❌'}"
        await interaction.response.edit_message(view=self)




class Admin(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client #디스코드 봇 모델
        self.uiddata = {} #정보들이 저장되는 딕셔너리
        self.uid = 0
        self.verifychannel = int(os.environ.get('REACT_VERIFYCHANNEL'))
        self.verifierrole = int(os.environ.get('REACT_VERIFIER_ROLD_ID'))
        self.cooldowns = {}  # 사용자 ID별 마지막 사용 시간 저장

        #랭킹 한계
        self.maxranking = 2001 #2000등 + 1

        # 기능
        self.verify_log = True # 로그 남기기
        self.deny_dm  = True # 등록 거절 시 DM 전송
        self.verify_dm = True # 등록 시 DM 전송

    def cleanup_old_requests(self, expire_seconds=3600):  # 1시간 기준
        now = time.time()
        expired_keys = [key for key, data in self.uiddata.items() if now - data.get("timestamp", now) > expire_seconds]
        for key in expired_keys:
            del self.uiddata[key]


    @lru_cache(maxsize=128)
    def get_uuid(self, username):
        try:
            response = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{username}", timeout=5)
            if response.status_code == 200:
                return response.json()["name"]
        except requests.RequestException:
            pass
        return None


    @app_commands.command(name="asc")
    @app_commands.checks.cooldown(1, 5)
    async def ascc(self, interaction: discord.Interaction, track_name: str):
        """[베리파이어 전용] 기록을 오름차순으로 정리합니다."""
        # 권한 체크
        if not any(role.id == int(self.verifierrole) for role in interaction.user.roles):
            return await interaction.response.send_message("❌ 당신은 이 명령어를 사용할 권한이 없습니다.", ephemeral=True)

        # 트랙 존재 여부 체크
        if track_name not in tracks:
            return await interaction.response.send_message(
                embed=discord.Embed(title="❌ 오류", description="존재하지 않는 트랙입니다.", color=EmbedColor.RED),
                ephemeral=True,
            )

        # 정렬 범위 설정
        sort_range = f"A2:{self.maxranking}"
        sort_column = 2

        # 시트 정렬
        sheet = self.doc.worksheet(track_name)
        sheet.sort((sort_column, "asc"), range=sort_range)

        return await interaction.response.send_message(
            embed=discord.Embed(title="✅ 오름차순 정리 완료", description=f"{track_name} 시트에 오름차순 정리를 하였습니다.", color=EmbedColor.GREEN),
            ephemeral=True,
        )


    @app_commands.command(name="이펭귄")
    @app_commands.checks.cooldown(1, 5)
    async def penguin(self, interaction: discord.Interaction):
        """이펭귄에 대한 모든 유저들의 생각"""
        await interaction.response.send_message(
            content="# 흉물",
            ephemeral=True
        )
        

    async def track_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
        app_commands.Choice(name=track, value=track)
        for track in tracks if current.lower() in track.lower()
        ][:25]  # 최대 25개
    
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
    @app_commands.choices(kartengine=[
        app_commands.Choice(name="전체", value="전체"),
    *[app_commands.Choice(name=f"(더미) {name}", value=name) if idx >= 9 else app_commands.Choice(name=name, value=name) for idx, name in enumerate(engine_names)]
    

    ])
    async def show_rank(self, interaction: discord.Interaction, track_name: str, kartengine: app_commands.Choice[str], toktoki: app_commands.Choice[str],
team: app_commands.Choice[str], infinity: app_commands.Choice[str], crash: app_commands.Choice[str], numb: discord.app_commands.Range[int, 1] = 1):
        user_id = interaction.user.id

        # 모드 번호
        mode_num = [] #톡톡이 팀 무부 벽

        #톡톡이 모드
        if toktoki.value == "1":
            mode_num.insert(0, "1")
        else:
            mode_num.insert(0, "0")
        #팀전
        if team.value == "1":
            mode_num.insert(1, "1")
        else:
            mode_num.insert(1, "0")
        #무부
        if infinity.value == "1":
            mode_num.insert(2, "1")
        else:
            mode_num.insert(2, "0")
        #벽 충돌 페널티
        if crash.value == "1":
            mode_num.insert(3, "1")
        else:
            mode_num.insert(3, "0")

        if all(num == "0" for num in mode_num):
            mode = "기본"
        else:
            mode = ", ".join(filter(None, [
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
            sheet = self.doc.worksheet(track_name)
            all_data = sheet.get_all_values()  # 전체 시트를 한 번에 가져옴 (1회 호출)
            contentlist = ""

            mode_num_str = str(mode_num)  # 비교를 위해 문자열로 변환

            # 어떻게든 되겠지 뭐        
            i = 1
            # 얘는 대충 설명에 순위 넣을 때 + 5로 딱 나누어 떨어질 때 마다 임베드 나누기
            count = 0
            # 얘는 대충 contentlist가 남았을 때 (count 변수가 5의 배수로 딱 떨어지면 contentlist의 내용물이 비어짐) 제목에 순위 넣을려고 만든 거
            x = 0

            # 임베드 페이지들이 모이는 공간
            embeds = []

            # i는 실제 시트에서 2번째 행부터 시작 (헤더 생략)
            for row_idx in range(i, len(all_data)):
                row = all_data[row_idx]
                if len(row) < 6:
                    continue  # 비정상 데이터 무시

                if row[0] and row[4] == mode_num_str and (row[3] == kartengine.value or kartengine.value == "전체"):
                    count += 1
                    contentlist += f'''
- **순위** : {count}등 
- **닉네임** : {row[0]}
- **기록** : {row[1]}
- **탑승 카트** : {row[2]} 
- **엔진** : {row[3]}
- **모드** : {mode}
- **영상** : {row[5]}\n\n'''

                # 한 임베드의 설명 안에 5개의 기록이 들어가 있는지
                if count % 5 == 0:
                    x = count + 1
                    # 임베드 저장
                    embeds.append(
                        discord.Embed(
                            title=f"🕐 {track_name} 순위 ({count - 4}등 ~ {count}등)",
                            description=contentlist,
                            color=EmbedColor.BLUE,
                        )
                    )
                    # 내용 초기화
                    contentlist = ""


            if contentlist:
                embeds.append(
                    discord.Embed(
                        title=f"🕐 {track_name} 순위 ({x}등 ~ {count}등)",
                        description=contentlist,
                        color=EmbedColor.BLUE,
                    )
                )

            if not len(embeds):
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title=f"🕐 {track_name} 순위",
                        description="⚠️ 표시할 데이터가 없습니다.",
                        color=EmbedColor.BLUE,
                    )
                )
                
            if numb > len(embeds):
                numb = len(embeds)

            await Paginator.Simple(InitialPage=numb-1).start(interaction, pages=embeds)

        except Exception as e:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ 예외 발생",
                    description=f"오류가 발생했습니다: `{type(e).__name__}`\n{str(e)}",
                    color=EmbedColor.RED,
                ),
                ephemeral=True,
            )


    async def send_dm_and_log(self, interaction, user, username, request_id, mcname, track_name, record, kartbody, kartengine, youtubevideo, mode):
        """DM 및 로그 전송을 처리하는 함수."""
        # DM 전송
        if self.verify_dm:
            ch = await username.create_dm()
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
        # 로그 전송
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
        
    async def track_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
        app_commands.Choice(name=track, value=track)
        for track in tracks if current.lower() in track.lower()
        ][:25]  # 최대 25개


    @app_commands.command(name="addrecord")
    @app_commands.autocomplete(track_name=track_autocomplete)
    @app_commands.choices(
        kartengine=[
                app_commands.Choice(name=f"(더미) {name}", value=name) if idx >= 9 else app_commands.Choice(name=name, value=name)
                for idx, name in enumerate(engine_names)
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
        """기록을 신청합니다."""

        # 유효성 검사 함수
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
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ 입력 오류",
                    description=validation_error,
                    color=EmbedColor.RED,
                ),
                ephemeral=True,
            ) 
        
        embed = discord.Embed(
                title="🔔 새 기록 등록",
                description=f"""
:bust_in_silhouette: **마크 닉네임** - `{mcname}`
:map: **트랙명** - `{track_name}`
:stopwatch: **기록** - `{record}`
:red_car: **카트** - `{kartbody} {kartengine.value}`
:arrow_forward: **유튜브 링크** - {youtubevideo}
""",
                color=EmbedColor.YELLOW,
            )

        
        await interaction.response.defer(ephemeral=True)

                # UID 생성 및 기록 저장
        uid = random.randint(1, 100000000)
        uiddata = {
            "username": interaction.user,
            "mcname": mcname,
            "track": track_name,
            "record": record,
            "kart": kartbody,
            "engine": kartengine.value,
            "youtubevideo": youtubevideo,
            "timestamp": time.time(),
        }
        await interaction.followup.send(
            embed=embed,
            view=AddRecordOptionView(
                author_interaction=interaction,
                uid=uid,
                uiddata=uiddata,
                parent=self
            ),
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

        async def send_fail_dm(username, request_id, mcname, track_name, record, old_record, kartbody, kartengine, mode, youtubevideo):
            ch = await username.create_dm()
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
                request_user = data["username"]
                mode = data["mode"]

                if self.deny_dm:
                    ch = await request_user.create_dm()
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
                uiddata = self.uiddata.get(request_id)
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
                username = uiddata["username"]
                mode_num = uiddata["mode_num"]
                mode = uiddata["mode"]

                if track_name in tracks:
                    sheet = doc.worksheet(track_name)
                    all_rows = sheet.get_all_values()  # 한 번만 API 호출
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
                                await self.send_dm_and_log(interaction, user, username, request_id, mcname, track_name, record, kartbody, kartengine, youtubevideo, mode)
                                for col, value in zip(columns, values):
                                    sheet.update_acell(f"{col}{i}", escape_formula(value))
                                sort_range = f"{columns[0]}2:{columns[-1]}{self.maxranking}"
                                sheet.sort((2, "asc"), range=sort_range)
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
                                if self.verify_dm:
                                    await send_fail_dm(username, request_id, mcname, track_name, record, cell_record, kartbody, kartengine, mode, youtubevideo)
                                    await asyncio.sleep(DELAY_TO_DELETE)
                                    await interaction.delete_original_response()
                                break
                        elif cell_mcname is None:
                            await self.send_dm_and_log(interaction, user, username, request_id, mcname, track_name, record, kartbody, kartengine, youtubevideo, mode)
                            for col, value in zip(columns, values):
                                sheet.update_acell(f"{col}{i}", escape_formula(value))
                            sort_range = f"{columns[0]}2:{columns[-1]}{self.maxranking}"
                            sheet.sort((2, "asc"), range=sort_range)
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
            uiddata = self.uiddata.get(request_id)
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

async def setup(bot):
    await bot.add_cog(Admin(bot))