import discord
import asyncio
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

    
async def setup(bot):
    await bot.add_cog(Admin(bot))

load_dotenv()

class Admin(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client #디스코드 봇 모델
        self.uiddata = {} #정보들이 저장되는 딕셔너리
        self.uid = 0
        self.json_key_path = os.environ.get('REACT_JSON_KEY_PATH')
        self.gc = gspread.service_account(filename=self.json_key_path) # 서비스 계정의 키

        self.sheet_url = os.environ.get('REACT_SHEET_URL') #스프레드시트 url
        self.doc = self.gc.open_by_url(self.sheet_url)
        self.sheet = self.doc.worksheet("포레스트 통나무") #시트 기본값
        self.tracks = trackss.TRACKK
        self.verifychannel = int(os.environ.get('REACT_VERIFYCHANNEL'))
        self.verifierrole = int(os.environ.get('REACT_VERIFIER_ROLD_ID'))
        self.cooldowns = {}  # 사용자 ID별 마지막 사용 시간 저장

        # 기능기
        self.verify_log = True # 로그 남기기
        self.deny_dm  = True # 등록 거절 시 DM 전송
        self.verify_dm = True # 등록 시 DM 전송

    def cleanup_old_requests(self, expire_seconds=3600):  # 1시간 기준
        now = time.time()
        expired_keys = [key for key, data in self.uiddata.items() if now - data.get("timestamp", now) > expire_seconds]
        for key in expired_keys:
            del self.uiddata[key]

    def is_on_cooldown(self, user_id: int, cooldown_time: float = 5.0) -> bool:
        """사용자가 쿨타임 중인지 확인"""
        now = time.time()
        if user_id in self.cooldowns:
            return now - self.cooldowns[user_id] < cooldown_time
        return False

    def update_cooldown(self, user_id: int):
        """쿨타임 갱신"""
        self.cooldowns[user_id] = time.time()



    
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
    @app_commands.choices(toktoki=[
        app_commands.Choice(name="활성화", value="1"),
        app_commands.Choice(name="비활성화", value="2"),
    ])
    @app_commands.rename(track_name="트랙이름", toktoki="톡톡이모드")
    async def ascc(self, interaction: discord.Interaction, track_name: str, toktoki: app_commands.Choice[str]):
        """[베리파이어 전용] 기록을 오름차순으로 정리합니다."""

        # 권한 체크
        if not any(role.id == int(self.verifierrole) for role in interaction.user.roles):
            return await interaction.response.send_message("❌ 당신은 이 명령어를 사용할 권한이 없습니다.", ephemeral=True)
        
        # 쿨다운 체크
        user_id = interaction.user.id
        if self.is_on_cooldown(user_id):
            return await interaction.response.send_message(
                embed=discord.Embed(title="⏳ 잠시만요!", description="명령어는 5초 간격으로만 사용할 수 있습니다.", color=EmbedColor.RED),
                ephemeral=True,
            )
        self.update_cooldown(user_id)

        # 트랙 존재 여부 체크
        if track_name not in self.tracks:
            return await interaction.response.send_message(
                embed=discord.Embed(title="❌ 오류", description="존재하지 않는 트랙입니다.", color=EmbedColor.RED),
                ephemeral=True,
            )

        # 정렬 범위 설정
        sort_range = "A2:E1001" if toktoki.name == "비활성화" else "G2:K1001"
        sort_column = 2 if toktoki.name == "비활성화" else 8

        # 시트 정렬
        sheet = self.doc.worksheet(track_name)
        sheet.sort((sort_column, "asc"), range=sort_range)

        return await interaction.response.send_message(
            embed=discord.Embed(title="✅ 오름차순 정리 완료", description=f"{track_name} 시트에 오름차순 정리를 하였습니다.", color=EmbedColor.GREEN),
            ephemeral=True,
        )


    @app_commands.command(name="showranking")
    @app_commands.rename(track_name="트랙이름", numb="페이지", toktoki="톡톡이모드")
    @app_commands.choices(toktoki=[
        app_commands.Choice(name="활성화", value="1"),
        app_commands.Choice(name="비활성화", value="2"),
    ])
    async def show_rank(self, interaction: discord.Interaction, track_name: str, numb: int, toktoki: app_commands.Choice[str]):
        user_id = interaction.user.id
        if self.is_on_cooldown(user_id):
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="⏳ 잠시만요!",
                    description="명령어는 5초 간격으로만 사용할 수 있습니다.",
                    color=EmbedColor.RED,
                ),
                ephemeral=True,
            )
        self.update_cooldown(user_id)
        
        await interaction.response.defer(ephemeral=True)

        if track_name not in self.tracks:
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
            contentlist = ""
            column_range = ("A", "B", "C", "D", "E") if toktoki.name == "비활성화" else ("G", "H", "I", "J", "K")

            for i in range(2 + ((numb - 1) * 5), 7 + ((numb - 1) * 5)):
                if sheet.acell(f"{column_range[0]}{i}").value is not None:
                    contentlist += f'''
- **순위** : {i-1}등 
- **닉네임** : {sheet.acell(f'{column_range[0]}{i}').value}
- **기록** : {sheet.acell(f'{column_range[1]}{i}').value}
- **탑승 카트** : {sheet.acell(f'{column_range[2]}{i}').value} 
- **엔진** : {sheet.acell(f'{column_range[3]}{i}').value} 
- **영상** : {sheet.acell(f'{column_range[4]}{i}').value}\n\n'''
                else:
                    break

            mode = "[톡톡이 모드 비활성화]" if toktoki.name == "비활성화" else "[톡톡이 모드 활성화]"
            await interaction.followup.send(
                embed=discord.Embed(
                    title=f"🕐 {track_name} 순위 ({1+((numb-1)*5)}등 ~ {5+((numb-1)*5)}등) {mode}",
                    description=contentlist + f"\n\n\n- {numb} -" or "⚠️ 표시할 데이터가 없습니다." + f"\n\n\n- {numb} -",
                    color=EmbedColor.BLUE,
                ),
                ephemeral=True,
            )

        except Exception as e:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ 예외 발생",
                    description=f"오류가 발생했습니다: `{type(e).__name__}`\n{str(e)}",
                    color=EmbedColor.RED,
                ),
                ephemeral=True,
            )



    @app_commands.command(name="verifyrecord")
    @app_commands.rename(request_id="아이디") 
    async def verify_record(self, interaction: discord.Interaction, request_id: int):
        """[베리파이어 전용] 기록 신청을 허용하고 등록합니다."""
        if not any(role.id == int(self.verifierrole) for role in interaction.user.roles):
            return await interaction.response.send_message("❌ 당신은 이 명령어를 사용할 권한이 없습니다.", ephemeral=True)
        
        user = interaction.user
        user_id = user.id

        if self.is_on_cooldown(user_id):
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="⏳ 잠시만요!",
                    description="명령어는 5초 간격으로만 사용할 수 있습니다.",
                    color=EmbedColor.RED,
                ),
                ephemeral=True,
            )
        self.update_cooldown(user_id)
        self.cleanup_old_requests()

        def escape_formula(value: str) -> str:
            """엑셀에서 수식을 방지하는 함수."""
            if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
                return "'" + value
            return value

        try:
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

            track_name = uiddata["track"]
            mcname = uiddata["mcname"]
            record = uiddata["record"]
            kartbody = uiddata["kart"]
            kartengine = uiddata["engine"]
            youtubevideo = uiddata["youtubevideo"]
            username = uiddata["username"]
            toktoki = uiddata["toktoki"]

            if track_name in self.tracks:
                sheet = self.doc.worksheet(track_name)

                for i in range(2, 1001):
                    if sheet.acell(f"A{i}").value is None or sheet.acell(f"A{i}").value == mcname:
                        # 기록을 삽입하거나 덮어쓰기
                        columns = ("A", "B", "C", "D", "E") if toktoki == "비활성화" else ("G", "H", "I", "J", "K")
                        values = [mcname, record, kartbody, kartengine, youtubevideo] if toktoki == "비활성화" else \
                                [mcname, record, kartbody, kartengine, youtubevideo]
                        # 기존 기록이 더 빠르면 등록 거절
                        if sheet.acell(f'B{i}').value is not None and sheet.acell(f'B{i}').value > record:
                            for col, value in zip(columns, values):
                                sheet.update_acell(f"{col}{i}", escape_formula(value))
                            sort_range = f"{columns[0]}2:{columns[-1]}1001"
                            sheet.sort((2, "asc"), range=sort_range)

                            # DM 및 로그 전송
                            await self.send_dm_and_log(interaction, user, username, request_id, mcname, track_name, record, kartbody, kartengine, youtubevideo, toktoki)
                            break
                        else:
                            await interaction.response.send_message(
                                embed=discord.Embed(
                                    title=f"❌ 등록 실패 - `#{request_id}`",
                                    description=f"""
- **닉네임** : {mcname}
- **트랙명** : {track_name}
- **기록** : {record} | (기존 기록 : {sheet.acell(f'B{i}').value})
- **탑승 카트** : {kartbody}
- **엔진** : {kartengine}
- **톡톡이모드**: {toktoki}
- **영상** : {youtubevideo}""",
                                    color=EmbedColor.RED,
                                ).set_footer(
                                    text="기존 기록이 신청한 기록보다 빠르거나 같습니다."
                                )
                            )
                            break
                    else:
                        continue

            else:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ 등록 실패",
                        description="존재하지 않는 트랙입니다.",
                        color=EmbedColor.RED,
                    ),
                    ephemeral=True,
                )

        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ 예외 발생",
                    description=f"오류가 발생했습니다: `{type(e).__name__}`\n{str(e)}",
                    color=EmbedColor.RED,
                ),
                ephemeral=True,
            )


    async def send_dm_and_log(self, interaction, user, username, request_id, mcname, track_name, record, kartbody, kartengine, youtubevideo, toktoki):
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
- **톡톡이모드**: {toktoki}
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
- **톡톡이모드**: {toktoki}
- **영상** : {youtubevideo}""",
                    color=EmbedColor.BLUE,
                ).set_footer(
                    text="관리자 전용 메시지입니다. 유출하지 마십시오."
                )
            )


    @app_commands.command(name="denyrecord")
    @app_commands.rename(request_id="아이디", reason="사유")
    async def deny_record(
        self, interaction: discord.Interaction, request_id: int, reason: str
    ):
        """[베리파이어 전용] 기록 신청을 거절합니다."""
        if not any(role.id == int(self.verifierrole) for role in interaction.user.roles):
            await interaction.response.send_message(
            "❌ 당신은 이 명령어를 사용할 권한이 없습니다.",
            ephemeral=True
        )
            return
        
        user = interaction.user
        user_id = user.id
        
        if self.is_on_cooldown(user_id):
            await interaction.response.send_message(
            embed=discord.Embed(
                title="⏳ 잠시만요!",
                description="명령어는 5초 간격으로만 사용할 수 있습니다.",
                color=EmbedColor.RED,
            ),
            ephemeral=True,
        )
            return
        self.update_cooldown(user_id)

        try:
            track_name = self.uiddata[request_id]["track"]
            mcname = self.uiddata[request_id]["mcname"]
            record = self.uiddata[request_id]["record"]
            kartbody = self.uiddata[request_id]["kart"]
            kartengine = self.uiddata[request_id]["engine"]
            youtubevideo = self.uiddata[request_id]["youtubevideo"]
            request_user = self.uiddata[request_id]["username"]
            toktoki = self.uiddata[request_id]["toktoki"]
            
            if self.deny_dm == True:
                ch = await request_user.create_dm() #기록 신청한 유저에게 개인 메시지
                await ch.send(
                    embed=discord.Embed(
                        title=f"❌ 등록 거부됨 - `#{request_id}`",
                        description=f"""
