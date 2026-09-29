#!/usr/bin/env python3

"""
Cyber-Fly Android Bridge

Android scrcpy
        ↓
    FFmpeg
        ↓
   RGB Frame
        ↓
Cyber-Fly :8765
        ↓
   Screen Vision
        ↓
      Eyes
        ↓
     MaleCNS
        ↓
   MotorDecoder
        ↓
   Action JSON
        ↓
Android Bridge
        ↓
coordinates.py
        ↓
Android UID 2000 Shell
        ↓
     input

核心原則：

    Bridge 不解讀 MaleCNS 的真正意圖。
    Bridge 只負責把 Cyber-Fly 已定義的
    platform-independent action 映射成 Android 操作。

Cyber-Fly protocol：

    4 bytes  big-endian payload length
    N bytes  UTF-8 JSON

Bridge → Cyber-Fly：

    {
        "type": "frame",
        "width": ...,
        "height": ...,
        "channels": 3,
        "pixels": "<base64 RGB bytes>"
    }

Cyber-Fly → Bridge：

    {
        "type": "action",
        "action": "click",
        "parameters": {
            "x": ...,
            "y": ...,
            "x2": ...,
            "y2": ...,
            "duration": ...,
            "key": ...
        }
    }

Android action mapping：

    click
        → CLICK

    double_click
        → DOUBLE_CLICK

    long_press
        → LONG_PRESS

    release
        → RELEASE

    swipe
        → SWIPE

    move_forward
        → MOVE_FORWARD

    move_backward
        → MOVE_BACKWARD

    move_left
        → MOVE_LEFT

    move_right
        → MOVE_RIGHT

Unsupported Cyber-Fly actions：

    ignored

Bridge 不猜測未知 action 的意思。
"""

import base64
import json
import os
import random
import socket
import struct
import subprocess
import threading
import time

from pathlib import Path


# ============================================================
# Runtime Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

FFMPEG_DIR = (
    BASE_DIR
    / "FFmpeg FFprobe"
)

FFMPEG = str(
    FFMPEG_DIR
    / "bin"
    / "ffmpeg"
)

FFMPEG_LIB_DIR = str(
    FFMPEG_DIR
    / "lib"
)

PYTHON_DIR = (
    BASE_DIR
    / "Python"
)

PYTHON_LIB_DIR = str(
    PYTHON_DIR
    / "lib"
)

PYTHON_STDLIB_DIR = str(
    PYTHON_DIR
    / "lib"
    / "python3.14"
)


# ------------------------------------------------------------
# Bundled runtime environment
#
# Python itself is already running at this point, so these
# variables are mainly inherited by child processes such as
# FFmpeg and Python native extensions loaded later.
# ------------------------------------------------------------

_existing_ld_library_path = os.environ.get(
    "LD_LIBRARY_PATH",
    "",
)

_runtime_library_paths = [
    FFMPEG_LIB_DIR,
    PYTHON_LIB_DIR,
    PYTHON_STDLIB_DIR,
]

if _existing_ld_library_path:
    _runtime_library_paths.append(
        _existing_ld_library_path
    )

os.environ["LD_LIBRARY_PATH"] = ":".join(
    _runtime_library_paths
)


from coordinates import (
    COORDINATES,
    MOVE_COORDINATES,
    is_supported_semantic,
)


# ============================================================
# Configuration
# ============================================================

# ------------------------------------------------------------
# Cyber-Fly
# ------------------------------------------------------------

CYBERFLY_HOST = "127.0.0.1"
CYBERFLY_PORT = 8765

MAX_MESSAGE_SIZE = 16 * 1024 * 1024

# ------------------------------------------------------------
# Android / scrcpy
# ------------------------------------------------------------

SCRCPY_HOST = "127.0.0.1"
SCRCPY_PORT = 1234

# ------------------------------------------------------------
# Android shell
# ------------------------------------------------------------

TEST_MODE = True

# ------------------------------------------------------------
# FFmpeg
# ------------------------------------------------------------

JPEG_QUALITY = 5

# ------------------------------------------------------------
# Touch
# ------------------------------------------------------------

SWIPE_DURATION_MIN = 1000
SWIPE_DURATION_MAX = 2000

HOLD_DURATION = 60000

DOUBLE_CLICK_INTERVAL = 0.08


