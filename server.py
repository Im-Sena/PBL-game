import socket #Socketライブラリのインポート(python標準) 
import threading #マルチクライアントをのためのライブラリ(python標準)
import sys #システムにアクセスするためのライブラリ(python標準)

clients =[]  # 現在接続している全クライアントのソケット 
clients_full = [] #現在接続している全クライアントのソケット ,アドレス, usernameを格納
clients_lock=threading.Lock()

roomPlayer = 0 #現在のルーム内の人数を格納する 
CAPACITY = 4 #最大人数 



#メッセージを他の人に送信する関数(送信者を除く)
def broadcast(message, sender_conn):
    global roomPlayer
    # 同時に操作されないようにロック withを使うことで中の処理が終わったら自動的にロック解除 
    #lock.acquire(),lock.release()で挟むのも可 
    with clients_lock: #threadに割り込み(排他的制御) 
        for client in clients: #clientsのリスト/回 loop 
            if client != sender_conn:  # 送信者には送らない  
                try:
                    client.send(message.encode('utf-8'))  # メッセージを送信 
                except:
                    clients.remove(client)  # 接続が切れたら削除 
                    roomPlayer -= 1


#サーバーから他の人にメッセージを送る
def server_message(message):
    global roomPlayer
    # 同時に操作されないようにロック withを使うことで中の処理が終わったら自動的にロック解除 
    #lock.acquire(),lock.release()で挟むのも可 
    with clients_lock: #threadに割り込み(排他的制御) 
        for client in clients: #clientsのリスト/回 loop 
            try:
                client.send(message.encode('utf-8'))  # メッセージを送信 
            except:
                clients.remove(client)  # 接続が切れたら削除 
                roomPlayer -= 1


# 個々のクライアントを処理する関数 
def handle_client(connection, address):
    print_safe(f"Client connected: {address}")

    global roomPlayer

    #ユーザーネーム登録
    try:
        username = connection.recv(1024).decode("utf-8")  # 最初にユーザー名を受信
    except:
        connection.close()
        return

    with clients_lock: #割り込み 
         clients.append(connection) #配列の末尾に追加 
         clients_full.append((conn, addr, username))
         roomPlayer += 1
    try:
        while True:
            data = connection.recv(4096).decode() #相手から送信されるデータを待ち受けてbytesオブジェクトとして受信,デコード recvの引数はバッファ 
            if not data or data == "quit":#空かquitなら処理終了 
                roomPlayer -=1
                break
            print_safe(f"[{username}] {data}") #コンソール上に受信したメッセージを記 
            #response = f"[{address}] said : [{data}]" 
            #connection.send(response.encode("utf-8")) #エンコード,送信 
            broadcast(f"[{username}] {data}", connection)  # みんなに配信 
    except:
        pass
    finally:
        # 切断処理 
        with clients_lock:
            clients.remove(connection)
            clients_full.remove((conn, addr))
            clients_full[:] = [(c, a, n) for (c, a, n) in clients_full if c != connection] #clients_full に格納されているすべての (conn, addr, name) タプルの中から、切断されたクライアントの connection を持つ要素だけ削除する。
        connection.close(connection)
        print(f"[-] Disconnected {username}")
        


# コンソールから入力を受け付ける別スレッド 
def input_thread():
    global running #グローバル変数 
    while True:
        cmd = input('>>>')
        if cmd == "exit":
            running = False
            break
        elif cmd == "list":
            with clients_lock:
                if not clients:
                    print("[接続中クライアント] なし")
                else:
                    print("[接続中クライアント]")
                    for i, (conn, addr, uname) in enumerate(clients_full, 1):#enumerateでインデックスを付与
                        print(f"  {i}: {uname} ({addr[0]}:{addr[1]})")
        elif cmd == "say":
            msg = input('>')
            print(f"全クライアントに'{msg}'を送信しました。")
            server_message(f"[server]:{msg}")
        elif cmd == "cap":
            print(f"{roomPlayer}/{CAPACITY}")
            server_message(f"{roomPlayer}/{CAPACITY}")

#コンソールに常に[>]を出すための割り込み処理 
def print_safe(*args, **kwargs): #可変長引数を使う 
    with threading.Lock(): #threadに割り込み 
        print(*args, **kwargs)        # 普通のログ出力 
        sys.stdout.write(">>>")        # プロンプト再表示（改行なし）
        sys.stdout.flush()            # 画面に即時反映 




#サーバのipとport設定 
ip = '127.0.0.1' #(127.0.0.1)はlocalhost host名の指定も可 
print("ポートを入力してください")
#port = 8003 #0-1023以外
port = int(input(">>>"))

#ソケットの作成
s= socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
#ソケットを作成して変数sに割り当て AF_INET = ipv4 
#ストリームソケットはTCPを使用して通信を行えるようにしてくれる 
s.bind((ip, port)) #ipとportをタプルで指定  
s.listen(CAPACITY) #サーバを有効にして接続を受け取る 引数で最大接続人数指定可 

s.settimeout(1.0)  # 1秒ごとに accept() をタイムアウト 
running = True


print(f"[✓]Server started on {ip}:{port}, waiting for connections...")
print("Type 'exit' to shut down.")


threading.Thread(target=input_thread, daemon=True).start() #inputをスレッドで実行 

#loop 
while running:
    try:
        conn, addr = s.accept() #s.accept()で接続を受け付け 
        #新しいスレッドの作成, target=handle_clientでスレッドが実行される関数を指定 
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start() #スレッド実行 

    except socket.timeout:
        #タイムアウト = 新しい接続なし → 何もしないで次のループへ 
        continue

s.close()
print("Server stopped.")