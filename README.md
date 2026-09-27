## 🪰 Cyber-Fly Bridge

Cyber-Fly Bridge 是 Cyber-Fly / MaleCNS 數位果蠅神經系統與真實 Android 裝置之間的環境橋接層。

Bridge 本身不負責判斷果蠅的「真正意圖」，也不訓練果蠅玩特定 App。

它只負責：

«接收環境 → 傳送神經系統 → 接收行為語意 → 執行對應操作 → 取得新的環境 → 重複»

也就是：

看見
 ↓
神經處理
 ↓
產生語意
 ↓
執行行動
 ↓
看見新的結果
 ↓
再次行動
 ↓
...

---

## 📌 專案定位

Cyber-Fly Bridge 採用 純 CLI 架構。

Android 端不需要：

- Android Studio
- AndroidIDE
- AIDE
- Gradle
- APK
- 自訂 Android Application

Bridge 直接在 Android 的 UID 2000 Shell 環境中執行。

主要依賴：

- "Python"
- "scrcpy"
- "rish / Shizuku"
- "adb"
- Android Shell / "input"
- TCP

---

## 🏗️ 架構

                    Cyber-Fly / MaleCNS
                           │
                           │ TCP :8765
                           │
                    ┌──────▼──────┐
                    │   bridge.py │
                    │              │
                    │  Environment │
                    │  Translator  │
                    │  Action      │
                    │  Executor    │
                    └──────┬──────┘
                           │
             ┌─────────────┴─────────────┐
             │                           │
        Screen Input                Action Output
             │                           │
          scrcpy                 Android Shell
             │                           │
             ▼                           ▼
       Android Screen              input tap/swipe

Bridge 的核心概念：

Android
   ↓
scrcpy
   ↓
Screen Frame
   ↓
bridge.py
   ↓
TCP :8765
   ↓
Cyber-Fly
   ↓
Semantic Behavior
   ↓
bridge.py
   ↓
coordinates.py
   ↓
Android Shell
   ↓
Android

---

## 📂 專案結構

最基本的 Bridge 只需要兩個 Python 檔案：

Cyber-Fly-Bridge/
│
├── bridge.py
│
├── coordinates.py
│
└── README.md

---

## 📄 coordinates.py

"coordinates.py" 負責保存 環境座標資料。

Bridge 的程式邏輯與座標資料分離。

例如：

COORDINATES = {
    "CLICK": [
        (500, 800),
        (700, 900),
        (900, 1000),
    ],

    "DOUBLE_CLICK": [
        (500, 800),
        (700, 900),
    ],

    "LONG_PRESS": [
        (600, 900),
    ],

    "SWIPE": [
        (500, 500),
        (800, 600),
    ],

    "MOVE_FORWARD": [
        (600, 700),
    ],

    "MOVE_BACKWARD": [
        (600, 700),
    ],

    "MOVE_LEFT": [
        (600, 700),
    ],

    "MOVE_RIGHT": [
        (600, 700),
    ],
}

同一個語意可以擁有：

一個座標
多個座標
大量座標

Bridge 會從對應座標中進行隨機選擇。

---

## 🎲 座標選擇

如果某個語意只有一個座標：

CLICK
 └── (500, 800)

直接使用該座標。

如果有多個：

CLICK
 ├── (500, 800)
 ├── (700, 900)
 ├── (900, 1000)
 └── (1000, 700)

Bridge 可以隨機選擇：

一個
多個
全部

例如一次可能選：

(500, 800)
(900, 1000)

下一次可能選：

(700, 900)

再下一次可能：

全部座標

座標本身是實驗環境設定，不是果蠅的「意圖」。

---

## 🧠 Cyber-Fly 語意

目前 Bridge 支援以下語意：

語意| 意義
"NONE"| 無動作
"CLICK"| 點擊
"DOUBLE_CLICK"| 雙擊
"LONG_PRESS"| 長按
"RELEASE"| 放開 / 取消持續行為
"SWIPE"| 滑動
"MOVE_FORWARD"| 向前移動
"MOVE_BACKWARD"| 向後移動
"MOVE_LEFT"| 向左移動
"MOVE_RIGHT"| 向右移動

---

## 🖱️ CLICK

CLICK

Bridge：

1. 找到 "CLICK" 座標。
2. 隨機選擇一個或多個座標。
3. 建立 Android Shell 指令。
4. 自動執行。

概念：

Cyber-Fly
    ↓
CLICK
    ↓
coordinates.py
    ↓
選擇座標
    ↓
input tap X Y

操作完成後立即結束。

---

## 🖱️ DOUBLE_CLICK

DOUBLE_CLICK

在選定座標執行兩次點擊：

tap
 ↓
短暫間隔
 ↓
tap

操作完成後立即結束。

---

## ✋ LONG_PRESS

LONG_PRESS

長按屬於持續行為。

啟動後：

LONG_PRESS
     ↓
開始操作
     ↓
保持
     ↓
等待 RELEASE

它不會自己立即結束。

---

## 👆 SWIPE

SWIPE

