import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function ProtectedRoute({ allowedRoles }) {
  const { isAuthenticated, role } = useAuth()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (allowedRoles && !allowedRoles.includes(role)) {
    return <Navigate to={role === 'STUDENT' ? '/student' : '/'} replace />
  }
  return <Outlet />
}
