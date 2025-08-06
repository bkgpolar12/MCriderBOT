class EmbedColor:
    RED = 0xFF213F
    BLUE = 0x0390FC
    GREEN = 0x88FF61
    GOLD = 0xFFE524
    BLURPLE = 0x5865F2
    EMBED = 0x2C2D31
    LIME = 0x95FF00
    YELLOW = 0xFFFF00

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