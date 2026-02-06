import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';

// --- ESTILOS GLOBAIS (Simulando um arquivo CSS) ---
const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f0f2f5',
    fontFamily: '"Segoe UI", Roboto, Helvetica, Arial, sans-serif',
  },
  card: {
    backgroundColor: '#ffffff',
    padding: '40px',
    borderRadius: '12px',
    boxShadow: '0 8px 24px rgba(0,0,0,0.1)',
    width: '100%',
    maxWidth: '400px',
    textAlign: 'center',
  },
  input: {
    width: '100%',
    padding: '12px',
    margin: '10px 0',
    border: '1px solid #ddd',
    borderRadius: '6px',
    fontSize: '16px',
    boxSizing: 'border-box',
  },
  button: {
    width: '100%',
    padding: '12px',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'background 0.3s',
    marginTop: '10px',
  },
  dashboardNav: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: '15px 30px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
    marginBottom: '30px'
  }
};

// --- COMPONENTE DE LOGIN ---
const Login = ({ onLogin }) => {
  const [user, setUser] = useState('');
  const [pass, setPass] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    // Aqui você integrará com sua API futuramente
    if (user === 'admin' && pass === '123') {
      onLogin({ id: "1", name: "Administrador" });
    } else {
      alert("Credenciais inválidas!");
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={{ color: '#1c1e21', marginBottom: '10px' }}>Henry Cloud</h2>
        <p style={{ color: '#606770', marginBottom: '25px' }}>Gerenciamento de Ponto Independente</p>
        <form onSubmit={handleSubmit}>
          <input 
            style={styles.input} 
            placeholder="Usuário" 
            value={user} 
            onChange={e => setUser(e.target.value)} 
          />
          <input 
            type="password" 
            style={styles.input} 
            placeholder="Senha" 
            value={pass} 
            onChange={e => setPass(e.target.value)} 
          />
          <button type="submit" style={styles.button}>Acessar Painel</button>
        </form>
      </div>
    </div>
  );
};

// --- COMPONENTE DASHBOARD ---
const Dashboard = ({ user, onLogout }) => {
  const [relogios, setRelogios] = useState([]);
  const [statusCmd, setStatusCmd] = useState('Sistema pronto');
  const [novoNS, setNovoNS] = useState('');
  
  const API_URL = "http://54.227.16.187:5000";

  const vincularRelogio = async (e) => {
    e.preventDefault();
    setStatusCmd('Processando vínculo...');
    try {
      const response = await fetch(`${API_URL}/api/vincular`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.id, ns: novoNS })
      });
      if (response.ok) {
        setStatusCmd('✅ Equipamento vinculado com sucesso!');
        setNovoNS('');
      } else {
        setStatusCmd('❌ Erro ao vincular. Verifique o NS.');
      }
    } catch (error) {
      setStatusCmd('⚠️ Erro de conexão com o servidor.');
    }
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8f9fa' }}>
      <nav style={styles.dashboardNav}>
        <h3 style={{ margin: 0, color: '#007bff' }}>Henry Cloud</h3>
        <div>
          <span style={{ marginRight: '15px', color: '#666' }}>Olá, <strong>{user.name}</strong></span>
          <button onClick={onLogout} style={{ ...styles.button, width: 'auto', padding: '5px 15px', marginTop: 0, backgroundColor: '#dc3545' }}>Sair</button>
        </div>
      </nav>

      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '0 20px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px' }}>
          
          {/* Coluna de Cadastro */}
          <div style={{ ...styles.card, maxWidth: 'none', textAlign: 'left' }}>
            <h4 style={{ marginTop: 0 }}>Vincular Equipamento</h4>
            <input 
              style={styles.input} 
              placeholder="Número de Série (Ex: 000123)" 
              value={novoNS} 
              onChange={e => setNovoNS(e.target.value)} 
            />
            <button onClick={vincularRelogio} style={styles.button}>Vincular Agora</button>
            <p style={{ fontSize: '12px', color: '#888', marginTop: '15px' }}>{statusCmd}</p>
          </div>

          {/* Coluna de Status */}
          <div style={{ ...styles.card, maxWidth: 'none', textAlign: 'left' }}>
            <h4 style={{ marginTop: 0 }}>Status em Tempo Real</h4>
            {relogios.length === 0 ? (
              <p style={{ color: '#999', fontStyle: 'italic' }}>Nenhum relógio monitorado.</p>
            ) : (
              relogios.map(r => (
                <div key={r.ns} style={{ padding: '10px', borderBottom: '1px solid #eee', display: 'flex', justifyContent: 'space-between' }}>
                  <span>NS: {r.ns}</span>
                  <span style={{ color: r.online ? '#28a745' : '#dc3545' }}>{r.online ? '● Online' : '● Offline'}</span>
                </div>
              ))
            )}
          </div>

        </div>
      </div>
    </div>
  );
};

// --- COMPONENTE PRINCIPAL (Gerenciador de Rotas) ---
const App = () => {
  const [sessao, setSessao] = useState(null);

  return (
    <>
      {!sessao ? (
        <Login onLogin={setSessao} />
      ) : (
        <Dashboard user={sessao} onLogout={() => setSessao(null)} />
      )}
    </>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);