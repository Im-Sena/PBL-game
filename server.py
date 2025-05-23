import socket  # ソケット通信ライブラリ
import threading  # マルチスレッド用ライブラリ
import sys  # システム制御用ライブラリ

# --- グローバル変数と排他制御用ロック ---
rooms = {}  # ルーム名をキーとし、(conn, name) のリストを値に持つ辞書
rooms_lock = threading.Lock()  # rooms操作の排他制御用ロック
CAPACITY = 4  # 一部用途で使用（人数上限表示など）

# --- ルームに所属するユーザー全員にメッセージを送る（送信者以外） ---
def broadcast_to_room(room, message, sender_conn):
    with rooms_lock:
        for conn, _ in rooms.get(room, []):
            if conn != sender_conn:
                try:
                    conn.send(message.encode('utf-8'))
                except:
                    pass  # エラー発生時もスキップ（切断など）

# --- ルームに所属するユーザー全員にメッセージを送る ---
def broadcast_to_room_all(room, message, sender_conn):
    with rooms_lock:
        for conn, _ in rooms.get(room, []):
            try:
                conn.send(message.encode('utf-8'))
            except Exception as e:
                print(f"[!] Error sending to {conn}: {e}")

# --- サーバーからメッセージを送信する（全ルーム対象） ---
def server_message(message):
    with rooms_lock:
        for users in rooms.values():
            for conn, _ in users:
                try:
                    conn.send(message.encode('utf-8'))
                except:
                    pass

# --- クライアント接続処理 ---
def handle_client(connection, address):
    print_safe(f"Client connected: {address}")

    # クライアントからルーム名とユーザーネームを受信
    room = connection.recv(1024).decode().strip()
    name = connection.recv(1024).decode().strip()
    
    ready = []

    # ルームが存在しない場合は新規作成し、ユーザーを追加
    with rooms_lock:
        if room not in rooms:
            rooms[room] = []
        rooms[room].append((connection, name))

    try:
        while True:
            data = connection.recv(4096).decode()  # メッセージ受信
            if not data or data == "/quit":  # 空または"/quit"で切断処理へ
                break
            elif data == "/start":
                broadcast_to_room_all(room, f"{name}がゲームを開始しました", connection)
                broadcast_to_room_all(room, f"今から皆さんにお題を送ります", connection)
                
            else:
                print_safe(f"[{room} / {name}] {data}")
                broadcast_to_room(room, f"{name}: {data}", connection)  # 他ユーザーに中継
    except:
        pass
    finally:
        # 切断処理
        with rooms_lock:
            rooms[room] = [(c, n) for (c, n) in rooms[room] if c != connection]
            if not rooms[room]:  # ルームが空になったら削除
                del rooms[room]
        connection.close()
        print(f"[-] Disconnected {name} from {room}")

# --- コンソール入力受付スレッド ---
def input_thread():
    global running
    while True:
        cmd = input('>>>')
        if cmd == "exit":
            running = False
            break
        elif cmd == "exit":
            running = False
            break
        elif cmd == "list":
            with rooms_lock:
                if not rooms:
                    print("[接続中] なし")
                else:
                    print("[ルーム一覧]")
                    for room, users in rooms.items():
                        print(f"  {room} ({len(users)}人)")
                        for conn, uname in users:
                            print(f"    - {uname}")
        elif cmd == "say":
            msg = input('>')
            print(f"全クライアントに'{msg}'を送信しました。")
            server_message(f"[server]: {msg}")
        elif cmd == "cap":
            with rooms_lock:
                total = sum(len(users) for users in rooms.values())
            print(f"総接続数: {total}/{CAPACITY}")
            server_message(f"接続数: {total}/{CAPACITY}")

# --- プロンプト補正付き出力 ---
def print_safe(*args, **kwargs):
    with threading.Lock():
        print(*args, **kwargs)
        sys.stdout.write(">>>")
        sys.stdout.flush()

# --- サーバー起動設定 ---
ip = '127.0.0.1'  # ローカルホスト
print("ポートを入力してください")
port = int(input(">>>"))  # ポート番号入力

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((ip, port))  # ソケットをバインド
s.listen(CAPACITY)  # 接続待機上限
s.settimeout(1.0)  # 1秒ごとに accept タイムアウト
running = True

print(f"[✓] Server started on {ip}:{port}, waiting for connections...")
print("Type 'exit' to shut down.")

# 入力スレッド起動
threading.Thread(target=input_thread, daemon=True).start()

# --- 接続ループ ---
while running:
    try:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()
    except socket.timeout:
        continue  # タイムアウト時はループ継続

s.close()
print("Server stopped.")