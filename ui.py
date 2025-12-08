
import pygame

from config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    HUD_TEXT_COLOR,
    INFO_BG_COLOR,
    INFO_BG_ALPHA,
)


def create_font():
    """게임 전반에서 사용할 기본 폰트 생성."""
    try:
        return pygame.font.SysFont("malgungothic", 20)
    except Exception:
        return pygame.font.SysFont(None, 20)


def draw_hud(
    screen,
    font,
    sword_mass,
    mouse_mass,
    last_slash_energy,
    last_required_energy,
    last_cut_ratio,
):
    """화면 상단 HUD 그리기."""
    lines = [
        f"검 무게: {sword_mass:.2f} kg / 마우스 무게: {mouse_mass:.2f} kg",
        f"마지막 베기 에너지(마우스 기준): {last_slash_energy:.2f}",
        f"완전 절단 필요 에너지(해당 경로 기준): {last_required_energy:.2f}",
        f"이번 베기 강도: {last_cut_ratio * 100.0:.1f} %",
    ]
    y = 10
    for text in lines:
        surf = font.render(text, True, HUD_TEXT_COLOR)
        screen.blit(surf, (10, y))
        y += surf.get_height() + 2


def draw_start_tip_overlay(screen, font):
    """처음 실행 시 한 번만 보여줄 시작 안내 오버레이."""
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    lines = [
        "I 키를 눌러 설명을 확인하세요.",
        "아무 키나 누르면 게임이 시작됩니다.",
    ]

    total_height = 0
    rendered = []
    for t in lines:
        surf = font.render(t, True, HUD_TEXT_COLOR)
        rendered.append(surf)
        total_height += surf.get_height() + 10

    start_y = (WINDOW_HEIGHT - total_height) // 2
    for surf in rendered:
        x = (WINDOW_WIDTH - surf.get_width()) // 2
        screen.blit(surf, (x, start_y))
        start_y += surf.get_height() + 10


# ---------- 설명창 관련 ----------

def get_info_lines():
    """설명창에 표시할 모든 줄을 리스트로 반환."""
    return [
        "[기본 조작]",
        "· 좌/우 클릭: 칼을 휘둘러 한 번의 '베기'를 기록합니다.",
        "· R 키: 허수아비를 처음 상태로 리셋합니다.",
        "· O 키: 설정창 열기/닫기",
        "· I 키: 이 설명창 열기/닫기",
        "· ESC 키: 게임 종료",
        "",
        "[화면 구성]",
        "· 상단 HUD: 무게, 에너지, 베기 강도(%)를 보여줍니다.",
        "· 중앙: 허수아비와 검의 실제 움직임이 보입니다.",
        "· 허수아비 위의 검은 선: 지금까지 남은 베인 자국입니다.",
        "",
        "[물리 계산 방식]",
        "· 한 번의 베기 = 클릭을 누르고 있는 동안 마우스가 움직인 경로입니다.",
        "· 마우스(손)의 속도 v로 운동에너지 E = 1/2 · m_mouse · v^2 를 계산합니다.",
        "· 한 번의 베기 동안 나왔던 E 중 가장 큰 값을",
        "  '이번 베기의 에너지'로 사용합니다.",
        "",
        "[허수아비 절단 조건]",
        "· 표면 강도(문턱 에너지, E_init)",
        "    - 허수아비 표면에 첫 칼집이 나기 시작하는 최소 에너지입니다.",
        "· 절단 저항(단위 길이당 에너지, k)",
        "    - 이미 칼집이 난 상태에서, 허수아비 안쪽을",
        "      길이 1만큼 더 자르기 위해 필요한 추가 에너지입니다.",
        "· 허수아비 안에서 검이 실제로 지나간 길이를 L_inside 라 할 때,",
        "  그 경로 전체를 완전히 자르는 데 필요한 에너지는",
        "  E_required = E_init + k · L_inside 입니다.",
        "· HUD에 표시되는 %는 E / E_required 를 0~100%로 환산한 값입니다.",
        "",
        "[기타]",
        "· 무게와 절단 관련 값들은 O 키로 여는 설정창에서 바꿀 수 있습니다.",
        "",
        "I 키를 다시 누르면 이 창이 닫힙니다.",
    ]


