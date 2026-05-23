import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { meApi } from '../api/client'

function fmt(d) {
  return new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function MyAttendancePage() {
  const now = new Date()
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [year, setYear] = useState(now.getFullYear())

  const { data: records = [], isLoading } = useQuery({
    queryKey: ['me-attendance', month, year],
    queryFn: () => meApi.attendance({ limit: 100 }).then((r) => r.data),
  })

  const { data: summary } = useQuery({
    queryKey: ['me-attendance-summary', month, year],
    queryFn: () => meApi.attendanceSummary({ month, year }).then((r) => r.data),
    retry: false,
  })

  const filtered = records.filter((r) => {
    const d = new Date(r.date)
    return d.getMonth() + 1 === month && d.getFullYear() === year
  })

  const present = filtered.filter((r) => r.status === 'PRESENT').length
  const absent  = filtered.filter((r) => r.status === 'ABSENT').length
  const late    = filtered.filter((r) => r.status === 'LATE').length

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">My Attendance</h1>

      {/* Month filter */}
      <div className="card mb-4">
        <div className="flex gap-3 items-end">
          <div>
            <label className="label">Month</label>
            <select className="input" value={month} onChange={(e) => setMonth(Number(e.target.value))}>
              {Array.from({ length: 12 }, (_, i) => (
                <option key={i + 1} value={i + 1}>
                  {new Date(2000, i).toLocaleString('default', { month: 'long' })}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Year</label>
            <input type="number" className="input w-24" min={2020} max={2099} value={year}
              onChange={(e) => setYear(Number(e.target.value))} />
          </div>
        </div>
      </div>

      {/* Summary pills */}
      <div className="grid grid-cols-4 gap-3 mb-4">
        {[
          { label: 'Total', value: filtered.length, cls: 'bg-gray-50 text-gray-700' },
          { label: 'Present', value: present, cls: 'bg-green-50 text-green-700' },
          { label: 'Absent', value: absent, cls: 'bg-red-50 text-red-700' },
          { label: 'Late', value: late, cls: 'bg-yellow-50 text-yellow-700' },
        ].map((s) => (
          <div key={s.label} className={`rounded-xl p-3 text-center ${s.cls}`}>
            <p className="text-xl font-bold">{s.value}</p>
            <p className="text-xs font-medium">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Percentage bar */}
      {summary && (
        <div className="card mb-4">
          <div className="flex justify-between text-sm mb-2">
            <span className="font-medium">Attendance rate</span>
            <span className="font-bold">{summary.attendance_percentage.toFixed(1)}%</span>
          </div>
          <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={`h-3 rounded-full transition-all ${summary.attendance_percentage >= 75 ? 'bg-green-500' : 'bg-red-500'}`}
              style={{ width: `${summary.attendance_percentage}%` }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-1">{summary.present_days} of {summary.total_days} days present</p>
        </div>
      )}

      {/* Records list */}
      <div className="card">
        <h2 className="text-base font-semibold text-gray-800 mb-3">Records</h2>
        {isLoading ? (
          <p className="text-gray-400 text-sm text-center py-8">Loading…</p>
        ) : filtered.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">No records for this month.</p>
        ) : (
          <div className="space-y-1">
            {filtered.map((r) => (
              <div key={r.id} className="flex items-center justify-between py-2 border-b border-gray-50">
                <span className="text-sm text-gray-700">{fmt(r.date)}</span>
                <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${
                  r.status === 'PRESENT' ? 'bg-green-100 text-green-800' :
                  r.status === 'LATE'    ? 'bg-yellow-100 text-yellow-800' :
                                           'bg-red-100 text-red-800'
                }`}>{r.status}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
