import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { studentsApi, attendanceApi, subscriptionsApi } from '../api/client'

function StatCard({ label, value, sub, color = 'brand' }) {
  const colors = {
    brand: 'bg-brand-50 text-brand-700',
    green: 'bg-green-50 text-green-700',
    red: 'bg-red-50 text-red-700',
    yellow: 'bg-yellow-50 text-yellow-700',
  }
  return (
    <div className="card flex items-center gap-4">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl ${colors[color]}`}>
        {sub}
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value ?? '—'}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </div>
  )
}

function RiskBadge({ level }) {
  if (level === 'HIGH_RISK') return <span className="badge-risk">High Risk</span>
  if (level === 'MONITOR') return <span className="badge-monitor">Monitor</span>
  return <span className="badge-stable">Stable</span>
}

export default function DashboardPage() {
  const { role } = useAuth()

  const { data: students = [] } = useQuery({
    queryKey: ['students'],
    queryFn: () => studentsApi.list({ limit: 100 }).then((r) => r.data),
  })

  const { data: highRisk = [] } = useQuery({
    queryKey: ['attendance', 'high-risk'],
    queryFn: () => attendanceApi.getHighRisk({ limit: 10 }).then((r) => r.data),
    enabled: role === 'SCHOOL_ADMIN' || role === 'SUPER_ADMIN',
  })

  const { data: subStatus } = useQuery({
    queryKey: ['subscription', 'status'],
    queryFn: () => subscriptionsApi.status().then((r) => r.data),
    enabled: role === 'SCHOOL_ADMIN',
    retry: false,
  })

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {/* Subscription warning banner */}
      {subStatus?.is_in_grace_period && (
        <div className="mb-6 p-4 rounded-xl bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm">
          ⚠ Your subscription expired. You have {7 - Math.abs(subStatus.days_remaining)} grace day(s) left. Contact support to renew.
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Students" value={students.length} sub="👤" color="brand" />
        <StatCard label="High Risk" value={highRisk.length} sub="⚠" color="red" />
        <StatCard
          label="Subscription"
          value={subStatus ? `${subStatus.days_remaining}d left` : '—'}
          sub="📅"
          color={subStatus?.days_remaining < 30 ? 'yellow' : 'green'}
        />
        <StatCard label="Active" value={students.filter((s) => s.is_active).length} sub="✓" color="green" />
      </div>

      {/* High-risk students table */}
      {(role === 'SCHOOL_ADMIN' || role === 'SUPER_ADMIN') && highRisk.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-800">High-Risk Students</h2>
            <Link to="/students" className="text-sm text-brand-600 hover:underline">View all →</Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2 text-gray-500 font-medium">Student</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Attendance %</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Risk</th>
                </tr>
              </thead>
              <tbody>
                {highRisk.map((s) => (
                  <tr key={s.student_id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2.5 font-medium">{s.student_name}</td>
                    <td className="py-2.5 text-gray-600">{s.attendance_percentage.toFixed(1)}%</td>
                    <td className="py-2.5"><RiskBadge level={s.risk_level} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Quick actions for instructors */}
      {role === 'INSTRUCTOR' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Link to="/attendance" className="card hover:border-brand-200 transition-colors text-center">
            <p className="text-3xl mb-2">✓</p>
            <p className="font-semibold text-gray-800">Mark Attendance</p>
            <p className="text-sm text-gray-500 mt-1">Record today's attendance</p>
          </Link>
          <Link to="/survey" className="card hover:border-brand-200 transition-colors text-center">
            <p className="text-3xl mb-2">📋</p>
            <p className="font-semibold text-gray-800">Submit Survey</p>
            <p className="text-sm text-gray-500 mt-1">Monthly wellness survey</p>
          </Link>
        </div>
      )}
    </div>
  )
}
