import api from './api'

export const parseService = {
  // Start parsing a repository
  parseRepository: (projectId, repoUrl, branch = 'main') => 
    api.post('/parse/repository', { project_id: projectId, repo_url: repoUrl, branch }),
  
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