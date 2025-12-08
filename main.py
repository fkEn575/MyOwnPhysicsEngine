
import pygame

from config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    FPS,
    BACKGROUND_COLOR,
    HUD_TEXT_COLOR,
    E_INIT_DEFAULT,
    ENERGY_PER_LENGTH_DEFAULT,
)
from physics import compute_speed, kinetic_energy
from entities import SwordController, Scarecrow


def clamp(value, vmin, vmax):
    return max(vmin, min(vmax, value))


def create_font():
    # 한글 지원 폰트가 있으면 사용, 없으면 기본 폰트
    try:
        return pygame.font.SysFont("malgungothic", 18)
    except Exception:
        return pygame.font.SysFont(None, 18)


def draw_hud(
    screen,
    font,
    sword_mass,
    last_slash_energy,
    last_required_energy,
    last_cut_ratio,
):
    lines = [
        f"검 무게: {sword_mass:.2f} kg   ([ / ] 키로 변경)",
        f"마지막 베기 에너지: {last_slash_energy:.2f}",
        f"완전 절단 필요 에너지(해당 경로 기준): {last_required_energy:.2f}",
        f"이번 베기 강도: {last_cut_ratio * 100.0:.1f} %",
        "좌/우 클릭: 베기, R: 허수아비 리셋, I: 정보창, O: 설정창",
    ]
    y = 10
    for text in lines:
        surf = font.render(text, True, HUD_TEXT_COLOR)
        screen.blit(surf, (10, y))
        y += surf.get_height() + 2


def draw_info_overlay(screen, font):
    """I 키로 토글되는 물리 설명창."""
    info_lines = [
        "[물리 엔진 설명]",
        "· 좌/우 클릭을 누른 동안의 마우스 움직임이 한 번의 '베기'입니다.",
        "· 검은 질량이 있어서 마우스를 바로 따라가지 못하고,",
        "  무거울수록 더 둔하게 움직입니다.",
        "· 검 팁의 속도로 운동에너지 E = 1/2 m v^2 를 계산합니다.",
        "· 한 번의 베기에서 가장 큰 E를 '검의 에너지'로 사용합니다.",
        "· 허수아비 안에서 검이 지나간 실제 길이를 L_inside 라고 할 때,",
        "  이 경로 전체를 완전히 자르는 데 필요한 에너지는",
        "  E_required = E_init + k * L_inside 로 계산합니다.",
        "· HUD의 % 값은 E / E_required 를 0~100%로 환산한 값입니다.",
        "",
        "I 키를 다시 누르면 이 창이 닫힙니다.",
    ]
    # 반투명 배경
    overlay = pygame.Surface((WINDOW_WIDTH - 40, 260), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (20, 60))

    y = 70
    for line in info_lines:
        surf = font.render(line, True, HUD_TEXT_COLOR)
        screen.blit(surf, (30, y))
        y += surf.get_height() + 2


