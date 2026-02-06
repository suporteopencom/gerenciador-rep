import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';

// 1. Definição do Componente Dashboard (deve vir antes da renderização)
const Dashboard = ({ userId }) => {
  const [relogios, setRelogios] = useState([]);
  const [statusCmd, setStatusCmd] = useState('');
  
  // Estados para o formulário
  const [novoNS, setNovoNS] = useState('');
  const [userRelogio, setUserRelogio] = useState('admin');
  const [passRelogio, setPassRelogio] = useState('123');

  // URL da sua instância AWS que configuramos nos segredos
  const API_URL = "http://54.227.16.187:5000";

  const vincularRelogio = async (e) => {
    e.preventDefault();
    setStatusCmd('Vinculando...');
    try {
      const response = await fetch(`${API_URL}/api/vincular`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          ns: novoNS,
          user_relogio: userRelogio,
          pass_relogio: passRelogio
        })
      });
      if (response.ok) {
        setStatusCmd('Relógio cadastrado com sucesso!');
        setNovoNS('');
      } else {
        setStatusCmd('Erro na resposta do servidor.');
      }
    } catch (error) {
      setStatusCmd('Erro ao conectar com a API.');
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h2>Meus Relógios Henry (Cloud)</h2>
      
      {/* Formulário de Cadastro */}
      <form onSubmit={vincularRelogio} style={{ background: '#f4f4f4', padding: '15px', borderRadius: '8px', maxWidth: '500px' }}>
        <h3>Vincular Novo Equipamento</h3>
        <div style={{ marginBottom: '10px' }}>
          <input 
            placeholder="Número de Série (NS)" 
            value={novoNS} 
            onChange={e => setNovoNS(e.target.value)} 
            style={{ width: '95%', padding: '8px', marginBottom: '10px' }}
          />
          <input 
            placeholder="Usuário do Relógio" 
            value={userRelogio} 
            onChange={e => setUserRelogio(e.target.value)} 
            style={{ width: '45%', padding: '8px', marginRight: '5%' }}
          />
          <input 
            type="password"
            placeholder="Senha do Relógio" 
            value={passRelogio} 
            onChange={e => setPassRelogio(e.target.value)} 
            style={{ width: '45%', padding: '8px' }}
          />
        </div>
        <button type="submit" style={{ padding: '10px 20px', cursor: 'pointer', background: '#007bff', color: '#fff', border: 'none', borderRadius: '4px' }}>
          Cadastrar Relógio
        </button>
      </form>

      {/* Listagem de Relógios */}
      <div style={{ marginTop: '30px' }}>
        <h3>Status dos Equipamentos</h3>
        {relogios.length === 0 ? <p>Nenhum relógio vinculado.</p> : relogios.map(r => (
          <div key={r.ns} style={{ border: '1px solid #ccc', padding: '15px', marginBottom: '10px', borderRadius: '5px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <strong>NS: {r.ns}</strong> 
              <span style={{ marginLeft: '15px', color: r.online ? 'green' : 'red' }}>
                {r.online ? '🟢 ONLINE' : '🔴 OFFLINE'}
              </span>
            </div>
          </div>
        ))}
      </div>
      
      <div style={{ marginTop: '20px', padding: '10px', background: '#eee', borderRadius: '4px' }}>
        <strong>Log do Sistema:</strong> {statusCmd}
      </div>
    </div>
  );
};

// 2. Renderização Final no elemento 'root' definido no seu index.html
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <Dashboard userId="1" />
  </React.StrictMode>
);