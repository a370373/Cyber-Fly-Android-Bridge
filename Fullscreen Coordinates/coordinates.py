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

    RELEASE
        由 Bridge 管理目前的持續操作

    NONE
        不操作

已取消：
    MOVE_FORWARD
    MOVE_BACKWARD
    MOVE_LEFT
    MOVE_RIGHT
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
    """
    建立整個螢幕的可操作座標。

    所有座標保證：

        0 <= X < SCREEN_WIDTH
        0 <= Y < SCREEN_HEIGHT
    """

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

            points.append((x, y))

    return points


ACTION_COORDINATES = _build_fullscreen_points()


# ============================================================
# Full-screen SWIPE
# ============================================================

def _build_swipe_coordinates():
    """
    建立全螢幕 SWIPE 座標。

    支援：

        上
        下
        左
        右

    每個項目：

        (X1, Y1, X2, Y2)
    """

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

        if x + horizontal_distance < SCREEN_WIDTH:
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

        if x - horizontal_distance >= 0:
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

        if y + vertical_distance < SCREEN_HEIGHT:
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

        if y - vertical_distance >= 0:
            movements.append(
                (
                    x,
                    y,
                    x,
                    y - vertical_distance,
                )
            )

    return movements


SWIPE_COORDINATES = _build_swipe_coordinates()


# ============================================================
# Semantic → coordinates
# ============================================================

COORDINATES = {

    # 全螢幕點擊
    "CLICK": ACTION_COORDINATES,

    # 全螢幕雙擊
    "DOUBLE_CLICK": ACTION_COORDINATES,

    # 全螢幕長按
    "LONG_PRESS": ACTION_COORDINATES,

    # 全螢幕四方向滑動
    "SWIPE": SWIPE_COORDINATES,
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
)


NO_ACTION_SEMANTICS = {
    "NONE",
}


RELEASE_SEMANTICS = {
    "RELEASE",
}


# ============================================================
# Public API
# ============================================================

def is_supported_semantic(semantic):
    """
    判斷語意是否支援。
    """

    return semantic in SUPPORTED_SEMANTICS


def get_coordinates(semantic):
    """
    取得指定語意的座標。

    Bridge 原本 API 不變。
    """

    if not is_supported_semantic(semantic):
        return None

    if semantic in NO_ACTION_SEMANTICS:
        return None

    if semantic in RELEASE_SEMANTICS:
        return None

    return COORDINATES.get(semantic)