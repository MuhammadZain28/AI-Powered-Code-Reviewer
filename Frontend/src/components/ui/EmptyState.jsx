import React from 'react'

const EmptyState = ({ title, description, icon, action }) => {
  return (
    <div className="text-center py-12">
      {icon && (
        <div className="mx-auto h-24 w-24 text-gray-400 mb-4">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-500 mb-6">{description}</p>
      {action && <div>{action}</div>}
    </div>
  )
}

export default EmptyState