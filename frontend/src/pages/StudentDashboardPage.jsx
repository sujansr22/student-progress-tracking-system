import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { meApi } from '../api/client'

function StatCard({ label, value, icon, color = 'brand' }) {
  const colors = {
    brand: 'bg-brand-50 text-brand-700',
    green: 'bg-green-50 text-green-700',
    orange: 'bg-orange-50 text-orange-700',
    red: 'bg-red-50 text-red-700',
  }
  return (
    <div className="card flex items-center gap-4">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl ${colors[color]}`}>
        {icon}
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value ?? '—'}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </div>
  )
}

const LEVEL_COLORS = {
  THRIVING: 'text-green-600 bg-green-50',
  STABLE: 'text-blue-600 bg-blue-50',
  NEEDS_ATTENTION: 'text-yellow-600 bg-yellow-50',
  CRITICAL: 'text-red-600 bg-red-50',
  INSUFFICIENT_DATA: 'text-gray-500 bg-gray-50',
}

export default function StudentDashboardPage() {
  const now = new Date()
  const [month] = useState(now.getMonth() + 1)
  const [year] = useState(now.getFullYear())

  const { data: profile } = useQuery({
    queryKey: ['me-profile'],
    queryFn: () => meApi.profile().then((r) => r.data),
  })

  const { data: summary } = useQuery({
    queryKey: ['me-attendance-summary'],
    queryFn: () => meApi.attendanceSummary().then((r) => r.data),
    retry: false,
  })

  const { data: performance } = useQuery({
    queryKey: ['me-performance', month, year],
    queryFn: () => meApi.performance(month, year).then((r) => r.data),
    retry: false,
  })

  const { data: pending = [] } = useQuery({
    queryKey: ['me-pending-surveys'],
    queryFn: () => meApi.pendingSurveys().then((r) => r.data),
  })

  const levelCfg = performance ? LEVEL_COLORS[performance.progress_level] || LEVEL_COLORS.INSUFFICIENT_DATA : null

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back{profile ? `, ${profile.first_name}` : ''} 🎓
        </h1>
        {profile && (
          <p className="text-gray-500 text-sm mt-1">
            Student ID: {profile.student_unique_id} · Class ID: {profile.class_id}
          </p>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <StatCard
          label="Attendance"
          value={summary ? `${summary.attendance_percentage.toFixed(1)}%` : '—'}
          icon="✓"
          color={summary?.attendance_percentage >= 75 ? 'green' : 'red'}
        />
        <StatCard
          label={`Performance (${month}/${year})`}
          value={performance?.final_progress_score != null ? `${performance.final_progress_score.toFixed(0)}%` : '—'}
          icon="📈"
          color="brand"
        />
        <StatCard
          label="Pending Surveys"
          value={pending.length}
          icon="📋"
          color={pending.length > 0 ? 'orange' : 'green'}
        />
      </div>

      {/* Progress level card */}
      {performance && (
        <div className={`card mb-6 ${levelCfg}`}>
          <p className="text-sm text-gray-500 mb-1">This month's progress level</p>
          <p className="text-2xl font-bold">
            {performance.progress_level.replace('_', ' ')}
          </p>
          <div className="mt-3 grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Attendance</p>
              <p className="font-semibold">{performance.attendance_percentage.toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-gray-500">Instructor view</p>
              <p className="font-semibold">{performance.instructor_survey_percentage.toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-gray-500">Self score</p>
              <p className="font-semibold">{performance.student_survey_percentage.toFixed(1)}%</p>
            </div>
          </div>
        </div>
      )}

      {/* Pending surveys alert */}
      {pending.length > 0 && (
        <div className="card border-orange-200 bg-orange-50 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-semibold text-orange-800">📋 You have {pending.length} pending survey{pending.length > 1 ? 's' : ''}</p>
              <p className="text-sm text-orange-600 mt-0.5">Your instructor is waiting for your self-assessment</p>
            </div>
            <Link to="/student/my-surveys" className="btn-primary bg-orange-500 hover:bg-orange-600 text-sm">
              Take now →
            </Link>
          </div>
        </div>
      )}

      {/* Quick links */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Link to="/student/my-attendance" className="card hover:border-brand-200 transition-colors text-center">
          <p className="text-3xl mb-2">📅</p>
          <p className="font-semibold text-gray-800">My Attendance</p>
          <p className="text-sm text-gray-500 mt-1">View your attendance history</p>
        </Link>
        <Link to="/student/my-performance" className="card hover:border-brand-200 transition-colors text-center">
          <p className="text-3xl mb-2">📈</p>
          <p className="font-semibold text-gray-800">My Performance</p>
          <p className="text-sm text-gray-500 mt-1">Track your progress score</p>
        </Link>
      </div>
    </div>
  )
}
