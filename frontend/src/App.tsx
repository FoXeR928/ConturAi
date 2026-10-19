import { useState, useEffect } from 'react';
import { Login } from './pages/Login';
import { ChatPage } from './pages/ChatPage';

function App() {
  const [isAuth, setIsAuth] = useState<boolean>(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) setIsAuth(true);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuth(false);
  };

  return isAuth 
    ? <ChatPage onLogout={handleLogout} /> 
    : <Login onLogin={() => setIsAuth(true)} />;
}

export default App;