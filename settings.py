class EmbedColor:
    RED = 0xFF213F
    BLUE = 0x0390FC
    GREEN = 0x88FF61
    GOLD = 0xFFE524
    BLURPLE = 0x5865F2
    EMBED = 0x2C2D31
    LIME = 0x95FF00
    YELLOW = 0xFFFF00

class Option: # 맞춤설정
    latest_version_check = True  # 최신 버전 체크 여부
    latest_version_check_interval = 1 # 시간 (단위: 시간)
    maxranking = 2001
    verify_log = True
    deny_dm  = True
    verify_dm = True

class CustomID:
    VERIFY_RECORD = "#mcrider_bot/verify/"
    DENY_RECORD = "#mcrider_bot/deny/"
        
    def make_verify_record(uid: int) -> str:
        return f"{CustomID.VERIFY_RECORD}{uid}"

    def get_verify_record_uid(custom_id: str) -> int:
        return int(custom_id.removeprefix(CustomID.VERIFY_RECORD))

    def make_deny_record(uid: int) -> str:
        return f"{CustomID.DENY_RECORD}{uid}"

    def get_deny_record_uid(custom_id: str) -> int:
        return int(custom_id.removeprefix(CustomID.DENY_RECORD))
    
class BotInfo:
    NAME = "도로주행 기능사 로봇"
    VERSION = "v1.2.0"
    AUTHOR = "MCriderBOT | By 북극곰(BKGpolar), 미간(migan.), 헧사(hexx_4)"
    GITHUB_URL = "https://github.com/bkgpolar12/MCriderBOT"
    GITHUB_API = "https://api.github.com/repos/bkgpolar12/MCriderBOT/releases/latest"
    # GITHUB_URL_TEST = "https://github.com/bkgpolar12/test"
    # GITHUB_API_TEST = "https://api.github.com/repos/bkgpolar12/test/releases/latest"