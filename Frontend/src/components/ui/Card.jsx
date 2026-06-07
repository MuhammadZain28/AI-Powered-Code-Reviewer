import React from 'react'

const Card = ({ children, className = '', title, actions }) => {
  return (
    <div className={`border border-gray-500 rounded-lg shadow-lg overflow-hidden ${className}`}>
      {(title || actions) && (
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          {title && <h3 className="text-lg font-semibold">{title}</h3>}
          {actions && <div className="flex space-x-2">{actions}</div>}
        </div>
      )}
      <div className="p-6">
        {children}
      </div>
    </div>
  )
}

export default Card