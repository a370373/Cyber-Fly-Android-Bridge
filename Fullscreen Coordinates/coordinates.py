"""
Cyber-Fly Bridge
coordinates.py

全螢幕座標配置。

預設解析度：
    1080 × 2400

如果使用者的 Android 裝置解析度不同，
只需要修改：

    SCREEN_WIDTH
    SCREEN_HEIGHT

Bridge 本體不需要修改。

操作規則：

    CLICK
        全螢幕可操作

    DOUBLE_CLICK
        全螢幕可操作

    LONG_PRESS
        全螢幕可操作

    SWIPE
        全螢幕任意位置
        支援上、下、左、右

    TURN_LEFT
        使用全螢幕向左 SWIPE

    TURN_RIGHT
        使用全螢幕向右 SWIPE

    TURN_FORWARD
        使用全螢幕向上 SWIPE

    TURN_BACKWARD
        使用全螢幕向下 SWIPE

    RELEASE
        由 Bridge 管理目前的持續操作

    NONE
        不操作
"""


# ============================================================
# Screen resolution
# ============================================================

SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 2400


# ============================================================
# Full-screen grid
# ============================================================

GRID_COLUMNS = 18
GRID_ROWS = 30


def _build_fullscreen_points():

    points = []

    for row in range(GRID_ROWS):

        y = int(
            (row + 0.5)
            * SCREEN_HEIGHT
            / GRID_ROWS
        )

        for column in range(GRID_COLUMNS):

            x = int(
                (column + 0.5)
                * SCREEN_WIDTH
                / GRID_COLUMNS
            )

            x = max(
                0,
                min(SCREEN_WIDTH - 1, x)
            )

            y = max(
                0,
                min(SCREEN_HEIGHT - 1, y)
            )

            points.append(
                (x, y)
            )

    return points


ACTION_COORDINATES = (
    _build_fullscreen_points()
)


# ============================================================
# Full-screen SWIPE
# ============================================================

def _build_swipe_coordinates():

    movements = []

    horizontal_distance = int(
        SCREEN_WIDTH * 0.20
    )

    vertical_distance = int(
        SCREEN_HEIGHT * 0.20
    )

    for x, y in ACTION_COORDINATES:

        # ----------------------------
        # 向右
        # ----------------------------

        if (
            x + horizontal_distance
            < SCREEN_WIDTH
        ):

            movements.append(
                (
                    x,
                    y,
                    x + horizontal_distance,
                    y,
                )
            )

        # ----------------------------
        # 向左
        # ----------------------------

        if (
            x - horizontal_distance
            >= 0
        ):

            movements.append(
                (
                    x,
                    y,
                    x - horizontal_distance,
                    y,
                )
            )

        # ----------------------------
        # 向下
        # ----------------------------

        if (
            y + vertical_distance
            < SCREEN_HEIGHT
        ):

            movements.append(
                (
                    x,
                    y,
                    x,
                    y + vertical_distance,
                )
            )

        # ----------------------------
        # 向上
        # ----------------------------

        if (
            y - vertical_distance
            >= 0
        ):

            movements.append(
                (
                    x,
                    y,
                    x,
                    y - vertical_distance,
                )
            )

    return movements


SWIPE_COORDINATES = (
    _build_swipe_coordinates()
)


# ============================================================
# Semantic aliases
#
# TURN_* 不建立新的座標。
#
# 直接使用既有全螢幕 SWIPE 座標，
# 只是提供 Cyber-Fly semantic vocabulary
# 的相容名稱。
# ============================================================

SEMANTIC_ALIASES = {

    "TURN_LEFT": "SWIPE_LEFT",

    "TURN_RIGHT": "SWIPE_RIGHT",

    "TURN_FORWARD": "SWIPE_UP",

    "TURN_BACKWARD": "SWIPE_DOWN",
}


# ============================================================
# Directional SWIPE coordinates
#
# 從全螢幕 SWIPE 座標中分離方向。
# ============================================================

SWIPE_LEFT_COORDINATES = []
SWIPE_RIGHT_COORDINATES = []
SWIPE_UP_COORDINATES = []
SWIPE_DOWN_COORDINATES = []


for movement in SWIPE_COORDINATES:

    x1, y1, x2, y2 = movement

    if x2 < x1:

        SWIPE_LEFT_COORDINATES.append(
            movement
        )

    elif x2 > x1:

        SWIPE_RIGHT_COORDINATES.append(
            movement
        )

    elif y2 < y1:

        SWIPE_UP_COORDINATES.append(
            movement
        )

    elif y2 > y1:

        SWIPE_DOWN_COORDINATES.append(
            movement
        )


# ============================================================
# Semantic → coordinates
# ============================================================

COORDINATES = {

    "CLICK":
        ACTION_COORDINATES,

    "DOUBLE_CLICK":
        ACTION_COORDINATES,

    "LONG_PRESS":
        ACTION_COORDINATES,

    "SWIPE":
        SWIPE_COORDINATES,

    "SWIPE_LEFT":
        SWIPE_LEFT_COORDINATES,

    "SWIPE_RIGHT":
        SWIPE_RIGHT_COORDINATES,

    "SWIPE_UP":
        SWIPE_UP_COORDINATES,

    "SWIPE_DOWN":
        SWIPE_DOWN_COORDINATES,

    # TURN aliases
    "TURN_LEFT":
        SWIPE_LEFT_COORDINATES,

    "TURN_RIGHT":
        SWIPE_RIGHT_COORDINATES,

    "TURN_FORWARD":
        SWIPE_UP_COORDINATES,

    "TURN_BACKWARD":
        SWIPE_DOWN_COORDINATES,
}


# ============================================================
# Supported semantics
# ============================================================

SUPPORTED_SEMANTICS = (

    "NONE",

    "CLICK",
    "DOUBLE_CLICK",
    "LONG_PRESS",

    "RELEASE",

    "SWIPE",

    "SWIPE_LEFT",
    "SWIPE_RIGHT",
    "SWIPE_UP",
    "SWIPE_DOWN",

    "TURN_LEFT",
    "TURN_RIGHT",
    "TURN_FORWARD",
    "TURN_BACKWARD",
)


# ============================================================
# Special semantics
# ============================================================

NO_ACTION_SEMANTICS = {
    "NONE",
}


RELEASE_SEMANTICS = {
    "RELEASE",
}


# ============================================================
# Semantic normalization
# ============================================================

def normalize_semantic(semantic):

    if not isinstance(
        semantic,
        str,
    ):

        return None

    semantic = (
        semantic
        .strip()
        .upper()
    )

    return SEMANTIC_ALIASES.get(
        semantic,
        semantic,
    )


# ============================================================
# Supported semantic
# ============================================================

def is_supported_semantic(semantic):

    semantic = normalize_semantic(
        semantic
    )

    return (
        semantic in SUPPORTED_SEMANTICS
    )


# ============================================================
# Coordinate lookup
# ============================================================

def get_coordinates(semantic):

    semantic = normalize_semantic(
        semantic
    )

    if semantic is None:
        return None

    if semantic in NO_ACTION_SEMANTICS:
        return None

    if semantic in RELEASE_SEMANTICS:
        return None

    return COORDINATES.get(
        semantic
    )