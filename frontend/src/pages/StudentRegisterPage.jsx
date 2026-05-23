import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authApi } from '../api/client'

export default function StudentRegisterPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    if (password !== confirm) { setError('Passwords do not match'); return }
    setError('')
    setLoading(true)
    try {
      await authApi.studentRegister(email, password)
      navigate('/login', { state: { message: 'Account created! Sign in to continue.' } })
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orange-50 to-amber-100 px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <p className="text-4xl mb-2">🎓</p>
          <h1 className="text-2xl font-bold text-gray-900">Student Registration</h1>
          <p className="text-gray-500 text-sm mt-1">Use the email your school has on record</p>
        </div>

        <div className="card">
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">{error}</div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">School email</label>
              <input
                type="email" className="input" placeholder="your.name@school.com"
                value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus
              />
              <p className="text-xs text-gray-400 mt-1">Must match the email your school registered you with</p>
            </div>
            <div>
              <label className="label">Password</label>
              <input
                type="password" className="input" placeholder="Min. 8 characters"
                value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} required
              />
            </div>
            <div>
              <label className="label">Confirm password</label>
              <input
                type="password" className="input" placeholder="Re-enter password"
                value={confirm} onChange={(e) => setConfirm(e.target.value)} required
              />
            </div>
            <button type="submit" disabled={loading} className="w-full py-2 px-4 bg-orange-500 text-white text-sm font-medium rounded-lg hover:bg-orange-600 transition-colors disabled:opacity-50">
              {loading ? 'Creating account…' : 'Create account'}
            </button>
          </form>
          <p className="mt-4 text-center text-sm text-gray-500">
            Already have an account?{' '}
            <Link to="/login" className="text-orange-600 hover:underline">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
