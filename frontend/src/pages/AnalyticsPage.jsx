import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { studentsApi, analyticsApi } from '../api/client'

const LEVEL_CONFIG = {
  EXCELLENT:   { label: 'Excellent',    color: 'text-green-600',  bar: 'bg-green-500',  bg: 'bg-green-50'  },
  GOOD:        { label: 'Good',         color: 'text-blue-600',   bar: 'bg-blue-500',   bg: 'bg-blue-50'   },
  AVERAGE:     { label: 'Average',      color: 'text-yellow-600', bar: 'bg-yellow-500', bg: 'bg-yellow-50' },
  NEEDS_IMPROVEMENT: { label: 'Needs Improvement', color: 'text-orange-600', bar: 'bg-orange-500', bg: 'bg-orange-50' },
  HIGH_RISK:   { label: 'High Risk',    color: 'text-red-600',    bar: 'bg-red-500',    bg: 'bg-red-50'    },
  INSUFFICIENT_DATA: { label: 'Insufficient Data', color: 'text-gray-500', bar: 'bg-gray-300', bg: 'bg-gray-50' },
}

function ScoreBar({ label, value }) {
  const pct = Math.min(100, Math.max(0, value ?? 0))
  return (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600">{label}</span>
        <span className="font-medium">{value != null ? `${pct.toFixed(1)}%` : '—'}</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className="h-2 bg-brand-500 rounded-full transition-all" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function AnalyticsPage() {
  const now = new Date()
  const [studentId, setStudentId] = useState('')
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [year, setYear] = useState(now.getFullYear())

  const { data: students = [] } = useQuery({
    queryKey: ['students'],
    queryFn: () => studentsApi.list({ limit: 100 }).then((r) => r.data),
  })

  const { data: progress, isLoading, error } = useQuery({
    queryKey: ['analytics', studentId, month, year],
    queryFn: () => analyticsApi.getStudentProgress(studentId, month, year).then((r) => r.data),
    enabled: !!studentId,
    retry: false,
  })

  const cfg = progress ? (LEVEL_CONFIG[progress.progress_level] || LEVEL_CONFIG.INSUFFICIENT_DATA) : null

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Analytics</h1>

      <div className="card mb-6">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="col-span-2">
            <label className="label">Student</label>
            <select className="input" value={studentId} onChange={(e) => setStudentId(e.target.value)}>
              <option value="">Select student…</option>
              {students.map((s) => (
                <option key={s.id} value={s.id}>{s.first_name} {s.last_name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Month</label>
            <select className="input" value={month} onChange={(e) => setMonth(Number(e.target.value))}>
              {Array.from({ length: 12 }, (_, i) => (
                <option key={i + 1} value={i + 1}>
                  {new Date(2000, i).toLocaleString('default', { month: 'short' })}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Year</label>
            <input type="number" className="input" min={2020} max={2099} value={year} onChange={(e) => setYear(Number(e.target.value))} />
          </div>
        </div>
      </div>

      {!studentId && (
        <p className="text-gray-400 text-sm text-center py-12">Select a student to view analytics.</p>
      )}

      {isLoading && <p className="text-gray-400 text-sm text-center py-8">Loading…</p>}

      {error && (
        <div className="card text-center">
          <p className="text-gray-500 text-sm">
            {error.response?.data?.detail || 'No analytics data available for this period.'}
          </p>
        </div>
      )}

      {progress && cfg && (
        <div className="space-y-4">
          {/* Level indicator */}
          <div className={`card ${cfg.bg}`}>
            <div className="flex items-center justify-between mb-2">
              <div>
                <p className="text-sm text-gray-500">{progress.student_name} · {progress.month}/{progress.year}</p>
                <p className={`text-3xl font-bold mt-1 ${cfg.color}`}>{cfg.label}</p>
              </div>
              <div className="text-right">
                <p className="text-4xl font-bold text-gray-800">
                  {progress.final_progress_score != null ? `${progress.final_progress_score.toFixed(0)}%` : '—'}
                </p>
                <p className="text-xs text-gray-500">Overall score</p>
              </div>
            </div>
          </div>

          {/* Component breakdown */}
          <div className="card">
            <h2 className="text-base font-semibold text-gray-800 mb-4">Score Breakdown</h2>
            <ScoreBar label="Attendance" value={progress.attendance_percentage} />
            <ScoreBar label="Instructor Survey" value={progress.instructor_survey_percentage} />
            <ScoreBar label="Student Survey" value={progress.student_survey_percentage} />
          </div>

          {/* Level guide */}
          <div className="card">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">Progress Levels</h2>
            <div className="space-y-1.5">
              {Object.entries(LEVEL_CONFIG).filter(([k]) => k !== 'INSUFFICIENT_DATA').map(([key, c]) => (
                <div key={key} className={`flex items-center gap-2 text-xs rounded-lg px-3 py-2 ${progress.progress_level === key ? c.bg : ''}`}>
                  <span className={`w-2 h-2 rounded-full ${c.bar}`} />
                  <span className={progress.progress_level === key ? `font-semibold ${c.color}` : 'text-gray-500'}>
                    {c.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
