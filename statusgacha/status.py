import cv2                          # 画像処理用ライブラリ
import numpy as np                  # 数値計算・配列操作用ライブラリ
import pyautogui                    # 画面キャプチャ用ライブラリ
import time                         # 待機用ライブラリ
import pygetwindow as gw            # ウィンドウ取得用ライブラリ
import keyboard                     # キーボード検知用ライブラリ
import pydirectinput                # ゲーム向けマウス／キー送信ライブラリ
import os                           # ファイル操作用ライブラリ
import sys                          # プログラム終了用ライブラリ
import signal                       # Ctrl+C 受け取り用ライブラリ

# ────────────────────────────────────────
# Ctrl+C をどこでもキャッチして終了する
# ────────────────────────────────────────
def _sigint_handler(signum, frame):
    print("\nKeyboardInterrupt を受け取りました。プログラムを終了します。")
    sys.exit()
signal.signal(signal.SIGINT, _sigint_handler)

# ────────────────────────────────────────
# スクリプト配置フォルダ取得
# ────────────────────────────────────────
script_dir = os.path.dirname(os.path.abspath(__file__))

# ────────────────────────────────────────
# テンプレート画像情報（ファイル名, 左上座標, 範囲名）
# ────────────────────────────────────────
template_info = [
    ("STRbar.png", (584, 262), "STR"),
    ("MAGbar.png", (584, 285), "MAG"),
    ("CONbar.png", (584, 309), "CON"),
    ("SPRbar.png", (584, 332), "SPR"),
    ("AGIbar.png", (584, 355), "AGI"),
    ("LUKbar.png", (584, 379), "LUK"),
]

# ────────────────────────────────────────
# 範囲一致時に一度だけクリックする座標
# （スクリーンショット原点(0,0)基準）
# ────────────────────────────────────────
click_region_coords = [
    (809, 266),
    (809, 289),
    (809, 313),
    (809, 336),
    (809, 359),
    (809, 383),
]

# ────────────────────────────────────────
# 全一致／再試行時のクリック座標
# ────────────────────────────────────────
click_all_ok = (750, 563)   # 全6領域一致したらここをクリック
click_retry  = (560, 563)   # 不一致ならここをクリックして再試行

# ────────────────────────────────────────
# テンプレート画像読み込み＆リスト作成
# ────────────────────────────────────────
templates = []
positions = []
names     = []
for fname, pos, name in template_info:
    path = os.path.join(script_dir, fname)
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        print(f"テンプレート画像が見つかりません: {path}")
        sys.exit()
    templates.append(img)
    positions.append(pos)
    names.append(name)

# ────────────────────────────────────────
# 一度クリックした範囲インデックスを保持するセット
# ────────────────────────────────────────
clicked_indices = set()

# ────────────────────────────────────────
# 対象ウインドウ登録（Aキーで設定）
# ────────────────────────────────────────
print("【対象ウインドウ登録】対象ウインドウ上で A キーを押してください。")
keyboard.wait("a")
mx, my = pyautogui.position()
target_window = None
for win in gw.getAllWindows():
    if win.left <= mx <= win.left + win.width and win.top <= my <= win.top + win.height:
        target_window = win
        break
if target_window is None:
    print("対象ウインドウが見つかりませんでした。")
    sys.exit()
print("対象ウインドウが決定されました:", target_window.title)

# ────────────────────────────────────────
# Rキー押下時の一致チェック＆クリック処理
# ────────────────────────────────────────
def on_r_press(event=None):
    left, top = target_window.left, target_window.top
    w, h     = target_window.width, target_window.height

    # 小学生にもわかるコメント：ウィンドウ全体をキャプチャするよ
    screenshot = pyautogui.screenshot(region=(left, top, w, h))
    frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    all_match = True

    # 各領域を順にチェック
    for idx, template in enumerate(templates):
        # クリック済みの領域は後回し（取得もスキップ）
        if idx in clicked_indices:
            continue

        px, py = positions[idx]
        th, tw = template.shape[:2]
        region = frame[py:py+th, px:px+tw]

        # 小学生にもわかるコメント：範囲名と一致度をログに出すよ
        # ピクセル単位で一致数を数える
        matches = np.sum(region == template)
        total   = region.size
        ratio   = matches / total
        print(f"[{names[idx]}] 一致度: {ratio:.2f}")

        # サイズが違う場合は不一致扱い
        if region.shape[:2] != (th, tw):
            all_match = False
            continue

        # 完全一致なら一度だけクリック（先着3箇所まで）
        if ratio == 1.0 and len(clicked_indices) < 3:
            rel_x, rel_y = click_region_coords[idx]
            abs_x = left + rel_x
            abs_y = top  + rel_y

            # 小学生にもわかるコメント：ウィンドウをアクティブ→移動→クリック
            target_window.restore()
            target_window.activate()
            time.sleep(0.1)
            pydirectinput.moveTo(abs_x, abs_y)
            time.sleep(0.05)
            pydirectinput.click()
            print(f"[{names[idx]}] 一致 → ({abs_x},{abs_y}) をクリック")
            clicked_indices.add(idx)
        else:
            all_match = False

    # ────────────────────────────────────────
    # Ctrl+C 押下チェック（毎回確認）
    # ────────────────────────────────────────
    if keyboard.is_pressed('ctrl+c') or (keyboard.is_pressed('ctrl') and keyboard.is_pressed('c')):
        print("Ctrl+C が検出されました。終了します。")
        sys.exit()

    # ────────────────────────────────────────
    # 全一致／再試行ボタンのクリック
    # ────────────────────────────────────────
    if all_match:
        rel_x, rel_y = click_all_ok
        print("全6領域一致：OKボタンをクリックします。")
    else:
        rel_x, rel_y = click_retry
        print("不一致検出：リトライボタンをクリックします。")
    abs_x = left + rel_x
    abs_y = top  + rel_y

    target_window.restore()
    target_window.activate()
    time.sleep(0.1)
    pydirectinput.moveTo(abs_x, abs_y)
    time.sleep(0.05)
    pydirectinput.click()

    # 全一致なら終了、そうでなければ少し待って再試行
    if all_match:
        sys.exit()
    else:
        time.sleep(0.2)
        on_r_press()

# Rキーに処理を登録
keyboard.on_press_key('r', on_r_press)
print("Rキーを押すと一致チェック→クリック処理を実行します。")
print("Ctrl+C でいつでもプログラムを終了できます。")
keyboard.wait()
