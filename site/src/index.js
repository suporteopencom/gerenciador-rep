import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';

// --- ESTILOS GLOBAIS ---
const styles = {
  container: { minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f0f2f5', fontFamily: '"Segoe UI", Roboto, sans-serif' },
  card: { backgroundColor: '#ffffff', padding: '30px', borderRadius: '12px', boxShadow: '0 8px 24px rgba(0,0,0,0.1)', width: '100%', maxWidth: '400px', textAlign: 'center' },
  input: { width: '100%', padding: '12px', margin: '10px 0', border: '1px solid #ddd', borderRadius: '6px', fontSize: '14px', boxSizing: 'border-box' },
  button: { width: '100%', padding: '12px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '6px', fontWeight: '600', cursor: 'pointer', marginTop: '10px' },
  nav: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#fff', padding: '15px 30px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)', marginBottom: '30px' },
  badge: { padding: '4px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold' },
  table: { width: '100%', borderCollapse: 'collapse', marginTop: '20px' },
  th: { textAlign: 'left', padding: '12px', borderBottom: '2px solid #eee', color: '#666' },
  td: { padding: '12px', borderBottom: '1px solid #eee' }
};

// --- COMPONENTE GESTÃO DE USUÁRIOS (Nova Funcionalidade) ---
const GerenciarUsuarios = () => {
  const [usuarios, setUsuarios] = useState([
    { id: 1, nome: 'Suporte Opencom', login: 'admin', status: 'ativo' }
  ]);
  const [novoUser, setNovoUser] = useState({ nome: '', login: '', senha: '' });

  const adicionarUsuario = () => {
    if (!novoUser.nome || !novoUser.login) return alert("Preencha os campos!");
    const user = { ...novoUser, id: Date.now(), status: 'ativo' };
    setUsuarios([...usuarios, user]);
    setNovoUser({ nome: '', login: '', senha: '' });
  };

  const alternarStatus = (id) => {
    setUsuarios(usuarios.map(u => u.id === id ? { ...u, status: u.status === 'ativo' ? 'bloqueado' : 'ativo' } : u));
  };

  const excluirUsuario = (id) => {
    if(window.confirm("Deseja excluir este usuário?")) setUsuarios(usuarios.filter(u => u.id !== id));
  };

  return (
    <div style={{ ...styles.card, maxWidth: '800px', margin: '0 auto', textAlign: 'left' }}>
      <h3>Gestão de Usuários do Sistema</h3>
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <input style={styles.input} placeholder="Nome" value={novoUser.nome} onChange={e => setNovoUser({...novoUser, nome: e.target.value})} />
        <input style={styles.input} placeholder="Login" value={novoUser.login} onChange={e => setNovoUser({...novoUser, login: e.target.value})} />
        <input style={styles.input} type="password" placeholder="Senha" value={novoUser.senha} onChange={e => setNovoUser({...novoUser, senha: e.target.value})} />
        <button style={{ ...styles.button, width: '200px' }} onClick={adicionarUsuario}>Cadastrar</button>
      </div>

      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>Nome</th>
            <th style={styles.th}>Login</th>
            <th style={styles.th}>Status</th>
            <th style={styles.th}>Ações</th>
          </tr>
        </thead>
        <tbody>
          {usuarios.map(u => (
            <tr key={u.id}>
              <td style={styles.td}>{u.nome}</td>
              <td style={styles.td}>{u.login}</td>
              <td style={styles.td}>
                <span style={{ ...styles.badge, backgroundColor: u.status === 'ativo' ? '#e1f7e1' : '#fce4e4', color: u.status === 'ativo' ? '#28a745' : '#dc3545' }}>
                  {u.status.toUpperCase()}
                </span>
              </td>
              <td style={styles.td}>
                <button onClick={() => alternarStatus(u.id)} style={{ marginRight: '5px', cursor: 'pointer' }}>{u.status === 'ativo' ? '🚫 Bloquear' : '✅ Ativar'}</button>
                <button onClick={() => excluirUsuario(u.id)} style={{ color: 'red', cursor: 'pointer' }}>🗑️ Excluir</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// --- COMPONENTE LOGIN ---
const Login = ({ onLogin }) => {
  const [user, setUser] = useState('');
  const [pass, setPass] = useState('');
  const handleSubmit = (e) => {
    e.preventDefault();
    if (user === 'admin' && pass === '123') onLogin({ id: "1", name: "Administrador", role: 'admin' });
    else alert("Acesso negado!");
  };
  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2>Gerenciador REP Cloud</h2>
        <form onSubmit={handleSubmit}>
          <input style={styles.input} placeholder="Usuário" value={user} onChange={e => setUser(e.target.value)} />
          <input type="password" style={styles.input} placeholder="Senha" value={pass} onChange={e => setPass(e.target.value)} />
          <button type="submit" style={styles.button}>Entrar</button>
        </form>
      </div>
    </div>
  );
};

// --- COMPONENTE DASHBOARD ---
const Dashboard = ({ user, onLogout }) => {
  const [abaAtiva, setAbaAtiva] = useState('relogios');
  const [novoNS, setNovoNS] = useState('');
  const [statusCmd, setStatusCmd] = useState('Pronto');

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8f9fa' }}>
      <nav style={styles.nav}>
        <div>
          <h3 style={{ margin: 0, color: '#007bff', display: 'inline-block', marginRight: '30px' }}>Henry Cloud</h3>
          <button onClick={() => setAbaAtiva('relogios')} style={{ border: 'none', background: 'none', cursor: 'pointer', fontWeight: abaAtiva === 'relogios' ? 'bold' : 'normal', color: abaAtiva === 'relogios' ? '#007bff' : '#666' }}>Relógios</button>
          {user.role === 'admin' && (
            <button onClick={() => setAbaAtiva('usuarios')} style={{ border: 'none', background: 'none', cursor: 'pointer', marginLeft: '20px', fontWeight: abaAtiva === 'usuarios' ? 'bold' : 'normal', color: abaAtiva === 'usuarios' ? '#007bff' : '#666' }}>👥 Usuários</button>
          )}
        </div>
        <div>
          <span style={{ marginRight: '15px' }}>Olá, <strong>{user.name}</strong></span>
          <button onClick={onLogout} style={{ ...styles.button, width: 'auto', padding: '5px 15px', marginTop: 0, backgroundColor: '#dc3545' }}>Sair</button>
        </div>
      </nav>

      <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '20px' }}>
        {abaAtiva === 'relogios' ? (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div style={{ ...styles.card, maxWidth: 'none', textAlign: 'left' }}>
              <h4>Vincular Equipamento</h4>
              <input style={styles.input} placeholder="Número de Série" value={novoNS} onChange={e => setNovoNS(e.target.value)} />
              <button style={styles.button} onClick={() => setStatusCmd('✅ Vinculado!')}>Vincular</button>
              <p style={{ fontSize: '12px', color: '#888' }}>{statusCmd}</p>
            </div>
            <div style={{ ...styles.card, maxWidth: 'none', textAlign: 'left' }}>
              <h4>Status</h4>
              <p style={{ color: '#999' }}>Nenhum relógio ativo.</p>
            </div>
          </div>
        ) : (
          <GerenciarUsuarios />
        )}
      </div>
    </div>
  );
};

const App = () => {
  const [sessao, setSessao] = useState(null);
  return !sessao ? <Login onLogin={setSessao} /> : <Dashboard user={sessao} onLogout={() => setSessao(null)} />;
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);