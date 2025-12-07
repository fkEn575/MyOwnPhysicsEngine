
import math
from config import CUT_THRESHOLDS

def distance(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.hypot(dx, dy)

def compute_speed(prev_pos, curr_pos, dt):
    """픽셀/초 단위 속도 계산."""
    if dt <= 0.0:
        return 0.0
    d = distance(prev_pos, curr_pos)
    return d / dt

def compute_impact(mass, speed):
    """
    아주 단순화된 '임팩트' 값.
    실제 물리 공식(1/2 m v^2)의 스케일을 줄이기 위해 속도 스케일링을 약간 적용.
    """
    speed_scale = 0.02  # 숫자 튜닝용
    v = speed * speed_scale
    return 0.5 * mass * (v ** 2)

def classify_cut(impact_value):
    """
    임팩트에 따라 베임 정도를 분류.
    """
    if impact_value < CUT_THRESHOLDS["no_cut"]:
        return "none"
    elif impact_value < CUT_THRESHOLDS["shallow"]:
        return "shallow"
    elif impact_value < CUT_THRESHOLDS["medium"]:
        return "medium"
    else:
        return "deep"