- **닉네임** : {mcname}
- **트랙명** : {track_name}
- **기록** : {record}
- **탑승 카트** : {kartbody}
- **엔진** : {kartengine}
- **톡톡이 모드** : {toktoki}
- **영상** : {youtubevideo}


- **사유** : {reason}""",
                        color=EmbedColor.RED,
                    ).set_footer(
                        text="등록 조건에 맞춰 제출하시기 바랍니다."
                    )
                )
            if self.verify_log == True:
                    ch = self.client.get_channel(int(os.environ.get('REACT_VERIFYLOGCHANNEL')))
                    await ch.send(
                        embed=discord.Embed(
                            title=f"❌ 등록 거부 - `#{request_id}`",
                            description=f"""
- **담당자** : {user.display_name} ({user.name})
- **닉네임** : {mcname}
- **트랙명** : {track_name}
- **기록** : {record}
- **탑승 카트** : {kartbody}
- **엔진** : {kartengine}
- **톡톡이모드**: {toktoki}
- **영상** : {youtubevideo}


- **사유** : {reason}""",
                            color=EmbedColor.BLUE,
                        ).set_footer(
                            text="관리자 전용 메시지입니다. 유출하지 마십시오."
                        )
                    )
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="✅ 거절 완료",
                    description=f"요청 `#{request_id}`을 거절하였습니다.",
                    color=EmbedColor.GREEN,
                ),
                ephemeral=True
            )
        except KeyError:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ 등록 실패",
                    description="존재하지 않는 ID입니다.",
                    color=EmbedColor.RED,
                ),
                ephemeral=True,
            )

    @app_commands.command(name="addrecord")
    @app_commands.rename(
        mcname="마크닉네임",
        track_name="트랙명",
        record="기록",
        kartbody="탑승카트",
        kartengine="엔진",
        youtubevideo="영상",
        toktoki="톡톡이모드"
    )
    @app_commands.choices(toktoki=[
        app_commands.Choice(name="활성화", value="1"),
        app_commands.Choice(name="비활성화", value="2"),
    ])
    async def add_record(self, interaction: discord.Interaction, mcname: str, track_name: str, record: str, kartbody: str, kartengine: str, youtubevideo: str, toktoki: app_commands.Choice[str]):
        """기록을 신청합니다."""
        user_id = interaction.user.id

        if self.is_on_cooldown(user_id):
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="⏳ 잠시만요!",
                    description="명령어는 5초 간격으로만 사용할 수 있습니다.",
                    color=EmbedColor.RED,
                ),
                ephemeral=True,
            )

        self.update_cooldown(user_id)
        self.cleanup_old_requests()

        # 유효성 검사 함수
        def validate_input():
            if not re.match(r'^https?://(?:www\.)?(youtube\.com|youtu\.be)', youtubevideo):
                return "유효한 유튜브 링크를 입력해주세요."

            if not re.match(r'^\d{1,2}:[0-5][0-9]\.\d{3}$', record):
                return "기록은 `00:00.000` 형식으로 입력해주세요 (예: 01:23.456)."

            if len(kartbody) > 20:
                return "탑승 카트 이름은 20글자 이하여야 합니다."

            if len(kartengine) > 8:
                return "엔진 이름은 8글자 이하여야 합니다."

            if track_name not in trackss.TRACKK:
                return "존재하지 않은 트랙이거나 트랙 이름이 올바르지 않습니다."

            if not self.get_uuid(mcname):
                return "이 이름을 가진 마인크래프트 유저를 찾을 수 없습니다."

            return None

        # 입력값 검증
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

        # UID 생성 및 기록 저장
        uid = random.randint(1, 100000000)
        while uid in self.uiddata:
            uid = random.randint(1, 100000000)

        self.uiddata[uid] = {
            "username": interaction.user,
            "mcname": mcname,
            "track": track_name,
            "record": record,
            "kart": kartbody,
            "engine": kartengine,
            "youtubevideo": youtubevideo,
            "toktoki": toktoki.name,
            "timestamp": time.time(),
        }

        # 채널 확인 및 메시지 전송
        verifychannel = os.environ.get('REACT_VERIFYCHANNEL')
        if not verifychannel or int(verifychannel) == 0:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ 신청 실패",
                    description="관리자가 기록 등록 메시지가 전송될 채널을 지정하지 않았습니다. 이 문제를 해결하기 위해 관리자에게 문의하세요.",
                    color=EmbedColor.RED,
                ),
                ephemeral=True
            )

        channel = self.client.get_channel(int(verifychannel))
        if not channel:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ 신청 실패",
                    description="지정된 채널을 찾을 수 없습니다.",
                    color=EmbedColor.RED,
                ),
                ephemeral=True,
            )

        # 채널에 기록 신청 전송
        await channel.send(
            embed=discord.Embed(
                title=f"🔔 기록 등록 신청 - `#{uid}`",
                description=f"""
- **신청자** : {self.uiddata[uid]['username'].display_name} ({self.uiddata[uid]['username'].name})
- **마크 닉네임** : {self.uiddata[uid]['mcname']}
- **트랙명** : {self.uiddata[uid]['track']}
- **기록** : {self.uiddata[uid]['record']}
- **탑승 카트** : {self.uiddata[uid]['kart']}
- **엔진** : {self.uiddata[uid]['engine']}
- **톡톡이 모드** : {self.uiddata[uid]['toktoki']}
- **영상** : {self.uiddata[uid]['youtubevideo']}""",
                color=EmbedColor.YELLOW,
            ).set_footer(
                text="/denyrecord [ID] [사유] 를 통해 거절하거나 /verifyrecord 를 입력하여 등록해 주세요."
            ),
            mention_author=False,
        )

        # 사용자에게 신청 완료 메시지 전송
        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ 신청 완료",
                description="관리자에게 요청이 전송되었습니다.",
                color=EmbedColor.GREEN,
            ),
            ephemeral=True,
        )
