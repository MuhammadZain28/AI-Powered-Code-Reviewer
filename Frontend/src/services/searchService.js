import api from './api'

export const searchService = {
  // Semantic search
  semanticSearch: (projectId, query, limit = 10) => 
    api.post('/search/semantic', { project_id: projectId, query, limit }),
  
  // Code search
  codeSearch: (projectId, codeSnippet, limit = 10) => 
    api.post('/search/code', { project_id: projectId, code_snippet: codeSnippet, limit }),
  
  // Get similar code
  getSimilarCode: (chunkId, limit = 5) => 
    api.get(`/search/similar/${chunkId}?limit=${limit}`),
  
  // Search history
  getSearchHistory: (projectId) => api.get(`/search/history/${projectId}`)
}