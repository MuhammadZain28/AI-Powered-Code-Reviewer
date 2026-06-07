import api from './api'

export const reviewService = {
  // Get all reviews for a project
  getProjectReviews: (projectId, page = 1, limit = 50) => 
    api.get(`/review/project/${projectId}?page=${page}&limit=${limit}`),
  
  // Get reviews for a specific file
  getFileReviews: (fileId) => api.get(`/review/file/${fileId}`),
  
  // Get review summary
  getReviewSummary: async (projectId) => {  
    const response = await api.get(`/review/summary/${projectId}`)
    console.log("Review summary response:", response)
    return response
  },
  
  // Trigger AI review
  triggerReview: () => 
    api.post('/review'),
  
  // Update review status
  updateReviewStatus: (reviewId, status, comment = '') => 
    api.put(`/review/${reviewId}`, { status, comment }),
  
  // Get review by ID
  getReview: (reviewId) => api.get(`/review/${reviewId}`)
}