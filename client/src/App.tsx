import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Switch, Redirect, useHistory } from 'react-router-dom';
import Login from './components/Login';
import Signup from './components/Signup';
import AdminDashboard from './components/AdminDashboard';
import UserDashboard from './components/UserDashboard';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');
    
    if (token && userStr) {
      setIsAuthenticated(true);
      setUser(JSON.parse(userStr));
    }
    setLoading(false);
  }, []);

  const handleLogin = (token: string, userData: any) => {
    setIsAuthenticated(true);
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setIsAuthenticated(false);
    setUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <Router>
      <Switch>
        <Route exact path="/login">
          {isAuthenticated ? (
            <Redirect to={user?.role === 'admin' ? '/admin' : '/user'} />
          ) : (
            <Login onLogin={handleLogin} />
          )}
        </Route>
        
        <Route exact path="/signup">
          {isAuthenticated ? (
            <Redirect to={user?.role === 'admin' ? '/admin' : '/user'} />
          ) : (
            <Signup onLogin={handleLogin} />
          )}
        </Route>

        <Route exact path="/admin">
          {isAuthenticated && user?.role === 'admin' ? (
            <AdminDashboard />
          ) : (
            <Redirect to="/login" />
          )}
        </Route>

        <Route exact path="/user">
          {isAuthenticated ? (
            <UserDashboard />
          ) : (
            <Redirect to="/login" />
          )}
        </Route>

        <Route exact path="/">
          <Redirect to={isAuthenticated ? (user?.role === 'admin' ? '/admin' : '/user') : '/login'} />
        </Route>

        <Route>
          <Redirect to="/" />
        </Route>
      </Switch>
    </Router>
  );
}

export default App;
