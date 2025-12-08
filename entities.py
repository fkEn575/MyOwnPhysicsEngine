
import pygame

from config import (
    SCARECROW_RECT,
    SCARECROW_COLOR,
    SCARECROW_OUTLINE,
    SLASH_COLOR,
    SWORD_BASE_MASS,
    SWORD_STIFFNESS_BASE,
)
from physics import distance, polyline_length


class SwordController:
    """
    마우스 위치(target)를 그대로 쓰지 않고,
    질량에 따라 느리게 따라가는 '검 팁 위치'를 관리하는 컨트롤러.
    """

    def __init__(self, mass, start_pos):
        self.mass = mass
        self.pos = pygame.Vector2(start_pos)
        self.prev_pos = pygame.Vector2(start_pos)
        self.control_multiplier = 1.0  # 설정창에서 조절 가능한 컨트롤 민감도

    def set_mass(self, mass):
        self.mass = mass

    def set_control_multiplier(self, value: float):
        self.control_multiplier = max(0.1, float(value))

    def update(self, target_pos, dt):
        """
        target_pos: 실제 마우스 위치
        dt: 프레임 간 시간(초)
        """
        if dt <= 0.0:
            return self.pos

        target = pygame.Vector2(target_pos)
        direction = target - self.pos
        dist = direction.length()

        # 그리기용으로 이전 위치 저장
        self.prev_pos = self.pos.copy()

        if dist < 1e-6:
            self.pos = target
            return self.pos

        # 기본 질량 대비 비율로, 무게에 따라 따라가는 속도 조절
        # 무거울수록 mass_ratio < 1 → stiffness 작아짐 → 더 둔하게 움직임
        mass_ratio = SWORD_BASE_MASS / max(self.mass, 0.1)
        stiffness = SWORD_STIFFNESS_BASE * mass_ratio * self.control_multiplier

        step = stiffness * dt * dist

        if step >= dist:
            self.pos = target
        else:
            direction.scale_to_length(step)
            self.pos += direction

        return self.pos

    def draw(self, surface):
        """검 모양 커서를 그린다."""
        tip = pygame.Vector2(self.pos)

        # 이전 프레임 위치와의 차이를 이용해 검의 방향 계산
        direction = tip - self.prev_pos
        if direction.length_squared() < 1e-4:
            direction = pygame.Vector2(1, 0)

        blade_length = 40
        direction = direction.normalize() * blade_length

        hilt_base = tip - direction

        # 칼날
        pygame.draw.line(
            surface,
            (230, 230, 255),
            (int(hilt_base.x), int(hilt_base.y)),
            (int(tip.x), int(tip.y)),
            3,
        )

        # 손잡이(십자 가드) 표현
        guard = pygame.Vector2(-direction.y, direction.x)
        guard.scale_to_length(6)
        guard_left = tip - guard
        guard_right = tip + guard

        pygame.draw.line(
            surface,
            (230, 230, 255),
            (int(guard_left.x), int(guard_left.y)),
            (int(guard_right.x), int(guard_right.y)),
            2,
        )

        # 검 끝 강조
        pygame.draw.circle(
            surface, (255, 255, 255), (int(tip.x), int(tip.y)), 4
        )


