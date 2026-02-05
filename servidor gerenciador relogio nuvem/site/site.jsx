import React, { useState, useEffect } from 'react';

/**
 * Componente Dashboard
 * @param {string} userId - O ID do usuário logado vindo do sistema de autenticação
 */
const Dashboard = ({ userId }) => {
  const [relogios, setRelogios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusCmd, setStatusCmd] = useState('');

  // Configuração da API na AWS (Mantenha o IP da sua instância)
  const API_URL = "http://54.227.16.187:5000"; 

  useEffect(() => {
    // Busca apenas os relógios vinculados a este usuário logado no banco SQLite
    // A rota /api/meus-relogios deve filtrar por ID no backend
    fetch(`${API_URL}/api/meus-relogios?userId=${userId}`)
      .then(res => {
        if (!res.ok) throw new Error("Erro ao buscar relógios");
        return res.json();
      })
      .then(data => {
        setRelogios(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [userId]);

  /**
   * Envia comandos binários para o relógio através da API Python
   * Utiliza os comandos 'RQ' ou 'RC' definidos no seu hexa_client.py
   */
  const enviarComando = async (ipRelogio, comando) => {
    setStatusCmd('Enviando comando para a AWS...');
    try {
      const response = await fetch(`${API_URL}/api/comando`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ip: ipRelogio,    // Identificador da conexão TCP ativa
          comando: comando, // Ex: 'RQ' (Quantidade) ou 'RC' (Configurações)
          user_id: userId
        })
      });
      
      const result = await response.json();
      
      // Status '00' geralmente indica sucesso no protocolo Henry
      if (result.status === '00') {
        setStatusCmd(`Sucesso! Resposta: ${JSON.stringify(result.resposta)}`);
      } else {
        setStatusCmd(`Erro no Relógio: ${result.resposta}`);
      }
    } catch (error) {
      setStatusCmd('Erro crítico: Não foi possível alcançar o servidor Python na AWS.');
    }
  };

  if (loading) return <div style={styles.container}><p>Carregando dispositivos vinculados...</p></div>;

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1>Painel de Controle Henry</h1>
        <p>Bem-vindo, Usuário: <strong>{userId}</strong></p>
      </header>
      
      <hr />
      
      <section style={styles.grid}>
        {relogios.length === 0 ? (
          <p>Você ainda não possui relógios cadastrados neste ID.</p>
        ) : (
          relogios.map(relogio => (
            <div key={relogio.ns} style={styles.card}>
              <h3>Relógio Henry - NS: {relogio.ns}</h3>
              <p>Status: <span style={styles.onlineTag}>● Online na Nuvem</span></p>
              <p><small>IP de Origem: {relogio.ip}</small></p>
              
              <div style={styles.buttonGroup}>
                <button 
                  style={styles.button} 
                  onClick={() => enviarComando(relogio.ip, 'RQ')}
                >
                  Consultar Batidas (RQ)
                </button>
                <button 
                  style={{...styles.button, backgroundColor: '#6c757d'}} 
                  onClick={() => enviarComando(relogio.ip, 'RC')}
                >
                  Ler Configurações (RC)
                </button>
              </div>
            </div>
          ))
        )}
      </section>

      <footer style={styles.footer}>
        <strong>Status da Operação:</strong> 
        <span style={styles.statusText}> {statusCmd}</span>
      </footer>
    </div>
  );
};

// Estilização simples em objetos para facilitar o uso imediato
const styles = {
  container: { padding: '20px', fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif', color: '#333' },
  header: { marginBottom: '20px' },
  grid: { display: 'flex', flexDirection: 'column', gap: '15px' },
  card: { border: '1px solid #ddd', borderRadius: '8px', padding: '20px', backgroundColor: '#f9f9f9', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' },
  onlineTag: { color: '#28a745', fontWeight: 'bold' },
  buttonGroup: { marginTop: '15px', display: 'flex', gap: '10px' },
  button: { 
    padding: '10px 15px', 
    backgroundColor: '#007bff', 
    color: '#fff', 
    border: 'none', 
    borderRadius: '4px', 
    cursor: 'pointer',
    fontWeight: 'bold'
  },
  footer: { marginTop: '30px', padding: '15px', borderTop: '1px solid #eee', backgroundColor: '#f1f1f1' },
  statusText: { color: '#0056b3' }
};

export default Dashboard;