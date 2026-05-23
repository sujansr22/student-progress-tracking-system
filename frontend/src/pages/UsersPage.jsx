import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { usersApi } from '../api/client'
import { useAuth } from '../contexts/AuthContext'

function AddUserModal({ institutionId, onClose, onSaved }) {
  const [form, setForm] = useState({ email: '', full_name: '', password: '', role: 'INSTRUCTOR', institution_id: institutionId })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      await usersApi.create(form)
      onSaved()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create user')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Add Instructor</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
        </div>
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-200">{error}</div>
        )}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="label">Full name</label>
            <input className="input" value={form.full_name} onChange={(e) => set('full_name', e.target.value)} />
          </div>
          <div>
            <label className="label">Email</label>
            <input type="email" className="input" value={form.email} onChange={(e) => set('email', e.target.value)} required />
          </div>
          <div>
            <label className="label">Password</label>
            <input type="password" className="input" placeholder="Min. 8 chars" minLength={8} value={form.password} onChange={(e) => set('password', e.target.value)} required />
          </div>
          <div className="flex gap-3 pt-2">
            <button type="submit" disabled={saving} className="btn-primary flex-1">{saving ? 'Adding…' : 'Add Instructor'}</button>
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function UsersPage() {
  const { role, user } = useAuth()
  const qc = useQueryClient()
  const [showAdd, setShowAdd] = useState(false)

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => usersApi.list({ limit: 100 }).then((r) => r.data),
  })

  const ROLE_LABEL = { SUPER_ADMIN: 'Super Admin', SCHOOL_ADMIN: 'Admin', INSTRUCTOR: 'Instructor' }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Users</h1>
        {(role === 'SCHOOL_ADMIN' || role === 'SUPER_ADMIN') && (
          <button onClick={() => setShowAdd(true)} className="btn-primary">+ Add Instructor</button>
        )}
      </div>

      <div className="card">
        {isLoading ? (
          <p className="text-gray-400 text-sm py-8 text-center">Loading users…</p>
        ) : users.length === 0 ? (
          <p className="text-gray-400 text-sm py-8 text-center">No users found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2 text-gray-500 font-medium">Name</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Email</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Role</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Institution</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2.5 font-medium">{u.full_name || '—'}</td>
                    <td className="py-2.5 text-gray-600">{u.email}</td>
                    <td className="py-2.5">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        u.role === 'SUPER_ADMIN' ? 'bg-purple-100 text-purple-800'
                        : u.role === 'SCHOOL_ADMIN' ? 'bg-brand-100 text-brand-800'
                        : 'bg-gray-100 text-gray-700'
                      }`}>
                        {ROLE_LABEL[u.role] || u.role}
                      </span>
                    </td>
                    <td className="py-2.5 text-gray-500">{u.institution_id ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showAdd && (
        <AddUserModal
          institutionId={user?.institution_id}
          onClose={() => setShowAdd(false)}
          onSaved={() => { setShowAdd(false); qc.invalidateQueries({ queryKey: ['users'] }) }}
        />
      )}
    </div>
  )
}
