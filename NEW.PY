import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import keyboard
import os
import concurrent.futures
import time
import ctypes
import win32gui
import win32con

# Windows用のマウス操作に必要な型定義
PUL = ctypes.POINTER(ctypes.c_ulong)

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("mi", MouseInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]

# マウスボタンが押されているかを記録する変数
is_holding = False

# 最初のスクリーンショットを一度だけ撮るための変数
first_loop = True

# マウス左ボタンを押す関数
def send_mouse_down():
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(0, 0, 0, 0x0002, 0, ctypes.pointer(extra))
    command = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))
    print("[SendInput] マウス左ボタンを押しました")

# マウス左ボタンを離す関数
def send_mouse_up():
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(0, 0, 0, 0x0004, 0, ctypes.pointer(extra))
    command = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))
    print("[SendInput] マウス左ボタンを離しました")

# テンプレート画像を読み込む辞書
templates = {}
for i in range(14):
    path = f"{i}.png"
    if os.path.exists(path):
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            templates[str(i)] = img
        else:
            print(f"{path} の読み込みに失敗")
    else:
        print(f"{path} が見つかりません")

# テンプレートが読み込めなかったら終了
if not templates:
    print("テンプレートがありません")
    exit()

# ユーザーにウィンドウを選んでもらう
print("ウィンドウ上でAキーを押してください")
keyboard.wait("a")
x, y = pyautogui.position()
target_window = None
for win in gw.getWindowsWithTitle(""):
    if win.left <= x <= win.left + win.width and win.top <= y <= win.top + win.height:
        target_window = win
        break

# ウィンドウが見つからなければ終了
if target_window is None:
    print("ウィンドウが見つかりません")
    exit()

print(f"選択ウィンドウ: {target_window.title}")

# クライアント領域の座標と大きさを取得する関数
def get_client_rect(hwnd):
    rect = win32gui.GetClientRect(hwnd)
    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    width = rect[2] - rect[0]
    height = rect[3] - rect[1]
    return left, top, width, height

# 対象ウィンドウのハンドルを取得
hwnd = win32gui.FindWindow(None, target_window.title)

# ユーザーにクリック位置を登録させる
print("ゲーム内のクリックしたい位置でSキーを押してください")
keyboard.wait("s")
click_pos = pyautogui.position()
print(f"クリック座標登録: ({click_pos.x}, {click_pos.y})")

# 画像からテンプレートマッチングして最も一致した番号を返す関数
def process_and_match(capture_img):
    gray = cv2.cvtColor(capture_img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

    def match_template(name):
        tmpl = templates[name]
        if tmpl.shape != binary.shape:
            return name, -1
        result = cv2.matchTemplate(binary, tmpl, cv2.TM_CCOEFF_NORMED)
        return name, result[0][0]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(match_template, templates.keys()))

    best_match = max(results, key=lambda x: x[1])[0]
    return best_match

# 離す対象の番号リスト（最初は"1"のみ）
release_targets = ["1"]

# 離す対象の範囲を段階的に増やすカウンタ（0→["1"], 1→["1","2"], 2→["1","2","3"]...）
zero_trigger_count = 0

# 前回の13までに0が出たかどうか
zero_detected_since_last_13 = False

print("テンプレートマッチング開始。Ctrl+Aで終了")

# メインループ
while True:
    # 終了判定（Ctrl+A）
    if keyboard.is_pressed("ctrl+a"):
        print("終了します")
        if is_holding:
            send_mouse_up()
        break

    # 初回だけスクリーンショット保存
    if first_loop:
        left_c, top_c, width_c, height_c = get_client_rect(hwnd)
        full_img = pyautogui.screenshot(region=(left_c, top_c, width_c, height_c))
        full_img = np.array(full_img)
        full_img = cv2.cvtColor(full_img, cv2.COLOR_RGB2BGR)
        cv2.imwrite("image2.png", full_img)
        print("1回目のクライアント領域スクリーンショットを image2.png に保存しました")
        first_loop = False

    # 小さな範囲をスクショして画像に変換
    left = target_window.left + 217
    top = target_window.top + 32
    width, height = 17, 12
    img = pyautogui.screenshot(region=(left, top, width, height))
    img = np.array(img)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # テンプレートマッチして一致番号を取得
    match_name = process_and_match(img)
    print(f"一致: {match_name}")

    # 13が出たらカウントを進める＆リスト更新
    if match_name == "13":
        if zero_detected_since_last_13:
            zero_trigger_count += 1  # 離す対象の段階を1つ増やす
            zero_detected_since_last_13 = False
            print(f"13検出でリセット。離す番号: 1〜{1 + zero_trigger_count}")
        else:
            print("13検出したが0がなかったので変化なし")

        release_targets = [str(i) for i in range(1, 2 + zero_trigger_count)]

    # 0が出たらフラグを立てる
    elif match_name == "0":
        zero_detected_since_last_13 = True
        print("0を検出、13が来たら段階アップします")

    # 離す対象に含まれていなければ押し続ける
    if match_name not in release_targets:
        if not is_holding:
            send_mouse_down()
            is_holding = True
    else:
        if is_holding:
            send_mouse_up()
            is_holding = False

    # 処理の間隔（速すぎ防止）
    time.sleep(0.05)
