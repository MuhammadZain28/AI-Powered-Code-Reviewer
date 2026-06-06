import { useState, useCallback } from 'react'
import { reviewService } from '../services/reviewService'
import toast from 'react-hot-toast'

export const useReviews = (projectId) => {
  const [reviews, setReviews] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [selectedReview, setSelectedReview] = useState(null)

  const loadReviews = useCallback(async (page = 1, limit = 50) => {
    setLoading(true)
    try {
      const data = await reviewService.getProjectReviews(projectId, page, limit)
      setReviews(data)
      return data
    } catch (error) {
      toast.error('Failed to load reviews')
      throw error
    } finally {
      setLoading(false)
    }
  }, [projectId])

  const loadSummary = useCallback(async () => {
    try {
      const data = await reviewService.getReviewSummary(projectId)
      setSummary(data)
      return data
    } catch (error) {
      console.error('Failed to load summary:', error)
      return null
    }
  }, [projectId])

  const triggerReview = useCallback(async (fileId, contextLines = 10) => {
    setLoading(true)
    try {
      const result = await reviewService.triggerReview(fileId, contextLines)
      toast.success('Review triggered successfully')
      await loadReviews()
      return result
    } catch (error) {
      toast.error(error.message || 'Failed to trigger review')
      throw error
    } finally {
      setLoading(false)
    }
  }, [loadReviews])

  const updateReviewStatus = useCallback(async (reviewId, status, comment = '') => {
    try {
      const result = await reviewService.updateReviewStatus(reviewId, status, comment)
      toast.success('Review status updated')
      await loadReviews()
      return result
    } catch (error) {
      toast.error(error.message || 'Failed to update review status')
      throw error
    }
  }, [loadReviews])

  const getFileReviews = useCallback(async (fileId) => {
    setLoading(true)
    try {
      const data = await reviewService.getFileReviews(fileId)
      return data
    } catch (error) {
      toast.error('Failed to load file reviews')
      throw error
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    reviews,
    summary,
    loading,
    selectedReview,
    setSelectedReview,
    loadReviews,
    loadSummary,
    triggerReview,
    updateReviewStatus,
    getFileReviews
  }
}