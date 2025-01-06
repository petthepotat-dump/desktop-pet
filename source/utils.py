from pygame.math import Vector2


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_vec(a, b, t):
    return Vector2(lerp(a.x, b.x, t), lerp(a.y, b.y, t))