# ============================================================
# Global State
# ============================================================

active_actions = []
active_actions_lock = threading.Lock()

cyberfly_socket = None
cyberfly_socket_lock = threading.Lock()

cyberfly_send_lock = threading.Lock()

shutdown_event = threading.Event()


# ============================================================
# TCP Protocol
# ============================================================

def encode_json_message(message):
    """
    Cyber-Fly protocol：

        4 bytes  big-endian JSON length
        N bytes  UTF-8 JSON
    """

    payload = json.dumps(
        message,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    if len(payload) <= 0:
        raise ValueError(
            "empty JSON message"
        )

    if len(payload) > MAX_MESSAGE_SIZE:
        raise ValueError(
            f"message too large: {len(payload)}"
        )

    return (
        struct.pack(
            "!I",
            len(payload),
        )
        + payload
    )


def receive_exact(sock, size):
    """
    Receive exactly `size` bytes.
    """

    data = bytearray()

    while len(data) < size:

        chunk = sock.recv(
            size - len(data)
        )

        if not chunk:
            raise ConnectionError(
                "peer disconnected"
            )

        data.extend(chunk)

    return bytes(data)


def receive_json_message(sock):
    """
    Receive one Cyber-Fly JSON message.
    """

    header = receive_exact(
        sock,
        4,
    )

    size = struct.unpack(
        "!I",
        header,
    )[0]

    if size <= 0:
        raise ValueError(
            "invalid message size"
        )

    if size > MAX_MESSAGE_SIZE:
        raise ValueError(
            f"message too large: {size}"
        )

    payload = receive_exact(
        sock,
        size,
    )

    return json.loads(
        payload.decode("utf-8")
    )


# ============================================================
# Cyber-Fly Socket
# ============================================================

def set_cyberfly_socket(sock):

    global cyberfly_socket

    with cyberfly_socket_lock:

        cyberfly_socket = sock


def get_cyberfly_socket():

    with cyberfly_socket_lock:

        return cyberfly_socket


def clear_cyberfly_socket(sock=None):

    global cyberfly_socket

    with cyberfly_socket_lock:

        if (
            sock is None
            or cyberfly_socket is sock
        ):

            cyberfly_socket = None


def close_cyberfly_socket(sock=None):

    if sock is None:

        sock = get_cyberfly_socket()

    if sock is None:
        return

    clear_cyberfly_socket(
        sock
    )

    try:
        sock.shutdown(
            socket.SHUT_RDWR
        )
    except Exception:
        pass

    try:
        sock.close()
    except Exception:
        pass


def send_to_cyberfly(message):

    sock = get_cyberfly_socket()

    if sock is None:

        return False

    try:

        packet = encode_json_message(
            message
        )

        with cyberfly_send_lock:

            sock.sendall(
                packet
            )

        return True

    except Exception as e:

        print(
            "[CYBER-FLY] send error:",
            e,
        )

        close_cyberfly_socket(
            sock
        )

        return False


# ============================================================
# Android Shell
# ============================================================

def execute_command(
    command,
    wait=False,
):
    """
    執行 Android UID 2000 Shell command。

    TEST_MODE=True：

        只顯示 command。

    TEST_MODE=False：

        真正執行。
    """

    print(
        "[ANDROID]",
        command,
    )

    if TEST_MODE:
        return None

    if wait:

        return subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    return subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


# ============================================================
# Coordinates
# ============================================================

def choose_coordinates(
    semantic
):
    """
    CLICK / DOUBLE_CLICK / LONG_PRESS / SWIPE：

        從 coordinates.py 的座標集合中
        隨機選擇一個到全部。
    """

    coordinates = COORDINATES.get(
        semantic
    )

    if not coordinates:
        return []

    count = random.randint(
        1,
        len(coordinates),
    )

    return random.sample(
        coordinates,
        count,
    )


def choose_move_coordinate(
    semantic
):
    """
    MOVE：

        (start_x, start_y)
            →
        (end_x, end_y)
    """

    move = MOVE_COORDINATES.get(
        semantic
    )

    if move is None:
        return None

    start, end = move

    return start, end


# ============================================================
# Persistent Action
# ============================================================

class ActiveAction:

    def __init__(
        self,
        semantic,
        coordinate,
        worker,
    ):

        self.semantic = semantic
        self.coordinate = coordinate
        self.worker = worker

        self.stop_event = (
            threading.Event()
        )

        self.process = None
        self.thread = None


def register_action(
    action
):

    with active_actions_lock:

        active_actions.append(
            action
        )


def unregister_action(
    action
):

    with active_actions_lock:

        if action in active_actions:

            active_actions.remove(
                action
            )


def terminate_action_process(
    action
):

    process = action.process

    if process is None:
        return

    try:

        process.terminate()

    except Exception:

        pass

    action.process = None


# ============================================================
# Continuous Hold
# ============================================================

def hold_at_position(
    action,
    x,
    y,
):
    """
    在指定位置持續按住。

    RELEASE：

        stop_event
            ↓
        terminate subprocess
            ↓
        touch release
    """

    command = (
        f"input swipe "
        f"{x} {y} "
        f"{x} {y} "
        f"{HOLD_DURATION}"
    )

    if TEST_MODE:

        print(
            "[ANDROID]",
            command,
        )

        while not action.stop_event.wait(
            0.5
        ):
            pass

        return

    while not action.stop_event.is_set():

        try:

            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            action.process = process

            while process.poll() is None:

                if action.stop_event.wait(
                    0.1
                ):
                    break

            if action.stop_event.is_set():

                terminate_action_process(
                    action
                )

                break

        except Exception as e:

            print(
                "[HOLD] error:",
                e,
            )

            if action.stop_event.wait(
                0.2
            ):
                break

        finally:

            action.process = None


# ============================================================
# MOVE
# ============================================================

def move_worker(
    action
):
    """
    MOVE：

        實測起點
            ↓
        實測終點
            ↓
        抵達
            ↓
        持續按住
            ↓
        RELEASE
    """

    start, end = action.coordinate

    start_x, start_y = start
    end_x, end_y = end

    duration = random.randint(
        SWIPE_DURATION_MIN,
        SWIPE_DURATION_MAX,
    )

    slide_command = (
        f"input swipe "
        f"{start_x} {start_y} "
        f"{end_x} {end_y} "
        f"{duration}"
    )

    print(
        f"[MOVE] "
        f"{start_x},{start_y} "
        f"-> "
        f"{end_x},{end_y} "
        f"duration={duration}ms"
    )

    if TEST_MODE:

        print(
            "[ANDROID]",
            slide_command,
        )

        print(
            "[ANDROID]",
            f"input swipe "
            f"{end_x} {end_y} "
            f"{end_x} {end_y} "
            f"{HOLD_DURATION}"
        )

        while not action.stop_event.wait(
            0.5
        ):
            pass

        return

    try:

        # ----------------------------------------------------
        # Phase 1
        # ----------------------------------------------------

        process = subprocess.Popen(
            slide_command,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        action.process = process

        while process.poll() is None:

            if action.stop_event.wait(
                0.05
            ):

                terminate_action_process(
                    action
                )

                return

        action.process = None

        if action.stop_event.is_set():
            return

        # ----------------------------------------------------
        # Phase 2
        # ----------------------------------------------------

        hold_at_position(
            action,
            end_x,
            end_y,
        )

    except Exception as e:

        print(
            "[MOVE] error:",
            e,
        )

    finally:

        action.process = None


# ============================================================
# SWIPE
# ============================================================

def random_swipe_endpoint(
    start_x,
    start_y,
):
    """
    SWIPE endpoint 由 Bridge 隨機決定。

    不從 endpoint 推導任何意圖。
    """

    directions = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
        (-1, -1),
        (-1, 1),
        (1, -1),
        (1, 1),
    ]

    dx, dy = random.choice(
        directions
    )

    distance = random.randint(
        100,
        500,
    )

    end_x = max(
        0,
        min(
            9999,
            start_x + dx * distance,
        ),
    )

    end_y = max(
        0,
        min(
            9999,
            start_y + dy * distance,
        ),
    )

    return end_x, end_y


def execute_swipe(
    coordinate
):

    start_x, start_y = coordinate

    end_x, end_y = (
        random_swipe_endpoint(
            start_x,
            start_y,
        )
    )

    duration = random.randint(
        SWIPE_DURATION_MIN,
        SWIPE_DURATION_MAX,
    )

    command = (
        f"input swipe "
        f"{start_x} {start_y} "
        f"{end_x} {end_y} "
        f"{duration}"
    )

    print(
        f"[SWIPE] "
        f"{start_x},{start_y} "
        f"-> "
        f"{end_x},{end_y} "
        f"duration={duration}ms"
    )

    if TEST_MODE:

        print(
            "[ANDROID]",
            command,
        )

        return

    try:

        subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    except Exception as e:

        print(
            "[SWIPE] error:",
            e,
        )


# ============================================================
# LONG PRESS
# ============================================================

def long_press_worker(
    action
):

    x, y = action.coordinate

    hold_at_position(
        action,
        x,
        y,
    )


# ============================================================
# Start Persistent Action
# ============================================================

def start_persistent_action(
    semantic,
    coordinate,
):

    if semantic in (
        "MOVE_FORWARD",
        "MOVE_BACKWARD",
        "MOVE_LEFT",
        "MOVE_RIGHT",
    ):

        worker = move_worker

    elif semantic == "LONG_PRESS":

        worker = long_press_worker

    else:

        return

    action = ActiveAction(
        semantic,
        coordinate,
        worker,
    )

    register_action(
        action
    )

    def run():

        try:

            worker(action)

        finally:

            terminate_action_process(
                action
            )

            unregister_action(
                action
            )

    thread = threading.Thread(
        target=run,
        daemon=True,
    )

    action.thread = thread

    thread.start()


# ============================================================
# CLICK
# ============================================================

def execute_click(
    coordinate
):

    x, y = coordinate

    execute_command(
        f"input tap {x} {y}"
    )


# ============================================================
# DOUBLE CLICK
# ============================================================

def execute_double_click(
    coordinate
):

    x, y = coordinate

    execute_command(
        f"input tap {x} {y}"
    )

    time.sleep(
        DOUBLE_CLICK_INTERVAL
    )

    execute_command(
        f"input tap {x} {y}"
    )


# ============================================================
# RELEASE
# ============================================================

def release_actions():

    with active_actions_lock:

        if not active_actions:

            print(
                "[RELEASE] no active actions"
            )

            return

        count = random.randint(
            1,
            len(active_actions),
        )

        selected = random.sample(
            active_actions,
            count,
        )

    print(
        f"[RELEASE] releasing "
        f"{len(selected)} action(s)"
    )

    for action in selected:

        action.stop_event.set()

        terminate_action_process(
            action
        )


# ============================================================
# Semantic Handler
# ============================================================

def handle_semantic(
    semantic
):
    """
    Cyber-Fly action → Android operation。

    不猜測。
    不補全。
    不重新解釋。
    """

    if not isinstance(
        semantic,
        str,
    ):
        return

    semantic = (
        semantic
        .strip()
        .upper()
    )

    print(
        "[SEMANTIC]",
        semantic,
    )

    if not is_supported_semantic(
        semantic
    ):

        print(
            "[SEMANTIC] "
            "unsupported -> ignored"
        )

        return

    if semantic == "NONE":
        return

    if semantic == "RELEASE":

        release_actions()

        return

    if semantic.startswith(
        "MOVE_"
    ):

        move_coordinate = (
            choose_move_coordinate(
                semantic
            )
        )

        if move_coordinate is None:

            print(
                "[MOVE] "
                "no coordinate -> ignored"
            )

            return

        start_persistent_action(
            semantic,
            move_coordinate,
        )

        return

    if semantic == "SWIPE":

        coordinates = choose_coordinates(
            semantic
        )

        if not coordinates:

            print(
                "[SWIPE] "
                "no coordinate -> ignored"
            )

            return

        for coordinate in coordinates:

            execute_swipe(
                coordinate
            )

        return

    if semantic == "LONG_PRESS":

        coordinates = choose_coordinates(
            semantic
        )

        if not coordinates:

            print(
                "[LONG_PRESS] "
                "no coordinate -> ignored"
            )

            return

        for coordinate in coordinates:

            start_persistent_action(
                "LONG_PRESS",
                coordinate,
            )

        return

    if semantic == "CLICK":

        coordinates = choose_coordinates(
            semantic
        )

        if not coordinates:

            print(
                "[CLICK] "
                "no coordinate -> ignored"
            )

            return

        for coordinate in coordinates:

            execute_click(
                coordinate
            )

        return

    if semantic == "DOUBLE_CLICK":

        coordinates = choose_coordinates(
            semantic
        )

        if not coordinates:

            print(
                "[DOUBLE_CLICK] "
                "no coordinate -> ignored"
            )

            return

        for coordinate in coordinates:

            execute_double_click(
                coordinate
            )

        return


# ============================================================
# Cyber-Fly Action Receiver
# ============================================================

def handle_action_message(
    message
):
    """
    Cyber-Fly 現行 ActionMessage：

        {
            "type": "action",
            "action": "click",
            "parameters": {
                ...
            }
        }

    parameters 保留給 platform-independent
    protocol。

    Android Bridge 的座標策略仍由
    coordinates.py 決定。
    """

    if message.get("type") != "action":

        print(
            "[CYBER-FLY] "
            f"unsupported message type: "
            f"{message.get('type')}"
        )

        return

    action = message.get(
        "action"
    )

    if not isinstance(
        action,
        str,
    ):

        print(
            "[ACTION] invalid action"
        )

        return

    parameters = message.get(
        "parameters",
        {},
    )

    print(
        "[ACTION]",
        action,
        parameters,
    )

    semantic = action.strip().upper()

    handle_semantic(
        semantic
    )


def cyberfly_receive_loop(
    sock
):

    try:

        while not shutdown_event.is_set():

            message = receive_json_message(
                sock
            )

            message_type = message.get(
                "type"
            )

            if message_type == "action":

                handle_action_message(
                    message
                )

            elif message_type == "event":

                print(
                    "[CYBER-FLY EVENT]",
                    message.get(
                        "event"
                    ),
                    message.get(
                        "data",
                        {},
                    ),
                )

            else:

                print(
                    "[CYBER-FLY] "
                    "unsupported incoming type:",
                    message_type,
                )

    except Exception as e:

        if not shutdown_event.is_set():

            print(
                "[CYBER-FLY] "
                "receive error:",
                e,
            )

    finally:

        close_cyberfly_socket(
            sock
        )


# ============================================================
# Cyber-Fly Client
# ============================================================

def cyberfly_connection_loop():

    while not shutdown_event.is_set():

        sock = None

        try:

            print(
                "[CYBER-FLY] connecting to "
                f"{CYBERFLY_HOST}:"
                f"{CYBERFLY_PORT}..."
            )

            sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM,
            )

            sock.settimeout(5)

            sock.connect(
                (
                    CYBERFLY_HOST,
                    CYBERFLY_PORT,
                )
            )

            sock.settimeout(None)

            set_cyberfly_socket(
                sock
            )

            print(
                "[CYBER-FLY] connected"
            )

            print(
                "[CYBER-FLY] "
                "bidirectional communication active"
            )

            cyberfly_receive_loop(
                sock
            )

        except Exception as e:

            if not shutdown_event.is_set():

                print(
                    "[CYBER-FLY] "
                    "connection failed:",
                    e,
                )

        finally:

            if sock is not None:

                close_cyberfly_socket(
                    sock
                )

        if not shutdown_event.is_set():

            print(
                "[CYBER-FLY] reconnecting..."
            )

            time.sleep(1)


