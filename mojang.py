# 원래는 uuid로 가져와야 했는데 이 API를 쓰니 이름으로도 되는!
# 그래서 나는 무척 기쁘다.
MINOTAR_URL = "https://minotar.net/helm"


def get_player_head_url(name: str) -> str:
    return f"{MINOTAR_URL}/{name}"
        