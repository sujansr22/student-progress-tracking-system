import { useState } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { authApi } from '../api/client'

export default function ResetPasswordPage() {
  const [params] = useSearchParams()
  const token = params.get('token') || ''
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await authApi.resetPassword(token, password)
      navigate('/login', { state: { message: 'Password updated. Sign in with your new password.' } })
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid or expired token.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-50 to-indigo-100 px-4">
      <div className="w-full max-w-sm card">
        <h2 className="text-xl font-semibold text-gray-800 mb-6">Set new password</h2>
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">{error}</div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">New password</label>
            <input
              type="password"
              className="input"
              placeholder="Min. 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={8}
              required
            />
          </div>
          <button type="submit" disabled={loading || !token} className="btn-primary w-full">
            {loading ? 'Updating…' : 'Update password'}
          </button>
        </form>
        <p className="mt-4 text-center text-sm">
          <Link to="/login" className="text-brand-600 hover:underline">Back to sign in</Link>
        </p>
      </div>
    </div>
  )
}
