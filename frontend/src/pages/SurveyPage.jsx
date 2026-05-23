import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { studentsApi, surveysApi, assignedSurveysApi } from '../api/client'

const INSTRUCTOR_QUESTIONS = [
  { key: 'q1', label: 'Student participates actively in class activities' },
  { key: 'q2', label: 'Student completes assignments on time' },
  { key: 'q3', label: 'Student shows positive attitude toward learning' },
  { key: 'q4', label: 'Student interacts well with peers' },
  { key: 'q5', label: 'Student follows school rules and discipline' },
  { key: 'q6', label: 'Student appears physically healthy and energetic' },
  { key: 'q7', label: 'Student communicates openly about concerns' },
  { key: 'q8', label: 'Overall student wellness this month' },
]

const STUDENT_QUESTIONS = [
  { key: 'q1', label: 'I enjoy coming to school' },
  { key: 'q2', label: 'I feel safe at school' },
  { key: 'q3', label: 'I have friends I can talk to' },
  { key: 'q4', label: 'I understand the lessons being taught' },
  { key: 'q5', label: 'I feel good about my progress' },
  { key: 'q6', label: 'I am able to focus during class' },
  { key: 'q7', label: 'My physical health is good' },
  { key: 'q8', label: 'Overall I feel happy and motivated' },
]

const SCORE_LABELS = { 1: 'Poor', 2: 'Below avg', 3: 'Average', 4: 'Good', 5: 'Excellent' }

