import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { studentsApi } from '../api/client'
import { useAuth } from '../contexts/AuthContext'

function AddStudentModal({ onClose, onSaved }) {
  const [form, setForm] = useState({
    student_unique_id: '', first_name: '', last_name: '', email: '',
    age: '', gender: 'Male', enrollment_date: new Date().toISOString().slice(0, 10),
    academic_year_id: '', class_id: '', health_notes: '',
  })
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
      await studentsApi.create({
        ...form,
        age: parseInt(form.age),
        academic_year_id: parseInt(form.academic_year_id),
        class_id: parseInt(form.class_id),
      })
      onSaved()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create student')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Add Student</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-200">{error}</div>
        )}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">First name</label>
              <input className="input" value={form.first_name} onChange={(e) => set('first_name', e.target.value)} required />
            </div>
            <div>
              <label className="label">Last name</label>
              <input className="input" value={form.last_name} onChange={(e) => set('last_name', e.target.value)} required />
            </div>
          </div>
          <div>
            <label className="label">Email</label>
            <input type="email" className="input" value={form.email} onChange={(e) => set('email', e.target.value)} required />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Student ID</label>
              <input className="input" value={form.student_unique_id} onChange={(e) => set('student_unique_id', e.target.value)} required />
            </div>
            <div>
              <label className="label">Age</label>
              <input type="number" className="input" min={1} max={100} value={form.age} onChange={(e) => set('age', e.target.value)} required />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Gender</label>
              <select className="input" value={form.gender} onChange={(e) => set('gender', e.target.value)}>
                <option>Male</option>
                <option>Female</option>
                <option>Other</option>
              </select>
            </div>
            <div>
              <label className="label">Enrollment date</label>
              <input type="date" className="input" value={form.enrollment_date} onChange={(e) => set('enrollment_date', e.target.value)} required />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Academic Year ID</label>
              <input type="number" className="input" value={form.academic_year_id} onChange={(e) => set('academic_year_id', e.target.value)} required />
            </div>
            <div>
              <label className="label">Class ID</label>
              <input type="number" className="input" value={form.class_id} onChange={(e) => set('class_id', e.target.value)} required />
            </div>
          </div>
          <div>
            <label className="label">Health notes (optional)</label>
            <textarea className="input" rows={2} value={form.health_notes} onChange={(e) => set('health_notes', e.target.value)} />
          </div>
          <div className="flex gap-3 pt-2">
            <button type="submit" disabled={saving} className="btn-primary flex-1">{saving ? 'Saving…' : 'Add Student'}</button>
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function StudentsPage() {
  const { role } = useAuth()
  const [page, setPage] = useState(0)
  const [search, setSearch] = useState('')
  const [showAdd, setShowAdd] = useState(false)
  const limit = 20

  const { data: students = [], isLoading, refetch } = useQuery({
    queryKey: ['students', page],
    queryFn: () => studentsApi.list({ skip: page * limit, limit }).then((r) => r.data),
  })

  const filtered = students.filter((s) =>
    search === '' ||
    `${s.first_name} ${s.last_name}`.toLowerCase().includes(search.toLowerCase()) ||
    s.email.toLowerCase().includes(search.toLowerCase()) ||
    s.student_unique_id.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Students</h1>
        {role === 'INSTRUCTOR' && (
          <button onClick={() => setShowAdd(true)} className="btn-primary">+ Add Student</button>
        )}
      </div>

      <div className="card">
        <div className="mb-4">
          <input
            className="input max-w-xs"
            placeholder="Search by name, email, or ID…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {isLoading ? (
          <p className="text-gray-400 text-sm py-8 text-center">Loading students…</p>
        ) : filtered.length === 0 ? (
          <p className="text-gray-400 text-sm py-8 text-center">No students found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2 text-gray-500 font-medium">Name</th>
                  <th className="text-left py-2 text-gray-500 font-medium">ID</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Email</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Age</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Gender</th>
                  <th className="text-left py-2 text-gray-500 font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((s) => (
                  <tr key={s.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2.5 font-medium">{s.first_name} {s.last_name}</td>
                    <td className="py-2.5 text-gray-500">{s.student_unique_id}</td>
                    <td className="py-2.5 text-gray-500">{s.email}</td>
                    <td className="py-2.5 text-gray-500">{s.age}</td>
                    <td className="py-2.5 text-gray-500">{s.gender}</td>
                    <td className="py-2.5">
                      <Link to={`/students/${s.id}`} className="text-brand-600 hover:underline text-xs">
                        View →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="btn-secondary text-xs px-3 py-1"
          >
            ← Prev
          </button>
          <span className="text-sm text-gray-500">Page {page + 1}</span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={students.length < limit}
            className="btn-secondary text-xs px-3 py-1"
          >
            Next →
          </button>
        </div>
      </div>

      {showAdd && (
        <AddStudentModal
          onClose={() => setShowAdd(false)}
          onSaved={() => { setShowAdd(false); refetch() }}
        />
      )}
    </div>
  )
}
