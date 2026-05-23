import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { studentsApi, attendanceApi } from '../api/client'

const STATUSES = ['PRESENT', 'ABSENT', 'LATE']

export default function AttendancePage() {
  const qc = useQueryClient()
  const today = new Date().toISOString().slice(0, 10)
  const [date, setDate] = useState(today)
  const [marks, setMarks] = useState({})   // { studentId: status }
  const [saving, setSaving] = useState(false)
  const [results, setResults] = useState([])

  const { data: students = [], isLoading } = useQuery({
    queryKey: ['students'],
    queryFn: () => studentsApi.list({ limit: 100 }).then((r) => r.data),
  })

  function setMark(id, status) {
    setMarks((m) => ({ ...m, [id]: status }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setResults([])
    const entries = Object.entries(marks)
    if (entries.length === 0) {
      setSaving(false)
      return
    }
    const res = await Promise.allSettled(
      entries.map(([studentId, status]) =>
        attendanceApi.mark({ student_id: studentId, date, status })
      )
    )
    const errors = res
      .map((r, i) => r.status === 'rejected' ? `${students.find((s) => s.id === entries[i][0])?.first_name}: ${r.reason?.response?.data?.detail || 'Error'}` : null)
      .filter(Boolean)
    setResults(errors)
    setSaving(false)
    if (errors.length === 0) {
      setMarks({})
      qc.invalidateQueries({ queryKey: ['attendance'] })
    }
  }

  const marked = Object.keys(marks).length

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Mark Attendance</h1>

      <div className="card">
        <div className="flex items-center gap-4 mb-6">
          <div>
            <label className="label">Date</label>
            <input
              type="date"
              className="input"
              value={date}
              max={today}
              onChange={(e) => setDate(e.target.value)}
            />
          </div>
          <div className="flex-1" />
          <div className="text-sm text-gray-500">
            {marked} of {students.length} marked
          </div>
        </div>

        {results.length > 0 && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm space-y-1">
            {results.map((r, i) => <p key={i}>{r}</p>)}
          </div>
        )}

        {isLoading ? (
          <p className="text-gray-400 text-sm text-center py-8">Loading students…</p>
        ) : students.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">No students found.</p>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="space-y-2 mb-6">
              {students.map((s) => (
                <div key={s.id} className="flex items-center justify-between py-2.5 border-b border-gray-50">
                  <div>
                    <p className="text-sm font-medium">{s.first_name} {s.last_name}</p>
                    <p className="text-xs text-gray-400">{s.student_unique_id}</p>
                  </div>
                  <div className="flex gap-1">
                    {STATUSES.map((st) => (
                      <button
                        key={st}
                        type="button"
                        onClick={() => setMark(s.id, st)}
                        className={`px-2.5 py-1 text-xs rounded-lg border font-medium transition-colors ${
                          marks[s.id] === st
                            ? st === 'PRESENT' ? 'bg-green-500 text-white border-green-500'
                            : st === 'ABSENT' ? 'bg-red-500 text-white border-red-500'
                            : 'bg-yellow-500 text-white border-yellow-500'
                            : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                        }`}
                      >
                        {st}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <button type="submit" disabled={saving || marked === 0} className="btn-primary w-full">
              {saving ? 'Saving…' : `Save ${marked} Record${marked !== 1 ? 's' : ''}`}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
