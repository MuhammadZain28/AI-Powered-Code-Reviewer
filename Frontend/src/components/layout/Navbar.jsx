import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import Button from '../ui/Button'

const Navbar = ({ theme, toggleTheme }) => {
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <nav className="bg-white dark:bg-dark-card border-b border-gray-200 dark:border-dark-border sticky top-0 z-50 transition-colors duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <svg className="h-8 w-8 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
              <span className="font-bold text-xl text-gray-900 dark:text-dark-text">CodeReview</span>
              <span className="text-xs bg-primary-600 text-white px-2 py-0.5 rounded-full">AI</span>
            </Link>
            
            {isAuthenticated && (
              <div className="hidden md:flex ml-10 space-x-1">
                <NavItem to="/dashboard">Dashboard</NavItem>
                <NavItem to="/projects">Projects</NavItem>
                <NavItem to="/ai-search">AI Search</NavItem>
                <NavItem to="/reviews">Reviews</NavItem>
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg bg-gray-100 dark:bg-dark-bg border border-gray-300 dark:border-dark-border hover:bg-gray-200 dark:hover:bg-dark-hover transition-colors"
            >
              {theme === 'dark' ? (
                <svg className="w-5 h-5 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              ) : (
                <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              )}
            </button>

            {isAuthenticated ? (
              <>
                <div className="flex items-center space-x-3">
                  <div className="relative group">
                    <button className="flex items-center space-x-2 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-hover transition-colors">
                      <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center">
                        <span className="text-white font-medium text-sm">
                          {user?.name?.charAt(0) || user?.email?.charAt(0)}
                        </span>
                      </div>
                      <svg className="w-4 h-4 text-gray-500 dark:text-dark-textSecondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                    <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-dark-card border border-gray-200 dark:border-dark-border rounded-lg shadow-lg hidden group-hover:block">
                      <div className="px-4 py-3 border-b border-gray-200 dark:border-dark-border">
                        <p className="text-sm text-gray-900 dark:text-dark-text">{user?.name}</p>
                        <p className="text-xs text-gray-500 dark:text-dark-textSecondary">{user?.email}</p>
                      </div>
                      <button onClick={handleLogout} className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-50 dark:hover:bg-dark-hover transition-colors">
                        Sign out
                      </button>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <Button onClick={() => navigate('/login')}>
                Sign in
              </Button>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}

const NavItem = ({ to, children }) => (
  <Link to={to} className="px-3 py-2 rounded-md text-sm font-medium text-gray-600 dark:text-dark-textSecondary hover:text-gray-900 dark:hover:text-dark-text hover:bg-gray-50 dark:hover:bg-dark-hover transition-all">
    {children}
  </Link>
)

export default Navbar