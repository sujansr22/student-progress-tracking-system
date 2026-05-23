import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const NAV = [
  { to: '/', label: 'Dashboard', icon: '▦', roles: ['SCHOOL_ADMIN', 'INSTRUCTOR', 'SUPER_ADMIN'] },
  { to: '/students', label: 'Students', icon: '👤', roles: ['SCHOOL_ADMIN', 'INSTRUCTOR', 'SUPER_ADMIN'] },
  { to: '/attendance', label: 'Attendance', icon: '✓', roles: ['INSTRUCTOR'] },
  { to: '/survey', label: 'Surveys', icon: '📋', roles: ['INSTRUCTOR'] },
  { to: '/analytics', label: 'Analytics', icon: '📈', roles: ['SCHOOL_ADMIN', 'INSTRUCTOR', 'SUPER_ADMIN'] },
  { to: '/users', label: 'Users', icon: '👥', roles: ['SCHOOL_ADMIN', 'SUPER_ADMIN'] },
  { to: '/admin', label: 'Super Admin', icon: '⚙', roles: ['SUPER_ADMIN'] },
]

export default function Layout() {
  const { user, role, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  const links = NAV.filter((n) => n.roles.includes(role))

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 bg-brand-700 text-white flex flex-col flex-shrink-0">
        <div className="px-4 py-5 border-b border-brand-600">
          <p className="text-xs font-semibold uppercase tracking-widest text-brand-100 mb-1">SPTS</p>
          <p className="text-sm font-medium truncate">{user?.sub || 'User'}</p>
          <p className="text-xs text-brand-200">{role}</p>
        </div>
        <nav className="flex-1 py-4 overflow-y-auto">
          {links.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                  isActive
                    ? 'bg-brand-600 text-white font-medium'
                    : 'text-brand-100 hover:bg-brand-600 hover:text-white'
                }`
              }
            >
              <span className="text-base w-5 text-center">{n.icon}</span>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-brand-600">
          <button
            onClick={handleLogout}
            className="w-full text-left text-sm text-brand-200 hover:text-white transition-colors py-1"
          >
            Sign out →
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
