
import pygame
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS,
    BACKGROUND_COLOR, HUD_TEXT_COLOR,
    SWORD_BASE_MASS, SWORD_MIN_MASS, SWORD_MAX_MASS,
    SLASH_SPEED_THRESHOLD,
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

    # 시스템 마우스 커서 숨기기 (검 모양으로 직접 그림)
    pygame.mouse.set_visible(False)

    font = pygame.font.SysFont("malgungothic", 18)

    scarecrow = Scarecrow()

    # 검 컨트롤러 초기화 (처음에는 화면 중앙에서 시작)
    start_pos = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
    sword_mass = SWORD_BASE_MASS
    sword = SwordController(sword_mass, start_pos)

    trail = SwordTrail()
    last_trail_points = []  # 마지막으로 완성된 슬래시 경로

    slash_active = False
    prev_pos = pygame.Vector2(start_pos)
    last_depth = "none"

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # 초 단위

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    scarecrow.reset()
                    last_depth = "none"
                if event.key == pygame.K_LEFTBRACKET:   # '['
                    sword_mass = clamp(sword_mass - 0.25, SWORD_MIN_MASS, SWORD_MAX_MASS)
                    sword.set_mass(sword_mass)
                if event.key == pygame.K_RIGHTBRACKET:  # ']'
                    sword_mass = clamp(sword_mass + 0.25, SWORD_MIN_MASS, SWORD_MAX_MASS)
                    sword.set_mass(sword_mass)

        # --- 업데이트 ---
        mouse_pos = pygame.mouse.get_pos()
        sword_pos = sword.update(mouse_pos, dt)  # 질량에 따른 '검 팁' 위치

        # 이번 프레임의 속도 계산 (검 팁 기준)
        speed = compute_speed(prev_pos, sword_pos, dt)

        if speed > SLASH_SPEED_THRESHOLD:
            # 충분히 빠르게 움직이는 중 → 슬래시 진행 상태
            if not slash_active:
                slash_active = True
                trail.clear()  # 새 슬래시 시작

            impact = compute_impact(sword_mass, speed)
            trail.add_point(tuple(sword_pos), impact, classify_cut)
        else:
            # 느리게 움직이거나 멈춤 → 슬래시가 진행 중이었다면 종료
            if slash_active and len(trail.points) > 1:
                scarecrow.apply_slash(trail.points, trail.depth)
                last_depth = trail.depth
                last_trail_points = list(trail.points)  # 마지막 경로 저장
            slash_active = False

        prev_pos = sword_pos.xy

        # --- 그리기 ---
        screen.fill(BACKGROUND_COLOR)

        scarecrow.draw(screen)

        # 마지막으로 완성된 슬래시 경로 (항상 남겨둠, 다음 슬래시가 생기면 덮어씀)
        if len(last_trail_points) > 1:
            pygame.draw.lines(screen, (150, 150, 255), False, last_trail_points, 1)

        # 현재 진행 중인 슬래시 경로는 조금 더 진하게 표시
        if slash_active and len(trail.points) > 1:
            pygame.draw.lines(screen, (200, 200, 255), False, trail.points, 2)

        sword.draw(screen)

        draw_hud(screen, font, sword_mass, last_depth)

        pygame.display.flip()

    pygame.quit()


def draw_hud(screen, font, sword_mass, last_depth):
    lines = [
        f"검 무게: {sword_mass:.2f} kg   ([ / ] 키로 변경)",
        "마우스를 빠르게 움직이면 베기",
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
