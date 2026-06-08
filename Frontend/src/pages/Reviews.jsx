import React, { useEffect, useState } from 'react'
import { useProjects } from '../hooks/useProjects'
import { reviewService } from '../services/reviewService'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import Loader from '../components/ui/Loader'
import { getSeverityColor } from '../utils/statusColors'
import { formatDate } from '../utils/helpers'
import ReactMarkdown from 'react-markdown'
import Button from '../components/ui/Button'

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

  const triggerReview = async () => {
    setLoading(true)
    try {
      await reviewService.triggerReview(currentProject.id)
      await loadReviews()
      await loadSummary()
    } catch (error) {
      console.error('Failed to trigger review:', error)
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
        <h1 className="text-2xl font-bold text-gray-900">Code Reviews</h1>
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
      <div className="flex justify-between items-center">
        <h2 className="mt-1 text-lg font-medium">
          AI-powered analysis for {currentProject.name}
        </h2>
        <Button onClick={() => triggerReview()} disabled={loading}>
          Trigger AI Review
        </Button>
      </div>
      <div className="gap-4 flex justify-between items-start">
        <button
          onClick={() => setCurrentProject(null)}
          className="btn btn-outline"
        >
          Back to Projects
        </button>
        <Button onClick={() => loadReviews()}>
          Refresh Reviews
        </Button>
      </div>

      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-600">Total Reviews</p>
              <p className="text-2xl font-bold text-gray-900">{summary.total_issues || 0}</p>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-600">Critical Issues</p>
              <p className="text-2xl font-bold text-red-600">{summary.critical_issues || 0}</p>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-600">Moderate Issues</p>
              <p className="text-2xl font-bold text-green-600">{summary.medium_issues || 0}</p>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-600">Minor Issues</p>
              <p className="text-2xl font-bold text-yellow-600">{summary.low_issues || 0}</p>
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
                key={review.path}
                className=""
              >
                <h2 className="text-xl font-bold">{review.path}</h2>
                {review.chunks.map((review_chunks) => (
                  <div key={review_chunks.function} className="flex flex-col gap-2 p-4 border-b border-gray-200">
                    <div className="my-4">
                      <p className="mt-1 text-md"><span className="font-medium mr-2">Name:</span> {review_chunks.function}({review_chunks.parameters?.join(', ') || ''})</p>
                      {review_chunks.class && (
                        <p className="mt-1 text-md"><span className="font-medium mr-2">Class:</span> {review_chunks.class}</p>
                      )}
                      <p className="mt-1 text-md"><span className="font-medium mr-2">Lines:</span> {review_chunks.start} - {review_chunks.end}</p>
                      {review_chunks.return_values && (
                        <p className="mt-1 text-md flex flex-col"><span className="font-medium mr-2">Return Values:</span> {review_chunks.return_values.map((value, index) => (
                          value.length < 100 && <span key={index}>{index + 1}: {value}</span>
                        ))}</p>
                      )}
                      <p className="mt-1 text-md"><span className="font-medium">Purpose:</span></p> 
                      <p className="mt-1 text-sm">{review_chunks.purpose}</p>
                    </div>
                    {review_chunks.issues.map((issues) => (
                      <div key={issues.review_id} className="flex justify-between items-start border border-gray-200 rounded-lg p-4 hover:shadow-md shadow-sm transition-shadow">
                        <div className="flex flex-col gap-2 w-full  ">
                          <div className="flex items-center justify-between space-x-3 w-full">
                            <Badge className={getSeverityColor(issues.severity)}>
                              {issues.severity}
                            </Badge>
                            <Badge variant="info">{issues.category}</Badge>
                            <span className="text-sm">
                              {issues.created_at.split('T')[0]}
                            </span>
                          </div>
                          <p className="text-gray-600 mt-1 text-sm flex flex-col">
                            <span className="font-medium">Review:</span>
                            <ReactMarkdown>{issues.review}</ReactMarkdown>
                          </p>
                          <p className="text-gray-600 mt-1 text-sm flex flex-col">
                            <span className="font-medium">Suggested Fix:</span>
                            <ReactMarkdown>{issues.suggested_fix}</ReactMarkdown>
                          </p>
                        </div>
                        {/* <div className="flex space-x-2">
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
                        </div> */}
                      </div>
                    ))}
                </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

export default Reviews