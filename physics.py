
import math
from config import PIXELS_PER_METER


def distance(p1, p2):
    """두 점 사이의 유클리드 거리."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.hypot(dx, dy)


def compute_speed(prev_pos, curr_pos, dt):
    """픽셀/초 단위 속도 계산."""
    if dt <= 0.0:
        return 0.0
    d = distance(prev_pos, curr_pos)
    return d / dt


def kinetic_energy(mass, speed_pixels_per_sec):
    """
    검의 운동에너지 (대략 J 단위).
    speed_pixels_per_sec: 화면 상의 속도 (px/s)
    """
    v_m_s = speed_pixels_per_sec / PIXELS_PER_METER
    return 0.5 * mass * v_m_s * v_m_s


def polyline_length(points):
    """연속된 점들로 이루어진 경로의 총 길이."""
    if len(points) < 2:
        return 0.0
    total = 0.0
    for i in range(len(points) - 1):
        total += distance(points[i], points[i + 1])
    return total
