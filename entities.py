
import pygame
from config import (
    SCARECROW_RECT, SCARECROW_COLOR, SCARECROW_OUTLINE,
    SLASH_COLOR, SLASH_SHALLOW_WIDTH, SLASH_MEDIUM_WIDTH, SLASH_DEEP_WIDTH
)
from physics import distance

class Scarecrow:
    def __init__(self):
        self.base_rect = pygame.Rect(SCARECROW_RECT)
        self.cuts = []  # 각 cut: {"points": [...], "depth": "shallow/medium/deep"}

    def reset(self):
        self.cuts.clear()

    def apply_slash(self, points, depth):
        """
        slash 경로(points)가 허수아비와 겹치면 커트로 등록.
        depth: "shallow", "medium", "deep"
        """
        if depth == "none":
            return
        if len(points) < 2:
            return

        # 허수아비 rect 안을 지나갔는지 간단 검증
        if not self._path_intersects_rect(points, self.base_rect):
            return

        self.cuts.append({
            "points": list(points),
            "depth": depth
        })

    def _path_intersects_rect(self, points, rect):
        """아주 단순하게: 경로 중 하나라도 rect 안에 들어오면 통과했다고 판단."""
        for x, y in points:
            if rect.collidepoint(x, y):
                return True
        return False

    def draw(self, surface):
        # 몸통
        pygame.draw.rect(surface, SCARECROW_COLOR, self.base_rect)
        pygame.draw.rect(surface, SCARECROW_OUTLINE, self.base_rect, 2)

        # 잘린 자국들
        for cut in self.cuts:
            pts = cut["points"]
            if len(pts) < 2:
                continue
            depth = cut["depth"]
            if depth == "shallow":
                width = SLASH_SHALLOW_WIDTH
            elif depth == "medium":
                width = SLASH_MEDIUM_WIDTH
            else:
                width = SLASH_DEEP_WIDTH
            pygame.draw.lines(surface, SLASH_COLOR, False, pts, width)


class SwordTrail:
    """
    한 번의 휘두르기(마우스 드래그)에 대한 궤적 & 그 동안의 최대 임팩트.
    """
    def __init__(self):
        self.points = []
        self.max_impact = 0.0
        self.depth = "none"

    def add_point(self, pos, impact_value, classify_fn):
        self.points.append(pos)
        if impact_value > self.max_impact:
            self.max_impact = impact_value
            self.depth = classify_fn(self.max_impact)

    def clear(self):
        self.points.clear()
        self.max_impact = 0.0
        self.depth = "none"


class SwordController:
    """
    마우스 위치를 그대로 쓰지 않고,
    '검 팁 위치'가 마우스를 따라가되 무게에 따라 느리게 움직이게 하는 컨트롤러.
    """
    def __init__(self, mass, start_pos):
        self.mass = mass
        self.pos = pygame.Vector2(start_pos)

    def set_mass(self, mass):
        self.mass = mass

    def update(self, target_pos, dt):
        """
        target_pos: 실제 마우스 위치
        dt: 프레임 간 시간(초)
        """
        target = pygame.Vector2(target_pos)
        direction = target - self.pos
        dist = direction.length()
        if dist == 0:
            return self.pos

        # 질량이 클수록 느리게(가속도 작게) 따라감
        stiffness = 30.0 / max(self.mass, 0.1)  # mass 커질수록 값 감소
        step = stiffness * dt * dist

        if step >= dist:
            self.pos = target
        else:
            direction.scale_to_length(step)
            self.pos += direction

        return self.pos

    def draw(self, surface):
        # 검 팁을 작은 원으로 표현
        pygame.draw.circle(surface, (200, 200, 255), (int(self.pos.x), int(self.pos.y)), 5)
