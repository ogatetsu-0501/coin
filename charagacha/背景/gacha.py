import cv2                          # 画像処理用ライブラリ
import numpy as np                  # 数値計算・配列操作用ライブラリ
import pyautogui                    # 画面キャプチャやキー操作用ライブラリ
import time                         # 待機用ライブラリ
import pygetwindow as gw            # ウィンドウ位置・サイズ取得用ライブラリ
import keyboard                     # キーボード入力検知用ライブラリ
import pytesseract                  # OCR（文字認識）用ライブラリ
import pydirectinput                # ゲーム向けキー入力送信用ライブラリ
import os                           # ファイル・ディレクトリ操作用ライブラリ
from pathlib import Path            # パス操作用ライブラリ
import re                           # 文字列操作用ライブラリ

# ── OCR結果ごとに一意のIDを付与するための辞書と次のID ──
# 小学生にもわかるコメント：
# それぞれの文字列に1から順番に番号をつけて覚えておくよ
safe_to_id = {}
next_id = 1

# ── Unicodeパス対応の画像読み込み関数 ──
# 小学生にもわかるコメント：
# どんな文字のパスでも画像を開けるようにするよ
def load_image_unicode(path, flags=cv2.IMREAD_COLOR):
    try:
        with open(path, 'rb') as f:           # バイナリでファイルを開く
            data = f.read()                   # データを全部読む
        arr = np.frombuffer(data, np.uint8)   # OpenCVが扱える配列に変える
        img = cv2.imdecode(arr, flags)        # 画像にデコードする
        return img
    except Exception as e:
        print(f"画像読み込みエラー: {path}\n  {e}")
        return None

# ── スクリプトと同じフォルダの image.png を絶対パスで読み込む ──
# 小学生にもわかるコメント：
# このスクリプトがある場所と同じフォルダにある image.png を読み込むよ
script_dir    = Path(__file__).resolve().parent
template_path = script_dir / "image.png"
template = load_image_unicode(str(template_path), cv2.IMREAD_COLOR)
if template is None:
    print(f"テンプレート画像が読み込めませんでした: {template_path}")
    exit()

# ── 読み込んだテンプレートサイズを確認 ──
# 小学生にもわかるコメント：
# テンプレート画像の幅と高さを教えてくれるよ
temp_h, temp_w = template.shape[:2]
print(f"読み込んだテンプレートサイズ: {temp_w}×{temp_h}")

# ── OCR 用設定 ──
# 小学生にもわかるコメント：
# 数字だけ読む設定と日本語読む設定を用意するよ
tess_config_num = "--psm 7 -c tessedit_char_whitelist=0123456789"
tess_config_jpn = "--psm 7 -l jpn"

# ── 起動時にテンプレートOCRを一度だけ実行 ──
# 小学生にもわかるコメント：
# テンプレートに書いてある数字を一度だけ確認するよ
def get_template_text():
    gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)          # グレースケールに変える
    _, binary = cv2.threshold(gray, 144, 255, cv2.THRESH_BINARY)  # 白黒にする
    return pytesseract.image_to_string(binary, config=tess_config_num).strip()

template_text = get_template_text()
print(f"起動時のテンプレートOCR結果: '{template_text}'")

# ── 対象ウインドウの登録 ──
# 小学生にもわかるコメント：
# ここで OCR するウインドウを決めるよ。画面上で A キーを押してね
print("【対象ウインドウ登録】対象ウインドウ上で A キーを押してください。")
keyboard.wait("a")
mx, my = pyautogui.position()
target_window = None
for w in gw.getAllWindows():
    if w.left <= mx <= w.left + w.width and w.top <= my <= w.top + w.height:
        target_window = w
        break

if target_window is None:
    print("対象ウインドウが見つかりません。")
    exit()

print("対象ウインドウが決定されました:", target_window.title)

