# 画像を扱うためのライブラリを読み込みます
import cv2  # 画像処理に使うツールです

# 数字の計算と配列操作をするためのライブラリを読み込みます
import numpy as np  # 数値計算と配列操作に使います

# 画面キャプチャとキー操作のライブラリを読み込みます
import pyautogui  # 画面の画像を撮ったりキー操作をしたりできます

# 時間を扱うライブラリを読み込みます
import time  # プログラム内で待機するためのツールです

# 画面上のウインドウ情報を取得するライブラリを読み込みます
import pygetwindow as gw  # ウインドウの位置や大きさを取得できます

# キーボード入力を検知するライブラリを読み込みます
import keyboard  # キーが押されたかどうかを検知します

# OCR を実行するライブラリを読み込みます
import pytesseract  # OCR（文字認識）を行うツールです

# ゲームなどでキー入力を認識させるためのライブラリを読み込みます
import pydirectinput  # ゲームでも認識されやすいキー入力を送信します

# pytesseract の設定：ここでは数字のみ認識する設定です
tess_config = "--psm 7 -c tessedit_char_whitelist=0123456789"

# テンプレート画像のファイル名を相対パスで指定します
# この Python ファイルと同じフォルダの image.png を使用します
template_path = "image.png"  # テンプレート画像のファイル名です

# テンプレート画像をカラーで読み込みます
template = cv2.imread(template_path, cv2.IMREAD_COLOR)
if template is None:
    print("テンプレート画像が見つかりません。")
    exit()

# ---------- 対象ウインドウ（監視するウインドウ）の登録 ----------
print("【対象ウインドウ登録】対象ウインドウを決定するため、そのウインドウ上でAキーを押してください。")
keyboard.wait("a")  # ユーザーが A キーを押すまで待機します
x, y = pyautogui.position()  # Aキー押下時のマウス位置を取得します
print("Aキー押下時のマウス位置は:", x, y)
target_window = None
for win in gw.getAllWindows():
    # マウス位置がウインドウ内にあるかを確認します
    if win.left <= x <= win.left + win.width and win.top <= y <= win.top + win.height:
        target_window = win
        break
if target_window is None:
    print("Aキー押下位置に対象ウインドウが見つかりません。")
    exit()
print("対象ウインドウが決定されました:", target_window.title)

# ---------- アクティブにするウインドウの登録 ----------
print("【アクティブウインドウ登録】アクティブにするウインドウを決定するため、そのウインドウ上でAキーを押してください。")
keyboard.wait("a")  # ユーザーが A キーを押すまで待機します
ax, ay = pyautogui.position()  # Aキー押下時のマウス位置を取得します
print("Aキー押下時のマウス位置は:", ax, ay)
active_window = None
for win in gw.getAllWindows():
    # マウス位置がウインドウ内にあるかを確認します
    if win.left <= ax <= win.left + win.width and win.top <= ay <= win.top + win.height:
        active_window = win
        break
if active_window is None:
    print("Aキー押下位置にアクティブにするウインドウが見つかりません。")
    exit()
print("アクティブにするウインドウが決定されました:", active_window.title)

