class EmbedColor:
    RED = 0xFF213F
    BLUE = 0x0390FC
    GREEN = 0x88FF61
    GOLD = 0xFFE524
    BLURPLE = 0x5865F2
    EMBED = 0x2C2D31
    LIME = 0x95FF00
    YELLOW = 0xFFFF00
    
def make_verify_record_custom_id(uid: int) -> str:
    return f"#mcrider_bot/verify/{uid}"

def make_deny_record_custom_id(uid: int) -> str:
    return f"#mcrider_bot/deny/{uid}"