def get_info_scroll_limits(font):
    """
    설명창 스크롤 오프셋의 최소/최대값을 계산.
    return: (min_offset, max_offset)
      - offset은 텍스트를 그릴 때 더해지는 y 이동량.
      - 0이 맨 위, min_offset(음수)이 맨 아래.
    """
    lines = get_info_lines()
    line_height = font.get_linesize()
    total_text_height = line_height * len(lines)
    padding_top_bottom = 20

    # 설명창 배경 높이(화면 안에 들어오도록 제한)
    overlay_height = total_text_height + padding_top_bottom * 2
    max_overlay_height = WINDOW_HEIGHT - 80
    overlay_height = min(overlay_height, max_overlay_height)

    visible_height = overlay_height - padding_top_bottom * 2

    if total_text_height <= visible_height:
        min_offset = 0
    else:
        min_offset = visible_height - total_text_height  # 음수

    max_offset = 0
    return min_offset, max_offset


def draw_info_overlay(screen, font, scroll_offset):
    """I 키로 토글되는 물리 설명/매뉴얼 창 (스크롤 가능)."""
    info_lines = get_info_lines()

    line_height = font.get_linesize()
    total_text_height = line_height * len(info_lines)
    padding_top_bottom = 20

    overlay_height = total_text_height + padding_top_bottom * 2
    max_overlay_height = WINDOW_HEIGHT - 80
    overlay_height = min(overlay_height, max_overlay_height)

    # 1) overlay Surface 안에 글씨를 모두 그린 다음
    overlay = pygame.Surface((WINDOW_WIDTH - 40, overlay_height), pygame.SRCALPHA)
    overlay.fill((*INFO_BG_COLOR, INFO_BG_ALPHA))

    y = padding_top_bottom + scroll_offset  # overlay 내부 좌표
    for line in info_lines:
        # [섹션 제목] 라인은 볼드 처리
        if line.startswith("[") and line.endswith("]"):
            font.set_bold(True)
        else:
            font.set_bold(False)

        surf = font.render(line, True, HUD_TEXT_COLOR)
        # overlay 기준으로 blit
        overlay.blit(surf, (10, y))
        y += surf.get_height() + 2

    font.set_bold(False)

    # 2) 완성된 overlay를 화면에 한 번만 blit
    screen.blit(overlay, (20, 60))


# ---------- 설정창 ----------

def draw_settings_overlay(
    screen,
    font,
    selected_index,
    sword_mass,
    mouse_mass,
    e_init,
    energy_per_len,
    input_mode,
    input_value,
):
    """O 키로 토글되는 설정창 (이 창이 켜져 있을 때는 게임이 멈춤)."""
    settings_lines = [
        "[설정]",
        "",
        f"1. 검 질량 (kg): {sword_mass:.2f}  (클수록 마우스를 더 느리게 따라갑니다.)",
        f"2. 마우스 질량 (kg): {mouse_mass:.2f}  (클수록 같은 속도에서 에너지가 더 큽니다.)",
        f"3. 표면 강도(문턱 에너지): {e_init:.2f}  (클수록 처음 칼집이 잘 안 생깁니다.)",
        f"4. 절단 저항(단위 길이당 에너지): {energy_per_len:.3f}  (클수록 깊은 베기가 어렵습니다.)",
        "",
        "↑ / ↓ : 항목 선택   ← / → : 값 조절",
    ]

    if input_mode:
        settings_lines.append("입력 중: Enter=확정, Esc=취소, Backspace=지우기")
    else:
        settings_lines.append("Enter: 직접 값 입력   O: 설정창 닫기")

    line_height = font.get_linesize()
    total_text_height = line_height * len(settings_lines)
    padding_top_bottom = 20

    overlay_height = total_text_height + padding_top_bottom * 2
    max_overlay_height = WINDOW_HEIGHT - 80
    overlay_height = min(overlay_height, max_overlay_height)

    # 1) overlay를 만든 뒤 그 위에 텍스트를 모두 그림
    overlay = pygame.Surface((WINDOW_WIDTH - 40, overlay_height), pygame.SRCALPHA)
    overlay.fill((*INFO_BG_COLOR, INFO_BG_ALPHA))

    y = padding_top_bottom
    for i, line in enumerate(settings_lines):
        if 2 <= i <= 5:
            idx = i - 2
            prefix = "> " if idx == selected_index else "  "
            text = prefix + line

            if input_mode and idx == selected_index:
                text += f"  [입력: {input_value}_]"
        else:
            text = line

        # [설정] 같은 제목은 볼드
        if text.strip().startswith("[") and text.strip().endswith("]"):
            font.set_bold(True)
        else:
            font.set_bold(False)

        surf = font.render(text, True, HUD_TEXT_COLOR)
        overlay.blit(surf, (10, y))
        y += surf.get_height() + 2

    font.set_bold(False)

    # 2) 완성된 overlay를 화면에 한 번 blit
    screen.blit(overlay, (20, 60))
