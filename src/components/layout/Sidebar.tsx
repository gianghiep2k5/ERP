import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';
import './Sidebar.css';

interface NavItem {
  to: string;
  label: string;
  icon: string;
}

const NAV_ITEMS: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard', icon: '▦' },
  { to: '/inventory', label: 'Inventory', icon: '⊟' },
  { to: '/expiry-risk', label: 'Expiry Risk', icon: '⚠' },
  { to: '/forecast', label: 'Forecast', icon: '↗' },
  { to: '/recommendations', label: 'Recommendations', icon: '✓' },
  { to: '/audit', label: 'Audit Log', icon: '≡' },
];

export default function Sidebar() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  function handleSignOut() {
    signOut();
    navigate('/login', { replace: true });
  }

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <span className="sidebar-logo-icon">⬡</span>
        <span className="sidebar-logo-text">V-IMS AI</span>
      </div>

      {/* Nav */}
      <nav className="sidebar-nav" aria-label="Main navigation">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `sidebar-link${isActive ? ' sidebar-link--active' : ''}`
            }
          >
            <span className="sidebar-icon" aria-hidden="true">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* User footer */}
      <div className="sidebar-footer">
        <div className="sidebar-user">
          <span className="sidebar-username">{user?.username}</span>
          <span className="sidebar-role">{user?.role}</span>
        </div>
        <button
          id="sidebar-signout"
          type="button"
          className="sidebar-signout"
          onClick={handleSignOut}
          title="Sign out"
        >
          ⏻
        </button>
      </div>
    </aside>
  );
}
