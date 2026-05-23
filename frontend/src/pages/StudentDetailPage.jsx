import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { studentsApi, attendanceApi, surveysApi } from '../api/client'
import { useAuth } from '../contexts/AuthContext'

function RiskBadge({ level }) {
  if (level === 'HIGH_RISK') return <span className="badge-risk">High Risk</span>
  if (level === 'MONITOR') return <span className="badge-monitor">Monitor</span>
  return <span className="badge-stable">Stable</span>
}

function fmt(dateStr) {
  return new Date(dateStr).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function StudentDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { role } = useAuth()
  const qc = useQueryClient()
  const [deleteConfirm, setDeleteConfirm] = useState(false)
  const [purgeConfirm, setPurgeConfirm] = useState(false)

  const { data: student, isLoading: loadingStudent } = useQuery({
    queryKey: ['student', id],
    queryFn: () => studentsApi.get(id).then((r) => r.data),
  })

  const { data: attendance = [] } = useQuery({
    queryKey: ['attendance', id],
    queryFn: () => attendanceApi.getStudentAttendance(id, { limit: 30 }).then((r) => r.data),
    enabled: !!id,
  })

  const { data: pct } = useQuery({
    queryKey: ['attendance-pct', id],
    queryFn: () => attendanceApi.getStudentPercentage(id).then((r) => r.data),
    enabled: !!id,
    retry: false,
  })

  const { data: surveys = [] } = useQuery({
    queryKey: ['surveys', id],
    queryFn: () => surveysApi.getStudentSurveys(id, { limit: 10 }).then((r) => r.data),
    enabled: !!id,
  })

  async function handleDelete() {
    await studentsApi.delete(id)
    qc.invalidateQueries({ queryKey: ['students'] })
    navigate('/students')
  }

  async function handlePurge() {
    await studentsApi.purge(id)
    qc.invalidateQueries({ queryKey: ['students'] })
    navigate('/students')
  }

  if (loadingStudent) return <p className="text-gray-400 text-sm p-8">Loading…</p>
  if (!student) return <p className="text-red-500 p-8">Student not found.</p>

  return (
    <div className="max-w-4xl">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-2">← Back</button>
          <h1 className="text-2xl font-bold text-gray-900">{student.first_name} {student.last_name}</h1>
          <p className="text-gray-500 text-sm">{student.email} · ID: {student.student_unique_id}</p>
        </div>
        {(role === 'SCHOOL_ADMIN' || role === 'SUPER_ADMIN') && (
          <div className="flex gap-2">
            <button onClick={() => setDeleteConfirm(true)} className="btn-secondary text-sm">Soft Delete</button>
            <button onClick={() => setPurgeConfirm(true)} className="btn-danger text-sm">Purge</button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        {/* Profile card */}
        <div className="card col-span-2">
          <h2 className="text-base font-semibold text-gray-800 mb-3">Profile</h2>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <div><dt className="text-gray-500">Age</dt><dd className="font-medium">{student.age}</dd></div>
            <div><dt className="text-gray-500">Gender</dt><dd className="font-medium">{student.gender}</dd></div>
            <div><dt className="text-gray-500">Enrolled</dt><dd className="font-medium">{fmt(student.enrollment_date)}</dd></div>
            <div><dt className="text-gray-500">Class ID</dt><dd className="font-medium">{student.class_id}</dd></div>
            <div><dt className="text-gray-500">Year ID</dt><dd className="font-medium">{student.academic_year_id}</dd></div>
            <div><dt className="text-gray-500">Status</dt><dd>{student.is_active ? <span className="badge-stable">Active</span> : <span className="badge-risk">Inactive</span>}</dd></div>
            {student.health_notes && (
              <div className="col-span-2">
                <dt className="text-gray-500">Health notes</dt>
                <dd className="font-medium">{student.health_notes}</dd>
              </div>
            )}
          </dl>
        </div>

        {/* Attendance risk card */}
        <div className="card">
          <h2 className="text-base font-semibold text-gray-800 mb-3">Attendance</h2>
          {pct ? (
            <>
              <p className="text-3xl font-bold text-gray-900">{pct.attendance_percentage.toFixed(1)}%</p>
              <p className="text-sm text-gray-500 mb-3">{pct.present_days} / {pct.total_days} days</p>
              <RiskBadge level={pct.risk_level} />
            </>
          ) : (
            <p className="text-gray-400 text-sm">No data yet.</p>
          )}
        </div>
      </div>

      {/* Attendance history */}
      <div className="card mb-4">
        <h2 className="text-base font-semibold text-gray-800 mb-3">Recent Attendance</h2>
        {attendance.length === 0 ? (
          <p className="text-gray-400 text-sm">No attendance records.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2 text-gray-500 font-medium">Date</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {attendance.map((a) => (
                  <tr key={a.id} className="border-b border-gray-50">
                    <td className="py-2">{fmt(a.date)}</td>
                    <td className="py-2">
                      <span className={
                        a.status === 'PRESENT' ? 'badge-stable' :
                        a.status === 'LATE' ? 'badge-monitor' : 'badge-risk'
                      }>{a.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Surveys */}
      <div className="card">
        <h2 className="text-base font-semibold text-gray-800 mb-3">Survey History</h2>
        {surveys.length === 0 ? (
          <p className="text-gray-400 text-sm">No surveys yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2 text-gray-500 font-medium">Period</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Type</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Score</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Risk</th>
                </tr>
              </thead>
              <tbody>
                {surveys.map((s) => (
                  <tr key={s.id} className="border-b border-gray-50">
                    <td className="py-2">{s.month}/{s.year}</td>
                    <td className="py-2 text-gray-500">{s.survey_type}</td>
                    <td className="py-2">{s.total_score}/40 ({s.percentage.toFixed(0)}%)</td>
                    <td className="py-2"><RiskBadge level={s.risk_level} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Confirm modals */}
      {deleteConfirm && (
        <ConfirmModal
          title="Soft Delete Student"
          message="Mark this student inactive? All records are preserved."
          onConfirm={handleDelete}
          onCancel={() => setDeleteConfirm(false)}
        />
      )}
      {purgeConfirm && (
        <ConfirmModal
          title="Permanently Purge Student"
          message="This will irreversibly delete ALL data for this student including attendance and surveys. This cannot be undone."
          danger
          onConfirm={handlePurge}
          onCancel={() => setPurgeConfirm(false)}
        />
      )}
    </div>
  )
}

function ConfirmModal({ title, message, danger, onConfirm, onCancel }) {
  const [loading, setLoading] = useState(false)
  async function go() {
    setLoading(true)
    await onConfirm()
  }
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
        <p className="text-sm text-gray-600 mb-6">{message}</p>
        <div className="flex gap-3">
          <button onClick={go} disabled={loading} className={danger ? 'btn-danger flex-1' : 'btn-primary flex-1'}>
            {loading ? 'Processing…' : 'Confirm'}
          </button>
          <button onClick={onCancel} className="btn-secondary flex-1">Cancel</button>
        </div>
      </div>
    </div>
  )
}
