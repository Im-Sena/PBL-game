import socket  # ソケット通信ライブラリ
import threading  # マルチスレッド用ライブラリ
import sys  # システム制御用ライブラリ

# --- 接続設定 ---
ip = '127.0.0.1'
#print("ポートを入力してください")
#port = int(input(">>>"))
port = 8000
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ip, port))
print("Connected!!!!!")

# --- ユーザー情報送信 ---
print("ルーム名を入力してください")
#room = input(">>>")
room = str(111)
print("ユーザーネームを入力してください")
name = input(">>>")
s.sendall((room + "\n").encode('utf-8'))
s.sendall((name + "\n").encode('utf-8'))

# --- プロンプト補正付き出力 ---
def print_safe(*args, **kwargs):
    with threading.Lock():
        print(*args, **kwargs)
        sys.stdout.write(">")
        sys.stdout.flush()

#1回の recv に複数のデータが来ても区切って正しく読み取れるようにするための関数
def recv_line(conn):
    buffer = ""
    while True:
        chunk = conn.recv(1).decode()
        if not chunk:  # 0バイト受信→切断
            return None
        if chunk == "\n":  # 改行で終わり
            break
        buffer += chunk
    return buffer.strip()  # 前後の空白・改行を除去して返す


# --- サーバからのメッセージ受信処理 ---
'''
def receive_messages(sock):
    while True:
        try:
            msg = recv_line(sock)
            if msg.startswith("%"):
                print_safe("コマンドです")  # 改行＋プロンプト復活
            elif msg:
                print_safe(msg)  # 改行＋プロンプト復活
        except:
            break


'''
def receive_messages(sock):
    buffer = ""  # 受信データをためるバッファ

    while True:
        try:
            # まとめて最大1024バイト受信（複数メッセージを一度に受け取るため）
            chunk = sock.recv(1024).decode()
            if not chunk:
                # 0バイト受信＝サーバ切断の可能性あり
                print("サーバ切断")
                break
            
            buffer += chunk  # バッファに追記

            # バッファに改行が含まれる限り繰り返し処理
            while "\n" in buffer:
                # 改行で区切って1行を取り出し、残りはバッファに戻す
                line, buffer = buffer.split("\n", 1) #split("\n", 1) は、最初の \n で文字列を2つに分割。　その後lineに代入
                line = line.strip()  # 前後の空白や改行を除去

                # メッセージがコマンドっぽい場合の処理（例）
                if line.startswith("%"):
                    print_safe("コマンドです")
                    #lineの%を除去して表示
                    line = line[1:].strip()
                    print_safe(line)         
                else:
                    # 普通のメッセージは画面に表示
                    print_safe(line)
        
        except Exception as e:
            # 例外が起きたら原因を表示してループを抜ける
            print(f"[ERROR] receive_messages: {e}")
            break



# --- 受信スレッド開始 ---
threading.Thread(target=receive_messages, args=(s,), daemon=True).start()

# --- メッセージ送信ループ ---
while True:
    message = input('>')
    if message == "/quit":
        s.sendall((message + "\n").encode("utf-8"))
        break
    if not message:
        continue
    s.sendall((message + "\n").encode("utf-8"))

s.close()
print("END")