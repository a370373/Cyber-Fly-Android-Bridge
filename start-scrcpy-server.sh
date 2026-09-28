#!/system/bin/sh

# ============================================================
# Cyber-Fly / My-ADB-Shell
# scrcpy Server Launcher
#
# Architecture:
#
# UID 2000
#
#   scrcpy Server
#        ↓
#   localabstract:scrcpy
#        ↓
#   Python TCP Relay
#        ↓
#   127.0.0.1:1234
#        ↓
#   Cyber-Fly Android Bridge
#
# Python:
#   Provided by Termux
#
# 1234 is created INSIDE the UID 2000 environment.
# No adb forward is required here.
# ============================================================

clear

VERSION="4.1"

SERVER="/data/local/tmp/scrcpy-server.jar"

HOST="127.0.0.1"
PORT="1234"
SOCKET="scrcpy"

# Termux-provided Python.
#
# IMPORTANT:
# The Python process is launched BY UID 2000.
# Termux only provides the Python executable/runtime.
#
PYTHON="/data/data/com.termux/files/usr/bin/python"

echo "======================================"
echo " Cyber-Fly scrcpy Server"
echo "======================================"
echo
echo "[INFO] Checking UID..."

# ------------------------------------------------------------
# UID check
# ------------------------------------------------------------

UID_NOW="$(id -u 2>/dev/null)"

if [ "$UID_NOW" != "2000" ]; then
    echo "[ERROR] This script must run as Android UID 2000."
    echo "[ERROR] Current UID: $UID_NOW"
    exit 1
fi

echo "[OK] UID 2000"

# ------------------------------------------------------------
# Server check
# ------------------------------------------------------------

if [ ! -f "$SERVER" ]; then
    echo "[ERROR] scrcpy server not found:"
    echo "        $SERVER"
    exit 1
fi

echo "[OK] scrcpy server found"
echo "     $SERVER"

# ------------------------------------------------------------
# app_process check
# ------------------------------------------------------------

if ! command -v app_process >/dev/null 2>&1; then
    echo "[ERROR] app_process not found."
    exit 1
fi

echo "[OK] app_process"

# ------------------------------------------------------------
# Python check
# ------------------------------------------------------------

echo "[INFO] Checking Termux Python..."

if [ ! -x "$PYTHON" ]; then
    echo "[ERROR] Termux Python not found or not executable:"
    echo "        $PYTHON"
    exit 1
fi

echo "[OK] Python:"
echo "     $PYTHON"

# ------------------------------------------------------------
# Python runtime check
# ------------------------------------------------------------

echo "[INFO] Testing Python runtime..."

PYTHON_VERSION="$("$PYTHON" --version 2>&1)"

if [ $? -ne 0 ]; then
    echo "[ERROR] Termux Python could not be executed."
    echo
    echo "Path:"
    echo "    $PYTHON"
    echo
    echo "Output:"
    echo "    $PYTHON_VERSION"
    exit 1
fi

echo "[OK] $PYTHON_VERSION"

# ------------------------------------------------------------
# Stop old relay if possible
# ------------------------------------------------------------

echo
echo "[INFO] Checking TCP port $PORT..."

# Best-effort cleanup.
#
# The relay is created from this launcher, and the process is
# normally cleaned up when scrcpy exits.
#
# Keep this optional in case pkill is unavailable.
#

if command -v pkill >/dev/null 2>&1; then
    pkill -f "CYBER_FLY_SCRCPY_RELAY_1234" 2>/dev/null
fi

# ------------------------------------------------------------
# Start UID 2000 local TCP relay
#
# TCP:
#     127.0.0.1:1234
#
# forwards raw bytes to:
#
#     @scrcpy
#
# Android localabstract socket.
# ------------------------------------------------------------

echo "[INFO] Starting local TCP relay..."
echo
echo "       TCP:"
echo "       127.0.0.1:$PORT"
echo
echo "       ↓"
echo
echo "       Android localabstract:"
echo "       @$SOCKET"
echo

"$PYTHON" - "$HOST" "$PORT" "$SOCKET" <<'PYTHON' &
# CYBER_FLY_SCRCPY_RELAY_1234

import socket
import sys
import threading
import signal
import time


HOST = sys.argv[1]
PORT = int(sys.argv[2])
SOCKET_NAME = sys.argv[3]

running = True
server_socket = None


# ------------------------------------------------------------
# Signal handler
# ------------------------------------------------------------

def stop_handler(signum, frame):
    global running

    running = False

    try:
        if server_socket is not None:
            server_socket.close()
    except Exception:
        pass


signal.signal(signal.SIGTERM, stop_handler)
signal.signal(signal.SIGINT, stop_handler)


# ------------------------------------------------------------
# Bidirectional pipe
# ------------------------------------------------------------

