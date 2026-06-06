import React from 'react'
import Card from '../ui/Card'

const ReviewSummary = ({ summary }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      <Card>
        <div className="text-center">
          <p className="text-sm text-gray-600">Total Reviews</p>
          <p className="text-2xl font-bold text-gray-900">{summary.total_reviews || 0}</p>
        </div>
      </Card>
      <Card>
        <div className="text-center">
          <p className="text-sm text-gray-600">Critical Issues</p>
          <p className="text-2xl font-bold text-red-600">{summary.critical_count || 0}</p>
        </div>
      </Card>
      <Card>
        <div className="text-center">
          <p className="text-sm text-gray-600">Resolved</p>
          <p className="text-2xl font-bold text-green-600">{summary.resolved_count || 0}</p>
        </div>
      </Card>
      <Card>
        <div className="text-center">
          <p className="text-sm text-gray-600">Open Issues</p>
          <p className="text-2xl font-bold text-yellow-600">{summary.open_count || 0}</p>
        </div>
      </Card>
    </div>
  )
}

export default ReviewSummary