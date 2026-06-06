import React from 'react'
import Card from '../ui/Card'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const ActivityChart = ({ data }) => {
  return (
    <Card title="Activity Overview">
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="reviews" stroke="#3b82f6" strokeWidth={2} />
            <Line type="monotone" dataKey="projects" stroke="#22c55e" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}

export default ActivityChart