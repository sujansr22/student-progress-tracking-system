import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { meApi } from '../api/client'

const QUESTIONS = [
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

function SurveyForm({ assignment, profile, onDone }) {
  const [scores, setScores] = useState({})
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const qc = useQueryClient()
  const allAnswered = QUESTIONS.every((q) => scores[q.key])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      await meApi.submitSurvey({
        student_id: profile.id,
        month: assignment.month,
        year: assignment.year,
        survey_type: 'STUDENT',
        answers: QUESTIONS.map((q) => ({ question_key: q.key, score: parseInt(scores[q.key]) })),
      })
      qc.invalidateQueries({ queryKey: ['me-pending-surveys'] })
      qc.invalidateQueries({ queryKey: ['me-surveys'] })
      onDone()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit survey')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="card">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 bg-orange-100 rounded-xl flex items-center justify-center text-xl">📋</div>
        <div>
          <p className="font-semibold text-gray-800">Self-Assessment Survey</p>
          <p className="text-sm text-gray-500">{assignment.month}/{assignment.year}</p>
        </div>
      </div>
      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">{error}</div>
      )}
      <form onSubmit={handleSubmit} className="space-y-4">
        {QUESTIONS.map((q, i) => (
          <div key={q.key} className="p-4 rounded-xl border border-gray-100 bg-gray-50">
            <p className="text-sm font-medium text-gray-800 mb-3">{i + 1}. {q.label}</p>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => setScores((s) => ({ ...s, [q.key]: val }))}
                  className={`flex-1 py-2.5 text-xs rounded-lg border font-medium transition-colors ${
                    parseInt(scores[q.key]) === val
                      ? 'bg-orange-500 text-white border-orange-500'
                      : 'border-gray-200 text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  {val}
                  <span className="block text-[10px] font-normal opacity-70 hidden sm:block">{SCORE_LABELS[val]}</span>
                </button>
              ))}
            </div>
          </div>
        ))}
        <button
          type="submit"
          disabled={saving || !allAnswered}
          className="w-full py-2.5 px-4 bg-orange-500 text-white text-sm font-medium rounded-lg hover:bg-orange-600 transition-colors disabled:opacity-50"
        >
          {saving ? 'Submitting…' : 'Submit Survey'}
        </button>
      </form>
    </div>
  )
}

export default function MySurveysPage() {
  const [activeSurvey, setActiveSurvey] = useState(null)
  const [submitted, setSubmitted] = useState(false)

  const { data: profile } = useQuery({
    queryKey: ['me-profile'],
    queryFn: () => meApi.profile().then((r) => r.data),
  })

  const { data: pending = [] } = useQuery({
    queryKey: ['me-pending-surveys'],
    queryFn: () => meApi.pendingSurveys().then((r) => r.data),
  })

  const { data: history = [] } = useQuery({
    queryKey: ['me-surveys'],
    queryFn: () => meApi.surveys({ limit: 20 }).then((r) => r.data),
  })

  if (submitted) {
    return (
      <div className="max-w-lg">
        <div className="card text-center py-8">
          <p className="text-5xl mb-4">🎉</p>
          <h2 className="text-xl font-semibold mb-2">Survey Submitted!</h2>
          <p className="text-gray-500 text-sm mb-6">Your self-assessment has been recorded.</p>
          <button onClick={() => { setSubmitted(false); setActiveSurvey(null) }} className="w-full py-2 px-4 bg-orange-500 text-white text-sm font-medium rounded-lg hover:bg-orange-600">
            Back to Surveys
          </button>
        </div>
      </div>
    )
  }

  if (activeSurvey && profile) {
    return (
      <div className="max-w-lg">
        <button onClick={() => setActiveSurvey(null)} className="text-sm text-gray-400 hover:text-gray-600 mb-4 block">← Back</button>
        <SurveyForm assignment={activeSurvey} profile={profile} onDone={() => setSubmitted(true)} />
      </div>
    )
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">My Surveys</h1>

      {/* Pending */}
      {pending.length > 0 && (
        <div className="mb-6">
          <h2 className="text-base font-semibold text-gray-800 mb-3">
            Pending <span className="text-orange-500">({pending.length})</span>
          </h2>
          <div className="space-y-3">
            {pending.map((a) => (
              <div key={a.id} className="card border-orange-100 bg-orange-50 flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-800">Self-Assessment — {a.month}/{a.year}</p>
                  {a.due_date && (
                    <p className="text-xs text-orange-600 mt-0.5">
                      Due: {new Date(a.due_date).toLocaleDateString('en-IN')}
                    </p>
                  )}
                </div>
                <button
                  onClick={() => setActiveSurvey(a)}
                  className="px-4 py-1.5 bg-orange-500 text-white text-sm font-medium rounded-lg hover:bg-orange-600"
                >
                  Start →
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {pending.length === 0 && (
        <div className="card text-center py-6 mb-6 bg-green-50 border-green-100">
          <p className="text-green-700 font-medium">✓ All caught up! No pending surveys.</p>
        </div>
      )}

      {/* History */}
      <div className="card">
        <h2 className="text-base font-semibold text-gray-800 mb-3">Survey History</h2>
        {history.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-6">No surveys submitted yet.</p>
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
                {history.map((s) => (
                  <tr key={s.id} className="border-b border-gray-50">
                    <td className="py-2.5">{s.month}/{s.year}</td>
                    <td className="py-2.5 text-gray-500">{s.survey_type}</td>
                    <td className="py-2.5">{s.total_score}/40 ({s.percentage.toFixed(0)}%)</td>
                    <td className="py-2.5">
                      <span className={
                        s.risk_level === 'STABLE' ? 'badge-stable' :
                        s.risk_level === 'MONITOR' ? 'badge-monitor' : 'badge-risk'
                      }>{s.risk_level}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