# ============================================================
# JPEG Parser
# ============================================================

class JPEGParser:

    def __init__(self):

        self.buffer = bytearray()

    def feed(
        self,
        data,
    ):

        self.buffer.extend(
            data
        )

        frames = []

        while True:

            start = self.buffer.find(
                b"\xff\xd8"
            )

            if start < 0:

                self.buffer.clear()

                break

            end = self.buffer.find(
                b"\xff\xd9",
                start + 2,
            )

            if end < 0:

                if start > 0:

                    del self.buffer[
                        :start
                    ]

                break

            end += 2

            frame = bytes(
                self.buffer[
                    start:end
                ]
            )

            del self.buffer[
                :end
            ]

            frames.append(
                frame
            )

        return frames


# ============================================================
# JPEG Dimensions
# ============================================================

def jpeg_dimensions(
    data
):
    """
    從 JPEG SOF marker 取得：

        width
        height

    不需要額外 Python image library。
    """

    if len(data) < 10:
        return None

    if data[:2] != b"\xff\xd8":
        return None

    i = 2

    sof_markers = {
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC5,
        0xC6,
        0xC7,
        0xC9,
        0xCA,
        0xCB,
        0xCD,
        0xCE,
        0xCF,
    }

    while i + 9 < len(data):

        if data[i] != 0xFF:

            i += 1

            continue

        while (
            i < len(data)
            and data[i] == 0xFF
        ):
            i += 1

        if i >= len(data):
            break

        marker = data[i]
        i += 1

        if marker in (
            0xD8,
            0xD9,
        ):
            continue

        if (
            0xD0
            <= marker
            <= 0xD7
        ):
            continue

        if i + 2 > len(data):
            break

        segment_length = (
            (data[i] << 8)
            | data[i + 1]
        )

        if segment_length < 2:
            return None

        if (
            marker in sof_markers
            and i + 7 <= len(data)
        ):

            height = (
                (data[i + 3] << 8)
                | data[i + 4]
            )

            width = (
                (data[i + 5] << 8)
                | data[i + 6]
            )

            if width > 0 and height > 0:

                return (
                    width,
                    height,
                )

            return None

        i += segment_length

    return None


