import cv2                          # 画像処理用ライブラリ
import numpy as np                  # 数値計算・配列操作用ライブラリ
import pyautogui                    # 画面キャプチャやキー操作用ライブラリ
import time                         # 待機用ライブラリ
import pygetwindow as gw            # ウィンドウ位置・サイズ取得用ライブラリ
import keyboard                     # キーボード入力検知用ライブラリ
import pytesseract                  # OCR（文字認識）用ライブラリ
import pydirectinput                # ゲーム向けキー入力送信用ライブラリ
import concurrent.futures           # 並列処理用ライブラリ
import os                           # ファイル・ディレクトリ操作用ライブラリ

# pytesseract の設定：数字のみ認識する
tess_config = "--psm 7 -c tessedit_char_whitelist=0123456789"

# テンプレート画像 (image.png) の読み込み
template_path = "image.png"         # テンプレート画像のファイル名
template = cv2.imread(template_path, cv2.IMREAD_COLOR)
if template is None:
    print("テンプレート画像が見つかりません。")
    exit()

# 起動時にテンプレート画像にOCRをかけ、その結果をグローバル変数に保存
def get_template_text():
    # 小学生にもわかるコメント：テンプレートを白黒にして文字を読む準備をするよ
    t_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    ret, t_binary = cv2.threshold(t_gray, 144, 255, cv2.THRESH_BINARY)
    return pytesseract.image_to_string(t_binary, config=tess_config).strip()

template_text = get_template_text()
print(f"起動時のテンプレート画像のOCR結果: '{template_text}'")

# OCR を並列処理するための関数
def ocr_region(region):
    # 小学生にもわかるコメント：領域画像を白黒にして文字を読み込むよ
    region_gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    ret, region_binary = cv2.threshold(region_gray, 144, 255, cv2.THRESH_BINARY)
    return pytesseract.image_to_string(region_binary, config=tess_config).strip()

# ---------- 対象ウインドウの登録 ----------
print("【対象ウインドウ登録】対象ウインドウ上でAキーを押してください。")
keyboard.wait("a")                 # ユーザーがAキーを押すまで待機
x, y = pyautogui.position()        # Aキー押下時のマウス位置取得
target_window = None
for win in gw.getAllWindows():
    if win.left <= x <= win.left + win.width and win.top <= y <= win.top + win.height:
        target_window = win
        break
if target_window is None:
    print("対象ウインドウが見つかりません。")
    exit()
print("対象ウインドウが決定されました:", target_window.title)

# OCR対象の4箇所の座標（スクリーンショット内での相対座標）
positions = [(677,228), (677,299), (677,370), (677,440)]
temp_h, temp_w = template.shape[:2]

# ────────── ここから追加部分：Bキーで領域画像を保存 ──────────

# Bキーが押されたとき、その時点の4領域を保存する関数
def on_b_press(event):
    time.sleep(0.1)  # 小学生にもわかるコメント：ちょっと待つよ

    # ウインドウ位置とサイズを取得
    left = target_window.left
    top = target_window.top
    width = target_window.width
    height = target_window.height

    # 対象ウインドウ全体のスクリーンショットを取得
    screenshot = pyautogui.screenshot(region=(left, top, width, height))
    screenshot = np.array(screenshot)
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)

    # 画像保存用ディレクトリを作成
    save_dir = "captured_regions"
    os.makedirs(save_dir, exist_ok=True)

    # 各座標の領域を切り出して保存
    for idx, (px, py) in enumerate(positions, start=1):
        if px + temp_w > width or py + temp_h > height:
            print(f"領域{idx}がウインドウ外です、スキップします。")
            continue
        region = screenshot[py:py+temp_h, px:px+temp_w]
        filename = os.path.join(save_dir, f"region_{idx}_{int(time.time())}.png")
        cv2.imwrite(filename, region)
        print(f"領域{idx}を保存しました：{filename}")

# Bキー押下で on_b_press を呼び出す設定
keyboard.on_press_key('b', on_b_press)
print("Bキーで指定4領域の画像を保存できます。")

# ────────── 追加部分ここまで ──────────

# ---------- Rキー押下時の処理 ----------
def on_r_press(event):
    time.sleep(0.2)  # 0.3秒待機

    # 対象ウインドウの位置とサイズを取得
    left = target_window.left
    top = target_window.top
    width = target_window.width
    height = target_window.height

    # 対象ウインドウのスクリーンショットを取得
    screenshot = pyautogui.screenshot(region=(left, top, width, height))
    screenshot = np.array(screenshot)
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)

    # テンプレート画像のOCR結果は起動時に取得したもの (template_text)

    # 各指定領域について、領域画像を抽出
    regions = []
    valid_positions = []
    for pos in positions:
        px, py = pos
        s_h, s_w = screenshot.shape[:2]
        if px + temp_w > s_w or py + temp_h > s_h:
            continue
        region = screenshot[py:py+temp_h, px:px+temp_w]
        regions.append(region)
        valid_positions.append(pos)

    # 並列処理で各領域のOCR結果を取得
    match_found = False
    with concurrent.futures.ThreadPoolExecutor() as executor:
        ocr_results = list(executor.map(ocr_region, regions))
    
    # 各領域のOCR結果とテンプレートのOCR結果を比較
    for pos, region_text in zip(valid_positions, ocr_results):
        # 完全一致または、双方が "4" または "8" の場合に一致とみなす
        if (template_text == region_text) or ((template_text in ["4", "8"]) and (region_text in ["4", "8"])):
            match_found = True
            px, py = pos
            # 一致した領域の中央をクリック（絶対座標に変換）
            click_x = left + px + temp_w // 2
            click_y = top + py + temp_h // 2
            print(f"一致: 指定領域 {pos} のOCR結果 '{region_text}'")
            pydirectinput.click(x=click_x, y=click_y)
            time.sleep(0.3)
            pydirectinput.click(x=1131, y=613)
            time.sleep(0.3)
            break

    # OCR処理終了後、自動でRキーを送信して繰り返し処理
    pydirectinput.press('r')

# Rキーが押されたときに on_r_press 関数を呼び出す設定
keyboard.on_press_key('r', on_r_press)

print("Rキー（または自動送信）によりOCR処理が実行されます。")
print("テンプレート画像のOCR結果は起動時に1回のみ実行されます。")
print("指定領域でOCR結果が一致（または4/8とみなす）すればクリック処理が行われます。")
print("プログラム終了はCtrl+Cで。")
keyboard.wait()