# ── デバッグ用：ウインドウ全体スクリーンショットを保存 ──
# 小学生にもわかるコメント：
# ウインドウの全体を debug_window.png に保存して確認できるよ
left, top = target_window.left, target_window.top
width, height = target_window.width, target_window.height
debug_shot = pyautogui.screenshot(region=(left, top, width, height))
debug_shot = cv2.cvtColor(np.array(debug_shot), cv2.COLOR_RGB2BGR)
os.makedirs("debug", exist_ok=True)
cv2.imwrite(os.path.join("debug", "debug_window.png"), debug_shot)
print("デバッグ用ウインドウスクリーンショットを保存しました: debug/debug_window.png")

# ── OCR対象の領域座標リスト ──
# 小学生にもわかるコメント：
# ここにOCRをする場所を(x, y)で書いておくよ
positions = [(677, 228), (677, 299), (677, 370), (677, 440)]
os.makedirs("ocr_captures", exist_ok=True)

# ── Rキー押下時のメイン処理 ──
# 小学生にもわかるコメント：
# R キーを押すとこの関数が動くよ
def on_r_press(event):
    global next_id  # next_id を更新できるようにする
    time.sleep(0.2)  # クリック前にちょっと待つよ

    # ウインドウ位置・サイズを再取得
    left, top = target_window.left, target_window.top
    width, height = target_window.width, target_window.height

    # 全体スクリーンショットを撮る
    shot = pyautogui.screenshot(region=(left, top, width, height))
    shot = cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)

    # 各ポジションでクリック＆OCR＆保存
    for idx, (px, py) in enumerate(positions, start=1):
        # 領域外チェック
        if px + temp_w > width or py + temp_h > height:
            print(f"領域{idx}がウインドウ外です、スキップします。")
            continue

        # 領域中央をクリック
        cx = left + px + temp_w // 2
        cy = top  + py + temp_h // 2
        pydirectinput.click(x=cx, y=cy)
        time.sleep(0.1)  # クリック後に待つよ

        # クリック後に再度スクリーンショット
        updated = pyautogui.screenshot(region=(left, top, width, height))
        updated = cv2.cvtColor(np.array(updated), cv2.COLOR_RGB2BGR)

        # 小学生にもわかるコメント：
        # ここで OCR する部分を切り取るよ
        ox, oy, ow, oh = 889, 395, 72, 14
        rel_x = ox - left
        rel_y = oy - top
        ocr_img = updated[rel_y:rel_y+oh, rel_x:rel_x+ow]

        # 日本語OCRを実行
        ocr_text = pytesseract.image_to_string(ocr_img, config=tess_config_jpn).strip()

        # ファイル名用に不正文字を消す
        safe = re.sub(r'[\\/:*?"<>|]', '', ocr_text)
        if not safe:
            safe = "no_text"

        # ── OCR結果ごとに一意のIDを割り当て ──
        # 小学生にもわかるコメント：
        # 新しい文字列なら next_id を当てて、それ以降は同じIDを使うよ
        if safe not in safe_to_id:
            safe_to_id[safe] = next_id
            next_id += 1
        file_id = safe_to_id[safe]

        # 小学生にもわかるコメント：
        # ID.png で保存するよ（例: 1.png, 2.png）
        fn = os.path.join("ocr_captures", f"{file_id}.png")
        cv2.imwrite(fn, ocr_img)

        # 小学生にもわかるコメント：
        # どこに保存したか教えてくれるよ
        print(f"領域{idx}クリック → OCR結果 '{ocr_text}' → 保存: {fn}")

    # 自動で R キーを押して繰り返す
    pydirectinput.press('r')

# R キーに処理を登録
keyboard.on_press_key('r', on_r_press)

# ── プログラム常駐ループ ──
# 小学生にもわかるコメント：
# Ctrl+C されるまでずっと待機するよ
print("Rキーでクリック＋日本語OCR画像保存が動作します。終了するには Ctrl+C を押してください。")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nユーザー操作により終了します。")
