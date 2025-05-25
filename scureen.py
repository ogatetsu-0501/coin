import pyautogui                   # スクリーンショットやマウス座標取得用
import keyboard                    # キーボード入力を検出するライブラリ
import pygetwindow as gw           # ウィンドウ情報取得用ライブラリ
import time                        # 時間待機用ライブラリ

print("【ウィンドウ選択】対象ウィンドウの上にマウスを置いて Aキー を押してください。")

# 最初のAキーで対象ウィンドウを選ぶ
keyboard.wait("a")
x, y = pyautogui.position()

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
print("その後、Aキーを押すたびに image2.png を保存します。")
print("Ctrl + A を押すと終了します。")

# 無限ループ開始（Ctrl+Aが押されるまで）
while True:
    # Ctrl + A が押されたら終了
    if keyboard.is_pressed("ctrl+a"):
        print("Ctrl + A が押されたので終了します。")
        break

    # Aキーが押されたらスクリーンショットを撮る
    if keyboard.is_pressed("a"):
        # 対象ウィンドウの位置とサイズを取得
        left = target_window.left
        top = target_window.top
        width = target_window.width
        height = target_window.height

        # ウィンドウのスクリーンショットを撮る
        img = pyautogui.screenshot(region=(left, top, width, height))

        # 画像を image2.png として保存（毎回上書き）
        img.save("image2.png")
        print("image2.png を保存しました。")

        # Aキーが離されるまで待機（押しっぱなし対策）
        while keyboard.is_pressed("a"):
            time.sleep(0.05)

    time.sleep(0.01)  # CPUに優しい待機
