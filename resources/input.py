
import pygame

from .config import SWORD_MIN_MASS, SWORD_MAX_MASS
from .ui import get_info_scroll_limits


def clamp(value, vmin, vmax):
    return max(vmin, min(vmax, value))


class UIState:
    """I/O에 의해 바뀌는 UI 관련 상태들을 모아둔 클래스."""
    def __init__(self):
        self.show_info = False
        self.show_settings = False
        self.settings_index = 0
        self.settings_input_mode = False
        self.settings_input_value = ""
        self.info_scroll_offset = 0
        self.show_start_tip = True  # 처음 안내 오버레이 표시 여부


class SlashState:
    """슬래시(베기) 입력 상태를 관리하는 클래스."""
    def __init__(self, start_pos):
        self.attack_buttons_down = set()     # 현재 눌려 있는 공격 버튼들 (1, 3)
        self.slash_recording = False         # 현재 슬래시를 기록 중인지
        self.slash_points = []               # 검 팁이 지나간 경로
        self.slash_max_energy = 0.0          # 이번 슬래시 동안의 최대 에너지
        self.prev_mouse_pos = pygame.Vector2(start_pos)  # 속도 계산용 이전 마우스 위치


def handle_events(
    events,
    ui_state: UIState,
    slash_state: SlashState,
    sword,
    scarecrow,
    sword_mass: float,
    mouse_mass: float,
    e_init: float,
    energy_per_len: float,
    font,
):
    """
    pygame 이벤트들을 처리해서:
      - ui_state / slash_state 를 갱신하고
      - 검/허수아비/절단 파라미터를 조정하고
      - 게임 종료 / 리셋 / 슬래시 결과 등의 신호를 반환한다.

    반환값:
      quit_game: bool
      sword_mass: float (변경된 값)
      mouse_mass: float (변경된 값)
      e_init: float (변경된 값)
      energy_per_len: float (변경된 값)
      reset_stats: bool (허수아비/베기 통계를 리셋해야 하는지)
      slash_result: None 또는 (L_inside, E_required_full, cut_ratio, did_full_cut, slash_energy)
    """
    quit_game = False
    reset_stats = False
    slash_result = None

    for event in events:
        # 창 닫기(X 버튼)
        if event.type == pygame.QUIT:
            quit_game = True
            continue

        # --- 키보드 입력 ---
        if event.type == pygame.KEYDOWN:
            # ESC: 언제나 종료
            if event.key == pygame.K_ESCAPE:
                quit_game = True
                continue

            # 시작 안내 화면이 떠 있을 때: 첫 키 입력으로 게임 시작
            if ui_state.show_start_tip:
                ui_state.show_start_tip = False
                # 첫 키가 I면 바로 설명창 열기
                if event.key == pygame.K_i:
                    ui_state.show_info = True
                # 시작 안내 상태에서는 다른 처리 없이 다음 이벤트로
                continue

            # 여기부터는 실제 게임 진행 중일 때의 키 처리
            if event.key == pygame.K_r:
                # 허수아비 리셋
                scarecrow.reset()
                # 진행 중인 슬래시도 취소
                slash_state.slash_recording = False
                slash_state.attack_buttons_down.clear()
                slash_state.slash_points.clear()
                slash_state.slash_max_energy = 0.0
                reset_stats = True

            elif event.key == pygame.K_i:
                ui_state.show_info = not ui_state.show_info
                if ui_state.show_info:
                    ui_state.show_settings = False
                    ui_state.settings_input_mode = False
                    ui_state.settings_input_value = ""
                    ui_state.info_scroll_offset = 0  # 설명창 열 때 맨 위로

            elif event.key == pygame.K_o:
                ui_state.show_settings = not ui_state.show_settings
                if ui_state.show_settings:
                    ui_state.show_info = False
                    # 설정창을 여는 순간 진행 중인 슬래시는 취소
                    slash_state.slash_recording = False
                    slash_state.attack_buttons_down.clear()
                else:
                    ui_state.settings_input_mode = False
                    ui_state.settings_input_value = ""

            # 설정창이 켜져 있고 직접 입력 모드일 때의 키 처리
            elif ui_state.show_settings and ui_state.settings_input_mode:
                if event.key == pygame.K_RETURN:
                    # 입력 확정
                    if ui_state.settings_input_value.strip() != "":
                        try:
                            v = float(ui_state.settings_input_value)
                            if ui_state.settings_index == 0:
                                # 검 질량
                                sword_mass = clamp(v, SWORD_MIN_MASS, SWORD_MAX_MASS)
                                sword.set_mass(sword_mass)
                            elif ui_state.settings_index == 1:
                                # 마우스 질량
                                mouse_mass = clamp(v, 0.1, 5.0)
                            elif ui_state.settings_index == 2:
                                # 표면 강도
                                e_init = max(0.0, v)
                            elif ui_state.settings_index == 3:
                                # 절단 저항
                                energy_per_len = max(0.0, v)
                        except ValueError:
                            # 잘못된 숫자는 무시
                            pass
                    ui_state.settings_input_mode = False
                    ui_state.settings_input_value = ""

                elif event.key == pygame.K_ESCAPE:
                    # 입력 취소
                    ui_state.settings_input_mode = False
                    ui_state.settings_input_value = ""

                elif event.key == pygame.K_BACKSPACE:
                    ui_state.settings_input_value = ui_state.settings_input_value[:-1]

                else:
                    # 숫자/소수점/음수 기호 입력 허용
                    if event.unicode in "0123456789.-":
                        ui_state.settings_input_value += event.unicode

            # 설정창이 켜져 있고, 일반 설정 조정 모드
            elif ui_state.show_settings:
                if event.key == pygame.K_UP:
                    ui_state.settings_index = (ui_state.settings_index - 1) % 4
                elif event.key == pygame.K_DOWN:
                    ui_state.settings_index = (ui_state.settings_index + 1) % 4
                elif event.key == pygame.K_LEFT:
                    if ui_state.settings_index == 0:
                        sword_mass = clamp(
                            sword_mass - 0.1, SWORD_MIN_MASS, SWORD_MAX_MASS
                        )
                        sword.set_mass(sword_mass)
                    elif ui_state.settings_index == 1:
                        mouse_mass = clamp(mouse_mass - 0.1, 0.1, 5.0)
                    elif ui_state.settings_index == 2:
                        e_init = max(0.0, e_init - 0.5)
                    elif ui_state.settings_index == 3:
                        energy_per_len = max(0.0, energy_per_len - 0.005)
                elif event.key == pygame.K_RIGHT:
                    if ui_state.settings_index == 0:
                        sword_mass = clamp(
                            sword_mass + 0.1, SWORD_MIN_MASS, SWORD_MAX_MASS
                        )
                        sword.set_mass(sword_mass)
                    elif ui_state.settings_index == 1:
                        mouse_mass = clamp(mouse_mass + 0.1, 0.1, 5.0)
                    elif ui_state.settings_index == 2:
                        e_init = e_init + 0.5
                    elif ui_state.settings_index == 3:
                        energy_per_len = energy_per_len + 0.005
                elif event.key == pygame.K_RETURN:
                    # 선택된 항목 직접 값 입력 모드로 전환
                    ui_state.settings_input_mode = True
                    if ui_state.settings_index == 0:
                        current = sword_mass
                    elif ui_state.settings_index == 1:
                        current = mouse_mass
                    elif ui_state.settings_index == 2:
                        current = e_init
                    else:
                        current = energy_per_len
                    ui_state.settings_input_value = f"{current:.3f}"

            # 설명창이 켜져 있을 때: 키보드로 스크롤
            elif ui_state.show_info:
                scroll_step = font.get_linesize() * 3
                min_off, max_off = get_info_scroll_limits(font)

                if event.key == pygame.K_UP:
                    ui_state.info_scroll_offset = min(
                        ui_state.info_scroll_offset + scroll_step, max_off
                    )
                elif event.key == pygame.K_DOWN:
                    ui_state.info_scroll_offset = max(
                        ui_state.info_scroll_offset - scroll_step, min_off
                    )
                elif event.key == pygame.K_PAGEUP:
                    ui_state.info_scroll_offset = min(
                        ui_state.info_scroll_offset + scroll_step * 3, max_off
                    )
                elif event.key == pygame.K_PAGEDOWN:
                    ui_state.info_scroll_offset = max(
                        ui_state.info_scroll_offset - scroll_step * 3, min_off
                    )

        # 마우스 휠로 설명창 스크롤
        if event.type == pygame.MOUSEWHEEL and ui_state.show_info:
            scroll_step = font.get_linesize() * 3
            min_off, max_off = get_info_scroll_limits(font)
            ui_state.info_scroll_offset += event.y * scroll_step
            if ui_state.info_scroll_offset > max_off:
                ui_state.info_scroll_offset = max_off
            if ui_state.info_scroll_offset < min_off:
                ui_state.info_scroll_offset = min_off

        # --- 마우스 버튼(슬래시 시작/종료) ---
        # 시작 안내 또는 설정창이 켜져 있으면 슬래시는 시작하지 않음
        if (not ui_state.show_start_tip) and (not ui_state.show_settings):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                if not slash_state.attack_buttons_down:
                    # 새로운 슬래시 시작
                    slash_state.slash_recording = True
                    slash_state.slash_points = []
                    slash_state.slash_max_energy = 0.0
                    slash_state.prev_mouse_pos = pygame.Vector2(
                        pygame.mouse.get_pos()
                    )
                slash_state.attack_buttons_down.add(event.button)

            elif event.type == pygame.MOUSEBUTTONUP and event.button in (1, 3):
                if event.button in slash_state.attack_buttons_down:
                    slash_state.attack_buttons_down.remove(event.button)

                # 모든 공격 버튼이 떼어진 순간 → 슬래시 종료
                if slash_state.slash_recording and not slash_state.attack_buttons_down:
                    slash_state.slash_recording = False

                    if len(slash_state.slash_points) >= 2:
                        (
                            L_inside,
                            E_required_full,
                            cut_ratio,
                            did_full_cut,
                        ) = scarecrow.apply_slash(
                            slash_state.slash_points,
                            slash_state.slash_max_energy,
                            e_init,
                            energy_per_len,
                        )
                        slash_result = (
                            L_inside,
                            E_required_full,
                            cut_ratio,
                            did_full_cut,
                            slash_state.slash_max_energy,
                        )
                    else:
                        # 슬래시가 너무 짧았던 경우
                        slash_result = (0.0, 0.0, 0.0, False, 0.0)

    return (
        quit_game,
        sword_mass,
        mouse_mass,
        e_init,
        energy_per_len,
        reset_stats,
        slash_result,
    )
