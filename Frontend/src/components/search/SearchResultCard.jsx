import React, { useState } from 'react'
import Card from '../ui/Card'
import Badge from '../ui/Badge'

const SearchResultCard = ({ result, children }) => {
  const [expanded, setExpanded] = useState(false)

  return (
    <Card>
      <div className="space-y-3">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              {children}
              <Badge variant="info">{result.language || 'code'}</Badge>
            </div>
            <h3 className="text-lg font-semibold text-gray-900">
              {result.file_path}
            </h3>
            <p className="text-sm text-gray-500">
              Lines {result.start_line} - {result.end_line}
            </p>
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-primary-600 hover:text-primary-700 text-sm"
          >
            {expanded ? 'Show less' : 'Show more'}
          </button>
        </div>
        
        <pre className="text-sm bg-gray-50 p-3 rounded-lg overflow-x-auto">
          <code>{expanded ? result.content : result.content.substring(0, 300) + (result.content.length > 300 ? '...' : '')}</code>
        </pre>
        
        {result.similarity_score && (
          <div className="text-right">
            <span className="text-xs text-gray-500">
              Similarity: {(result.similarity_score * 100).toFixed(1)}%
            </span>
          </div>
        )}
      </div>
    </Card>
  )
}

export default SearchResultCard