function AssignSurveyTab({ students }) {
  const qc = useQueryClient()
  const now = new Date()
  const [studentId, setStudentId] = useState('')
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [year, setYear] = useState(now.getFullYear())
  const [dueDate, setDueDate] = useState('')
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState('')

  const { data: assigned = [] } = useQuery({
    queryKey: ['assigned-surveys'],
    queryFn: () => assignedSurveysApi.list().then((r) => r.data),
  })

  async function handleAssign(e) {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      await assignedSurveysApi.assign({
        student_id: studentId,
        month: parseInt(month),
        year: parseInt(year),
        due_date: dueDate || null,
      })
      qc.invalidateQueries({ queryKey: ['assigned-surveys'] })
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
      setStudentId('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to assign survey')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="card">
        <h2 className="text-base font-semibold text-gray-800 mb-4">Assign Self-Assessment to Student</h2>
        {error && <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">{error}</div>}
        {success && <div className="mb-4 p-3 rounded-lg bg-green-50 border border-green-200 text-green-700 text-sm">✓ Survey assigned! Student will see it in their portal.</div>}
        <form onSubmit={handleAssign} className="space-y-3">
          <div>
            <label className="label">Student</label>
            <select className="input" value={studentId} onChange={(e) => setStudentId(e.target.value)} required>
              <option value="">Select student…</option>
              {students.map((s) => <option key={s.id} value={s.id}>{s.first_name} {s.last_name}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="label">Month</label>
              <select className="input" value={month} onChange={(e) => setMonth(e.target.value)}>
                {Array.from({ length: 12 }, (_, i) => (
                  <option key={i + 1} value={i + 1}>{new Date(2000, i).toLocaleString('default', { month: 'short' })}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Year</label>
              <input type="number" className="input" min={2020} max={2099} value={year} onChange={(e) => setYear(e.target.value)} />
            </div>
            <div>
              <label className="label">Due date (opt.)</label>
              <input type="date" className="input" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
            </div>
          </div>
          <button type="submit" disabled={saving || !studentId} className="btn-primary w-full">
            {saving ? 'Assigning…' : 'Assign Survey'}
          </button>
        </form>
      </div>

      {assigned.length > 0 && (
        <div className="card">
          <h2 className="text-base font-semibold text-gray-800 mb-3">Assigned Surveys</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2 text-gray-500 font-medium">Student</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Period</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Status</th>
                  <th className="text-left py-2 text-gray-500 font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {assigned.map((a) => {
                  const stu = students.find((s) => s.id === a.student_id)
                  return (
                    <tr key={a.id} className="border-b border-gray-50">
                      <td className="py-2.5 font-medium">{stu ? `${stu.first_name} ${stu.last_name}` : a.student_id}</td>
                      <td className="py-2.5 text-gray-500">{a.month}/{a.year}</td>
                      <td className="py-2.5">
                        <span className={a.status === 'COMPLETED' ? 'badge-stable' : 'badge-monitor'}>
                          {a.status}
                        </span>
                      </td>
                      <td className="py-2.5">
                        {a.status === 'PENDING' && (
                          <button
                            onClick={async () => {
                              await assignedSurveysApi.cancel(a.id)
                              qc.invalidateQueries({ queryKey: ['assigned-surveys'] })
                            }}
                            className="text-xs text-red-500 hover:underline"
                          >
                            Cancel
                          </button>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default function SurveyPage() {
  const [tab, setTab] = useState('submit')
  const now = new Date()
  const [studentId, setStudentId] = useState('')
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [year, setYear] = useState(now.getFullYear())
  const [surveyType, setSurveyType] = useState('INSTRUCTOR')
  const [scores, setScores] = useState({})
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState(null)
  const [error, setError] = useState('')

  const { data: students = [] } = useQuery({
    queryKey: ['students'],
    queryFn: () => studentsApi.list({ limit: 100 }).then((r) => r.data),
  })

  const questions = surveyType === 'INSTRUCTOR' ? INSTRUCTOR_QUESTIONS : STUDENT_QUESTIONS
  const allAnswered = questions.every((q) => scores[q.key])

  function setScore(key, val) {
    setScores((s) => ({ ...s, [key]: val }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      const result = await surveysApi.submit({
        student_id: studentId,
        month: parseInt(month),
        year: parseInt(year),
        survey_type: surveyType,
        answers: questions.map((q) => ({ question_key: q.key, score: parseInt(scores[q.key]) })),
      })
      setSuccess(result.data)
      setScores({})
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit survey')
    } finally {
      setSaving(false)
    }
  }

  if (success) {
    return (
      <div className="max-w-lg">
        <div className="card text-center">
          <div className="text-4xl mb-3">✅</div>
          <h2 className="text-lg font-semibold mb-2">Survey Submitted</h2>
          <p className="text-gray-600 text-sm mb-1">Score: {success.total_score}/40 ({success.percentage.toFixed(0)}%)</p>
          <p className="text-gray-600 text-sm mb-6">
            Risk level: <strong>{success.risk_level}</strong>
          </p>
          <button onClick={() => setSuccess(null)} className="btn-primary w-full">Submit another</button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Surveys</h1>
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
          {[['submit', 'Submit Survey'], ['assign', 'Assign to Student']].map(([key, label]) => (
            <button key={key} onClick={() => setTab(key)}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${tab === key ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {tab === 'assign' && <AssignSurveyTab students={students} />}
      {tab === 'submit' && <div className="card">
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Setup row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="col-span-2">
              <label className="label">Student</label>
              <select className="input" value={studentId} onChange={(e) => setStudentId(e.target.value)} required>
                <option value="">Select student…</option>
                {students.map((s) => (
                  <option key={s.id} value={s.id}>{s.first_name} {s.last_name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Month</label>
              <select className="input" value={month} onChange={(e) => setMonth(e.target.value)}>
                {Array.from({ length: 12 }, (_, i) => (
                  <option key={i + 1} value={i + 1}>
                    {new Date(2000, i).toLocaleString('default', { month: 'short' })}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Year</label>
              <input type="number" className="input" min={2020} max={2099} value={year} onChange={(e) => setYear(e.target.value)} />
            </div>
          </div>

          {/* Survey type */}
          <div>
            <label className="label">Survey type</label>
            <div className="flex gap-3">
              {['INSTRUCTOR', 'STUDENT'].map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => { setSurveyType(t); setScores({}) }}
                  className={`flex-1 py-2 text-sm rounded-lg border font-medium transition-colors ${
                    surveyType === t
                      ? 'bg-brand-600 text-white border-brand-600'
                      : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {t === 'INSTRUCTOR' ? '👩‍🏫 Instructor' : '👤 Student'}
                </button>
              ))}
            </div>
          </div>

          {/* Questions */}
          <div className="space-y-4">
            {questions.map((q, i) => (
              <div key={q.key} className="p-4 rounded-xl border border-gray-100 bg-gray-50">
                <p className="text-sm font-medium text-gray-800 mb-3">
                  {i + 1}. {q.label}
                </p>
                <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map((val) => (
                    <button
                      key={val}
                      type="button"
                      onClick={() => setScore(q.key, val)}
                      className={`flex-1 py-2 text-xs rounded-lg border font-medium transition-colors ${
                        parseInt(scores[q.key]) === val
                          ? 'bg-brand-600 text-white border-brand-600'
                          : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      {val}
                      <span className="block text-[10px] font-normal opacity-70 hidden sm:block">
                        {SCORE_LABELS[val]}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <button type="submit" disabled={saving || !allAnswered || !studentId} className="btn-primary w-full">
            {saving ? 'Submitting…' : 'Submit Survey'}
          </button>
        </form>
      </div>}
    </div>
  )
}
