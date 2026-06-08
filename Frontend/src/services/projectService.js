import api from './api'

// Mock data for development
const mockProjects = [
  {
    id: 1,
    name: 'E-Commerce Platform',
    description: 'Full-stack e-commerce application with React and Node.js',
    status: 'active',
    file_count: 245,
    review_count: 67,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    repo_url: 'https://github.com/example/ecommerce'
  },
  {
    id: 2,
    name: 'AI Code Assistant',
    description: 'AI-powered code review and assistance tool',
    status: 'processing',
    file_count: 89,
    review_count: 12,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    repo_url: 'https://github.com/example/ai-assistant'
  },
  {
    id: 3,
    name: 'Mobile Banking App',
    description: 'React Native mobile banking application',
    status: 'active',
    file_count: 412,
    review_count: 145,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    repo_url: 'https://github.com/example/mobile-banking'
  }
]

export const projectService = {
  // Get all projects
  getAllProjects: async () => {
    try {
      // Try to fetch from API first
      const response = await api.get(`/projects`)
      console.log("API response for projects:", response)  // Debugging statement
      return Array.isArray(response) ? response : []
    } catch (error) {
      // Return mock data if API fails (for development)
      console.warn('Using mock project data:', error.message)
      return mockProjects
    }
  },
  
  // Get single project
  getProject: async (projectId) => {
    try {
      const response = await api.get(`/projects/${projectId}`)
      console.log("API response for project:", response)  // Debugging statement
      return response
    } catch (error) {
      // Return mock project if API fails
      const mockProject = mockProjects.find(p => p.id === parseInt(projectId))
      if (mockProject) return mockProject
      throw error
    }
  },
  
  // Create project
  createProject: async (projectData) => {
    try {
      console.log("Creating project with data:", projectData)  // Debugging statement
      const response = await api.post('/projects', projectData)
      console.log("API response for project creation:", response)  // Debugging statement
      return response.data
    } catch (error) {
      // Mock creation for development
      const newProject = {
        id: mockProjects.length + 1,
        ...projectData,
        status: 'active',
        file_count: 0,
        review_count: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
      mockProjects.push(newProject)
      return newProject
    }
  },
  
  // Update project
  updateProject: async (projectId, projectData) => {
    try {
      const response = await api.put(`/projects/${projectId}`, projectData)
      return response
    } catch (error) {
      // Mock update for development
      const index = mockProjects.findIndex(p => p.id === parseInt(projectId))
      if (index !== -1) {
        mockProjects[index] = { ...mockProjects[index], ...projectData }
        return mockProjects[index]
      }
      throw error
    }
  },
  
  // Delete project
  deleteProject: async (projectId) => {
    try {
      await api.delete(`/projects/${projectId}`)
      return { success: true }
    } catch (error) {
      // Mock delete for development
      const index = mockProjects.findIndex(p => p.id === parseInt(projectId))
      if (index !== -1) {
        mockProjects.splice(index, 1)
      }
      return { success: true }
    }
  },
  
  // Get project files
  getProjectFiles: async (projectId) => {
    try {
      const response = await api.get(`/projects/${projectId}/files`)
      console.log("API response for project files:", response)  // Debugging statement
      return Array.isArray(response) ? response : []
    } catch (error) {
      console.warn('Using mock files data')
      return [
        { id: 1, path: 'src/index.js', size: 2450, chunk_count: 5, modified_at: new Date().toISOString() },
        { id: 2, path: 'src/App.js', size: 8900, chunk_count: 12, modified_at: new Date().toISOString() },
        { id: 3, path: 'src/utils/helpers.js', size: 3400, chunk_count: 8, modified_at: new Date().toISOString() }
      ]
    }
  },
  
  // Get project statistics
  getProjectStats: async (projectId) => {
    try {
      const response = await api.get(`/projects/${projectId}/stats`)
      return response
    } catch (error) {
      return {
        total_files: 156,
        total_chunks: 423,
        total_reviews: 89,
        total_issues: 45
      }
    }
  }
}