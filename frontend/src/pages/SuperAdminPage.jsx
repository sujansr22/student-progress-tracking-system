import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { institutionsApi, subscriptionsApi } from '../api/client'

function CreateInstitutionModal({ onClose, onSaved }) {
  const [name, setName] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await institutionsApi.create({ name })
      onSaved()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">New Institution</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
        </div>
        {error && <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-200">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="label">Institution name</label>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary flex-1">{saving ? 'Creating…' : 'Create'}</button>
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}

function CreateSubscriptionModal({ institutionId, onClose, onSaved }) {
  const [endDate, setEndDate] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await subscriptionsApi.create({ institution_id: institutionId, end_date: endDate, is_active: true })
      onSaved()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Create Subscription</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
        </div>
        {error && <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-200">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="label">End date</label>
            <input type="date" className="input" value={endDate} onChange={(e) => setEndDate(e.target.value)} required />
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary flex-1">{saving ? 'Creating…' : 'Create'}</button>
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function SuperAdminPage() {
  const qc = useQueryClient()
  const [showCreateInst, setShowCreateInst] = useState(false)
  const [renewId, setRenewId] = useState(null)
  const [createSubId, setCreateSubId] = useState(null)
  const [renewDays, setRenewDays] = useState(365)
  const [renewing, setRenewing] = useState(false)

  const { data: institutions = [], isLoading } = useQuery({
    queryKey: ['institutions'],
    queryFn: () => institutionsApi.list({ limit: 100 }).then((r) => r.data),
  })

  const { data: subscriptions = [] } = useQuery({
    queryKey: ['subscriptions'],
    queryFn: () => subscriptionsApi.list({ limit: 100 }).then((r) => r.data),
  })

  function subFor(instId) {
    return subscriptions.find((s) => s.institution_id === instId)
  }

  async function handleRenew(e) {
    e.preventDefault()
    setRenewing(true)
    try {
      await subscriptionsApi.renew(renewId, renewDays)
      qc.invalidateQueries({ queryKey: ['subscriptions'] })
      setRenewId(null)
    } finally {
      setRenewing(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Super Admin Panel</h1>
        <button onClick={() => setShowCreateInst(true)} className="btn-primary">+ New Institution</button>
      </div>

      <div className="card">
        <h2 className="text-base font-semibold text-gray-800 mb-4">All Institutions</h2>
        {isLoading ? (
          <p className="text-gray-400 text-sm py-8 text-center">Loading…</p>
        ) : institutions.length === 0 ? (
          <p className="text-gray-400 text-sm py-8 text-center">No institutions yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2 text-gray-500 font-medium">ID</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Name</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Subscription</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Expires</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {institutions.map((inst) => {
                  const sub = subFor(inst.id)
                  const expired = sub && new Date(sub.end_date) < new Date()
                  return (
                    <tr key={inst.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-2.5 text-gray-400">{inst.id}</td>
                      <td className="py-2.5 font-medium">{inst.name}</td>
                      <td className="py-2.5">
                        {sub ? (
                          <span className={expired ? 'badge-risk' : 'badge-stable'}>
                            {expired ? 'Expired' : 'Active'}
                          </span>
                        ) : (
                          <span className="badge-risk">No subscription</span>
                        )}
                      </td>
                      <td className="py-2.5 text-gray-500">
                        {sub ? new Date(sub.end_date).toLocaleDateString('en-IN') : '—'}
                      </td>
                      <td className="py-2.5">
                        <div className="flex gap-2">
                          {sub ? (
                            <button
                              onClick={() => setRenewId(inst.id)}
                              className="text-xs text-brand-600 hover:underline"
                            >
                              Renew
                            </button>
                          ) : (
                            <button
                              onClick={() => setCreateSubId(inst.id)}
                              className="text-xs text-brand-600 hover:underline"
                            >
                              Add sub
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Renew modal */}
      {renewId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
            <h2 className="text-lg font-semibold mb-4">Renew Subscription</h2>
            <p className="text-sm text-gray-500 mb-4">
              Institution #{renewId} — extending from current end date (or today if expired).
            </p>
            <form onSubmit={handleRenew} className="space-y-3">
              <div>
                <label className="label">Extend by (days)</label>
                <input
                  type="number" className="input" min={1} max={1095}
                  value={renewDays} onChange={(e) => setRenewDays(Number(e.target.value))}
                />
              </div>
              <div className="flex gap-3">
                <button type="submit" disabled={renewing} className="btn-primary flex-1">
                  {renewing ? 'Renewing…' : 'Renew'}
                </button>
                <button type="button" onClick={() => setRenewId(null)} className="btn-secondary flex-1">Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showCreateInst && (
        <CreateInstitutionModal
          onClose={() => setShowCreateInst(false)}
          onSaved={() => { setShowCreateInst(false); qc.invalidateQueries({ queryKey: ['institutions'] }) }}
        />
      )}

      {createSubId && (
        <CreateSubscriptionModal
          institutionId={createSubId}
          onClose={() => setCreateSubId(null)}
          onSaved={() => { setCreateSubId(null); qc.invalidateQueries({ queryKey: ['subscriptions'] }) }}
        />
      )}
    </div>
  )
}
