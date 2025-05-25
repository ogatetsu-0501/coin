import cv2  # 画像処理用ライブラリ

# ---------------- 画像の読み込み ----------------
img = cv2.imread("0.PNG")  # 画像ファイルを読み込む
if img is None:
    print("画像ファイル 0.PNG が見つかりません。")
    exit()

# グレースケール変換
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# ウィンドウ名
window_name = "Binary Threshold"

# ---------------- ウィンドウをリサイズ可能にして作成 ----------------
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

# ---------------- トラックバーの更新関数 ----------------
def update_threshold(val):
    # グローバル変数にアクセス（ウィンドウサイズ取得のため）
    global gray, window_name

    # 2値化のしきい値 val を使用して2値化処理
    _, binary = cv2.threshold(gray, val, 255, cv2.THRESH_BINARY)

    # 現在のウィンドウサイズを取得
    try:
        win = cv2.getWindowImageRect(window_name)  # (x, y, width, height)
        win_w, win_h = win[2], win[3]
    except:
        # 取得失敗時は元サイズで表示
        win_w, win_h = binary.shape[1], binary.shape[0]

    # ウィンドウに合わせて2値化画像をリサイズ
    resized = cv2.resize(binary, (win_w, win_h), interpolation=cv2.INTER_NEAREST)

    # 画像を表示
    cv2.imshow(window_name, resized)

# ---------------- トラックバー作成（初期値127） ----------------
cv2.createTrackbar("Threshold", window_name, 127, 255, update_threshold)

# 初期表示（しきい値127で表示）
update_threshold(127)

print("ウィンドウサイズに応じて画像が拡大表示されます。")
print("トラックバーでしきい値を変えて、'q' キーで終了します。")

# ---------------- 終了処理ループ ----------------
while True:
    key = cv2.waitKey(100) & 0xFF

    # ウィンドウのサイズが変わっていたら再描画
    update_threshold(cv2.getTrackbarPos("Threshold", window_name))

    if key == ord("q"):
        break

cv2.destroyAllWindows()
