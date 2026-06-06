import React from 'react'
import Card from '../ui/Card'

const StatsCard = ({ title, value, icon, trend, color = 'primary' }) => {
  const colors = {
    primary: 'bg-primary-500',
    green: 'bg-green-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500'
  }

  return (
    <Card>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {trend && (
            <p className={`text-xs mt-2 ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}% from last month
            </p>
          )}
        </div>
        <div className={`${colors[color]} p-3 rounded-full`}>
          {icon}
        </div>
      </div>
    </Card>
  )
}

export default StatsCard