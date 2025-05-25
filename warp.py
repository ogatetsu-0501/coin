# pyautoguiライブラリをインポートする　# マウスの移動、クリック操作を行うためのライブラリ
import pyautogui  
# timeライブラリをインポートする　# 一定時間待つためのライブラリ
import time  
# pynputのmouseモジュールをインポートする　# マウスのクリック操作を検出するためのライブラリ
from pynput import mouse  
# pynputのkeyboardモジュールをインポートする　# キーボードの操作を検出するためのライブラリ
from pynput import keyboard  

# ターゲット座標を保存するための変数を初期化する　# 右クリックで登録する座標を入れる箱
target_position = None  

# マウスクリックがあったときに実行される関数を定義する
def on_click(x, y, button, pressed):
    # グローバル変数target_positionを使うことを宣言する
    global target_position  
    # もし押されたボタンが右クリックで、ボタンが押されたときなら
    if button == mouse.Button.right and pressed:
        # 右クリックしたときの座標をtarget_positionに保存する
        target_position = (x, y)  
        # リスナーを停止して、これ以上右クリックを待たないようにする
        return False  

# マウスクリックを監視するリスナーを作成する　# システム起動後、右クリックでターゲット座標を登録する
with mouse.Listener(on_click=on_click) as listener:
    # ユーザーが右クリックするのを待機する
    listener.join()  

# 登録されたターゲット座標を確認する　# 登録が完了したので、画面に表示する
print("登録されたターゲット座標:", target_position)

# キーが押されたときに実行される関数を定義する
def on_press(key):
    # 例外処理を使う　# キーにchar属性がない場合に備える
    try:
        # もし押されたキーがアルファベットの"a"なら
        if key.char == 'a':
            # 現在のマウス座標（元の座標）を取得してsource_positionに保存する
            source_position = pyautogui.position()  
            # 元の座標を表示する
            print("記録された元の座標:", source_position)
            # ターゲット座標にマウスカーソルを移動する　# 登録された場所に行く
            pyautogui.moveTo(target_position[0], target_position[1])
            # ターゲット座標に移動したことを表示する
            print("ターゲット座標に移動しました:", target_position)
            # 少し待つ　# 移動が完了するのを待つため（0.5秒）
            time.sleep(0.0)
            # ターゲット座標で左クリックする　# クリック操作を実行する
            pyautogui.click()
            # クリックしたことを表示する
            print("ターゲット座標でクリックしました。")
            # 少し待つ　# クリック処理が確実に終わるのを待つため（0.5秒）
            time.sleep(0.0)
            # 元の座標にマウスカーソルを戻す　# 先ほど記録した場所に戻る
            pyautogui.moveTo(source_position[0], source_position[1])
            # 元の座標に戻ったことを表示する
            print("元の座標に戻りました:", source_position)
    except AttributeError:
        # もしキーにchar属性がない場合は何もしない
        pass

# キーボードの操作を監視するリスナーを作成する　# Aキーが押されるのを待つ
with keyboard.Listener(on_press=on_press) as k_listener:
    # キーボードの監視を継続する　# Aキーが押されるたびにon_pressが呼ばれる
    k_listener.join()
