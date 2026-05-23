import axios from 'axios'

const client = axios.create({
  baseURL: '/api/v1',
})

export function setAuthToken(token) {
  if (token) {
    client.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete client.defaults.headers.common['Authorization']
  }
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email, password) => {
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)
    return client.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },
  refresh: (refreshToken) => client.post('/auth/refresh', { refresh_token: refreshToken }),
  logout: (refreshToken) => client.post('/auth/logout', { refresh_token: refreshToken }),
  forgotPassword: (email) => client.post('/auth/forgot-password', { email }),
  resetPassword: (token, newPassword) =>
    client.post('/auth/reset-password', { token, new_password: newPassword }),
  register: (email, password) => client.post('/auth/register', { email, password }),
  studentRegister: (email, password) =>
    client.post('/auth/student-register', { email, password }),
}

// ── Student Portal (/me) ──────────────────────────────────────────────────────
export const meApi = {
  profile: () => client.get('/me/profile'),
  attendance: (params) => client.get('/me/attendance', { params }),
  attendanceSummary: (params) => client.get('/me/attendance/summary', { params }),
  performance: (month, year) => client.get('/me/performance', { params: { month, year } }),
  surveys: (params) => client.get('/me/surveys', { params }),
  pendingSurveys: () => client.get('/me/surveys/pending'),
  submitSurvey: (data) => client.post('/me/surveys/submit', data),
}

// ── Assigned Surveys ──────────────────────────────────────────────────────────
export const assignedSurveysApi = {
  list: (params) => client.get('/assigned-surveys/', { params }),
  assign: (data) => client.post('/assigned-surveys/', data),
  cancel: (id) => client.delete(`/assigned-surveys/${id}`),
}

// ── Students ──────────────────────────────────────────────────────────────────
export const studentsApi = {
  list: (params) => client.get('/students/', { params }),
  get: (id) => client.get(`/students/${id}`),
  create: (data) => client.post('/students/', data),
  update: (id, data) => client.put(`/students/${id}`, data),
  delete: (id) => client.delete(`/students/${id}`),
  export: (id) => client.get(`/students/${id}/export`),
  purge: (id) => client.delete(`/students/${id}/purge`),
}

// ── Attendance ────────────────────────────────────────────────────────────────
export const attendanceApi = {
  mark: (data) => client.post('/attendance/mark', data),
  getStudentAttendance: (studentId, params) =>
    client.get(`/attendance/student/${studentId}`, { params }),
  getStudentPercentage: (studentId, params) =>
    client.get(`/attendance/student/${studentId}/percentage`, { params }),
  getInstitutionSummary: (params) =>
    client.get('/attendance/institution/summary', { params }),
  getHighRisk: (params) =>
    client.get('/attendance/institution/high-risk', { params }),
}

// ── Surveys ───────────────────────────────────────────────────────────────────
export const surveysApi = {
  submit: (data) => client.post('/survey/submit', data),
  getStudentSurveys: (studentId, params) =>
    client.get(`/survey/student/${studentId}`, { params }),
}

// ── Analytics ─────────────────────────────────────────────────────────────────
export const analyticsApi = {
  getStudentProgress: (studentId, month, year) =>
    client.get(`/analytics/student/${studentId}/progress`, { params: { month, year } }),
}

// ── Users ─────────────────────────────────────────────────────────────────────
export const usersApi = {
  list: (params) => client.get('/users/', { params }),
  create: (data) => client.post('/users/', data),
}

// ── Institutions ──────────────────────────────────────────────────────────────
export const institutionsApi = {
  list: (params) => client.get('/institutions/', { params }),
  create: (data) => client.post('/institutions/', data),
}

// ── Subscriptions ─────────────────────────────────────────────────────────────
export const subscriptionsApi = {
  list: (params) => client.get('/subscriptions/', { params }),
  status: (params) => client.get('/subscriptions/status', { params }),
  create: (data) => client.post('/subscriptions/', data),
  renew: (institutionId, days) =>
    client.put(`/subscriptions/${institutionId}/renew`, null, { params: { days } }),
}

// ── Academic Years ────────────────────────────────────────────────────────────
export const academicYearsApi = {
  list: (params) => client.get('/academic-years/', { params }),
  create: (data) => client.post('/academic-years/', data),
}

// ── Classes ───────────────────────────────────────────────────────────────────
export const classesApi = {
  list: (params) => client.get('/classes/', { params }),
  create: (data) => client.post('/classes/', data),
}

export default client