class Scarecrow:
    """
    허수아비 본체 + 베인 자국들을 관리.
    base_rect: 현재 남아 있는 허수아비 몸통
    cuts: 개별 베기 자국 (각각 연속적인 경로와 연속적인 베임 비율)
    """

    def __init__(self):
        x, y, w, h = SCARECROW_RECT
        self.base_rect = pygame.Rect(x, y, w, h)
        self.cuts = []  # {"points": [...], "ratio": float}

    def reset(self):
        """허수아비를 처음 상태로 되돌린다."""
        x, y, w, h = SCARECROW_RECT
        self.base_rect = pygame.Rect(x, y, w, h)
        self.cuts.clear()

    # --- 내부 유틸리티 ---

    def _clip_points_to_rect(self, points, rect):
        """
        경로(points)에서 rect와 실제로 겹치는 구간만 잘라낸다.
        points 중 rect 내부에 있는 첫/마지막 점을 기준으로
        양 끝은 선분 보간으로 경계까지 확장한다.
        """
        if len(points) < 2:
            return []

        # rect 안에 들어가는 점들의 인덱스
        inside_indices = [
            i for i, (x, y) in enumerate(points) if rect.collidepoint(x, y)
        ]
        if not inside_indices:
            return []

        first_i = inside_indices[0]
        last_i = inside_indices[-1]

        def interpolate_entry(p_out, p_in):
            ax, ay = p_out
            bx, by = p_in
            left, right = 0.0, 1.0
            for _ in range(8):
                mid = (left + right) / 2.0
                mx = ax + (bx - ax) * mid
                my = ay + (by - ay) * mid
                if rect.collidepoint(mx, my):
                    right = mid
                else:
                    left = mid
            mx = ax + (bx - ax) * right
            my = ay + (by - ay) * right
            return (mx, my)

        def interpolate_exit(p_in, p_out):
            ax, ay = p_in
            bx, by = p_out
            left, right = 0.0, 1.0
            for _ in range(8):
                mid = (left + right) / 2.0
                mx = ax + (bx - ax) * mid
                my = ay + (by - ay) * mid
                if rect.collidepoint(mx, my):
                    left = mid
                else:
                    right = mid
            mx = ax + (bx - ax) * left
            my = ay + (by - ay) * left
            return (mx, my)

        clipped = []

        # 시작점
        if first_i == 0:
            clipped.append(points[first_i])
        else:
            p_out = points[first_i - 1]
            p_in = points[first_i]
            start = interpolate_entry(p_out, p_in)
            clipped.append(start)

        # 중간의 내부 점들
        for i in range(first_i, last_i + 1):
            x, y = points[i]
            if rect.collidepoint(x, y):
                clipped.append(points[i])

        # 끝점
        if last_i == len(points) - 1:
            end = points[last_i]
            if end != clipped[-1]:
                clipped.append(end)
        else:
            p_in = points[last_i]
            p_out = points[last_i + 1]
            end = interpolate_exit(p_in, p_out)
            if end != clipped[-1]:
                clipped.append(end)

        return clipped

    def _truncate_path_by_length(self, points, target_len):
        """
        경로(points)를 앞에서부터 target_len 길이만큼만 남기고 잘라낸다.
        """
        if len(points) < 2 or target_len <= 0.0:
            return []

        out = [points[0]]
        acc = 0.0

        for i in range(len(points) - 1):
            p0 = points[i]
            p1 = points[i + 1]
            seg_len = distance(p0, p1)

            if acc + seg_len >= target_len:
                # 이 선분 안에서 잘려야 하는 경우
                if seg_len > 0.0:
                    t = (target_len - acc) / seg_len
                else:
                    t = 0.0
                x = p0[0] + (p1[0] - p0[0]) * t
                y = p0[1] + (p1[1] - p0[1]) * t
                out.append((x, y))
                break
            else:
                out.append(p1)
                acc += seg_len

        return out

    def _apply_full_cut_if_possible(self, inside_path, cut_ratio):
        """
        충분히 강한 베기(cut_ratio ≈ 1.0)이고,
        허수아비 폭 전체를 가로질렀다면 위쪽 몸통을 잘라낸다.
        """
        if cut_ratio < 0.999:
            return False

        rect = self.base_rect
        if rect.height <= 0:
            return False

        xs = [p[0] for p in inside_path]
        ys = [p[1] for p in inside_path]
        if not xs or not ys:
            return False

        min_x = min(xs)
        max_x = max(xs)

        # 허수아비의 왼쪽~오른쪽을 거의 모두 가로질렀는지 확인
        if min_x > rect.left + 2 or max_x < rect.right - 2:
            return False

        # 절단 높이(y)는 베기 경로의 평균 높이 근처로
        cut_y = sum(ys) / len(ys)

        if cut_y <= rect.top + 2 or cut_y >= rect.bottom - 2:
            return False

        # 위쪽은 날아가고, 아래쪽 몸통만 남도록 rect를 갱신
        new_top = int(cut_y)
        new_height = rect.bottom - new_top
        if new_height <= 0:
            # 몸통이 완전히 사라진 경우
            self.base_rect = pygame.Rect(rect.left, rect.bottom, rect.width, 0)
        else:
            self.base_rect = pygame.Rect(rect.left, new_top, rect.width, new_height)

        return True

    # --- 외부에서 호출하는 메인 로직 ---

    def apply_slash(self, points, slash_energy, e_init, energy_per_length):
        """
        한 번의 슬래시(points, slash_energy)에 대해
        - 허수아비 내부에서 실제로 지나간 길이를 구하고
        - 그 길이를 완전히 자르기 위한 에너지를 계산한 뒤
        - 이번 슬래시로 몇 %나 베었는지(cut_ratio)를 계산하여
          그 비율만큼의 길이만 실제 자국으로 남긴다.

        반환값:
            (L_inside, E_required_full, cut_ratio, did_full_cut)
        """
        # 허수아비가 이미 사라진 경우
        if self.base_rect.height <= 0 or len(points) < 2:
            return 0.0, 0.0, 0.0, False

        # 허수아비 내부 경로 추출
        inside = self._clip_points_to_rect(points, self.base_rect)
        if len(inside) < 2:
            return 0.0, 0.0, 0.0, False

        L_inside = polyline_length(inside)

        # 길이가 너무 짧으면 베이지 않은 것으로 처리
        if L_inside <= 1e-3:
            return 0.0, 0.0, 0.0, False

        # 이 경로 전체를 완전히 자르기 위해 필요한 에너지
        E_required_full = e_init + energy_per_length * L_inside

        if slash_energy <= 0.0:
            return L_inside, E_required_full, 0.0, False

        # 초기 에너지보다 작으면 베이지 않은 것으로 간주
        if slash_energy <= e_init:
            cut_ratio = 0.0
        else:
            cut_ratio = slash_energy / E_required_full
            if cut_ratio < 0.0:
                cut_ratio = 0.0
            if cut_ratio > 1.0:
                cut_ratio = 1.0

        if cut_ratio <= 0.0:
            return L_inside, E_required_full, 0.0, False

        # 허수아비 내부에서 cut_ratio 비율만큼의 길이만 실제 자국으로 남김
        L_cut = L_inside * cut_ratio
        cut_path = self._truncate_path_by_length(inside, L_cut)

        did_full_cut = False
        if len(cut_path) >= 2:
            self.cuts.append({"points": cut_path, "ratio": cut_ratio})
            # 충분히 강한 베기라면 완전 절단도 시도
            did_full_cut = self._apply_full_cut_if_possible(inside, cut_ratio)

        return L_inside, E_required_full, cut_ratio, did_full_cut

    def draw(self, surface):
        """허수아비 몸통과 자국들을 그린다."""
        if self.base_rect.height > 0:
            pygame.draw.rect(surface, SCARECROW_COLOR, self.base_rect)
            pygame.draw.rect(surface, SCARECROW_OUTLINE, self.base_rect, 2)

        # 베인 자국들
        for cut in self.cuts:
            pts = cut.get("points", [])
            if len(pts) < 2:
                continue
            ratio = float(cut.get("ratio", 1.0))
            # 비율이 클수록 조금 더 굵은 선
            width = 1 + int(4 * max(0.0, min(1.0, ratio)))
            pygame.draw.lines(surface, SLASH_COLOR, False, pts, width)
