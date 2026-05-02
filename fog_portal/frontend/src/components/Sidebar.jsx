import { NavLink, useLocation } from 'react-router-dom';

const navItems = [
  { to: '/',           icon: '🏠', label: 'Home' },
  { to: '/upload',     icon: '⬆', label: 'New Upload' },
  { to: '/subjects',   icon: '👤', label: 'Patients' },
  { to: '/stats',      icon: '📊', label: 'Population Stats' },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <NavLink to="/" className="logo-mark" style={{ textDecoration: 'none' }}>
          <div className="logo-icon">🧠</div>
          <div>
            <div className="logo-text">FOG Portal</div>
            <div className="logo-sub">Gait Analysis</div>
          </div>
        </NavLink>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-label">Navigation</div>
        {navItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        FOG Analysis Portal v1.0<br />
        <span style={{ color: 'var(--accent-light)' }}>●</span> Clinical Research Tool
      </div>
    </aside>
  );
}
