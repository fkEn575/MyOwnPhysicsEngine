
import pygame

from config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    FPS,
    BACKGROUND_COLOR,
    E_INIT_DEFAULT,
    ENERGY_PER_LENGTH_DEFAULT,
)
from physics import compute_speed, kinetic_energy
from entities import SwordController, Scarecrow
from ui import (
    create_font,
    draw_hud,
    draw_start_tip_overlay,
    draw_info_overlay,
    draw_settings_overlay,
)
from input import UIState, SlashState, handle_events


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("나만의 물리 엔진 - 허수아비 베기")
    clock = pygame.time.Clock()
    font = create_font()

    # 시스템 마우스 커서 숨기고, 우리가 그리는 검 모양만 보이게
    pygame.mouse.set_visible(False)

    # --- 검 이미지 로드 ---
    sword_image = pygame.image.load("sword.png").convert_alpha()
    # 필요하면 크기 살짝 조정 (너무 크면 줄이기)
    sword_image = pygame.transform.smoothscale(sword_image, (64, 64))

    scarecrow = Scarecrow()

    start_pos = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 100)

    # 질량들
    sword_mass = 1.5       # 기본 롱소드 질량
    mouse_mass = 0.5       # 기본 마우스(손) 질량, 적당히 가정

    sword = SwordController(sword_mass, start_pos, sword_image)

    # 절단 에너지 파라미터 (설정창에서 조절 가능)
    e_init = E_INIT_DEFAULT
    energy_per_len = ENERGY_PER_LENGTH_DEFAULT

    # 상태 객체들
    ui_state = UIState()
    slash_state = SlashState(start_pos)

    # 마지막 슬래시 결과 (HUD 표시용)
    last_slash_energy = 0.0
    last_required_energy = 0.0
    last_cut_ratio = 0.0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # --- 이벤트 처리 ---
        events = pygame.event.get()
        (
            quit_game,
            sword_mass,
            mouse_mass,
            e_init,
            energy_per_len,
            reset_stats,
            slash_result,
        ) = handle_events(
            events,
            ui_state,
            slash_state,
            sword,
            scarecrow,
            sword_mass,
            mouse_mass,
            e_init,
            energy_per_len,
            font,
        )

        if quit_game:
            running = False
            break

        if reset_stats:
            last_slash_energy = 0.0
            last_required_energy = 0.0
            last_cut_ratio = 0.0

        if slash_result is not None:
            (
                L_inside,
                E_required_full,
                cut_ratio,
                did_full_cut,
                slash_energy,
            ) = slash_result
            last_slash_energy = slash_energy
            last_required_energy = E_required_full
            last_cut_ratio = cut_ratio

        # --- 업데이트 ---
        mouse_pos = pygame.mouse.get_pos()
        tip = sword.update(mouse_pos, dt)

        # 슬래시 기록 중일 때만 에너지/경로 기록
        if slash_state.slash_recording:
            # 마우스(손) 속도 기준으로 에너지 계산
            speed_mouse = compute_speed(
                slash_state.prev_mouse_pos, mouse_pos, dt
            )
            energy = kinetic_energy(mouse_mass, speed_mouse)

            slash_state.slash_points.append((float(tip.x), float(tip.y)))
            if energy > slash_state.slash_max_energy:
                slash_state.slash_max_energy = energy

            slash_state.prev_mouse_pos = pygame.Vector2(mouse_pos)

        # --- 그리기 ---
        screen.fill(BACKGROUND_COLOR)

        scarecrow.draw(screen)

        # 현재 슬래시 경로 (녹화 중일 때만 표시)
        if slash_state.slash_recording and len(slash_state.slash_points) > 1:
            pygame.draw.lines(
                screen,
                (180, 180, 255),
                False,
                slash_state.slash_points,
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

        if ui_state.show_info:
            draw_info_overlay(screen, font, ui_state.info_scroll_offset)
        if ui_state.show_settings:
            draw_settings_overlay(
                screen,
                font,
                ui_state.settings_index,
                sword_mass,
                mouse_mass,
                e_init,
                energy_per_len,
                ui_state.settings_input_mode,
                ui_state.settings_input_value,
            )

        if ui_state.show_start_tip:
            draw_start_tip_overlay(screen, font)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
