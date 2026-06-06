import React from 'react'
import Modal from '../ui/Modal'
import Badge from '../ui/Badge'
import Button from '../ui/Button'
import { getSeverityColor } from '../../utils/statusColors'

const ReviewPanel = ({ review, isOpen, onClose, onUpdate }) => {
  if (!review) return null

  const handleStatusChange = (status) => {
    onUpdate(review.id, status)
    onClose()
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Review Details" size="lg">
      <div className="space-y-4">
        <div className="flex items-center space-x-3">
          <Badge variant={getSeverityColor(review.severity)}>
            {review.severity}
          </Badge>
          <Badge variant="info">{review.type}</Badge>
          <span className="text-sm text-gray-500">
            Created: {new Date(review.created_at).toLocaleDateString()}
          </span>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-900">{review.title}</h3>
          <p className="text-gray-700 mt-2">{review.description}</p>
        </div>

        {review.suggestion && (
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Suggestion</h4>
            <p className="text-gray-700 bg-blue-50 p-3 rounded-lg">{review.suggestion}</p>
          </div>
        )}

        {review.file_path && (
          <div>
            <h4 className="font-medium text-gray-900 mb-2">File Location</h4>
            <p className="text-sm text-gray-600 font-mono">{review.file_path}</p>
            {review.line_number && (
              <p className="text-sm text-gray-500">Line: {review.line_number}</p>
            )}
          </div>
        )}

        {review.code_snippet && (
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Code Snippet</h4>
            <pre className="bg-gray-900 text-gray-100 p-3 rounded-lg overflow-x-auto text-sm">
              <code>{review.code_snippet}</code>
            </pre>
          </div>
        )}

        <div className="pt-4 border-t border-gray-200">
          <h4 className="font-medium text-gray-900 mb-3">Update Status</h4>
          <div className="flex space-x-2">
            <Button size="sm" onClick={() => handleStatusChange('open')}>
              Open
            </Button>
            <Button size="sm" variant="secondary" onClick={() => handleStatusChange('in_progress')}>
              In Progress
            </Button>
            <Button size="sm" variant="secondary" onClick={() => handleStatusChange('resolved')}>
              Resolved
            </Button>
            <Button size="sm" variant="secondary" onClick={() => handleStatusChange('wont_fix')}>
              Won't Fix
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  )
}

export default ReviewPanel