# ============================================================
# RGB Frame Sender
# ============================================================

def send_rgb_frame(
    raw_rgb,
    width,
    height,
):
    """
    將 RGB24 raw frame 包成 Cyber-Fly frame message。
    """

    expected = (
        width
        * height
        * 3
    )

    if len(raw_rgb) != expected:

        print(
            "[FRAME] invalid RGB size:",
            len(raw_rgb),
            "expected:",
            expected,
        )

        return False

    message = {
        "type": "frame",
        "width": width,
        "height": height,
        "channels": 3,
        "pixels": base64.b64encode(
            raw_rgb
        ).decode("ascii"),
    }

    return send_to_cyberfly(
        message
    )


# ============================================================
# Scrcpy Stream
# ============================================================

class ScrcpyStream:

    def __init__(self):

        self.socket = None

        self.ffmpeg_process = None

        self.decoder_process = None

        self.width = None
        self.height = None

    def connect(self):

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        sock.settimeout(5)

        sock.connect(
            (
                SCRCPY_HOST,
                SCRCPY_PORT,
            )
        )

        sock.settimeout(None)

        self.socket = sock

        print(
            "[SCRCPY] connected to "
            f"{SCRCPY_HOST}:"
            f"{SCRCPY_PORT}"
        )

    def start_ffmpeg(self):

        command = [
            FFMPEG,

            "-loglevel",
            "quiet",

            "-f",
            "h264",

            "-i",
            "pipe:0",

            "-f",
            "mjpeg",

            "-q:v",
            str(JPEG_QUALITY),

            "pipe:1",
        ]

        self.ffmpeg_process = (
            subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        )

        print(
            "[FFMPEG] H264 -> MJPEG started"
        )

    def start_decoder(self):

        command = [
            FFMPEG,

            "-loglevel",
            "quiet",

            "-f",
            "mjpeg",

            "-i",
            "pipe:0",

            "-f",
            "rawvideo",

            "-pix_fmt",
            "rgb24",

            "pipe:1",
        ]

        self.decoder_process = (
            subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        )

        print(
            "[FFMPEG] MJPEG -> RGB24 started"
        )

    def feed_ffmpeg(self):

        try:

            while not shutdown_event.is_set():

                data = self.socket.recv(
                    65536
                )

                if not data:
                    break

                self.ffmpeg_process.stdin.write(
                    data
                )

                self.ffmpeg_process.stdin.flush()

        except Exception as e:

            if not shutdown_event.is_set():

                print(
                    "[FFMPEG INPUT] error:",
                    e,
                )

        finally:

            try:
                self.ffmpeg_process.stdin.close()
            except Exception:
                pass

    def feed_decoder(self):

        parser = JPEGParser()

        try:

            while not shutdown_event.is_set():

                data = (
                    self.ffmpeg_process.stdout.read(
                        65536
                    )
                )

                if not data:
                    break

                frames = parser.feed(
                    data
                )

                for frame in frames:

                    if (
                        self.width is None
                        or self.height is None
                    ):

                        dimensions = (
                            jpeg_dimensions(
                                frame
                            )
                        )

                        if dimensions is None:

                            print(
                                "[FRAME] "
                                "could not determine "
                                "JPEG dimensions"
                            )

                            continue

                        self.width, self.height = (
                            dimensions
                        )

                        print(
                            "[FRAME] "
                            f"detected "
                            f"{self.width}x"
                            f"{self.height}"
                        )

                    self.decoder_process.stdin.write(
                        frame
                    )

                    self.decoder_process.stdin.flush()

        except Exception as e:

            if not shutdown_event.is_set():

                print(
                    "[DECODER INPUT] error:",
                    e,
                )

        finally:

            try:
                self.decoder_process.stdin.close()
            except Exception:
                pass

    def read_decoder(self):

        if (
            self.width is None
            or self.height is None
        ):

            print(
                "[DECODER] waiting for "
                "frame dimensions"
            )

        raw_buffer = bytearray()

        try:

            while not shutdown_event.is_set():

                data = (
                    self.decoder_process.stdout.read(
                        65536
                    )
                )

                if not data:
                    break

                raw_buffer.extend(
                    data
                )

                if (
                    self.width is None
                    or self.height is None
                ):
                    continue

                frame_size = (
                    self.width
                    * self.height
                    * 3
                )

                while (
                    len(raw_buffer)
                    >= frame_size
                ):

                    frame = bytes(
                        raw_buffer[
                            :frame_size
                        ]
                    )

                    del raw_buffer[
                        :frame_size
                    ]

                    send_rgb_frame(
                        frame,
                        self.width,
                        self.height,
                    )

        except Exception as e:

            if not shutdown_event.is_set():

                print(
                    "[DECODER OUTPUT] error:",
                    e,
                )

    def cleanup(self):

        try:

            if self.socket is not None:

                self.socket.close()

        except Exception:

            pass

        try:

            if (
                self.ffmpeg_process
                is not None
            ):

                self.ffmpeg_process.kill()

        except Exception:

            pass

        try:

            if (
                self.decoder_process
                is not None
            ):

                self.decoder_process.kill()

        except Exception:

            pass

        self.socket = None

        self.ffmpeg_process = None

        self.decoder_process = None

        self.width = None
        self.height = None

    def run_once(self):

        self.connect()

        self.start_ffmpeg()

        self.start_decoder()

        input_thread = threading.Thread(
            target=self.feed_ffmpeg,
            daemon=True,
        )

        mjpeg_thread = threading.Thread(
            target=self.feed_decoder,
            daemon=True,
        )

        rgb_thread = threading.Thread(
            target=self.read_decoder,
            daemon=True,
        )

        input_thread.start()
        mjpeg_thread.start()
        rgb_thread.start()

        input_thread.join()
        mjpeg_thread.join()
        rgb_thread.join()

        self.cleanup()

    def run(self):

        while not shutdown_event.is_set():

            try:

                self.run_once()

            except Exception as e:

                if not shutdown_event.is_set():

                    print(
                        "[SCRCPY] error:",
                        e,
                    )

                self.cleanup()

            if not shutdown_event.is_set():

                print(
                    "[SCRCPY] reconnecting..."
                )

                time.sleep(1)


