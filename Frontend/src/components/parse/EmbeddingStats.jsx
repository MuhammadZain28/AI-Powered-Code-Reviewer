import React from 'react'
import Card from '../ui/Card'

const EmbeddingStats = ({ stats }) => {
  return (
    <Card title="Embedding Statistics">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="text-center">
          <p className="text-sm text-gray-600">Total Embeddings</p>
          <p className="text-2xl font-bold text-gray-900">{stats.total_embeddings || 0}</p>
        </div>
        <div className="text-center">
          <p className="text-sm text-gray-600">Vector Dimension</p>
          <p className="text-2xl font-bold text-gray-900">{stats.vector_dimension || 384}</p>
        </div>
        <div className="text-center">
          <p className="text-sm text-gray-600">Last Indexed</p>
          <p className="text-lg font-medium text-gray-900">
            {stats.last_indexed ? new Date(stats.last_indexed).toLocaleDateString() : 'Never'}
          </p>
        </div>
      </div>
    </Card>
  )
}

export default EmbeddingStats