def pipe(src, dst):

    try:

        while running:

            data = src.recv(65536)

            if not data:
                break

            dst.sendall(data)

    except Exception:
        pass

    finally:

        try:
            src.shutdown(socket.SHUT_RD)
        except Exception:
            pass

        try:
            dst.shutdown(socket.SHUT_WR)
        except Exception:
            pass


# ------------------------------------------------------------
# Handle TCP client
# ------------------------------------------------------------

def handle_client(client):

    abstract_socket = None

    try:

        # ----------------------------------------------------
        # Android localabstract socket
        #
        # Linux abstract UNIX socket:
        #
        #     \0scrcpy
        #
        # Android:
        #
        #     localabstract:scrcpy
        # ----------------------------------------------------

        abstract_socket = socket.socket(
            socket.AF_UNIX,
            socket.SOCK_STREAM
        )

        abstract_socket.connect(
            "\0" + SOCKET_NAME
        )

        # ----------------------------------------------------
        # TCP -> Android localabstract
        # ----------------------------------------------------

        t1 = threading.Thread(
            target=pipe,
            args=(client, abstract_socket),
            daemon=True
        )

        # ----------------------------------------------------
        # Android localabstract -> TCP
        # ----------------------------------------------------

        t2 = threading.Thread(
            target=pipe,
            args=(abstract_socket, client),
            daemon=True
        )

        t1.start()
        t2.start()

        t1.join()
        t2.join()

    except Exception:
        pass

    finally:

        try:
            if abstract_socket is not None:
                abstract_socket.close()
        except Exception:
            pass

        try:
            client.close()
        except Exception:
            pass


# ------------------------------------------------------------
# TCP listener
# ------------------------------------------------------------

try:

    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server_socket.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server_socket.bind(
        (HOST, PORT)
    )

    server_socket.listen(4)

    print(
        "[RELAY] CYBER_FLY_SCRCPY_RELAY_1234 READY",
        flush=True
    )

    print(
        "[RELAY] Listening on %s:%d"
        % (HOST, PORT),
        flush=True
    )

    print(
        "[RELAY] Forward target: localabstract:%s"
        % SOCKET_NAME,
        flush=True
    )

    # --------------------------------------------------------
    # Accept clients
    # --------------------------------------------------------

    while running:

        try:

            server_socket.settimeout(1.0)

            client, address = server_socket.accept()

        except socket.timeout:

            continue

        except Exception:

            if not running:
                break

            time.sleep(0.1)
            continue

        print(
            "[RELAY] Client connected: %s:%s"
            % (address[0], address[1]),
            flush=True
        )

        thread = threading.Thread(
            target=handle_client,
            args=(client,),
            daemon=True
        )

        thread.start()


except Exception as e:

    print(
        "[RELAY] ERROR: %s"
        % e,
        flush=True
    )


finally:

    try:
        if server_socket is not None:
            server_socket.close()
    except Exception:
        pass

PYTHON_RELAY_PID=$!

sleep 1

# ------------------------------------------------------------
# Check relay process
# ------------------------------------------------------------

if kill -0 "$PYTHON_RELAY_PID" 2>/dev/null; then

    echo "[OK] UID 2000 TCP relay started."
    echo "[OK] 127.0.0.1:$PORT"

else

    echo "[ERROR] Failed to start TCP relay."
    exit 1

fi

# ------------------------------------------------------------
# Start scrcpy Server
# ------------------------------------------------------------

echo
echo "======================================"
echo " Starting scrcpy Server"
echo "======================================"
echo
echo "[INFO] Version      : $VERSION"
echo "[INFO] Server       : $SERVER"
echo "[INFO] UID          : $UID_NOW"
echo "[INFO] Python       : $PYTHON"
echo "[INFO] Socket       : localabstract:$SOCKET"
echo "[INFO] TCP endpoint : 127.0.0.1:$PORT"
echo
echo "[INFO] raw_stream   : true"
echo "[INFO] audio        : false"
echo "[INFO] control      : false"
echo

CLASSPATH="$SERVER" \
app_process / \
com.genymobile.scrcpy.Server \
"$VERSION" \
tunnel_forward=true \
audio=false \
control=false \
cleanup=false \
raw_stream=true \
max_size=1920

RESULT=$?

# ------------------------------------------------------------
# Cleanup
# ------------------------------------------------------------

echo
echo "[INFO] scrcpy Server exited."
echo "[INFO] Exit code: $RESULT"

if kill -0 "$PYTHON_RELAY_PID" 2>/dev/null; then

    echo "[INFO] Stopping TCP relay..."

    kill "$PYTHON_RELAY_PID" 2>/dev/null

fi

wait "$PYTHON_RELAY_PID" 2>/dev/null

echo "[INFO] TCP relay stopped."

echo
echo "======================================"
echo " Finished"
echo "======================================"

exit "$RESULT"