# ============================================================
# CLI
# ============================================================

def cli_loop():

    print()
    print(
        "========================================"
    )
    print(
        " Cyber-Fly Android Bridge"
    )
    print(
        " UID 2000 Shell"
    )
    print(
        "========================================"
    )
    print()

    print(
        "Cyber-Fly:"
    )
    print(
        f"  {CYBERFLY_HOST}:"
        f"{CYBERFLY_PORT}"
    )

    print()

    print(
        "Commands:"
    )
    print(
        "  click"
    )
    print(
        "  double"
    )
    print(
        "  long"
    )
    print(
        "  swipe"
    )
    print(
        "  move forward"
    )
    print(
        "  move backward"
    )
    print(
        "  move left"
    )
    print(
        "  move right"
    )
    print(
        "  release"
    )
    print(
        "  semantic <SEMANTIC>"
    )
    print(
        "  status"
    )
    print(
        "  quit"
    )
    print()

    while not shutdown_event.is_set():

        try:

            command = input(
                "Bridge> "
            ).strip()

        except EOFError:

            break

        except KeyboardInterrupt:

            print()

            break

        if not command:
            continue

        parts = command.split()

        if (
            parts[0].lower()
            == "quit"
        ):

            shutdown_event.set()

            release_actions()

            close_cyberfly_socket()

            break

        if (
            parts[0].lower()
            == "status"
        ):

            with active_actions_lock:

                print(
                    "[STATUS] "
                    "active actions:",
                    len(active_actions),
                )

                for action in active_actions:

                    print(
                        " ",
                        action.semantic,
                        action.coordinate,
                    )

            sock = (
                get_cyberfly_socket()
            )

            print(
                "[STATUS] "
                "Cyber-Fly connected:",
                sock is not None,
            )

            continue

        if (
            parts[0].lower()
            == "release"
        ):

            handle_semantic(
                "RELEASE"
            )

            continue

        if (
            parts[0].lower()
            == "semantic"
        ):

            if len(parts) < 2:

                print(
                    "Usage: "
                    "semantic <SEMANTIC>"
                )

                continue

            handle_semantic(
                parts[1]
            )

            continue

        if (
            parts[0].lower()
            == "click"
        ):

            handle_semantic(
                "CLICK"
            )

            continue

        if (
            parts[0].lower()
            == "double"
        ):

            handle_semantic(
                "DOUBLE_CLICK"
            )

            continue

        if (
            parts[0].lower()
            == "long"
        ):

            handle_semantic(
                "LONG_PRESS"
            )

            continue

        if (
            parts[0].lower()
            == "swipe"
        ):

            handle_semantic(
                "SWIPE"
            )

            continue

        if (
            parts[0].lower()
            == "move"
        ):

            if len(parts) < 2:

                print(
                    "Usage: move "
                    "<forward|backward|"
                    "left|right>"
                )

                continue

            direction = (
                parts[1].lower()
            )

            mapping = {
                "forward":
                    "MOVE_FORWARD",

                "backward":
                    "MOVE_BACKWARD",

                "left":
                    "MOVE_LEFT",

                "right":
                    "MOVE_RIGHT",
            }

            semantic = mapping.get(
                direction
            )

            if semantic is None:

                print(
                    "Unknown move direction"
                )

                continue

            handle_semantic(
                semantic
            )

            continue

        print(
            "Unknown command:",
            command,
        )


