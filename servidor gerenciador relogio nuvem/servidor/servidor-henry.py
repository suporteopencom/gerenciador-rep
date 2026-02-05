import socket
import threading
import sqlite3
import logging
import re
import traceback
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_cors import CORS

# Importa a sua classe original
try:
    from hexa_client import HexaProtocolClient
except ImportError:
    logging.error("Ficheiro hexa_client.py não encontrado!")

# --- CONFIGURAÇÕES E GLOBAIS ---
app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aws'
CORS(app) # Essencial para o seu React conseguir comunicar com a API

DB_NAME = 'db_usuarios.sqlite'
# Dicionário para manter os relógios que se ligaram à AWS ativos na memória
# Chave: IP ou NS do Relógio | Valor: Objeto de conexão socket
relogios_ativos = {}

# --- MOTOR DE COMUNICAÇÃO TCP (AWS como Servidor) ---
def gerenciar_conexao_relogio(conn, addr):
    """Thread que mantém o 'cano' aberto com o relógio Henry."""
    ip_relogio = addr[0]
    logging.info(f"Relógio conectado: {ip_relogio}")
    relogios_ativos[ip_relogio] = conn
    
    try:
        while True:
            # Mantém a conexão viva. Se o relógio desconectar, o recv retorna vazio.
            data = conn.recv(1024)
            if not data:
                break
            # Aqui você poderia processar batidas de ponto em tempo real (Push)
    except Exception as e:
        logging.error(f"Erro na conexão com {ip_relogio}: {e}")
    finally:
        if ip_relogio in relogios_ativos:
            del relogios_ativos[ip_relogio]
        conn.close()

def iniciar_socket_server():
    """Inicia o servidor na porta 3000 para os relógios."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 3000)) # Porta aberta no seu Security Group
    server.listen(10)
    logging.info("Servidor TCP da AWS ouvindo na porta 3000...")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=gerenciar_conexao_relogio, args=(conn, addr), daemon=True).start()

# --- ADAPTAÇÃO DA SUA LÓGICA ORIGINAL (RELOGIO1.py) ---

def enviar_comando_via_socket_existente(ip_relogio, cmd, dados='', user='admin', password='123'):
    """
    Versão modificada da sua função coletar_dados_rep.
    Em vez de dar 'connect()', ela usa o socket que já está no dicionário relogios_ativos.
    """
    if ip_relogio not in relogios_ativos:
        return '99', "Relógio não está online (não se conectou à AWS)."

    conn = relogios_ativos[ip_relogio]
    client = HexaProtocolClient(ip_relogio)
    client.socket = conn # Injeta a conexão já aberta

    try:
        # O processo de autenticação usa a conexão injetada
        if not client.authenticate(user, password):
            return '99', "Falha na Autenticação no protocolo Henry."
        
        response = client.send_command(cmd, data=dados)
        return response.get('status', '99'), response.get('data', '')
    except Exception as e:
        return '99', str(e)

# --- ROTAS PARA O SEU REACT ---

@app.route('/api/status', methods=['GET'])
def get_status():
    """Retorna quais relógios estão conectados no momento."""
    return jsonify({"online": list(relogios_ativos.keys())})

@app.route('/api/comando', methods=['POST'])
def api_comando():
    """Rota que o seu React chamará para enviar comandos."""
    dados_req = request.json
    ip = dados_req.get('ip')
    comando = dados_req.get('comando', 'RQ')
    
    status, resposta = enviar_comando_via_socket_existente(ip, comando)
    return jsonify({"status": status, "resposta": resposta})

@app.route('/api/meus-relogios', methods=['GET'])
def meus_relogios():
    user_id = request.args.get('userId')
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT relogio_ns, relogio_ip FROM vinculos_relogios WHERE user_id = ?", (user_id,))
    vinculos = cursor.fetchall()
    conn.close()

    lista_relogios = []
    for ns, ip_cadastrado in vinculos:
        # Verifica se o relógio está ligado à AWS no dicionário de sockets
        # Tentamos encontrar o relógio pelo IP atual da conexão ativa
        status_online = any(ip_cadastrado == ip_ativo for ip_ativo in relogios_ativos.keys())
        
        lista_relogios.append({
            "ns": ns,
            "ip": ip_cadastrado,
            "online": status_online
        })
        
    return jsonify(lista_relogios)

@app.route('/api/cadastrar-relogio', methods=['POST'])
def cadastrar_relogio():
    dados = request.json
    user_id = dados.get('userId')
    ns = dados.get('ns')
    ip = dados.get('ip') # IP que aparece na tela do relógio ou logs da AWS

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO vinculos_relogios (user_id, relogio_ns, relogio_ip) VALUES (?, ?, ?)", 
                       (user_id, ns, ip))
        conn.commit()
        conn.close()
        return jsonify({"status": "00", "mensagem": "Relógio vinculado com sucesso!"})
    except Exception as e:
        return jsonify({"status": "99", "mensagem": str(e)})

# --- INICIALIZAÇÃO DO BANCO (Baseado no seu RELOGIO1.py) ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            matricula TEXT PRIMARY KEY,
            nome TEXT,
            pis TEXT,
            cartao TEXT,
            sincronizado INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            matricula TEXT PRIMARY KEY,
            nome TEXT,
            pis TEXT,
            cartao TEXT,
            sincronizado INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    # Inicia o servidor de relógios numa thread separada
    threading.Thread(target=iniciar_socket_server, daemon=True).start()
    # Inicia a API Flask para o React
    app.run(host='0.0.0.0', port=5000)