import socket
import threading
import sqlite3
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from hexa_client import HexaProtocolClient # O seu ficheiro enviado

app = Flask(__name__)
CORS(app)
DB_NAME = 'sistema_henry.sqlite'

# Dicionário de conexões ativas na porta 3000
# Chave: IP do relógio | Valor: Objeto socket
relogios_ativos = {}

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Tabela que vincula o Usuário do Site ao Relógio Físico
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vinculos (
            user_id TEXT,
            relogio_ns TEXT,
            relogio_ip TEXT,
            PRIMARY KEY (user_id, relogio_ns)
        )
    """)
    conn.commit()
    conn.close()

# --- MOTOR TCP (SOCKET) ---
def servidor_socket():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 3000))
    server.listen(100)
    print("Porta 3000 aberta: Aguardando relógios...")
    
    while True:
        conn, addr = server.accept()
        ip_relogio = addr[0]
        relogios_ativos[ip_relogio] = conn
        print(f"Relógio conectado via IP: {ip_relogio}")
        # Mantém a thread viva para não fechar o socket
        threading.Thread(target=manter_conexao, args=(conn, ip_relogio), daemon=True).start()

def manter_conexao(conn, ip):
    try:
        while True:
            if not conn.recv(1024): break
    except:
        pass
    finally:
        relogios_ativos.pop(ip, None)
        conn.close()

# --- LÓGICA DE VALIDAÇÃO ---
def usuario_tem_permissao(user_id, ns_relogio):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Agora validamos pelo NS (Número de Série) vinculado ao usuário
    cursor.execute("SELECT 1 FROM vinculos WHERE user_id = ? AND relogio_ns = ?", (user_id, ns_relogio))
    permitido = cursor.fetchone() is not None
    conn.close()
    return permitido

# --- ROTAS API ---

@app.route('/api/comando', methods=['POST'])
def enviar_comando():
    dados = request.json
    user_id = dados.get('user_id')
    ns_alvo = str(dados.get('ns')) # O React agora envia o NS
    cmd = dados.get('comando')

    # 1. Validação de Segurança (Validando se o NS pertence ao User)
    if not usuario_tem_permissao(user_id, ns_alvo):
        return jsonify({"status": "99", "resposta": "Acesso negado: Este NS não está vinculado à sua conta."}), 403

    # 2. Verificação de Status Online (Procurando o socket pelo NS)
    if ns_alvo not in relogios_ativos:
        return jsonify({"status": "99", "resposta": f"Relógio NS {ns_alvo} não está conectado na porta 3000."})

    # 3. Execução do Comando
    try:
        conn = relogios_ativos[ns_alvo]
        
        # Criamos o cliente passando o NS (o host aqui vira o NS para controle interno)
        client = HexaProtocolClient(ns_alvo)
        client.socket = conn # Importante: injetamos a conexão que já está aberta
        
        # Buscamos as credenciais do relógio que foram salvas no banco no momento do vínculo
        conn_db = sqlite3.connect(DB_NAME)
        cursor = conn_db.cursor()
        cursor.execute("SELECT user_relogio, pass_relogio FROM vinculos WHERE relogio_ns = ?", (ns_alvo,))
        credenciais = cursor.fetchone()
        conn_db.close()

        user_rep = credenciais[0] if credenciais else "admin"
        pass_rep = credenciais[1] if credenciais else "123"

        # Autentica usando os dados que o usuário cadastrou no React
        if client.authenticate(user_rep, pass_rep):
            res = client.send_command(cmd)
            # Retornamos a resposta do seu hexa_client.py
            return jsonify({"status": "00", "resposta": res})
        else:
            return jsonify({"status": "99", "resposta": "Falha de autenticação interna com o Relógio."})
            
    except Exception as e:
        logging.error(f"Erro ao processar comando: {traceback.format_exc()}")
        return jsonify({"status": "99", "resposta": str(e)})

@app.route('/api/vincular', methods=['POST'])
def vincular():
    dados = request.json
    # Salva a relação no banco para o React usar depois
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO vinculos VALUES (?, ?, ?)", 
                   (dados['user_id'], dados['ns'], dados['ip']))
    conn.commit()
    conn.close()
    return jsonify({"status": "00"})

@app.route('/api/meus-relogios', methods=['GET'])
def listar():
    user_id = request.args.get('userId')
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT relogio_ns, relogio_ip FROM vinculos WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    # Cruza dados do banco com relógios que estão com socket aberto agora
    lista = [{"ns": r[0], "ip": r[1], "online": r[1] in relogios_ativos} for r in rows]
    return jsonify(lista)

if __name__ == '__main__':
    init_db()
    threading.Thread(target=servidor_socket, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
    