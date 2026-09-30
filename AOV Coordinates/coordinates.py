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
# SWIPE
# ============================================================

SWIPE_START = (613, 1076)


# ============================================================
# MOVE
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
# TURN -> MOVE semantic aliases
#
# TURN_* 不建立新的座標。
#
# 它們直接使用既有 MOVE_* 實機座標。
#
# 這只是 platform-independent semantic vocabulary
# 的相容層，不代表 Bridge 解讀 MaleCNS 的真正意圖。
# ============================================================

SEMANTIC_ALIASES = {

    "TURN_FORWARD": "MOVE_FORWARD",
    "TURN_BACKWARD": "MOVE_BACKWARD",
    "TURN_LEFT": "MOVE_LEFT",
    "TURN_RIGHT": "MOVE_RIGHT",
}


# ============================================================
# Semantic -> Coordinates
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

    # TURN_* 使用既有 MOVE 座標
    "TURN_FORWARD": [
        MOVE_COORDINATES["MOVE_FORWARD"],
    ],

    "TURN_BACKWARD": [
        MOVE_COORDINATES["MOVE_BACKWARD"],
    ],

    "TURN_LEFT": [
        MOVE_COORDINATES["MOVE_LEFT"],
    ],

    "TURN_RIGHT": [
        MOVE_COORDINATES["MOVE_RIGHT"],
    ],
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

    "MOVE_FORWARD",
    "MOVE_BACKWARD",
    "MOVE_LEFT",
    "MOVE_RIGHT",

    "TURN_FORWARD",
    "TURN_BACKWARD",
    "TURN_LEFT",
    "TURN_RIGHT",
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
    """
    將語意正規化。

    TURN_* 是 MOVE_* 的語意別名。
    """

    if not isinstance(semantic, str):
        return None

    semantic = semantic.strip().upper()

    return SEMANTIC_ALIASES.get(
        semantic,
        semantic,
    )


# ============================================================
# Supported semantic check
# ============================================================

def is_supported_semantic(semantic):
    """
    判斷語意是否受到目前 Bridge 支援。
    """

    semantic = normalize_semantic(semantic)

    return semantic in SUPPORTED_SEMANTICS


# ============================================================
# Coordinate lookup
# ============================================================

def get_coordinates(semantic):
    """
    取得指定語意的座標資料。

    NONE / RELEASE：
        回傳 None。

    TURN_*：
        使用對應 MOVE_* 的座標。

    未支援：
        回傳 None。
    """

    semantic = normalize_semantic(semantic)

    if semantic is None:
        return None

    if semantic in NO_ACTION_SEMANTICS:
        return None

    if semantic in RELEASE_SEMANTICS:
        return None

    return COORDINATES.get(semantic)