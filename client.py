import socket #Socketライブラリのインポート(python標準) 
import threading #マルチクライアントをのためのライブラリ(python標準) 


#サーバのipとport設定 
ip = '127.0.0.1' #(127.0.0.1)はlocalhost host名の指定も可 
port = 8000 #0-1023以外

#ソケットの作成
s= socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
#ソケットを作成して変数sに割り当て AF_INET = ipv4 
#ストリームソケットはTCPを使用して通信を行えるようにしてくれる 
#s.bind((ip, port)) #ipとportをタプルで指定 
s.connect((ip, port))

print("Connected!!!!!")

# --- サーバからのメッセージを受け取って表示 ---
def receive_messages(sock):
    while True:
        try:
            msg = sock.recv(4096).decode('utf-8')
            if msg:
                print("\n" + msg + "\n> ", end="")  # 改行せずにプロンプト復活
        except:
            break

# --- メイン処理 ---
#with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#    s.connect((ip, port))  # サーバに接続

threading.Thread(target=receive_messages, args=(s,), daemon=True).start()
    #接続の維持
while True:
    print("<メッセージを入力してください>")
    message = input('>>>')
    if not message: #空だったらquitを送信 
        s.send("quit".encode("utf-8"))
        break
    s.send(message.encode("utf-8")) #エンコード,サーバに送信  
	
s.close()
print("END")