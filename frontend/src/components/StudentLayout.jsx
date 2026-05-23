import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const NAV = [
  { to: '/student',                label: 'Dashboard',     icon: '▦', end: true },
  { to: '/student/my-attendance',  label: 'My Attendance', icon: '📅' },
  { to: '/student/my-performance', label: 'My Performance',icon: '📈' },
  { to: '/student/my-surveys',     label: 'My Surveys',    icon: '📋' },
]

export default function StudentLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="w-56 bg-orange-600 text-white flex flex-col flex-shrink-0">
        <div className="px-4 py-5 border-b border-orange-500">
          <p className="text-xs font-semibold uppercase tracking-widest text-orange-200 mb-1">SPTS Student</p>
          <p className="text-sm font-medium truncate">{user?.sub || 'Student'}</p>
          <p className="text-xs text-orange-200">Student Portal</p>
        </div>
        <nav className="flex-1 py-4 overflow-y-auto">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                  isActive
                    ? 'bg-orange-500 text-white font-medium'
                    : 'text-orange-100 hover:bg-orange-500 hover:text-white'
                }`
              }
            >
              <span className="text-base w-5 text-center">{n.icon}</span>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-orange-500">
          <button onClick={handleLogout} className="w-full text-left text-sm text-orange-200 hover:text-white transition-colors py-1">
            Sign out →
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden">
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
