import socket  # ソケット通信ライブラリ
import threading  # マルチスレッド用ライブラリ
import sys  # システム制御用ライブラリ

# --- 接続設定 ---
ip = '16.ip.as.ply.gg'
print("ポートを入力してください")
port = int(input(">>>"))

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ip, port))
print("Connected!!!!!")

# --- ユーザー情報送信 ---
print("ルーム名を入力してください")
room = input(">>>")
print("ユーザーネームを入力してください")
name = input(">>>")
s.sendall(room.encode('utf-8'))
s.sendall(name.encode('utf-8'))

# --- プロンプト補正付き出力 ---
def print_safe(*args, **kwargs):
    with threading.Lock():
        print(*args, **kwargs)
        sys.stdout.write(">")
        sys.stdout.flush()


# --- サーバからのメッセージ受信処理 ---
def receive_messages(sock):
    while True:
        try:
            msg = sock.recv(4096).decode('utf-8')
            if msg:
                print_safe(msg)  # 改行＋プロンプト復活
        except:
            break

# --- 受信スレッド開始 ---
threading.Thread(target=receive_messages, args=(s,), daemon=True).start()

# --- メッセージ送信ループ ---
while True:
    message = input('>')
    if not message:
        s.send("/quit".encode("utf-8"))
        break
    s.send(message.encode("utf-8"))

s.close()
print("END")