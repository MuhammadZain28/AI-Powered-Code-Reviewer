import api from './api'

export const reviewService = {
  // Get all reviews for a project
  getProjectReviews: (projectId, page = 1, limit = 50) => 
    api.get(`/reviews/project/${projectId}?page=${page}&limit=${limit}`),
  
  // Get reviews for a specific file
  getFileReviews: (fileId) => api.get(`/reviews/file/${fileId}`),
  
  // Get review summary
  getReviewSummary: (projectId) => api.get(`/reviews/summary/${projectId}`),
  
  // Trigger AI review
  triggerReview: (fileId, contextLines = 10) => 
    api.post('/reviews/trigger', { file_id: fileId, context_lines: contextLines }),
  
  // Update review status
  updateReviewStatus: (reviewId, status, comment = '') => 
    api.put(`/reviews/${reviewId}`, { status, comment }),
  
  // Get review by ID
  getReview: (reviewId) => api.get(`/reviews/${reviewId}`)
}