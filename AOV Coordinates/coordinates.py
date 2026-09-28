"""
Cyber-Fly Bridge
coordinates.py

只負責保存：
    語意 -> 可使用座標

所有座標皆來自 Android 實機測量。

座標格式：
    (X, Y)

移動格式：
    (起點 X, 起點 Y, 終點 X, 終點 Y)
"""


# ============================================================
# 一般操作座標
#
# CLICK
# DOUBLE_CLICK
# LONG_PRESS
#
# 共用同一組可操作座標。
# ============================================================

ACTION_COORDINATES = [
    (564, 1871),
    (456, 1970),
    (464, 1674),
    (340, 1775),
    (255, 1546),
    (145, 1638),
    (323, 2073),
    (167, 1998),
    (87, 1792),
    (134, 1445),
    (158, 1271),
    (130, 1124),
    (677, 348),
    (566, 345),
]


# ============================================================
# SWIPE 起始座標
#
# SWIPE 會以這個位置作為起點，
# Bridge 再依照自己的 SWIPE 邏輯產生終點。
# ============================================================

SWIPE_START = (613, 1076)


# ============================================================
# MOVE 方向
#
# 格式：
#
#     (start_x, start_y, end_x, end_y)
#
# 這些是實機測量得到的方向座標。
# ============================================================

MOVE_COORDINATES = {

    "MOVE_FORWARD": (
        (254, 428),
        (356, 524),
    ),

    "MOVE_BACKWARD": (
        (254, 428),
        (147, 327),
    ),

    "MOVE_LEFT": (
        (254, 428),
        (400, 255),
    ),

    "MOVE_RIGHT": (
        (254, 428),
        (144, 678),
    ),
}


# ============================================================
# Semantic -> Coordinates
#
# Bridge 可以直接從這裡取得語意對應的座標。
#
# NONE：
#     不需要座標。
#
# RELEASE：
#     不需要座標。
#
# 未支援語意：
#     Bridge 忽略。
# ============================================================

COORDINATES = {

    "CLICK": ACTION_COORDINATES,

    "DOUBLE_CLICK": ACTION_COORDINATES,

    "LONG_PRESS": ACTION_COORDINATES,

    "SWIPE": [
        SWIPE_START,
    ],

    "MOVE_FORWARD": [
        MOVE_COORDINATES["MOVE_FORWARD"],
    ],

    "MOVE_BACKWARD": [
        MOVE_COORDINATES["MOVE_BACKWARD"],
    ],

    "MOVE_LEFT": [
        MOVE_COORDINATES["MOVE_LEFT"],
    ],

    "MOVE_RIGHT": [
        MOVE_COORDINATES["MOVE_RIGHT"],
    ],
}


# ============================================================
# Semantic information
#
# 方便 Bridge / 除錯程式確認目前有哪些可用語意。
# ============================================================

SUPPORTED_SEMANTICS = (
    "NONE",
    "CLICK",
    "DOUBLE_CLICK",
    "LONG_PRESS",
    "RELEASE",
    "SWIPE",
    "MOVE_FORWARD",
    "MOVE_BACKWARD",
    "MOVE_LEFT",
    "MOVE_RIGHT",
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
# Unsupported semantics
#
# 不在 SUPPORTED_SEMANTICS 裡的語意，
# Bridge 不執行任何 Android 操作。
# ============================================================

def is_supported_semantic(semantic):
    """
    判斷語意是否受到目前 Bridge 支援。
    """

    return semantic in SUPPORTED_SEMANTICS


def get_coordinates(semantic):
    """
    取得指定語意的座標資料。

    NONE / RELEASE：
        回傳 None。

    未支援：
        回傳 None。
    """

    if not is_supported_semantic(semantic):
        return None

    if semantic in NO_ACTION_SEMANTICS:
        return None

    if semantic in RELEASE_SEMANTICS:
        return None

    return COORDINATES.get(semantic)