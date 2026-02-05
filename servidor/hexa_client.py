# Importação das bibliotecas necessárias
# - socket: Para comunicação TCP/IP
import socket
 
# - base64: Para codificação/decodificação de dados
import base64

# - os: Para geração de números aleatórios seguros
import os

# - threading: Para sincronização de acesso ao socket
from threading import Lock

# - cryptography: Para operações criptográficas (AES e RSA)
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives import serialization, hashes


# Classe principal que implementa o cliente do protocolo HEXA
# Responsável por estabelecer conexão, autenticar e enviar comandos para o equipamento
class HexaProtocolClient:
    # Bytes de controle do protocolo
    START_BYTE = b'\x02'  # Marca o início do pacote
    END_BYTE = b'\x03'    # Marca o fim do pacote

    # Inicializa o cliente HEXA
    # Parâmetros:
    # - host: Endereço IP do equipamento
    # - port: Porta de conexão (padrão: 3000)
    def __init__(self, host, port=3000):
        # Exibe o host recebido para debug
        print(f"--- LÓGICA --- \nHost recebido no __init__: {repr(host)}\n---")
        
        # Armazena o endereço e porta do equipamento
        self.host = host
        self.port = port
        
        # Inicializa variáveis de estado
        self.socket = None              # Socket para comunicação TCP
        self.aes_key = None             # Chave de criptografia da sessão
        self.is_authenticated = False   # Estado de autenticação
        self.index_counter = 1          # Contador para índice dos pacotes
        self.socket_lock = Lock()       # Lock para sincronização de threads

    # Estabelece a conexão TCP com o equipamento
    # Retorna:
    # - True: se a conexão foi estabelecida com sucesso
    # - False: se houve falha na conexão
    def connect(self):
        # Log da tentativa de conexão
        print(f"--- LÓGICA --- \nTentando conectar com o host: {repr(self.host)} na porta {self.port}\n---")
        try:
            # Cria um novo socket TCP/IP
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Define timeout de 10 segundos para operações
            self.socket.settimeout(10.0)
            # Tenta estabelecer a conexão
            self.socket.connect((self.host, self.port))
            # Log de sucesso
            print(f"Conectado com sucesso a {self.host}:{self.port}")
            return True
        
        except socket.error as e:
            # Log detalhado do erro em caso de falha
            print(f"--- ERRO DETALHADO --- \nOcorreu o erro: {e} \nAo tentar usar o host: {repr(self.host)}\n---")
            print(f"Falha na conexão: {e}")
            # Limpa o socket em caso de erro
            self.socket = None
            return False

    # Encerra a conexão com o equipamento
    # - Fecha o socket
    # - Limpa as variáveis de estado
    # - Reseta o estado de autenticação
    def disconnect(self):
        if self.socket:
            self.socket.close()
            self.socket = None
            self.is_authenticated = False
            print("Conexão encerrada.")

    # Calcula o checksum dos dados do pacote
    # O checksum é calculado usando XOR de todos os bytes
    # Parâmetros:
    # - data_bytes: bytes para calcular o checksum
    # Retorna:
    # - Um byte contendo o valor do checksum
    def _calculate_checksum(self, data_bytes):
        checksum = 0
        for byte in data_bytes:
            checksum ^= byte
        return checksum.to_bytes(1, 'big')

    # Constrói um pacote do protocolo HEXA
    # Estrutura do pacote:
    # [START_BYTE][SIZE][PAYLOAD][CHECKSUM][END_BYTE]
    # Onde PAYLOAD = index+command+status+data
    # 
    # Parâmetros:
    # - command: comando a ser enviado
    # - status: código de status (padrão "00")
    # - data: dados adicionais do comando
    # - index: índice do pacote para controle
    # - use_aes: indica se deve criptografar o payload com AES
    def _build_packet(self, command, status="00", data="", index="01", use_aes=False):
        # Constrói a string do payload com formato: index+command+status+data
        payload_str = f"{index}+{command}+{status}"
        if data:
            payload_str += f"+{data}"
        
        # Converte o payload para bytes
        payload_bytes = payload_str.encode('utf-8')

        # Se necessário, criptografa o payload usando AES
        if use_aes and self.is_authenticated and self.aes_key:
            # Gera um IV (Vetor de Inicialização) aleatório
            iv = os.urandom(16) 
            # Cria o cipher AES no modo CBC
            cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(iv))
            encryptor = cipher.encryptor()
            
            # Adiciona padding para garantir tamanho múltiplo de 16 bytes
            padding_size = 16 - (len(payload_bytes) % 16)
            if padding_size == 0:
                padding_size = 16
            padded_data = payload_bytes + (b'\x00' * padding_size)
            
            # Criptografa os dados e concatena com o IV
            encrypted_payload = encryptor.update(padded_data) + encryptor.finalize()
            payload_bytes = iv + encrypted_payload

        # Monta o pacote final:
        # [START_BYTE][SIZE][PAYLOAD][CHECKSUM][END_BYTE]
        size = len(payload_bytes)
        size_bytes = size.to_bytes(2, 'little')
        checksum_data = size_bytes + payload_bytes
        checksum_byte = self._calculate_checksum(checksum_data)
        packet = self.START_BYTE + size_bytes + payload_bytes + checksum_byte + self.END_BYTE
        return packet

    # Analisa e processa a resposta recebida do equipamento
    # - Verifica a integridade do pacote (END_BYTE e checksum)
    # - Extrai o tamanho e payload
    # - Descriptografa o payload se necessário
    # - Decompõe o payload em suas partes (index, command, status, data)
    # 
    # Retorna um dicionário com as partes do payload
    def _parse_response(self, full_response):
        # Verifica se o pacote termina com o byte correto
        if full_response[-1] != self.END_BYTE[0]:
            raise ValueError("Pacote inválido (End Byte incorreto).")
        
        # Extrai o tamanho e o payload do pacote
        payload_size = int.from_bytes(full_response[1:3], 'little')
        payload_bytes = full_response[3:-2]
        
        # Valida se o tamanho do payload corresponde ao declarado
        if len(payload_bytes) != payload_size:
            raise ValueError(f"Tamanho do payload não corresponde. Esperado: {payload_size}, Recebido: {len(payload_bytes)}")

        # Verifica o checksum do pacote
        received_checksum = full_response[-2]
        checksum_data_to_verify = full_response[1:-2]
        calculated_checksum_val = 0
        for byte in checksum_data_to_verify:
            calculated_checksum_val ^= byte
        # Avisa se o checksum não corresponde, mas continua o processamento
        if received_checksum != calculated_checksum_val:
            print(f"AVISO: Checksum inválido. Recebido: {received_checksum}, Calculado: {calculated_checksum_val}. Prosseguindo...")
        # Tenta decodificar o payload para identificar o comando
        try:
            # Tenta converter os bytes para string UTF-8
            temp_payload_str = payload_bytes.decode('utf-8')
            # Extrai o comando da resposta (segundo campo após divisão por '+')
            command_in_response = temp_payload_str.split('+')[1]
        except (UnicodeDecodeError, IndexError):
            # Se não conseguir decodificar ou não encontrar o comando, define como None
            command_in_response = None

        # Verifica se é necessário descriptografar o payload
        # - Deve estar autenticado
        # - Não deve ser resposta dos comandos EA ou RA (que não são criptografados)
        if self.is_authenticated and command_in_response not in ['EA', 'RA']:
            print("DEBUG: Tentando descriptografar a resposta...")
            try:
                # Processo de descriptografia AES-CBC:
                # 1. Extrai o IV (16 bytes iniciais)
                iv = payload_bytes[:16]
                # 2. Separa o payload criptografado (restante dos bytes)
                encrypted_payload = payload_bytes[16:]
                # 3. Configura o objeto de descriptografia AES com a chave da sessão
                cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(iv))
                decryptor = cipher.decryptor()
                # 4. Descriptografa o payload
                payload_bytes = decryptor.update(encrypted_payload) + decryptor.finalize()
                print("DEBUG: Descriptografia bem-sucedida.")
            except ValueError as e:
                # Erro na descriptografia pode indicar problema com a chave AES
                raise ValueError(f"Erro de descriptografia irrecuperável: {e}. A chave AES está dessincronizada.")
                
        payload_str = payload_bytes.rstrip(b'\x00').decode('utf-8', errors='ignore')
        
        print(f"DEBUG: Payload final para parsing: {repr(payload_str)}")
        parts = payload_str.split('+')
        
        response_dict = {"index": "??", "command": "??", "status": "??", "data": ""}
        if len(parts) >= 3:
            response_dict["index"] = parts[0]; response_dict["command"] = parts[1]; response_dict["status"] = parts[2]
            if len(parts) > 3:
                response_dict["data"] = "+".join(parts[3:])
        else:
            print(f"AVISO: Payload mal formatado recebido: {parts}")
            if len(parts) > 0: response_dict["index"] = parts[0]
            if len(parts) > 1: response_dict["command"] = parts[1]
            if len(parts) > 2: response_dict["status"] = parts[2]

        return response_dict
        
    # Envia um pacote e recebe a resposta do equipamento
    # - Usa um lock para garantir acesso exclusivo ao socket
    # - Limpa o buffer de recebimento antes de enviar
    # - Envia o pacote e aguarda a resposta
    # - Lê o cabeçalho e o payload da resposta
    # - Processa a resposta usando _parse_response
    def _send_and_receive(self, packet):
        with self.socket_lock:  # Garante acesso exclusivo ao socket
            # Verifica se há conexão ativa
            if not self.socket:
                raise ConnectionError("Não conectado. Chame connect() primeiro.")
            
            # Limpa o buffer de recebimento
            self.socket.setblocking(False)
            try:
                while self.socket.recv(4096): pass
            except BlockingIOError:
                pass
            self.socket.setblocking(True)

            # Envia o pacote
            self.socket.sendall(packet)

            # Recebe o cabeçalho (3 bytes: START_BYTE + 2 bytes de tamanho)
            header = self.socket.recv(3)
            if not header or header[0] != self.START_BYTE[0]:
                raise ConnectionError("Resposta inválida ou conexão perdida (cabeçalho incorreto).")
            
            # Extrai o tamanho do payload e calcula bytes totais a receber
            payload_size = int.from_bytes(header[1:3], 'little')
            bytes_to_read = payload_size + 2  # +2 para checksum e END_BYTE
            
            # Recebe o resto do pacote em chunks
            response_data = b''
            while len(response_data) < bytes_to_read:
                chunk = self.socket.recv(bytes_to_read - len(response_data))
                if not chunk:
                    raise ConnectionError("Conexão perdida durante o recebimento da resposta.")
                response_data += chunk
                
            full_response = header + response_data
            
            return self._parse_response(full_response)
            
    # Realiza o processo de autenticação com o equipamento
    # Processo:
    # 1. Envia comando RA para receber a chave pública RSA
    # 2. Gera uma chave AES aleatória para a sessão
    # 3. Criptografa as credenciais e a chave AES com RSA
    # 4. Envia comando EA com as credenciais criptografadas
    # 
    # Parâmetros:
    # - user: nome do usuário
    # - password: senha do usuário
    # - _retry_count: contador interno de tentativas
    def authenticate(self, user, password, _retry_count=0):
        # Limita o número de tentativas de autenticação
        if _retry_count > 2:
            print("Falha na autenticação após múltiplas tentativas.")
            return False

        try:
            # Etapa 1: Requisição da chave pública RSA
            print(f"Enviando comando RA (Tentativa {_retry_count + 1})...")
            packet_ra = self._build_packet("RA", use_aes=False)
            response_ra = self._send_and_receive(packet_ra)
            
            # Se a sessão anterior expirou, tenta novamente
            if response_ra['status'] == "005":
                print("Sessão de autenticação anterior expirou. Reiniciando o processo...")
                return self.authenticate(user, password, _retry_count + 1)

            # Verifica se a resposta RA foi bem sucedida
            if response_ra['status'] in ["00", "000"]:
                pass
            else:
                print(f"Falha na etapa RA. Status: {response_ra['status']}")
                return False

            # Processa a resposta RA para extrair a chave pública
            data_str = response_ra['data'].strip()
            rsa_parts = data_str.split(']')
            if len(rsa_parts) < 2:
                print(f"Resposta RA OK, mas payload da chave está mal formatado: {data_str}")
                return False 
            
            # Extrai o módulo e expoente da chave RSA
            modulus_b64, exponent_b64 = rsa_parts[0], rsa_parts[1]

            # Gera uma nova chave AES aleatória para a sessão
            self.aes_key = os.urandom(16)
            aes_key_b64 = base64.b64encode(self.aes_key).decode('utf-8')
            # Monta a string de credenciais: versão + usuário + senha + chave AES
            credentials_str = f"1]{user}]{password}]{aes_key_b64}"
            
            # Reconstrói a chave pública RSA a partir dos dados recebidos
            modulus_val = int.from_bytes(base64.b64decode(modulus_b64), 'big')
            exponent_val = int.from_bytes(base64.b64decode(exponent_b64), 'big')
            public_key = rsa.RSAPublicNumbers(exponent_val, modulus_val).public_key()
            
            encrypted_credentials = public_key.encrypt(
                credentials_str.encode('utf-8'),
                asym_padding.PKCS1v15()
            )
            encrypted_credentials_b64 = base64.b64encode(encrypted_credentials).decode('utf-8')

            print("Enviando comando EA...")
            packet_ea = self._build_packet("EA", data=encrypted_credentials_b64, use_aes=False)
            response_ea = self._send_and_receive(packet_ea)
            
            if response_ea['status'] in ["07", "000"]:
                self.is_authenticated = True
                print("Autenticação bem-sucedida! Chave de sessão estabelecida.")
                return True
            else:
                self.aes_key = None
                error_details = response_ea.get('data', '')
                print(f"Falha na autenticação (etapa EA). Status: {response_ea['status']} - Detalhes: {error_details}")
                return False
                
        except Exception as e:
            print(f"Ocorreu um erro crítico durante a autenticação: {e}")
            import traceback
            traceback.print_exc()
            self.is_authenticated = False
            self.aes_key = None
            return False
            
    # Envia um comando para o equipamento
    # - Verifica se está autenticado (exceto para comandos RA e EA)
    # - Incrementa o contador de índice
    # - Constrói e envia o pacote
    # - Retorna a resposta processada
    # 
    # Parâmetros:
    # - command: comando a ser enviado
    # - status: código de status (padrão "00")
    # - data: dados adicionais do comando
    def send_command(self, command, status="00", data=""):
        # Verifica se é necessária autenticação para o comando
        if not self.is_authenticated:
            if command not in ["RA", "EA"]:  # Comandos RA e EA são permitidos sem autenticação
                raise PermissionError("Autenticação necessária para enviar este comando.")
        
        # Gera o índice do pacote (circular de 01 a 99)
        index_str = str(self.index_counter % 100).zfill(2)
        self.index_counter += 1

        # Constrói e envia o pacote, usando AES se autenticado
        packet = self._build_packet(command, status, data, index=index_str, use_aes=self.is_authenticated)
        return self._send_and_receive(packet)


# Código de exemplo e teste da classe
# Demonstra como usar o cliente para:
# 1. Conectar ao equipamento
# 2. Autenticar
# 3. Enviar comandos
# 4. Processar respostas
if __name__ == "__main__":
    # Configurações de exemplo para teste
    EQUIPMENT_IP = "192.168.1.200" 
    USER = "admin"
    PASSWORD = "123"
    
    # Cria uma instância do cliente
    client = HexaProtocolClient(EQUIPMENT_IP)

    # Tenta conectar ao equipamento
    if client.connect():
        # Tenta autenticar com as credenciais fornecidas
        if client.authenticate(USER, PASSWORD):
            print("\n--- Testando comando após autenticação ---")
            try:
                # Teste 1: Leitura de configurações
                print("Enviando comando RC (Ler Configurações)...")
                response = client.send_command("RC")
                print(f"Resposta RC: {response}")

                # Teste 2: Leitura de quantidades
                print("\nEnviando comando RQ (Ler Quantidades)...")
                response = client.send_command("RQ")
                print(f"Resposta RQ: {response}")
                
            except Exception as e:
                print(f"Erro ao enviar comando: {e}")
        
        # Encerra a conexão ao finalizar
        client.disconnect()