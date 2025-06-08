# ── ライブラリ読み込みブロック ──
# pyautogui：マウス操作（クリックや座標取得）を行うためのライブラリ
# time：待ち時間を入れるためのライブラリ
# ctypes：WindowsAPIを呼び出してマウスボタンの押下を検知するためのライブラリ
import pyautogui
import time
import ctypes

# ── 右クリック検知用の定数定義（Windows API） ──
# 0x02 は「右クリックボタン (VK_RBUTTON)」
VK_RBUTTON = 0x02

# GetAsyncKeyState は指定した仮想キーコードが
# 押されているかどうかを調べる Windows API 関数
GetAsyncKeyState = ctypes.windll.user32.GetAsyncKeyState

# ── 位置登録用データ構造の初期化 ──
# 右クリックで取得した座標を順番に入れておくリスト
positions = []

# ── 右クリックが「押された」かを調べるヘルパー関数 ──
def is_right_button_pressed():
    """
    WindowsのGetAsyncKeyStateを使って、
    右クリック (VK_RBUTTON) が押されているかチェックする関数

    戻り値:
      True  -> 右クリックが押されている状態
      False -> 右クリックが押されていない状態
    """
    # GetAsyncKeyState(VK_RBUTTON) の戻り値の最上位ビットが1なら「押されている」
    return (GetAsyncKeyState(VK_RBUTTON) & 0x8000) != 0

# ── 位置登録ブロック ──
print("［説明］")
print("1. 画面上の任意の場所で右クリックしてください。")
print("   1回目の右クリック → 位置１として登録")
print("   2回目の右クリック → 位置２として登録し、登録完了になります")
print("2. 位置登録が完了すると、自動で位置１・位置２を交互にクリックします。")
print("3. 終了するには、コンソールで Ctrl+C を押してください。")
print()

# 右クリックを2回検知するまでループする
while len(positions) < 2:
    # もし右クリックが押されたら
    if is_right_button_pressed():
        # 現在のマウス座標を取得
        x, y = pyautogui.position()
        positions.append((x, y))
        print(f"位置{len(positions)}を登録しました： ({x}, {y})")

        # 右クリックが離されるまで、少し待って多重登録を防ぐ
        # 右クリックを押しっぱなしにしていると複数回カウントされるため
        while is_right_button_pressed():
            time.sleep(0.01)

    # CPU負荷を下げるため少し待つ
    time.sleep(0.01)

# ここまでで positions に 2 つの座標が入っているはず
pos1 = positions[0]
pos2 = positions[1]

print()
print("→ 位置登録が完了しました。")
print(f"   位置1: {pos1}")
print(f"   位置2: {pos2}")
print("これから位置１と位置２を交互にクリックし続けます。")
print("終了したいときは、このウィンドウで Ctrl+C を押してください。")
print()

# ── クリックを繰り返すブロック ──
try:
    while True:
        # --- 位置１をクリックするブロック ---
        # pos1 の座標をクリックする
        # 小学生向け説明：pos1の場所を「ポチっと」クリックします
        pyautogui.click(pos1)
        pyautogui.click(pos1)
        # クリックしたあと、1秒待つ（次に位置２をクリックする準備時間）
        time.sleep(0.5)

        # --- 位置２をクリックするブロック ---
        # pos2 の座標をクリックする
        # 小学生向け説明：pos2の場所を「ポチっと」クリックします
        pyautogui.click(pos2)
        pyautogui.click(pos2)
        # クリックしたあと、1秒待つ（次に位置１をクリックする準備時間）
        time.sleep(0.5)

except KeyboardInterrupt:
    # Ctrl+C が押されたときにこの部分に来る
    print()
    print("→ 処理を中断しました。プログラムを終了します。")