def draw_settings_overlay(
    screen,
    font,
    selected_index,
    sword_mass,
    e_init,
    energy_per_len,
    control_mult,
):
    """O 키로 토글되는 설정창 (이 창이 켜져 있을 때는 게임이 멈춤)."""
    settings_lines = [
        "[설정]",
        "",
        f"1. 검 질량 (kg): {sword_mass:.2f}",
        f"2. E_init (처음 베이기 시작하는 에너지): {e_init:.2f}",
        f"3. k (길이 1px 당 추가 에너지): {energy_per_len:.3f}",
        f"4. 컨트롤 민감도: {control_mult:.2f}",
        "",
        "↑ / ↓ : 항목 선택",
        "← / → : 값 조절",
        "O 키: 설정창 닫기",
    ]

    overlay = pygame.Surface((WINDOW_WIDTH - 40, 260), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (20, 60))

    y = 70
    for i, line in enumerate(settings_lines):
        # 항목 라인(3~6번째 줄)에만 선택 표시
        if 2 <= i <= 5:
            idx = i - 2
            prefix = "> " if idx == selected_index else "  "
            text = prefix + line
        else:
            text = line

        surf = font.render(text, True, HUD_TEXT_COLOR)
        screen.blit(surf, (30, y))
        y += surf.get_height() + 2


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
    sword_mass = 1.5
    sword = SwordController(sword_mass, start_pos)

    # 절단 에너지 파라미터 (설정창에서 조절 가능)
    e_init = E_INIT_DEFAULT
    energy_per_len = ENERGY_PER_LENGTH_DEFAULT
    control_mult = 1.0
    sword.set_control_multiplier(control_mult)

    # 슬래시 기록 상태
    attack_buttons_down = set()
    slash_recording = False
    slash_points = []
    slash_max_energy = 0.0
    prev_tip_pos = pygame.Vector2(start_pos)

    # 마지막 슬래시 결과 (HUD 표시용)
    last_slash_energy = 0.0
    last_required_energy = 0.0
    last_cut_ratio = 0.0

    # UI 상태
    show_info = False
    show_settings = False
    settings_index = 0  # 0: mass, 1: e_init, 2: energy_per_len, 3: control_mult

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # --- 이벤트 처리 ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    scarecrow.reset()
                    last_slash_energy = 0.0
                    last_required_energy = 0.0
                    last_cut_ratio = 0.0
                elif event.key == pygame.K_i:
                    show_info = not show_info
                    if show_info:
                        show_settings = False
                elif event.key == pygame.K_o:
                    show_settings = not show_settings
                    if show_settings:
                        show_info = False
                        # 설정창을 여는 순간 진행 중인 슬래시는 취소
                        slash_recording = False
                        attack_buttons_down.clear()
                else:
                    # 설정창이 켜져 있을 때의 키 입력 (파라미터 조정)
                    if show_settings:
                        if event.key == pygame.K_UP:
                            settings_index = (settings_index - 1) % 4
                        elif event.key == pygame.K_DOWN:
                            settings_index = (settings_index + 1) % 4
                        elif event.key == pygame.K_LEFT:
                            if settings_index == 0:
                                sword_mass = clamp(sword_mass - 0.1, 0.5, 4.0)
                                sword.set_mass(sword_mass)
                            elif settings_index == 1:
                                e_init = max(0.0, e_init - 0.5)
                            elif settings_index == 2:
                                energy_per_len = max(0.0, energy_per_len - 0.005)
                            elif settings_index == 3:
                                control_mult = max(0.1, control_mult - 0.1)
                                sword.set_control_multiplier(control_mult)
                        elif event.key == pygame.K_RIGHT:
                            if settings_index == 0:
                                sword_mass = clamp(sword_mass + 0.1, 0.5, 4.0)
                                sword.set_mass(sword_mass)
                            elif settings_index == 1:
                                e_init = e_init + 0.5
                            elif settings_index == 2:
                                energy_per_len = energy_per_len + 0.005
                            elif settings_index == 3:
                                control_mult = control_mult + 0.1
                                sword.set_control_multiplier(control_mult)
                    else:
                        # 설정창이 꺼져 있을 때만 무게를 직접 조절
                        if event.key == pygame.K_LEFTBRACKET:  # '['
                            sword_mass = clamp(sword_mass - 0.25, 0.5, 4.0)
                            sword.set_mass(sword_mass)
                        elif event.key == pygame.K_RIGHTBRACKET:  # ']'
                            sword_mass = clamp(sword_mass + 0.25, 0.5, 4.0)
                            sword.set_mass(sword_mass)

            # 설정창이 켜져 있을 때는 새 슬래시를 시작하지 않는다
            if not show_settings:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                    if not attack_buttons_down:
                        # 새로운 슬래시 시작
                        slash_recording = True
                        slash_points = []
                        slash_max_energy = 0.0
                        prev_tip_pos = pygame.Vector2(sword.pos)
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
            speed = compute_speed(prev_tip_pos, tip, dt)
            energy = kinetic_energy(sword_mass, speed)

            slash_points.append((float(tip.x), float(tip.y)))
            if energy > slash_max_energy:
                slash_max_energy = energy

        prev_tip_pos = tip.copy()

        # --- 그리기 ---
        screen.fill(BACKGROUND_COLOR)

        scarecrow.draw(screen)

        # 현재 슬래시 경로 (녹화 중일 때만 표시)
        if slash_recording and len(slash_points) > 1:
            pygame.draw.lines(
                screen, (180, 180, 255), False, slash_points, 2
            )

        sword.draw(screen)

        draw_hud(
            screen,
            font,
            sword_mass,
            last_slash_energy,
            last_required_energy,
            last_cut_ratio,
        )

        if show_info:
            draw_info_overlay(screen, font)
        if show_settings:
            draw_settings_overlay(
                screen,
                font,
                settings_index,
                sword_mass,
                e_init,
                energy_per_len,
                control_mult,
            )

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
