
import pygame
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS,
    BACKGROUND_COLOR, HUD_TEXT_COLOR,
    SWORD_BASE_MASS, SWORD_MIN_MASS, SWORD_MAX_MASS
)
from physics import compute_speed, compute_impact, classify_cut
from entities import Scarecrow, SwordTrail, SwordController

def clamp(v, vmin, vmax):
    return max(vmin, min(vmax, v))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("나만의 물리 엔진 - 허수아비 베기")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("malgungothic", 18)

    scarecrow = Scarecrow()

    # 검 컨트롤러 초기화 (처음에는 화면 중앙에서 시작)
    start_pos = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
    sword_mass = SWORD_BASE_MASS
    sword = SwordController(sword_mass, start_pos)

    trail = SwordTrail()

    slash_active = False
    prev_pos = start_pos
    last_depth = "none"

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # 초 단위

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # 마우스 버튼
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 왼쪽 버튼으로 휘두르기 시작
                    slash_active = True
                    trail.clear()
                    # 새 슬래시 시작점
                    prev_pos = sword.pos.xy

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and slash_active:
                    # 슬래시 종료 → 허수아비에 적용
                    scarecrow.apply_slash(trail.points, trail.depth)
                    last_depth = trail.depth
                    slash_active = False
                    trail.clear()

            # 키보드 입력
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    scarecrow.reset()
                    last_depth = "none"
                # 검 무게 조절
                if event.key == pygame.K_LEFTBRACKET:   # '['
                    sword_mass = clamp(sword_mass - 0.25, SWORD_MIN_MASS, SWORD_MAX_MASS)
                    sword.set_mass(sword_mass)
                if event.key == pygame.K_RIGHTBRACKET:  # ']'
                    sword_mass = clamp(sword_mass + 0.25, SWORD_MIN_MASS, SWORD_MAX_MASS)
                    sword.set_mass(sword_mass)

        # --- 업데이트 ---
        mouse_pos = pygame.mouse.get_pos()
        sword_pos = sword.update(mouse_pos, dt)  # 질량에 따른 '검 팁' 위치

        if slash_active:
            # 이번 프레임의 속도/임팩트 계산
            speed = compute_speed(prev_pos, sword_pos, dt)
            impact = compute_impact(sword_mass, speed)
            depth = classify_cut(impact)
            trail.add_point(tuple(sword_pos), impact, classify_cut)
            prev_pos = sword_pos.xy

        # --- 그리기 ---
        screen.fill(BACKGROUND_COLOR)

        scarecrow.draw(screen)

        # 현재 진행 중인 슬래시 경로도 화면에 임시로 표시
        if slash_active and len(trail.points) > 1:
            pygame.draw.lines(screen, (150, 150, 255), False, trail.points, 1)

        sword.draw(screen)

        # HUD 텍스트
        draw_hud(screen, font, sword_mass, last_depth)

        pygame.display.flip()

    pygame.quit()


def draw_hud(screen, font, sword_mass, last_depth):
    lines = [
        f"검 무게: {sword_mass:.2f} kg   ([ / ] 키로 변경)",
        f"마우스 왼쪽 버튼 드래그로 베기",
        "R 키: 허수아비 리셋",
        f"마지막 베임 정도: {depth_korean(last_depth)}",
    ]
    x, y = 10, 10
    for line in lines:
        text_surf = font.render(line, True, HUD_TEXT_COLOR)
        screen.blit(text_surf, (x, y))
        y += text_surf.get_height() + 4


def depth_korean(depth):
    if depth == "none":
        return "안 베임"
    elif depth == "shallow":
        return "얕게 베임"
    elif depth == "medium":
        return "중간 정도로 베임"
    elif depth == "deep":
        return "깊게 베임"
    return depth


if __name__ == "__main__":
    main()
