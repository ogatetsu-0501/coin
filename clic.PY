import cv2                           # 画像処理ライブラリ
import numpy as np                   # 配列処理ライブラリ
import pyautogui                     # スクリーンショット用ライブラリ
import pygetwindow as gw             # ウィンドウ情報取得ライブラリ
import keyboard                      # キーボード入力検知ライブラリ
import os                            # ファイルの存在確認
import concurrent.futures            # 並列処理ライブラリ
import time                          # 待機用ライブラリ
import pydirectinput                 # ゲーム用のマウス・キーボード操作ライブラリ

# ---------------- テンプレート画像の読み込み ----------------
templates = {}
for i in range(14):  # 0.png ～ 13.png を読み込む
    path = f"{i}.png"
    if os.path.exists(path):
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            templates[str(i)] = img
        else:
            print(f"{path} の読み込みに失敗しました。")
    else:
        print(f"{path} が見つかりません。")

if len(templates) == 0:
    print("テンプレート画像が見つかりません。終了します。")
    exit()

# ---------------- ウィンドウ選択処理 ----------------
print("【ウィンドウ選択】対象ウィンドウの上にマウスを置いて Aキー を押してください。")
keyboard.wait("a")  # Aキーが押されるまで待機
x, y = pyautogui.position()  # 現在のマウス座標を取得

# マウス下のウィンドウを取得
target_window = None
for win in gw.getAllWindows():
    if win.left <= x <= win.left + win.width and win.top <= y <= win.top + win.height:
        target_window = win
        break

if target_window is None:
    print("ウィンドウが見つかりません。終了します。")
    exit()

print(f"対象ウィンドウが選ばれました: {target_window.title}")
print("Ctrl + A で終了します。")

# ---------------- テンプレートマッチ処理関数 ----------------
def process_and_match(capture_img):
    # 画像をグレースケールに変換
    gray = cv2.cvtColor(capture_img, cv2.COLOR_BGR2GRAY)

    # しきい値127で2値化（白黒）
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

    # テンプレートとマッチングを行う関数
    def match_template(template_name):
        template_img = templates[template_name]
        if template_img.shape != binary.shape:
            return template_name, -1  # サイズ不一致ならスキップ
        result = cv2.matchTemplate(binary, template_img, cv2.TM_CCOEFF_NORMED)
        return template_name, result[0][0]  # (テンプレート名, 類似度スコア)

    # 並列で全テンプレートと比較
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(match_template, templates.keys()))

    # 最もスコアが高いテンプレート名を返す
    best_match = max(results, key=lambda x: x[1])[0]
    return best_match

# ---------------- メインループ ----------------
while True:
    # Ctrl + A で終了
    if keyboard.is_pressed("ctrl+a"):
        print("終了します。")
        break

    # ウィンドウ (217,32) の 17x12 領域をスクリーンショット
    left = target_window.left + 217
    top = target_window.top + 32
    width, height = 17, 12

    screenshot = pyautogui.screenshot(region=(left, top, width, height))
    screenshot = np.array(screenshot)
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)  # RGB → BGR

    # テンプレートマッチング実行
    match_name = process_and_match(screenshot)
    print(f"最も一致した画像: {match_name}")

    # "1" 以外だったら ウィンドウの中央（X）× 上1/4（Y）をクリック
    if match_name != "1":
        click_x = target_window.left + target_window.width // 2
        click_y = target_window.top + target_window.height // 4
        pydirectinput.click(x=click_x, y=click_y)
        print("→ ウィンドウ上1/4の位置をクリックしました。")

    time.sleep(0.8)  # 高速処理のため最小の待機時間（必要なら調整）
