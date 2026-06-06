import React from 'react'

const Loader = ({ size = 'md', fullScreen = false }) => {
  const sizes = {
    sm: 'w-6 h-6',
    md: 'w-10 h-10',
    lg: 'w-16 h-16'
  }

  const spinner = (
    <div className="flex justify-center items-center">
      <div className={`${sizes[size]} border-4 border-gray-200 border-t-primary-500 rounded-full animate-spin`}></div>
    </div>
  )

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50">
        {spinner}
      </div>
    )
  }

  return spinner
}

export default Loader