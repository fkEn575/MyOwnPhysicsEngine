
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
FPS = 60

# 렌더링 스케일 (픽셀 ↔ 미터)
PIXELS_PER_METER = 100.0  # 100px ≈ 1m 정도로 가정

# 검 물리 파라미터
SWORD_BASE_MASS = 1.5  # kg, 기본 롱소드 질량
SWORD_MIN_MASS = 0.5
SWORD_MAX_MASS = 4.0

# 검 컨트롤러 기본 강성 (기본 질량일 때 기준)
SWORD_STIFFNESS_BASE = 20.0

# 절단 에너지 모델
# E_required_full = E_init + ENERGY_PER_LENGTH * L_inside
E_INIT_DEFAULT = 8.0          # 처음 칼집이 나기 시작하는 최소 에너지
ENERGY_PER_LENGTH_DEFAULT = 0.08  # 허수아비 내부 길이 1px 당 추가로 필요한 에너지

# 허수아비 기본 직사각형 (화면 중앙에 세워진 인형)
SCARECROW_RECT = (WINDOW_WIDTH // 2 - 60, WINDOW_HEIGHT // 2 - 120, 120, 240)

# 색상
BACKGROUND_COLOR = (30, 30, 30)
SCARECROW_COLOR = (190, 170, 90)
SCARECROW_OUTLINE = (90, 70, 30)

SLASH_COLOR = (220, 40, 40)  # 허수아비에 남는 자국은 빨간색

HUD_TEXT_COLOR = (230, 230, 230)

INFO_BG_COLOR = (0, 0, 0)      # 설명창 / 설정창 배경 (반투명 효과는 알파로 처리)
INFO_BG_ALPHA = 200
