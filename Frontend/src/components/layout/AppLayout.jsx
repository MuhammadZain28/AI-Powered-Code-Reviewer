import React from 'react'
import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'
import Sidebar from './Sidebar'
import { useAuth } from '../../hooks/useAuth'
import { useTheme } from '../../context/ThemeContext'

const AppLayout = () => {
  const { isAuthenticated } = useAuth()
  const { theme, toggleTheme } = useTheme()

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-bg transition-colors duration-200">
      <Navbar theme={theme} toggleTheme={toggleTheme} />
      <div className="flex">
        {isAuthenticated && <Sidebar />}
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default AppLayout