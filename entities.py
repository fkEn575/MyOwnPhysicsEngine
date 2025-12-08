
import pygame
from config import (
    SCARECROW_RECT, SCARECROW_COLOR, SCARECROW_OUTLINE,
    SLASH_COLOR, SLASH_SHALLOW_WIDTH, SLASH_MEDIUM_WIDTH, SLASH_DEEP_WIDTH
)
from physics import distance


class Scarecrow:
    def __init__(self):
        # 기본 허수아비 몸통
        self.base_rect = pygame.Rect(SCARECROW_RECT)
        self.cuts = []  # 각 cut: {"points": [...], "depth": "shallow/medium/deep"}

    def reset(self):
        # 허수아비를 완전히 원상복구
        self.base_rect = pygame.Rect(SCARECROW_RECT)
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

        # 현재 남아있는 허수아비 몸통에 닿았는지 확인
        if not self._path_intersects_rect(points, self.base_rect):
            return

        # deep 이면서, 허수아비를 가로질러 "전부" 베었는지 체크
        if depth == "deep" and self._is_full_cut(points, self.base_rect):
            self._apply_full_cut(points, depth)
        else:
            # 전부 베지 못했으면 그냥 자국만 남긴다
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

    def _is_full_cut(self, points, rect):
        """
        '전부 베임' 판정:
        - rect 안에 들어온 점들 중 x 최소/최대가
          허수아비 왼쪽~오른쪽을 거의 다 덮으면 "가로로 전부 베었다"고 본다.
        """
        inside = [(x, y) for (x, y) in points if rect.collidepoint(x, y)]
        if not inside:
            return False

        xs = [p[0] for p in inside]
        min_x = min(xs)
        max_x = max(xs)

        margin = 5  # 양 끝에서 이 정도는 여유 허용
        covers_left = min_x <= rect.left + margin
        covers_right = max_x >= rect.right - margin

        return covers_left and covers_right

    def _apply_full_cut(self, points, depth):
        """
        전부 베인 경우:
        - 허수아비 위쪽이 잘려 나가고
        - 잘린 높이 기준으로 남은 아래쪽만 남긴다.
        """
        rect = self.base_rect

        # rect 안에 있는 점들의 y 평균을 "절단 높이"로 사용 (단순화)
        inside = [(x, y) for (x, y) in points if rect.collidepoint(x, y)]
        ys = [p[1] for p in inside]
        if not ys:
            # 혹시라도 안전장치: inside 가 없다면 그냥 일반 cut 로 처리
            self.cuts.append({
                "points": list(points),
                "depth": depth
            })
            return

        cut_y = int(sum(ys) / len(ys))  # 절단선 높이

        bottom = rect.bottom
        # cut_y 아래만 남기고 위는 잘려 나간 것으로 처리
        if cut_y >= bottom:
            # 거의 바닥을 자른 경우: 몸통이 사실상 사라졌다고 보고 높이 0
            rect.height = 0
        else:
            rect.height = bottom - cut_y
            rect.top = cut_y

        # 기존 자국들 중에서, 이제 남은 몸통(rect)에 걸리는 것만 유지
        self.cuts = [
            c for c in self.cuts
            if self._path_intersects_rect(c["points"], self.base_rect)
        ]

        # 방금 deep 컷도 남은 몸통에 걸쳐 있으면 자국으로 추가
        if self._path_intersects_rect(points, self.base_rect):
            self.cuts.append({
                "points": list(points),
                "depth": depth
            })

    def draw(self, surface):
        # 몸통이 남아있지 않으면 아무것도 그리지 않음
        if self.base_rect.height <= 0:
            return

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
