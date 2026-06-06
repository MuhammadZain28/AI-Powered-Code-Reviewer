import React from 'react'

const Card = ({ children, className = '', title, actions }) => {
  return (
    <div className={`bg-dark-card border border-dark-border rounded-lg shadow-lg overflow-hidden ${className}`}>
      {(title || actions) && (
        <div className="px-6 py-4 border-b border-dark-border flex justify-between items-center">
          {title && <h3 className="text-lg font-semibold text-dark-text">{title}</h3>}
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