import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const DEMO_ROLES = [
  {
    label: 'Super Admin',
    icon: '⚙',
    email: 'owner@spts.com',
    password: 'Owner123!',
    color: 'bg-purple-50 border-purple-200 text-purple-700 hover:bg-purple-100',
    active: 'bg-purple-600 border-purple-600 text-white',
  },
  {
    label: 'School Admin',
    icon: '🏫',
    email: 'admin@greenwood.com',
    password: 'Admin123!',
    color: 'bg-brand-50 border-brand-200 text-brand-700 hover:bg-brand-100',
    active: 'bg-brand-600 border-brand-600 text-white',
  },
  {
    label: 'Instructor',
    icon: '👩‍🏫',
    email: 'teacher1@greenwood.com',
    password: 'Teacher123!',
    color: 'bg-green-50 border-green-200 text-green-700 hover:bg-green-100',
    active: 'bg-green-600 border-green-600 text-white',
  },
  {
    label: 'Student',
    icon: '🎓',
    email: '',
    password: '',
    color: 'bg-orange-50 border-orange-200 text-orange-700 hover:bg-orange-100',
    active: 'bg-orange-500 border-orange-500 text-white',
  },
]

export default function LoginPage() {
  const { login, loading } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [activeRole, setActiveRole] = useState(null)

  function selectRole(role) {
    setActiveRole(role.label)
    setEmail(role.email)
    setPassword(role.password)
    setError('')
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    const result = await login(email, password)
    if (result.ok) {
      navigate('/')
    } else {
      setError(result.message)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-50 to-indigo-100 px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-brand-700">SPTS</h1>
          <p className="text-gray-500 text-sm mt-1">Student Progress Tracking System</p>
        </div>

        {/* Role quick-select */}
        <div className="mb-4">
          <p className="text-xs text-center text-gray-400 mb-2 uppercase tracking-wide">Sign in as</p>
          <div className="grid grid-cols-3 gap-2">
            {DEMO_ROLES.map((role) => (
              <button
                key={role.label}
                type="button"
                onClick={() => selectRole(role)}
                className={`flex flex-col items-center gap-1 py-3 px-2 rounded-xl border text-xs font-medium transition-colors ${
                  activeRole === role.label ? role.active : role.color
                }`}
              >
                <span className="text-xl">{role.icon}</span>
                {role.label}
              </button>
            ))}
          </div>
        </div>

        <div className="card">
          <h2 className="text-xl font-semibold text-gray-800 mb-6">Sign in</h2>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Email</label>
              <input
                type="email"
                className="input"
                placeholder="you@school.com"
                value={email}
                onChange={(e) => { setEmail(e.target.value); setActiveRole(null) }}
                required
                autoFocus
              />
            </div>
            <div>
              <label className="label">Password</label>
              <input
                type="password"
                className="input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => { setPassword(e.target.value); setActiveRole(null) }}
                required
              />
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full mt-2">
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-gray-500">
            <Link to="/forgot-password" className="text-brand-600 hover:underline">
              Forgot password?
            </Link>
          </p>
        </div>

        {activeRole === 'Student' && (
          <p className="mt-3 text-center text-sm text-gray-500">
            First time?{' '}
            <Link to="/student-register" className="text-orange-600 font-medium hover:underline">
              Register as Student →
            </Link>
          </p>
        )}
      </div>
    </div>
  )
}
