import api from './api'

export const parseService = {
  // Start parsing a repository
  parseRepository: (projectId, repo_path) => 
    api.post(`/parse/${projectId}`, null, { params: { repo_path } }),
  
  parseChanges: (projectId, repo_path) => 
    api.post(`/parse/${projectId}/changed`, null, { params: { repo_path } }),
  
  // Get parsing status
  getParsingStatus: (parseId) => api.get(`/parse/status/${parseId}`),
  
  // Get chunks for a project
  getProjectChunks: (projectId, page = 1, limit = 50) => 
    api.get(`/parse/chunks/${projectId}?page=${page}&limit=${limit}`),
  
  // Get embedding stats
  getEmbeddingStats: (projectId) => api.get(`/parse/embeddings/${projectId}/stats`),
  
  // Re-index project
  reindexProject: (projectId) => api.post(`/parse/reindex/${projectId}`)
}