# ============================================================
# Main
# ============================================================

def main():

    print()
    print(
        "========================================"
    )
    print(
        " Cyber-Fly Android Bridge"
    )
    print(
        "========================================"
    )
    print()

    print(
        f"Cyber-Fly server : "
        f"{CYBERFLY_HOST}:"
        f"{CYBERFLY_PORT}"
    )

    print(
        f"scrcpy relay     : "
        f"{SCRCPY_HOST}:"
        f"{SCRCPY_PORT}"
    )

    print(
        f"FFmpeg           : "
        f"{FFMPEG}"
    )

    print(
        f"FFmpeg lib       : "
        f"{FFMPEG_LIB_DIR}"
    )

    print(
        f"TEST_MODE        : "
        f"{TEST_MODE}"
    )

    print()

    if not Path(FFMPEG).is_file():

        print(
            "[ERROR] FFmpeg not found:"
        )

        print(
            f"        {FFMPEG}"
        )

        return 1

    if not os.access(
        FFMPEG,
        os.X_OK,
    ):

        print(
            "[ERROR] FFmpeg is not executable:"
        )

        print(
            f"        {FFMPEG}"
        )

        return 1

    if not Path(
        FFMPEG_LIB_DIR
    ).is_dir():

        print(
            "[ERROR] FFmpeg library directory "
            "not found:"
        )

        print(
            f"        {FFMPEG_LIB_DIR}"
        )

        return 1

    cyberfly_thread = threading.Thread(
        target=cyberfly_connection_loop,
        daemon=True,
    )

    cyberfly_thread.start()

    scrcpy = ScrcpyStream()

    scrcpy_thread = threading.Thread(
        target=scrcpy.run,
        daemon=True,
    )

    scrcpy_thread.start()

    cli_loop()

    shutdown_event.set()

    release_actions()

    close_cyberfly_socket()

    scrcpy.cleanup()

    print()
    print(
        "[BRIDGE] stopped"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )