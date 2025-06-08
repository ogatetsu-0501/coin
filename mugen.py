# ───────────────────────────
# 必要なライブラリをインポート
# ───────────────────────────
import pyautogui             # マウス移動・クリック用
import time                  # 待機時間用
from pynput import mouse     # 右クリック登録用
from pynput import keyboard  # Aキー検知用
import keyboard as kb        # Ctrl+C検出用

# ───────────────────────────
# ターゲット座標を保存する変数
# ───────────────────────────
target_position = None  

# ───────────────────────────
# 右クリックでターゲット座標を登録する関数
# ───────────────────────────
def on_click(x, y, button, pressed):
    global target_position
    if button == mouse.Button.right and pressed:
        target_position = (x, y)  # 右クリック位置を保存
        return False              # リスナー停止

# ───────────────────────────
# 右クリックを待ってターゲット座標を登録
# ───────────────────────────
with mouse.Listener(on_click=on_click) as listener:
    listener.join()

print("登録されたターゲット座標:", target_position)

# ───────────────────────────
# Aキーが押されたときに動作を開始する関数
# ───────────────────────────
def on_press(key):
    try:
        if key.char == 'a':  # Aキーが押されたら
            # ① まず「元の座標」を記録
            source_position = pyautogui.position()
            print("ループ開始: 元の座標", source_position, "→ ターゲット", target_position)

            counter = 0  # ループ回数を数える

            # ② クリック→戻る→クリック を繰り返す
            while True:
                counter += 1
                print(f"{counter}回目のループ")

                # ── ターゲット座標へ移動してクリック ──
                pyautogui.moveTo(*target_position)
                print("ターゲットでクリック:", target_position)
                pyautogui.click()
                time.sleep(0.1)

                # ── Ctrl+C 検知(停止) ──
                if kb.is_pressed('ctrl') and kb.is_pressed('c'):
                    print("Ctrl+C 検知：ループ停止")
                    break

                # ── 元の座標へ戻ってクリック ──
                pyautogui.moveTo(*source_position)
                print("元の座標でクリック:", source_position)
                pyautogui.click()
                time.sleep(0.1)

                # ── Ctrl+C 検知(停止) ──
                if kb.is_pressed('ctrl') and kb.is_pressed('c'):
                    print("Ctrl+C 検知：ループ停止")
                    break

                # ── 30回ループしたら自動で停止 ──
                if counter >= 65:
                    print("30回ループしたので停止します")
                    break

            # ③ ループが終わったあと、必ず「元の座標」に戻す
            pyautogui.moveTo(*source_position)
            print("最終的に元の座標へ戻りました:", source_position)
            print("ループを終了しました\n")

            # ここで on_press を抜けるので、再度 'A' キー待ちの状態に戻ります

    except AttributeError:
        pass  # 文字キー以外は無視

# ───────────────────────────
# キーボード監視を開始（Aキーを待つ）
# ───────────────────────────
with keyboard.Listener(on_press=on_press) as k_listener:
    k_listener.join()
