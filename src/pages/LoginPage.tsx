import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import './LoginPage.css';

export default function LoginPage() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname ?? '/dashboard';

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const err = await signIn(username, password);
    setLoading(false);
    if (err) {
      setError(err);
    } else {
      navigate(from, { replace: true });
    }
  }

  const DEMO_USERS = [
    { username: 'warehouse.manager', role: 'Warehouse Manager' },
    { username: 'planner', role: 'Planner' },
    { username: 'warehouse.staff', role: 'Warehouse Staff' },
    { username: 'quality.manager', role: 'Quality Manager' },
    { username: 'branch.manager', role: 'Branch Manager' },
  ];

  return (
    <div className="login-root">
      <div className="login-card">
        {/* Logo */}
        <div className="login-logo">
          <span className="login-logo-icon">⬡</span>
          <span className="login-logo-text">V-IMS AI</span>
        </div>
        <p className="login-tagline">Inventory Management System</p>

        {/* Form */}
        <form className="login-form" onSubmit={handleSubmit} noValidate>
          <div className="login-field">
            <label htmlFor="login-username">Username</label>
            <input
              id="login-username"
              type="text"
              autoComplete="username"
              placeholder="e.g. warehouse.manager"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          <div className="login-field">
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              autoComplete="current-password"
              placeholder="Demo@123"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          {error && <p className="login-error" role="alert">{error}</p>}

          <button
            id="login-submit"
            type="submit"
            className="login-btn"
            disabled={loading || !username || !password}
          >
            {loading ? <span className="login-spinner" /> : 'Sign In'}
          </button>
        </form>

        {/* Demo credentials reference */}
        <div className="login-demo-panel">
          <p className="login-demo-title">Demo accounts — all use <code>Demo@123</code></p>
          <div className="login-demo-grid">
            {DEMO_USERS.map((u) => (
              <button
                key={u.username}
                type="button"
                className="login-demo-chip"
                onClick={() => setUsername(u.username)}
                title={u.role}
              >
                {u.username}
              </button>
            ))}
          </div>
        </div>

        {/* Disclaimer */}
        <p className="login-disclaimer">
          Demonstration using public product master references and synthetic
          operational data — not actual Vinamilk operational data.
        </p>
      </div>
    </div>
  );
}