Bridge 從設定的 "SWIPE" 座標開始。

終點由 Bridge 自行決定。

起點
 ↓
Bridge 隨機決定方向 / 終點
 ↓
滑動
 ↓
約 1～2 秒
 ↓
結束

因此：

«果蠅只產生 "SWIPE"。»

Bridge 不解釋：

«「果蠅到底想往哪裡？」»

終點屬於 Bridge 的環境映射。

---

## 🕹️ MOVE_FORWARD

MOVE_FORWARD

從指定座標開始進行短距離移動。

這類 "MOVE_*" 行為屬於持續行為。

MOVE_FORWARD
       ↓
短距離移動
       ↓
保持 / 持續
       ↓
RELEASE
       ↓
停止

---

## 🕹️ MOVE_BACKWARD

MOVE_BACKWARD

與 "MOVE_FORWARD" 相同，但方向相反。

---

## 🕹️ MOVE_LEFT

MOVE_LEFT

從指定座標開始向左進行有限距離的移動。

持續直到：

RELEASE

---

## 🕹️ MOVE_RIGHT

MOVE_RIGHT

從指定座標開始向右進行有限距離的移動。

持續直到：

RELEASE

---

## 🛑 RELEASE

"RELEASE" 用於取消目前正在進行的持續行為。

目前持續行為包括：

LONG_PRESS
MOVE_FORWARD
MOVE_BACKWARD
MOVE_LEFT
MOVE_RIGHT

Bridge 可以：

取消一個
取消多個
取消全部

並且可以採取隨機方式決定取消哪些目前活動中的操作。

例如：

目前：

LONG_PRESS
MOVE_LEFT
MOVE_RIGHT

收到：

RELEASE

可能：

取消 MOVE_LEFT

也可能：

取消 LONG_PRESS + MOVE_RIGHT

或者：

全部取消

"RELEASE" 不包含 Circle ID。

---

## ❌ NONE

NONE

代表：

無動作

Bridge 不執行任何 Android 操作。

---

## ❓ 未支援語意

如果 Cyber-Fly 傳送 Bridge 尚未支援的語意：

UNKNOWN

或其他未知值。

Bridge 將其視為：

NONE

不執行任何操作。

Bridge 不會自行猜測未知語意的意思。

---

## 🔌 TCP

Cyber-Fly 與 Bridge 使用 TCP 通訊。

預設：

PORT = 8765

概念：

Cyber-Fly
     │
     │ TCP :8765
     ▼
bridge.py

TCP 負責傳輸：

Cyber-Fly → Bridge

Semantic Behavior

例如：

CLICK
DOUBLE_CLICK
LONG_PRESS
RELEASE
SWIPE
MOVE_FORWARD
MOVE_BACKWARD
MOVE_LEFT
MOVE_RIGHT
NONE

Bridge → Cyber-Fly

Screen Frame

Bridge 將 Android 畫面持續提供給 Cyber-Fly。

---

##📱 Android Screen

Android 畫面由：

scrcpy

取得。

Bridge 的目標不是：

截一張圖
→ 分析
→ 結束

而是持續環境循環：

Frame
 ↓
Cyber-Fly
 ↓
Behavior
 ↓
Android Action
 ↓
新的 Frame
 ↓
Cyber-Fly
 ↓
Behavior
 ↓
...

也就是：

Environment ↔ Cyber-Fly

Bridge 是兩者之間的適配器。

---

## 🖥️ UID 2000

Bridge 預期在 Android UID 2000 Shell 環境中執行。

例如透過：

rish

取得 Shell。

然後啟動：

python bridge.py

Bridge 不要求使用者每次手動輸入 Cyber-Fly 產生的指令。

例如 Cyber-Fly 產生：

CLICK

Bridge 自己完成：

解析
 ↓
選擇座標
 ↓
建立 Shell 指令
 ↓
執行

使用者不需要手動輸入：

input tap 500 800

---

## 🧪 CLI 測試

Bridge 可以提供 CLI 供人工測試。

例如：

> click 500 800

或：

> long 600 900

或：

> swipe 300 500 800 500

或：

> release

這些指令只是：

«Bridge 開發 / 除錯用的人類輸入。»

正常 Cyber-Fly 運作時：

Cyber-Fly
   ↓
Semantic
   ↓
Bridge
   ↓
Automatic Execution

不需要人工介入。

---

## 🤖 Bridge 不負責什麼？

Bridge 不負責：

- 判斷果蠅真正意圖
- 解釋 MaleCNS 的心理狀態
- 決定果蠅應該做什麼
- 訓練果蠅
- 教果蠅玩遊戲
- 判斷 App 裡的目標
- 將行為重新解釋成「人類想法」

例如：

MaleCNS → CLICK

Bridge 不會判斷：

「果蠅想點這個按鈕」

而只是：

CLICK
 ↓
執行 CLICK 對應的環境操作

---

## 🧪 實驗哲學

Cyber-Fly Bridge 的核心原則：

«人類不指定行為，只盡量避免環境讓所有行為都變成無效行為。»

