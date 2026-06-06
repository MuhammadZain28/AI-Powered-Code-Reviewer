import React from 'react'
import Card from '../ui/Card'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

const ProjectStats = ({ stats }) => {
  const severityData = [
    { name: 'Critical', value: stats?.critical_count || 0, color: '#dc2626' },
    { name: 'High', value: stats?.high_count || 0, color: '#ea580c' },
    { name: 'Medium', value: stats?.medium_count || 0, color: '#eab308' },
    { name: 'Low', value: stats?.low_count || 0, color: '#22c55e' }
  ]

  const activityData = [
    { name: 'Files', value: stats?.total_files || 0 },
    { name: 'Chunks', value: stats?.total_chunks || 0 },
    { name: 'Reviews', value: stats?.total_reviews || 0 },
    { name: 'Issues', value: stats?.total_issues || 0 }
  ]

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <div className="text-center">
            <p className="text-sm text-gray-600">Total Files</p>
            <p className="text-2xl font-bold text-gray-900">{stats?.total_files || 0}</p>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <p className="text-sm text-gray-600">Code Chunks</p>
            <p className="text-2xl font-bold text-gray-900">{stats?.total_chunks || 0}</p>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <p className="text-sm text-gray-600">Total Reviews</p>
            <p className="text-2xl font-bold text-gray-900">{stats?.total_reviews || 0}</p>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <p className="text-sm text-gray-600">Issues Found</p>
            <p className="text-2xl font-bold text-red-600">{stats?.total_issues || 0}</p>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Issues by Severity">
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={severityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {severityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Project Overview">
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={activityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  )
}

export default ProjectStats