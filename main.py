
import pygame

from config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    FPS,
    BACKGROUND_COLOR,
    HUD_TEXT_COLOR,
    E_INIT_DEFAULT,
    ENERGY_PER_LENGTH_DEFAULT,
    INFO_BG_COLOR,
    INFO_BG_ALPHA,
)
from physics import compute_speed, kinetic_energy
from entities import SwordController, Scarecrow


def clamp(value, vmin, vmax):
    return max(vmin, min(vmax, value))


def create_font():
    # 한글 지원 폰트가 있으면 사용, 없으면 기본 폰트
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
    lines = [
        f"검 무게: {sword_mass:.2f} kg / 마우스 무게: {mouse_mass:.2f} kg   (O 키 설정창에서 변경)",
        f"마지막 베기 에너지(마우스 기준): {last_slash_energy:.2f}",
        f"완전 절단 필요 에너지(해당 경로 기준): {last_required_energy:.2f}",
        f"이번 베기 강도: {last_cut_ratio * 100.0:.1f} %",
        "좌/우 클릭: 베기",
    ]
    y = 10
    for text in lines:
        surf = font.render(text, True, HUD_TEXT_COLOR)
        screen.blit(surf, (10, y))
        y += surf.get_height() + 2


def draw_start_tip_overlay(screen, font):
    """처음 실행 시 한 번만 보여줄 시작 안내 오버레이."""
    # 전체 화면 반투명 어둡게
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    lines = [
        "I 키를 눌러 설명을 확인하세요.",
        "아무 키나 누르면 게임이 시작됩니다.",
    ]

    # 중앙 정렬
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
    """설명창 스크롤 오프셋의 최소/최대값을 계산한다."""
    lines = get_info_lines()
    line_height = font.get_linesize()
    total_text_height = line_height * len(lines)
    padding_top_bottom = 20

    overlay_height = total_text_height + padding_top_bottom * 2
    max_overlay_height = WINDOW_HEIGHT - 80
    overlay_height = min(overlay_height, max_overlay_height)

    visible_height = overlay_height - padding_top_bottom * 2

    if total_text_height <= visible_height:
        min_offset = 0
    else:
        min_offset = visible_height - total_text_height  # 음수 방향으로 내려감

    max_offset = 0
    return min_offset, max_offset