因此：

人類
 ↓
設定實驗環境
 ↓
設定必要座標
 ↓
啟動 Bridge
 ↓
Cyber-Fly 自行產生行為
 ↓
Bridge 執行
 ↓
觀察結果

人類主要負責：

Environment Configuration

而不是：

Behavior Selection

---

## 🔄 完整閉環

完整運作流程：

┌─────────────────────────────┐
│         Android             │
│                             │
│       Current Screen        │
└──────────────┬──────────────┘
               │
               │ scrcpy
               ▼
┌─────────────────────────────┐
│          Bridge             │
│                             │
│       Screen Receiver       │
└──────────────┬──────────────┘
               │
               │ TCP
               ▼
┌─────────────────────────────┐
│       Cyber-Fly / MaleCNS   │
│                             │
│      Neural Processing      │
└──────────────┬──────────────┘
               │
               │ Semantic
               ▼
┌─────────────────────────────┐
│          Bridge             │
│                             │
│      Semantic Translator    │
└──────────────┬──────────────┘
               │
               │
               ▼
┌─────────────────────────────┐
│       coordinates.py        │
│                             │
│       Environment Map       │
└──────────────┬──────────────┘
               │
               │ Shell Command
               ▼
┌─────────────────────────────┐
│       Android Shell         │
│                             │
│       input / actions       │
└──────────────┬──────────────┘
               │
               ▼
          Android Screen
               │
               └───────────────┐
                               │
                               ▼
                         下一個 Frame

形成：

看見
 ↓
神經處理
 ↓
產生語意
 ↓
Bridge 翻譯
 ↓
執行
 ↓
環境改變
 ↓
再次看見
 ↓
...

---

## 🚀 啟動

進入 Android UID 2000 Shell：

rish

確認 UID：

id

應看到：

uid=2000(shell)

進入 Bridge：

cd /path/to/Cyber-Fly-Bridge
python bridge.py

---

## 📊 啟動狀態

Bridge 啟動後可以顯示：

======================================
        Cyber-Fly Bridge
======================================

TCP       : 8765
SCRCPY    : CONNECTED
UID       : 2000
STATUS    : RUNNING

Waiting for Cyber-Fly...
>

---

## ⚠️ 注意事項

## 1. Bridge 不等於 Cyber-Fly

Bridge 只是：

Environment Adapter

神經系統仍然由：

Cyber-Fly / MaleCNS

負責。

---

## 2. coordinates.py 是環境設定

座標代表：

「這個實驗環境允許 Bridge 在哪些位置執行操作」

並不代表：

「果蠅想點哪裡」

---

## 3. 不支援的語意不會被猜測

如果收到未知語意：

UNKNOWN

Bridge 不會自行推測。

直接：

NONE

---

## 4. 持續行為需要 RELEASE

以下行為屬於持續操作：

LONG_PRESS
MOVE_FORWARD
MOVE_BACKWARD
MOVE_LEFT
MOVE_RIGHT

正常情況下需要：

RELEASE

才能停止。

---

## 📜 License

本專案的授權方式依 GitHub Repository 實際 LICENSE 為準。

---

## 🪰 Cyber-Fly

Cyber-Fly 的目的不是讓果蠅學會操作手機。

而是：

建立神經系統
        ↓
連接真實環境
        ↓
讓神經活動產生外部行為
        ↓
觀察
        ↓
記錄
        ↓
研究

Bridge 只是讓：

數位神經系統
        ↕
真實 Android 環境

能夠真正連接起來的那一層。

«Receive → Translate → Execute → Observe → Repeat

接收 → 翻譯 → 執行 → 觀察 → 重複»

---

## 📬 聯繫創作者

- Instagram：[a370373/XRH](https://instagram.com/a370373)
- 本人17歲🤔 做的不好請見諒
- 獨立開發 ＆ AI協作
- 緩慢更新 ＆ 除錯
- 純手機Termux 開發👀
- 持續開發中…

---

## 👀作品 & 產品 集

- [Cyber-Fly-Android-Bridge](https://github.com/a370373/Cyber-Fly-Android-Bridge)
- [My-ADB-Shell](https://github.com/a370373/My-ADB-Shell/tree/main)
- [Cyber-Fly](https://github.com/a370373/Cyber-Fly)
- [MyOS](https://github.com/a370373/MyOS)
- [RWM-1:1 Real World Minecraft](https://github.com/a370373/RWM-Real-World-Minecraft)
- [MyAI-Offline Personal AI Agent System](https://github.com/a370373/MyAI-Offline-Personal-AI-Agent-System-/tree/main)
- [WCL - Web Clone Lab](https://github.com/a370373/web-clone-lab/)
- 持續增加中…👀

---

## 🤖 AI 協作

Cyber-Fly-Android-Bridge 由 a370373/XRH 發起、設計與開發。

開發過程中使用 OpenAI ChatGPT 作為 AI 協作夥伴，協助進行 技術分析、程式碼檢查、除錯 & 文件整理。

產品方向、設計理念 & 最終決策由專案創作者負責。
