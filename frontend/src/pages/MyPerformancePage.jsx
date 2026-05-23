import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { meApi } from '../api/client'

const LEVEL_CONFIG = {
  THRIVING:          { label: 'Thriving',          color: 'text-green-600',  bar: 'bg-green-500',  bg: 'bg-green-50'  },
  STABLE:            { label: 'Stable',             color: 'text-blue-600',   bar: 'bg-blue-500',   bg: 'bg-blue-50'   },
  NEEDS_ATTENTION:   { label: 'Needs Attention',    color: 'text-yellow-600', bar: 'bg-yellow-500', bg: 'bg-yellow-50' },
  CRITICAL:          { label: 'Critical',           color: 'text-red-600',    bar: 'bg-red-500',    bg: 'bg-red-50'    },
  INSUFFICIENT_DATA: { label: 'Insufficient Data',  color: 'text-gray-500',   bar: 'bg-gray-300',   bg: 'bg-gray-50'   },
}

function ScoreBar({ label, value, barColor }) {
  const pct = Math.min(100, Math.max(0, value ?? 0))
  return (
    <div className="mb-4">
      <div className="flex justify-between text-sm mb-1.5">
        <span className="text-gray-600">{label}</span>
        <span className="font-semibold">{value != null ? `${pct.toFixed(1)}%` : '—'}</span>
      </div>
      <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-2.5 rounded-full transition-all ${barColor || 'bg-brand-500'}`}
          style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function MyPerformancePage() {
  const now = new Date()
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [year, setYear]   = useState(now.getFullYear())

  const { data: performance, isLoading, error } = useQuery({
    queryKey: ['me-performance', month, year],
    queryFn: () => meApi.performance(month, year).then((r) => r.data),
    retry: false,
  })

  const cfg = performance
    ? (LEVEL_CONFIG[performance.progress_level] || LEVEL_CONFIG.INSUFFICIENT_DATA)
    : null

  return (
    <div className="max-w-xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">My Performance</h1>

      {/* Period selector */}
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
            <input type="number" className="input w-24" min={2020} max={2099}
              value={year} onChange={(e) => setYear(Number(e.target.value))} />
          </div>
        </div>
      </div>

      {isLoading && <p className="text-gray-400 text-sm text-center py-8">Loading…</p>}

      {error && (
        <div className="card text-center py-8">
          <p className="text-gray-500 text-sm">No performance data for {month}/{year} yet.</p>
          <p className="text-gray-400 text-xs mt-1">Data appears once attendance and surveys are recorded.</p>
        </div>
      )}

      {performance && cfg && (
        <div className="space-y-4">
          {/* Overall score */}
          <div className={`card ${cfg.bg}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Progress level</p>
                <p className={`text-3xl font-bold mt-1 ${cfg.color}`}>{cfg.label}</p>
              </div>
              <div className="text-right">
                <p className="text-5xl font-bold text-gray-800">
                  {performance.final_progress_score != null
                    ? `${performance.final_progress_score.toFixed(0)}%`
                    : '—'}
                </p>
                <p className="text-xs text-gray-500">Overall score</p>
              </div>
            </div>
          </div>

          {/* Score breakdown */}
          <div className="card">
            <h2 className="text-base font-semibold text-gray-800 mb-4">Score Breakdown</h2>
            <ScoreBar label="Attendance" value={performance.attendance_percentage} barColor="bg-blue-500" />
            <ScoreBar label="Instructor Assessment" value={performance.instructor_survey_percentage} barColor="bg-indigo-500" />
            <ScoreBar label="My Self-Assessment" value={performance.student_survey_percentage} barColor="bg-orange-500" />
          </div>

          {/* What each means */}
          <div className="card">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">What the levels mean</h2>
            <div className="space-y-2">
              {Object.entries(LEVEL_CONFIG).filter(([k]) => k !== 'INSUFFICIENT_DATA').map(([key, c]) => (
                <div key={key} className={`flex items-center gap-2 text-xs rounded-lg px-3 py-2 ${performance.progress_level === key ? c.bg : ''}`}>
                  <span className={`w-2 h-2 rounded-full ${c.bar}`} />
                  <span className={performance.progress_level === key ? `font-semibold ${c.color}` : 'text-gray-500'}>
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
