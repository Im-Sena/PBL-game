import socket #Socketライブラリのインポート(python標準) 
import threading #マルチクライアントをのためのライブラリ(python標準)
import sys #システムにアクセスするためのライブラリ(python標準)

clients =[]  # 現在接続している全クライアントのソケット 
clients_full = []
clients_lock=threading.Lock()


#メッセージを他の人に送信する関数(送信者を除く)
def broadcast(message, sender_conn):
    # 同時に操作されないようにロック withを使うことで中の処理が終わったら自動的にロック解除 
    #lock.acquire(),lock.release()で挟むのも可 
    with clients_lock: #threadに割り込み(排他的制御) 
        for client in clients: #clientsのリスト/回 loop 
            if client != sender_conn:  # 送信者には送らない  
                try:
                    client.send(message.encode('utf-8'))  # メッセージを送信 
                except:
                    clients.remove(client)  # 接続が切れたら削除 


#サーバーから他の人にメッセージを送る
def server_message(message):
    # 同時に操作されないようにロック withを使うことで中の処理が終わったら自動的にロック解除 
    #lock.acquire(),lock.release()で挟むのも可 
    with clients_lock: #threadに割り込み(排他的制御) 
        for client in clients: #clientsのリスト/回 loop 
            try:
                client.send(message.encode('utf-8'))  # メッセージを送信 
            except:
                clients.remove(client)  # 接続が切れたら削除 


# 個々のクライアントを処理する関数 
def handle_client(connection, address):
    print_safe(f"Client connected: {address}")

    with clients_lock: #割り込み 
         clients.append(connection) #配列の末尾に追加 
         clients_full.append((conn, addr))
    try:
        while True:
            data = connection.recv(4096).decode() #相手から送信されるデータを待ち受けてbytesオブジェクトとして受信,デコード recvの引数はバッファ 
            if not data or data == "quit":#空かquitなら処理終了 
                break
            print_safe(f"[{address}] {data}") #コンソール上に受信したメッセージを記 
            #response = f"[{address}] said : [{data}]" 
            #connection.send(response.encode("utf-8")) #エンコード,送信 
            broadcast(f"[{address}] {data}", connection)  # みんなに配信 
    except:
        pass
    finally:
        # 切断処理 
        with clients_lock:
            clients.remove(connection)
            clients_full.remove((conn, addr))
        connection.close(connection)
        print(f"[-] Disconnected {address}")
        


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
                    for i, (conn, addr) in enumerate(clients_full, 1):#enumerateでインデックスを付与
                        print(f"  {i}: {addr[0]}:{addr[1]}")
        elif cmd == "say":
            msg = input('>')
            print(f"全クライアントに'{msg}'を送信しました。")
            server_message(f"[server]:{msg}")

#コンソールに常に[>]を出すための割り込み処理 
def print_safe(*args, **kwargs): #可変長引数を使う 
    with threading.Lock(): #threadに割り込み 
        print(*args, **kwargs)        # 普通のログ出力 
        sys.stdout.write(">>>")        # プロンプト再表示（改行なし）
        sys.stdout.flush()            # 画面に即時反映 




#サーバのipとport設定 
ip = '127.0.0.1' #(127.0.0.1)はlocalhost host名の指定も可 
port = 8000 #0-1023以外

#ソケットの作成
s= socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
#ソケットを作成して変数sに割り当て AF_INET = ipv4 
#ストリームソケットはTCPを使用して通信を行えるようにしてくれる 
s.bind((ip, port)) #ipとportをタプルで指定  
s.listen(4) #サーバを有効にして接続を受け取る 引数で最大接続人数指定可 

s.settimeout(1.0)  # 1秒ごとに accept() をタイムアウト 
running = True


print(f"[✓]Server started on {ip}:{port}, waiting for connections...")
print("Type 'exit' to shut down.")

'''
#接続の受付 
connection, address = s.accept() #s.accept()で接続を受け付け
print("client ; {}".format(address)) #接続相手のipをprint 
#接続の維持
while True:
    receive = connection.recv(4096).decode()#相手から送信されるデータを待ち受けてbytesオブジェクトとして受信,デコード recvの引数はバッファ 
    if receive == "quit": #quitを受信でbreak 
        break
    print("received -> message : {}".format(receive))
    send_message = "you said : [{}] ".format(receive)
    connection.send(send_message.encode("utf-8")) #エンコード,クライアントに送信 


#接続終了 
connection.close() #コネクション切断 
s.close()
print("Communication disconnected")
'''

threading.Thread(target=input_thread, daemon=True).start()

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