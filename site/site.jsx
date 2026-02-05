import React, { useState, useEffect } from 'react';

const Dashboard = ({ userId }) => {
  const [relogios, setRelogios] = useState([]);
  const [statusCmd, setStatusCmd] = useState('');
  
  // Estados apenas para NS, Usuário do Relógio e Senha do Relógio
  const [novoNS, setNovoNS] = useState('');
  const [userRelogio, setUserRelogio] = useState('admin');
  const [passRelogio, setPassRelogio] = useState('123');

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
      }
    } catch (error) {
      setStatusCmd('Erro ao cadastrar.');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Meus Relógios Henry (Cloud)</h2>
      
      {/* Formulário sem IP */}
      <form onSubmit={vincularRelogio} style={{ background: '#f4f4f4', padding: '15px', borderRadius: '8px' }}>
        <h3>Vincular Novo Equipamento</h3>
        <input 
          placeholder="Número de Série (NS)" 
          value={novoNS} 
          onChange={e => setNovoNS(e.target.value)} 
          style={{ marginRight: '10px', padding: '5px' }}
        />
        <input 
          placeholder="Usuário do Relógio" 
          value={userRelogio} 
          onChange={e => setUserRelogio(e.target.value)} 
          style={{ marginRight: '10px', padding: '5px' }}
        />
        <input 
          type="password"
          placeholder="Senha do Relógio" 
          value={passRelogio} 
          onChange={e => setPassRelogio(e.target.value)} 
          style={{ marginRight: '10px', padding: '5px' }}
        />
        <button type="submit">Cadastrar</button>
      </form>

      <div style={{ marginTop: '20px' }}>
        {relogios.map(r => (
          <div key={r.ns} style={{ border: '1px solid #ccc', padding: '10px', marginBottom: '5px' }}>
            <strong>NS: {r.ns}</strong> - 
            <span> {r.online ? '🟢 ONLINE' : '🔴 OFFLINE'}</span>
            <button onClick={() => enviarComando(r.ns, 'RQ')} style={{ marginLeft: '10px' }}>Ler Quantidade</button>
          </div>
        ))}
      </div>
      <p><strong>Log:</strong> {statusCmd}</p>
    </div>
  );
};

export default Dashboard;