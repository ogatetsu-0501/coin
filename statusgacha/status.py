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
import concurrent.futures           # 並列実行用ライブラリ

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
# 一致時クリック座標リスト
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
# 閾値到達一回だけクリック用セット（1～5箇所）
# ────────────────────────────────────────
thresholds_done = set()

# ────────────────────────────────────────
# 初回スキャンフラグ
# ────────────────────────────────────────
first_scan = True

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
    global first_scan
    left, top = target_window.left, target_window.top
    w, h      = target_window.width, target_window.height

    # 小学生にもわかるコメント：ループで繰り返し処理を行うよ
    while True:
        # ────────────────────────────────────────────────────
        # ウィンドウ全体をキャプチャするよ
        # ────────────────────────────────────────────────────
        screenshot = pyautogui.screenshot(region=(left, top, w, h))
        frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # ────────────────────────────────────────────────────
        # 並列化：テンプレートごとに一致度と完全一致判定を計算する関数
        # ────────────────────────────────────────────────────
        def check_template(idx):
            px, py = positions[idx]
            template = templates[idx]
            th, tw = template.shape[:2]
            region = frame[py:py+th, px:px+tw]

            # サイズチェック
            if region.shape[:2] != (th, tw):
                return idx, 0.0, False, False  # ratio, equal, valid=False

            # 一致度を計算
            matches = np.sum(region == template)
            ratio = matches / region.size
            equal = (matches == region.size)  # 完全一致か
            return idx, ratio, equal, True

        # ────────────────────────────────────────────────────
        # ThreadPoolExecutor で並列実行（最大テンプレート数）
        # ────────────────────────────────────────────────────
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(templates)) as executor:
            futures = [executor.submit(check_template, i) for i in range(len(templates))]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # ────────────────────────────────────────────────────
        # 結果をインデックス順にソート
        # ────────────────────────────────────────────────────
        results.sort(key=lambda x: x[0])

        # ────────────────────────────────────────────────────
        # 既存ロジック：個別一致チェック＆クリック
        # ────────────────────────────────────────────────────
        all_match = True
        for idx, ratio, equal, valid in results:
            # 既にクリック済みならスキップ
            if idx in clicked_indices:
                continue

            if not valid:
                print(f"[{names[idx]}] サイズ不一致")
                all_match = False
                continue

            # 一致度ログ
            print(f"[{names[idx]}] 一致度: {ratio:.2f}")

            # 完全一致かつ3箇所未満ならクリック
            if equal and len(clicked_indices) < 3:
                rel_x, rel_y = click_region_coords[idx]
                abs_x = left + rel_x
                abs_y = top  + rel_y

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

        # ────────────────────────────────────────────────────
        # 完全一致箇所数を数える
        # ────────────────────────────────────────────────────
        match_count = sum(1 for _, _, equal, valid in results if valid and equal)

        # ────────────────────────────────────────────────────
        # 初回スキャンで複数一致なら 1～match_count をスキップ扱い
        # ────────────────────────────────────────────────────
        if first_scan:
            if match_count > 1:
                up_to = min(match_count, 5)
                for i in range(1, up_to + 1):
                    thresholds_done.add(i)
                print(f"初回スキャン: 一致箇所 {match_count} 箇所 → 1～{up_to} をスキップ扱い")
            first_scan = False

        # ────────────────────────────────────────────────────
        # 閾値1～5箇所到達時のOK→Retryクリック（初回以降のみ）
        # ────────────────────────────────────────────────────
        if not first_scan and 1 <= match_count <= 5 and match_count not in thresholds_done:
            thresholds_done.add(match_count)
            target_window.restore()
            target_window.activate()
            time.sleep(0.1)
            # OKボタンをクリック
            pydirectinput.moveTo(left + click_all_ok[0], top + click_all_ok[1])
            time.sleep(0.05)
            pydirectinput.click()
            print(f"一致箇所 {match_count} 箇所 → OKボタンをクリック")
            time.sleep(0.2)
            # Retryボタンをクリック
            pydirectinput.moveTo(left + click_retry[0], top + click_retry[1])
            time.sleep(0.05)
            pydirectinput.click()
            print(f"一致箇所 {match_count} 箇所 → Retryボタンをクリック")
            time.sleep(0.2)
            continue  # ループ先頭に戻って再スキャン

        # ────────────────────────────────────────────────────
        # Ctrl+C 押下チェック（毎回確認）
        # ────────────────────────────────────────────────────
        if keyboard.is_pressed('ctrl+c') or (keyboard.is_pressed('ctrl') and keyboard.is_pressed('c')):
            print("Ctrl+C が検出されました。終了します。")
            sys.exit()

        # ────────────────────────────────────────────────────
        # 全一致／再試行ボタンのクリック（既存処理）
        # ────────────────────────────────────────────────────
        if all_match:
            target_window.restore()
            target_window.activate()
            time.sleep(0.1)
            pydirectinput.moveTo(left + click_all_ok[0], top + click_all_ok[1])
            time.sleep(0.05)
            pydirectinput.click()
            print("全6領域一致：OKボタンをクリックします。")
            sys.exit()
        else:
            target_window.restore()
            target_window.activate()
            time.sleep(0.1)
            pydirectinput.moveTo(left + click_retry[0], top + click_retry[1])
            time.sleep(0.05)
            pydirectinput.click()
            print("不一致検出：リトライボタンをクリックします。")
            time.sleep(0.2)
            continue  # ループ先頭に戻る

# Rキーに処理を登録
keyboard.on_press_key('r', on_r_press)
print("Rキーを押すと一致チェック→クリック処理を実行します。")
print("Ctrl+C でいつでもプログラムを終了できます。")
keyboard.wait()
