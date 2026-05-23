import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import Layout from './components/Layout'
import StudentLayout from './components/StudentLayout'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import StudentRegisterPage from './pages/StudentRegisterPage'
import DashboardPage from './pages/DashboardPage'
import StudentsPage from './pages/StudentsPage'
import StudentDetailPage from './pages/StudentDetailPage'
import AttendancePage from './pages/AttendancePage'
import SurveyPage from './pages/SurveyPage'
import AnalyticsPage from './pages/AnalyticsPage'
import UsersPage from './pages/UsersPage'
import SuperAdminPage from './pages/SuperAdminPage'
import StudentDashboardPage from './pages/StudentDashboardPage'
import MyAttendancePage from './pages/MyAttendancePage'
import MyPerformancePage from './pages/MyPerformancePage'
import MySurveysPage from './pages/MySurveysPage'

export default function App() {
  const { isAuthenticated, role } = useAuth()

  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/student-register" element={<StudentRegisterPage />} />

      {/* Student portal */}
      <Route path="student" element={<ProtectedRoute allowedRoles={['STUDENT']} />}>
        <Route element={<StudentLayout />}>
          <Route index element={<StudentDashboardPage />} />
          <Route path="my-attendance" element={<MyAttendancePage />} />
          <Route path="my-performance" element={<MyPerformancePage />} />
          <Route path="my-surveys" element={<MySurveysPage />} />
        </Route>
      </Route>

      {/* Staff portal */}
      <Route element={<ProtectedRoute allowedRoles={['SUPER_ADMIN', 'SCHOOL_ADMIN', 'INSTRUCTOR']} />}>
        <Route element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="students" element={<StudentsPage />} />
          <Route path="students/:id" element={<StudentDetailPage />} />
          <Route path="attendance" element={<AttendancePage />} />
          <Route path="survey" element={<SurveyPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="admin" element={
            role === 'SUPER_ADMIN' ? <SuperAdminPage /> : <Navigate to="/" replace />
          } />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to={isAuthenticated ? '/' : '/login'} replace />} />
    </Routes>
  )
}
