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
import sys                          # プログラム終了用

# ────────────────────────────────────────
# OCR設定
# ────────────────────────────────────────
# 小学生にもわかるコメント：数字だけ読む設定だよ
tess_config = "--psm 7 -c tessedit_char_whitelist=0123456789"
# 小学生にもわかるコメント：日本語も読む設定だよ
tess_config_jpn = "--psm 7 -l jpn"

# ────────────────────────────────────────
# テンプレート画像 (image.png) の読み込み
# ────────────────────────────────────────
template_path = os.path.join("charagacha", "image.png")  # 相対パス指定
template = cv2.imread(template_path, cv2.IMREAD_COLOR)
if template is None:
    print(f"テンプレート画像が見つかりません: {template_path}")
    sys.exit()

# ────────────────────────────────────────
# 起動時にテンプレート画像にOCRをかけ、その結果を保存
# ────────────────────────────────────────
def get_template_text():
    # 小学生にもわかるコメント：テンプレートを白黒にして文字を読む準備をするよ
    t_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    _, t_binary = cv2.threshold(t_gray, 144, 255, cv2.THRESH_BINARY)
    return pytesseract.image_to_string(t_binary, config=tess_config).strip()

template_text = get_template_text()
print(f"起動時のテンプレート画像のOCR結果: '{template_text}'")

# ────────────────────────────────────────
# 追加：11.png をもうひとつのテンプレートとして読み込む
# ────────────────────────────────────────
jpn_template_path = os.path.join("charagacha", "11.png")  # 相対パス指定
jpn_template = cv2.imread(jpn_template_path, cv2.IMREAD_COLOR)
if jpn_template is None:
    print(f"11.png が見つかりません: {jpn_template_path}")
    sys.exit()

def get_jpn_template_text():
    # 小学生にもわかるコメント：11.pngを白黒にして文字を読む準備をするよ
    gray = cv2.cvtColor(jpn_template, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 144, 255, cv2.THRESH_BINARY)
    return pytesseract.image_to_string(binary, config=tess_config_jpn).strip()

jpn_template_text = get_jpn_template_text()
print(f"起動時の11.pngのOCR結果: '{jpn_template_text}'")

# ────────────────────────────────────────
# OCR を並列処理するための関数
# ────────────────────────────────────────
def ocr_region(region):
    # 小学生にもわかるコメント：領域画像を白黒にして文字を読み込むよ
    region_gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    _, region_binary = cv2.threshold(region_gray, 144, 255, cv2.THRESH_BINARY)
    return pytesseract.image_to_string(region_binary, config=tess_config).strip()

# ────────────────────────────────────────
# 最終クリックカウンタ
# ────────────────────────────────────────
final_click_count = 0  # 小学生にもわかるコメント：何回クリックしたか数えるよ

# ────────────────────────────────────────
# 対象ウインドウの登録
# ────────────────────────────────────────
print("【対象ウインドウ登録】対象ウインドウ上でAキーを押してください。")
keyboard.wait("a")                 # ユーザーがAキーを押すまで待つ
x, y = pyautogui.position()        # Aキー押下時のマウス位置取得

target_window = None
for win in gw.getAllWindows():
    if win.left <= x <= win.left + win.width and win.top <= y <= win.top + win.height:
        target_window = win
        break

if target_window is None:
    print("対象ウインドウが見つかりません。")
    sys.exit()

print("対象ウインドウが決定されました:", target_window.title)

# OCR対象の4箇所の座標（スクリーンショット内での相対座標）
positions = [(677,228), (677,299), (677,370), (677,440)]
temp_h, temp_w = template.shape[:2]

# ────────── Bキーで領域画像を保存 ──────────
def on_b_press(event):
    time.sleep(0.1)  # 小学生にもわかるコメント：ちょっと待つよ

    left = target_window.left
    top = target_window.top
    width = target_window.width
    height = target_window.height

    screenshot = pyautogui.screenshot(region=(left, top, width, height))
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    save_dir = "captured_regions"
    os.makedirs(save_dir, exist_ok=True)

    for idx, (px, py) in enumerate(positions, start=1):
        if px + temp_w > width or py + temp_h > height:
            print(f"領域{idx}がウインドウ外です、スキップします。")
            continue
        region = screenshot[py:py+temp_h, px:px+temp_w]
        filename = os.path.join(save_dir, f"region_{idx}_{int(time.time())}.png")
        cv2.imwrite(filename, region)
        print(f"領域{idx}を保存しました：{filename}")

