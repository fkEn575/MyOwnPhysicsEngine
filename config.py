
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
FPS = 60

# 물리 파라미터
SWORD_BASE_MASS = 1.5  # kg, 기본 롱소드 질량
SWORD_MIN_MASS = 0.5
SWORD_MAX_MASS = 4.0

# '빠르게 휘두름'으로 인식할 최소 속도 (픽셀/초)
SLASH_SPEED_THRESHOLD = 600.0

# 검 컨트롤러 기본 강성 (기본 질량일 때 기준)
SWORD_STIFFNESS_BASE = 20.0

# 허수아비(밀짚) 잘리는 임계값들 (임팩트 값 기준)
# 값은 게임 밸런스용이라 자유롭게 조정하면 됩니다.
CUT_THRESHOLDS = {
    "no_cut": 5.0,     # 이하면 안 베임
    "shallow": 15.0,   # 얕게
    "medium": 35.0,    # 중간
    "deep": 70.0,      # 깊게
}

SCARECROW_RECT = (WINDOW_WIDTH // 2 - 60, WINDOW_HEIGHT // 2 - 120, 120, 240)

BACKGROUND_COLOR = (30, 30, 30)
SCARECROW_COLOR = (180, 160, 80)
SCARECROW_OUTLINE = (100, 80, 40)

SLASH_COLOR = (220, 30, 30)
SLASH_SHALLOW_WIDTH = 2
SLASH_MEDIUM_WIDTH = 4
SLASH_DEEP_WIDTH = 7

HUD_TEXT_COLOR = (230, 230, 230)
