def lerp(a, b, t):
    return a + (b - a) * t


def lerp_vec(a, b, t):
    return Vec2(lerp(a.x, b.x, t), lerp(a.y, b.y, t))
