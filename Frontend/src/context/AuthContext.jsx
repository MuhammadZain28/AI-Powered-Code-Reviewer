import React, { createContext, useState, useContext, useEffect } from 'react'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // AUTO-LOGIN FOR DEVELOPMENT
    const devUser = {
      id: 1,
      name: 'Developer',
      email: 'dev@example.com',
      role: 'admin'
    }
    setUser(devUser)
    setLoading(false)
  }, [])

  const login = async (email, password) => {
    // Mock login for development
    const mockUser = {
      id: 1,
      name: 'Developer',
      email: email,
      role: 'admin'
    }
    setUser(mockUser)
    return { access_token: 'mock-token' }
  }

  const logout = () => {
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  )
}