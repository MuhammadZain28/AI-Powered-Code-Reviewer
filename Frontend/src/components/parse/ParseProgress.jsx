import React from 'react'
import Card from '../ui/Card'

const ParseProgress = ({ status }) => {
  const getProgress = () => {
    if (status.total_files === 0) return 0
    return (status.processed_files / status.total_files) * 100
  }

  return (
    <Card title="Parsing Progress">
      <div className="space-y-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Status: {status.status}</span>
          <span className="text-gray-600">
            {status.processed_files} / {status.total_files} files
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-primary-500 h-2 rounded-full transition-all duration-500"
            style={{ width: `${getProgress()}%` }}
          />
        </div>
        {status.current_file && (
          <p className="text-sm text-gray-500">
            Currently processing: {status.current_file}
          </p>
        )}
      </div>
    </Card>
  )
}

export default ParseProgress