def draw_info_overlay(screen, font, scroll_offset):
    """I 키로 토글되는 물리 설명/매뉴얼 창 (스크롤 가능)."""
    info_lines = get_info_lines()

    # --- 배경 높이를 텍스트 양에 맞춰 자동 계산 ---
    line_height = font.get_linesize()
    total_text_height = line_height * len(info_lines)
    padding_top_bottom = 20

    overlay_height = total_text_height + padding_top_bottom * 2
    # 화면 밖으로 나가지 않도록 최대 높이 제한
    max_overlay_height = WINDOW_HEIGHT - 80
    overlay_height = min(overlay_height, max_overlay_height)

    overlay = pygame.Surface((WINDOW_WIDTH - 40, overlay_height), pygame.SRCALPHA)
    overlay.fill((*INFO_BG_COLOR, INFO_BG_ALPHA))
    screen.blit(overlay, (20, 60))

    # --- 텍스트 출력 (섹션 제목은 볼드, 스크롤 오프셋 반영) ---
    y = 60 + padding_top_bottom + scroll_offset
    for line in info_lines:
        # [섹션 제목] 라인은 볼드 처리
        if line.startswith("[") and line.endswith("]"):
            font.set_bold(True)
        else:
            font.set_bold(False)

        surf = font.render(line, True, HUD_TEXT_COLOR)
        screen.blit(surf, (30, y))
        y += surf.get_height() + 2

    font.set_bold(False)


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

    # --- 배경 높이 자동 계산 ---
    line_height = font.get_linesize()
    total_text_height = line_height * len(settings_lines)
    padding_top_bottom = 20

    overlay_height = total_text_height + padding_top_bottom * 2
    max_overlay_height = WINDOW_HEIGHT - 80
    overlay_height = min(overlay_height, max_overlay_height)

    overlay = pygame.Surface((WINDOW_WIDTH - 40, overlay_height), pygame.SRCALPHA)
    overlay.fill((*INFO_BG_COLOR, INFO_BG_ALPHA))
    screen.blit(overlay, (20, 60))

    # --- 텍스트 출력 (헤더 볼드, 선택 항목 표시) ---
    y = 60 + padding_top_bottom
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
        screen.blit(surf, (30, y))
        y += surf.get_height() + 2

    font.set_bold(False)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("나만의 물리 엔진 - 허수아비 베기")
    clock = pygame.time.Clock()
    font = create_font()

    # 시스템 마우스 커서 숨기고, 우리가 그리는 검 모양만 보이게
    pygame.mouse.set_visible(False)

    scarecrow = Scarecrow()

    start_pos = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 100)

    # 질량들
    sword_mass = 1.5       # 기본 롱소드 질량
    mouse_mass = 0.5       # 기본 마우스(손) 질량, 적당히 가정

    sword = SwordController(sword_mass, start_pos)

    # 절단 에너지 파라미터 (설정창에서 조절 가능)
    e_init = E_INIT_DEFAULT
    energy_per_len = ENERGY_PER_LENGTH_DEFAULT

    # 슬래시 기록 상태
    attack_buttons_down = set()
    slash_recording = False
    slash_points = []
    slash_max_energy = 0.0

    prev_mouse_pos = pygame.Vector2(start_pos)

    # 마지막 슬래시 결과 (HUD 표시용)
    last_slash_energy = 0.0
    last_required_energy = 0.0
    last_cut_ratio = 0.0

    # UI 상태
    show_info = False
    show_settings = False
    # 0: sword_mass, 1: mouse_mass, 2: e_init, 3: energy_per_len
    settings_index = 0

    # 설명창 스크롤 상태
    info_scroll_offset = 0

    # 설정값 직접 입력 모드 상태
    settings_input_mode = False
    settings_input_value = ""

    # --- 새로 추가: 시작 안내 오버레이 상태 ---
    show_start_tip = True  # True일 때만 "I키를 눌러..." 문구와 일시정지

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # --- 이벤트 처리 ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                # ESC는 언제나 종료
                if event.key == pygame.K_ESCAPE:
                    running = False
                    continue

                # 시작 안내가 떠 있을 때: 첫 키 입력으로 시작
                if show_start_tip:
                    show_start_tip = False
                    # 만약 첫 키가 I라면, 바로 설명창도 열어줌
                    if event.key == pygame.K_i:
                        show_info = True
                    # 시작 안내 상태에서는 다른 키 처리는 하지 않고 다음 이벤트로
                    continue

                # 여기부터는 실제 게임 진행 중일 때의 키 처리
                if event.key == pygame.K_r:
                    scarecrow.reset()
                    last_slash_energy = 0.0
                    last_required_energy = 0.0
                    last_cut_ratio = 0.0

                elif event.key == pygame.K_i:
                    show_info = not show_info
                    if show_info:
                        show_settings = False
                        settings_input_mode = False
                        settings_input_value = ""
                        info_scroll_offset = 0  # 설명창 열 때 맨 위로 이동

                elif event.key == pygame.K_o:
                    show_settings = not show_settings
                    if show_settings:
                        show_info = False
                        # 설정창을 여는 순간 진행 중인 슬래시는 취소
                        slash_recording = False
                        attack_buttons_down.clear()
                    else:
                        settings_input_mode = False
                        settings_input_value = ""

                # 설정창이 켜져 있을 때의 키 입력
                elif show_settings and settings_input_mode:
                    # 숫자 직접 입력 모드
                    if event.key == pygame.K_RETURN:
                        # 입력 확정
                        if settings_input_value.strip() != "":
                            try:
                                v = float(settings_input_value)
                                if settings_index == 0:
                                    sword_mass = clamp(v, 0.5, 4.0)
                                    sword.set_mass(sword_mass)
                                elif settings_index == 1:
                                    mouse_mass = clamp(v, 0.1, 5.0)
                                elif settings_index == 2:
                                    e_init = max(0.0, v)
                                elif settings_index == 3:
                                    energy_per_len = max(0.0, v)
                            except ValueError:
                                # 잘못된 숫자는 무시하고 원래 값 유지
                                pass
                        settings_input_mode = False
                        settings_input_value = ""

                    elif event.key == pygame.K_ESCAPE:
                        # 입력 취소 (게임 전체 종료는 위에서 이미 처리)
                        settings_input_mode = False
                        settings_input_value = ""

                    elif event.key == pygame.K_BACKSPACE:
                        settings_input_value = settings_input_value[:-1]

                    else:
                        # 숫자/소수점/음수 기호 입력 허용
                        if event.unicode in "0123456789.-":
                            settings_input_value += event.unicode

                elif show_settings:
                    # 일반 설정 조정 모드
                    if event.key == pygame.K_UP:
                        settings_index = (settings_index - 1) % 4
                    elif event.key == pygame.K_DOWN:
                        settings_index = (settings_index + 1) % 4
                    elif event.key == pygame.K_LEFT:
                        if settings_index == 0:
                            sword_mass = clamp(sword_mass - 0.1, 0.5, 4.0)
                            sword.set_mass(sword_mass)
                        elif settings_index == 1:
                            mouse_mass = clamp(mouse_mass - 0.1, 0.1, 5.0)
                        elif settings_index == 2:
                            e_init = max(0.0, e_init - 0.5)
                        elif settings_index == 3:
                            energy_per_len = max(0.0, energy_per_len - 0.005)
                    elif event.key == pygame.K_RIGHT:
                        if settings_index == 0:
                            sword_mass = clamp(sword_mass + 0.1, 0.5, 4.0)
                            sword.set_mass(sword_mass)
                        elif settings_index == 1:
                            mouse_mass = clamp(mouse_mass + 0.1, 0.1, 5.0)
                        elif settings_index == 2:
                            e_init = e_init + 0.5
                        elif settings_index == 3:
                            energy_per_len = energy_per_len + 0.005
                    elif event.key == pygame.K_RETURN:
                        # 선택된 항목 직접 값 입력 모드로 전환
                        settings_input_mode = True
                        # 현재 값을 기본값으로 채워 넣기
                        if settings_index == 0:
                            current = sword_mass
                        elif settings_index == 1:
                            current = mouse_mass
                        elif settings_index == 2:
                            current = e_init
                        else:
                            current = energy_per_len
                        settings_input_value = f"{current:.3f}"

                # 설명창이 켜져 있을 때: 스크롤 조작
                elif show_info:
                    scroll_step = font.get_linesize() * 3
                    min_off, max_off = get_info_scroll_limits(font)

                    if event.key == pygame.K_UP:
                        info_scroll_offset = min(info_scroll_offset + scroll_step, max_off)
                    elif event.key == pygame.K_DOWN:
                        info_scroll_offset = max(info_scroll_offset - scroll_step, min_off)
                    elif event.key == pygame.K_PAGEUP:
                        info_scroll_offset = min(info_scroll_offset + scroll_step * 3, max_off)
                    elif event.key == pygame.K_PAGEDOWN:
                        info_scroll_offset = max(info_scroll_offset - scroll_step * 3, min_off)

            # 마우스 휠로 설명창 스크롤
            if event.type == pygame.MOUSEWHEEL and show_info:
                scroll_step = font.get_linesize() * 3
                min_off, max_off = get_info_scroll_limits(font)
                info_scroll_offset += event.y * scroll_step
                if info_scroll_offset > max_off:
                    info_scroll_offset = max_off
                if info_scroll_offset < min_off:
                    info_scroll_offset = min_off

            # 마우스 이벤트 처리
            # 설정창이 켜져 있거나 시작 안내가 떠 있을 때는 새 슬래시를 시작하지 않는다
            if (not show_start_tip) and (not show_settings):
                if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                    if not attack_buttons_down:
                        # 새로운 슬래시 시작
                        slash_recording = True
                        slash_points = []
                        slash_max_energy = 0.0
                        # 슬래시 시작 시점의 마우스 위치 기준으로 속도 계산
                        prev_mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
                    attack_buttons_down.add(event.button)

                elif event.type == pygame.MOUSEBUTTONUP and event.button in (1, 3):
                    if event.button in attack_buttons_down:
                        attack_buttons_down.remove(event.button)

                    # 모든 공격 버튼이 떼어진 순간 → 슬래시 종료
                    if slash_recording and not attack_buttons_down:
                        slash_recording = False

                        if len(slash_points) >= 2:
                            (
                                L_inside,
                                E_required_full,
                                cut_ratio,
                                did_full_cut,
                            ) = scarecrow.apply_slash(
                                slash_points, slash_max_energy, e_init, energy_per_len
                            )
                            last_slash_energy = slash_max_energy
                            last_required_energy = E_required_full
                            last_cut_ratio = cut_ratio
                        else:
                            last_slash_energy = 0.0
                            last_required_energy = 0.0
                            last_cut_ratio = 0.0

        # --- 업데이트 ---
        mouse_pos = pygame.mouse.get_pos()
        tip = sword.update(mouse_pos, dt)

        # 슬래시 기록 중일 때만 에너지/경로 기록
        if slash_recording:
            # 마우스(손) 속도 기준으로 에너지 계산
            speed_mouse = compute_speed(prev_mouse_pos, mouse_pos, dt)
            energy = kinetic_energy(mouse_mass, speed_mouse)

            slash_points.append((float(tip.x), float(tip.y)))
            if energy > slash_max_energy:
                slash_max_energy = energy

            prev_mouse_pos = pygame.Vector2(mouse_pos)

        # --- 그리기 ---
        screen.fill(BACKGROUND_COLOR)

        scarecrow.draw(screen)

        # 현재 슬래시 경로 (녹화 중일 때만 표시)
        if slash_recording and len(slash_points) > 1:
            pygame.draw.lines(
                screen,
                (180, 180, 255),
                False,
                slash_points,
                2,
            )

        sword.draw(screen)

        draw_hud(
            screen,
            font,
            sword_mass,
            mouse_mass,
            last_slash_energy,
            last_required_energy,
            last_cut_ratio,
        )

        if show_info:
            draw_info_overlay(screen, font, info_scroll_offset)
        if show_settings:
            draw_settings_overlay(
                screen,
                font,
                settings_index,
                sword_mass,
                mouse_mass,
                e_init,
                energy_per_len,
                settings_input_mode,
                settings_input_value,
            )

        # 시작 안내는 가장 위에 덮어서, 게임이 일시정지된 느낌을 줌
        if show_start_tip:
            draw_start_tip_overlay(screen, font)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