keyboard.on_press_key('b', on_b_press)
print("Bキーで指定4領域の画像を保存できます。")

# ────────────────────────────────────────
# Rキー押下時の処理
# ────────────────────────────────────────
def on_r_press(event):
    global final_click_count  # カウンタを書き換えるのでグローバル宣言
    time.sleep(0.2)  # 小学生にもわかるコメント：0.2秒待つよ

    left = target_window.left
    top = target_window.top
    width = target_window.width
    height = target_window.height

    screenshot = pyautogui.screenshot(region=(left, top, width, height))
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    regions = []
    valid_positions = []
    for px, py in positions:
        if px + temp_w > width or py + temp_h > height:
            continue
        region = screenshot[py:py+temp_h, px:px+temp_w]
        regions.append(region)
        valid_positions.append((px, py))

    # 並列OCR
    with concurrent.futures.ThreadPoolExecutor() as executor:
        ocr_results = list(executor.map(ocr_region, regions))

    for pos, region_text in zip(valid_positions, ocr_results):
        # 小学生にもわかるコメント：テンプレートと同じか、4と8のペアか調べるよ
        if (template_text == region_text) or ((template_text in ["4", "8"]) and (region_text in ["4", "8"])):
            px, py = pos

            # ── 領域中央をクリック ──
            cx = left + px + temp_w // 2
            cy = top  + py + temp_h // 2
            pydirectinput.click(x=cx, y=cy)
            time.sleep(0.1)

            # ── クリック後に再度スクリーンショット ──
            updated = pyautogui.screenshot(region=(left, top, width, height))
            updated = cv2.cvtColor(np.array(updated), cv2.COLOR_RGB2BGR)

            # ── OCR 切り出し領域 ──
            # 小学生にもわかるコメント：ここで日本語の部分を切り取るよ
            ox, oy, ow, oh = 889, 395, 72, 14
            rel_x = ox - left
            rel_y = oy - top
            ocr_img = updated[rel_y:rel_y+oh, rel_x:rel_x+ow]

            # ── 日本語OCRを実行 ──
            ocr_text = pytesseract.image_to_string(ocr_img, config=tess_config_jpn).strip()
            print(f"11.png比較用OCR結果: '{ocr_text}'")

            if ocr_text == jpn_template_text:
                # ── 最終クリックを実行 ──
                pydirectinput.click(x=1131, y=613)
                time.sleep(0.3)

                # ── クリック回数を増やしてチェック ──
                final_click_count += 1  # 小学生にもわかるコメント：カウントをひとつ増やすよ
                print(f"最終クリック回数: {final_click_count} / 30")

                if final_click_count >= 30:
                    print("最終クリックを30回行ったのでプログラムを終了します。")
                    sys.exit()  # 小学生にもわかるコメント：ここでプログラムを終わらせるよ

                break  # forループ抜けて処理終了

            else:
                # ── 一致しなければ Rキー再送信 ──
                pydirectinput.press('r')
                return

    # ── OCR一致しなかったときも Rキー再送信 ──
    pydirectinput.press('r')

keyboard.on_press_key('r', on_r_press)

print("Rキー（または自動送信）によりOCR処理が実行されます。")
print("テンプレート画像のOCR結果は起動時に1回のみ実行されます。")
print("指定領域でOCR結果が一致（または4/8とみなす）すればクリック処理が行われます。")
print("11.pngの日本語OCR結果とも比較して、合致する場合に最終クリックを実行します。")
print("最終クリックを30回行ったらプログラムを終了します。")
print("プログラム終了はCtrl+CでもOKです。")

keyboard.wait()  # プログラムが終了されるまで待つよ
