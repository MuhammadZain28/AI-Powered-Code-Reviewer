import { useAuth as useAuthContext } from '../context/AuthContext'

export const useAuth = () => {
  const { user, loading, login, logout } = useAuthContext()
  
  const isAuthenticated = !!user
  const isAdmin = user?.role === 'admin'
  
  return {
    user,
    loading,
    isAuthenticated,
    isAdmin,
    login,
    logout
  }
}