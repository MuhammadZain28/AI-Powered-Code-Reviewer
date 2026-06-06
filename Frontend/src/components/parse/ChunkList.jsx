import React, { useState } from 'react'
import Card from '../ui/Card'
import Badge from '../ui/Badge'

const ChunkList = ({ chunks }) => {
  const [expandedChunk, setExpandedChunk] = useState(null)

  if (chunks.length === 0) {
    return (
      <p className="text-gray-500 text-center py-8">
        No code chunks available. Parse a repository to generate chunks.
      </p>
    )
  }

  return (
    <div className="space-y-4">
      {chunks.map((chunk) => (
        <div key={chunk.id} className="border border-gray-200 rounded-lg overflow-hidden">
          <div 
            className="bg-gray-50 px-4 py-3 cursor-pointer hover:bg-gray-100 flex justify-between items-center"
            onClick={() => setExpandedChunk(expandedChunk === chunk.id ? null : chunk.id)}
          >
            <div>
              <p className="font-medium text-gray-900">{chunk.file_path}</p>
              <p className="text-sm text-gray-500 mt-1">
                Lines {chunk.start_line} - {chunk.end_line}
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="info">{chunk.language}</Badge>
              <svg 
                className={`w-5 h-5 text-gray-400 transition-transform ${expandedChunk === chunk.id ? 'rotate-180' : ''}`}
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
          {expandedChunk === chunk.id && (
            <div className="p-4 bg-gray-50 border-t border-gray-200">
              <pre className="text-sm text-gray-800 overflow-x-auto">
                <code>{chunk.content}</code>
              </pre>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export default ChunkList