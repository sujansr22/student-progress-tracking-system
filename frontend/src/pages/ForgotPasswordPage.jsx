import { useState } from 'react'
import { Link } from 'react-router-dom'
import { authApi } from '../api/client'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    try {
      await authApi.forgotPassword(email)
    } finally {
      setSent(true)
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-50 to-indigo-100 px-4">
      <div className="w-full max-w-sm">
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Reset password</h2>
          {sent ? (
            <div className="mt-4">
              <p className="text-sm text-gray-600 mb-4">
                If that email exists, a reset link has been sent. Check your inbox.
              </p>
              <Link to="/login" className="btn-secondary w-full">Back to sign in</Link>
            </div>
          ) : (
            <>
              <p className="text-sm text-gray-500 mb-6">
                Enter your email and we'll send you a reset link.
              </p>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="label">Email</label>
                  <input
                    type="email"
                    className="input"
                    placeholder="you@school.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
                <button type="submit" disabled={loading} className="btn-primary w-full">
                  {loading ? 'Sending…' : 'Send reset link'}
                </button>
              </form>
              <p className="mt-4 text-center text-sm">
                <Link to="/login" className="text-brand-600 hover:underline">Back to sign in</Link>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