# ---------- Rキー押下時の処理 ----------
# この関数は、Rキーが押されたときに実行されます。
# 処理内容：
# 1. 0.5秒待機して対象ウインドウのスクリーンショットを取得・保存
# 2. テンプレート画像にOCRをかけ、数値を抽出
# 3. スクリーンショットから指定の4箇所の領域を切り出し、各領域にOCRをかけて数値を抽出
# 4. 各領域のOCR結果とテンプレートのOCR結果を比較し、一致する場合はその領域の中央をクリック、0.3秒待機、
#    続いて (1131,613) をクリックし、0.3秒待機する
# 5. 最後に自動でRキーを送信して、処理を繰り返す
def on_r_press(event):
    print("Rキーが押されました。0.5秒待機中・・・")
    time.sleep(0.5)  # 0.5秒待機

    # 対象ウインドウの位置とサイズを取得します
    left = target_window.left
    top = target_window.top
    width = target_window.width
    height = target_window.height

    # 対象ウインドウのスクリーンショットを取得します
    screenshot = pyautogui.screenshot(region=(left, top, width, height))
    screenshot = np.array(screenshot)
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)

    # スクリーンショット全体を保存します
    screenshot_filename = "screenshot_full.png"
    cv2.imwrite(screenshot_filename, screenshot)
    print(f"全体のスクリーンショット {screenshot_filename} を保存しました。")

    # ---------- テンプレート画像にOCRをかける ----------
    # テンプレート画像をグレースケールに変換し、二値化（閾値144）します
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    ret, template_binary = cv2.threshold(template_gray, 144, 255, cv2.THRESH_BINARY)
    # OCRで数値を抽出します（数字のみ認識する設定）
    template_text = pytesseract.image_to_string(template_binary, config=tess_config).strip()
    print(f"テンプレート画像のOCR結果: '{template_text}'")

    # ---------- 指定の4箇所の領域に対して処理 ----------
    positions = [(677,228), (677,299), (677,370), (677,440)]
    temp_h, temp_w = template.shape[:2]

    match_found = False  # 一致が見つかったかどうかのフラグ
    for i, pos in enumerate(positions):
        px, py = pos
        s_h, s_w = screenshot.shape[:2]
        # 指定領域がスクリーンショットの範囲内かチェック
        if px + temp_w > s_w or py + temp_h > s_h:
            print(f"位置 {pos} はスクリーンショットの範囲外です。")
            continue

        # 指定位置から領域を切り出し、保存します
        region = screenshot[py:py+temp_h, px:px+temp_w]
        filename = f"region_{i+1}_{px}_{py}.png"
        cv2.imwrite(filename, region)
        print(f"画像 {filename} を保存しました。")

        # 領域をグレースケールに変換し、二値化（閾値144）します
        region_gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        ret, region_binary = cv2.threshold(region_gray, 144, 255, cv2.THRESH_BINARY)
        # OCR を実施して数値を抽出します
        region_text = pytesseract.image_to_string(region_binary, config=tess_config).strip()
        print(f"画像 {filename} のOCR結果: '{region_text}'")

        # テンプレートのOCR結果と各領域のOCR結果を比較します
        if template_text == region_text:
            print(f"画像 {filename} のOCR結果がテンプレートと一致しました。")
            match_found = True
            # 一致した領域の中央をクリックします
            # ※クリックする座標はスクリーンショット上の領域の座標なので、対象ウインドウの左上座標を足して絶対座標に変換します
            click_x = left + px + temp_w // 2
            click_y = top + py + temp_h // 2
            print(f"領域中央をクリックします: ({click_x}, {click_y})")
            pydirectinput.click(x=click_x, y=click_y)
            time.sleep(0.3)  # 0.3秒待機

            # 次に、指定の座標 (1131,613) をクリックします
            print("座標 (1131,613) をクリックします。")
            pydirectinput.click(x=1131, y=613)
            time.sleep(0.3)  # 0.3秒待機

            # 一致したので、以降の領域は処理せずループを抜けます
            break

    # ---------- OCR処理が終了したら自動でRキーを送信 ----------
    print("OCR処理が終了しました。自動でRキーを送信します。")
    pydirectinput.press('r')
    # ※この処理により、繰り返しRキーが送信されOCR処理が実行されます

# Rキーが押されたときに on_r_press 関数を呼び出す設定をします
keyboard.on_press_key('r', on_r_press)
print("Rキーを押すか、Rキーの自動送信によりOCR処理が実行されます。")
print("各領域にOCRをかけ、テンプレート画像のOCR結果と比較し、一致すれば指定領域の中央と (1131,613) をクリックします。")
print("プログラムを終了するには、Ctrl+C を押してください。")

keyboard.wait()
