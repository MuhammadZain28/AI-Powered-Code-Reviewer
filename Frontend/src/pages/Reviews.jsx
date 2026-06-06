import React, { useEffect, useState } from 'react'
import { useProjects } from '../hooks/useProjects'
import { reviewService } from '../services/reviewService'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import Loader from '../components/ui/Loader'
import { getSeverityColor } from '../utils/statusColors'
import { formatDate } from '../utils/helpers'

const Reviews = () => {
  const { projects, currentProject, setCurrentProject } = useProjects()
  const [reviews, setReviews] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (currentProject) {
      loadReviews()
      loadSummary()
    }
  }, [currentProject])

  const loadReviews = async () => {
    setLoading(true)
    try {
      const data = await reviewService.getProjectReviews(currentProject.id)
      setReviews(data)
    } catch (error) {
      console.error('Failed to load reviews:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadSummary = async () => {
    try {
      const data = await reviewService.getReviewSummary(currentProject.id)
      setSummary(data)
    } catch (error) {
      console.error('Failed to load summary:', error)
    }
  }

  const handleUpdateStatus = async (reviewId, status) => {
    try {
      await reviewService.updateReviewStatus(reviewId, status)
      await loadReviews()
    } catch (error) {
      console.error('Failed to update review status:', error)
    }
  }

  if (!currentProject) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Code Reviews</h1>
        <Card>
          <p className="text-gray-500 text-center py-8">
            Select a project to view its code reviews
          </p>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Code Reviews</h1>
          <p className="text-gray-600 mt-1">
            AI-powered analysis for {currentProject.name}
          </p>
        </div>
        <select
          className="input w-64"
          value={currentProject?.id || ''}
          onChange={(e) => {
            const project = projects.find(p => p.id === parseInt(e.target.value))
            setCurrentProject(project)
          }}
        >
          <option value="">Select a project</option>
          {projects.map(project => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </div>

      {summary && (
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
      )}

      <Card title="Review Issues">
        {loading ? (
          <Loader />
        ) : reviews.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            No reviews found. Parse a repository and trigger AI reviews to see results.
          </p>
        ) : (
          <div className="space-y-4">
            {reviews.map((review) => (
              <div
                key={review.id}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <Badge variant={getSeverityColor(review.severity)}>
                        {review.severity}
                      </Badge>
                      <Badge variant="info">{review.type}</Badge>
                      <span className="text-sm text-gray-500">
                        {formatDate(review.created_at)}
                      </span>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mt-2">
                      {review.title}
                    </h3>
                    <p className="text-gray-600 mt-1 line-clamp-2">
                      {review.description}
                    </p>
                    <p className="text-sm text-gray-500 mt-2">
                      File: {review.file_path}
                    </p>
                  </div>
                  <div className="flex space-x-2">
                    <select
                      value={review.status}
                      onChange={(e) => handleUpdateStatus(review.id, e.target.value)}
                      className="text-sm border rounded px-2 py-1"
                    >
                      <option value="open">Open</option>
                      <option value="in_progress">In Progress</option>
                      <option value="resolved">Resolved</option>
                      <option value="wont_fix">Won't Fix</option>
                    </select>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

export default Reviews