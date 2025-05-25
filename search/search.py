import cv2                          # 画像処理用ライブラリ
import numpy as np                  # 数値計算・配列操作用ライブラリ
import pyautogui                    # 画面キャプチャ用ライブラリ
import pygetwindow as gw            # ウィンドウ情報取得用ライブラリ
import keyboard                     # キーボード入力検知用ライブラリ
import os                           # ファイルパス操作用ライブラリ
import time                         # 待機用ライブラリ

# ── Unicodeパス対応の画像読み込み関数 ──
def load_image_unicode(path, flags=cv2.IMREAD_UNCHANGED):
    """
    ファイルをバイナリで開いて OpenCV で読み込める形に変えるよ
    """
    try:
        with open(path, 'rb') as f:
            data = f.read()
        arr = np.frombuffer(data, np.uint8)
        img = cv2.imdecode(arr, flags)
        return img
    except Exception as e:
        print(f"画像読み込みエラー: {path}\n  {e}")
        return None

# ── スクリプトと同じフォルダ内のファイルパスを作るよ ──
script_dir = os.path.dirname(os.path.abspath(__file__))
path_bg_file = os.path.join(script_dir, "image2.png")  # 背景用
path_fg_file = os.path.join(script_dir, "image.png")   # 前景用

window_name = "Overlay"

# ── 背景画像の準備 ──
bg = load_image_unicode(path_bg_file)
if bg is None:
    print("背景画像が見つかりません。Aキーでキャプチャして背景を作成してください。")
    # Aキーが押されるまで待つループ
    while True:
        if keyboard.is_pressed('a'):
            # マウス下のウィンドウを探してキャプチャ
            mx, my = pyautogui.position()
            target = None
            for w in gw.getAllWindows():
                if w.left <= mx <= w.left+w.width and w.top <= my <= w.top+w.height:
                    target = w
                    break
            if target:
                region = (target.left, target.top, target.width, target.height)
                shot = pyautogui.screenshot(region=region)
                img = cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)
                cv2.imwrite(path_bg_file, img)   # image2.png に保存
                bg = img.copy()                  # 背景用変数をセット
                print(f"背景をキャプチャ＆保存しました: {path_bg_file}")
                break
            else:
                print("マウス下のウィンドウが見つかりません。再度 A キーを押してください。")
                time.sleep(0.5)
        time.sleep(0.1)

# 背景サイズを取得
bg_h, bg_w = bg.shape[:2]

# ── 前景画像の読み込み ──
fg = load_image_unicode(path_fg_file, flags=cv2.IMREAD_UNCHANGED)
if fg is None:
    print(f"前景画像が見つかりません：{path_fg_file}")
    exit()
# アルファチャンネルがあれば消すよ
if fg.shape[2] == 4:
    fg = cv2.cvtColor(fg, cv2.COLOR_BGRA2BGR)
fg_h, fg_w = fg.shape[:2]

# ── 描画設定 ──
pos_x, pos_y = 0, 0        # 前景の位置
zoom = 1.0                 # 拡大率
normal_speed = 1           # 通常移動速さ
fast_speed = 10            # Ctrl移動速さ
offset_x, offset_y = 0, 0  # ズーム中のスクロールオフセット

dragging = False           # ドラッグ中フラグ
drag_start_x, drag_start_y = 0, 0

# マウスイベント（ズーム＆ドラッグ）
def mouse_callback(event, x, y, flags, param):
    global zoom, dragging, drag_start_x, drag_start_y, offset_x, offset_y
    if event == cv2.EVENT_MOUSEWHEEL:
        # ホイールでズーム
        zoom *= 1.1 if flags > 0 else 0.9
        zoom = max(1.0, min(zoom, 10.0))
    elif event == cv2.EVENT_LBUTTONDOWN:
        dragging = True
        drag_start_x, drag_start_y = x, y
    elif event == cv2.EVENT_MOUSEMOVE and dragging:
        dx, dy = x - drag_start_x, y - drag_start_y
        offset_x -= dx
        offset_y -= dy
        drag_start_x, drag_start_y = x, y
    elif event == cv2.EVENT_LBUTTONUP:
        dragging = False

# ウィンドウの初期化
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.setMouseCallback(window_name, mouse_callback)

print("矢印キー：前景移動  Ctrl+矢印：高速移動")
print("マウスホイール：ズーム  ドラッグ：スクロール")
print("Aキー：マウス下のウィンドウをキャプチャして背景更新")
print("qキー：終了")

# ── メインループ ──
while True:
    # 背景と前景を合成
    comp = bg.copy()
    x1, y1 = max(0, pos_x), max(0, pos_y)
    x2, y2 = min(bg_w, pos_x+fg_w), min(bg_h, pos_y+fg_h)
    if x2 > x1 and y2 > y1:
        fx1, fy1 = x1-pos_x, y1-pos_y
        fx2, fy2 = fx1+(x2-x1), fy1+(y2-y1)
        roi_bg = comp[y1:y2, x1:x2]
        roi_fg = fg[fy1:fy2, fx1:fx2]
        comp[y1:y2, x1:x2] = cv2.addWeighted(roi_bg, 0.5, roi_fg, 0.5, 0)

    # ズームとスクロール表示
    ch, cw = comp.shape[:2]
    vw, vh = int(cw/zoom), int(ch/zoom)
    cx, cy = cw//2 + offset_x, ch//2 + offset_y
    vx = max(0, min(cw-vw, cx-vw//2))
    vy = max(0, min(ch-vh, cy-vh//2))
    view = comp[vy:vy+vh, vx:vx+vw]
    disp = cv2.resize(view, (cw, ch), interpolation=cv2.INTER_LINEAR)

    # 座標とズーム情報を表示
    cv2.putText(disp, f"Pos:({pos_x},{pos_y}) Zoom:{zoom:.2f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    cv2.imshow(window_name, disp)
    key = cv2.waitKey(30) & 0xFF

    # qキーで終了
    if key == ord('q'):
        break

    # 矢印キーで前景移動
    speed = fast_speed if keyboard.is_pressed("ctrl") else normal_speed
    if keyboard.is_pressed("up"):
        pos_y = max(0, pos_y - speed)
    if keyboard.is_pressed("down"):
        pos_y = min(bg_h - fg_h, pos_y + speed)
    if keyboard.is_pressed("left"):
        pos_x = max(0, pos_x - speed)
    if keyboard.is_pressed("right"):
        pos_x = min(bg_w - fg_w, pos_x + speed)

cv2.destroyAllWindows()
