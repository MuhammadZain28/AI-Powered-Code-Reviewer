import React, { createContext, useContext, useState, useCallback } from 'react'
import { projectService } from '../services/projectService'
import { parseService } from '../services/parseService'

const ProjectContext = createContext()

export const useProject = () => {
  const context = useContext(ProjectContext)
  if (!context) {
    throw new Error('useProject must be used within ProjectProvider')
  }
  return context
}

export const ProjectProvider = ({ children }) => {
  const [projects, setProjects] = useState([]) // Initialize as empty array
  const [currentProject, setCurrentProject] = useState(null)
  const [loading, setLoading] = useState(false)

  const loadProjects = useCallback(async () => {
    setLoading(true)
    try {
      const data = await projectService.getAllProjects()
      console.log("Loaded projects:", data)  // Debugging statement
      setProjects(Array.isArray(data) ? data : [])
    } catch (error) {
      console.error('Failed to load projects:', error)
      setProjects([]) // Set empty array on error
    } finally {
      setLoading(false)
    }
  }, [])

  const createProject = async (projectData) => {
    try {
      const newProject = await projectService.createProject(projectData)
      setProjects(prev => Array.isArray(prev) ? [...prev, newProject] : [newProject])
      return newProject
    } catch (error) {
      console.error('Failed to create project:', error)
      throw error
    }
  }

  const updateProject = async (projectId, projectData) => {
    try {
      const updated = await projectService.updateProject(projectId, projectData)
      setProjects(prev => Array.isArray(prev) 
        ? prev.map(p => p.id === projectId ? updated : p)
        : [updated]
      )
      if (currentProject?.id === projectId) {
        setCurrentProject(updated)
      }
      return updated
    } catch (error) {
      console.error('Failed to update project:', error)
      throw error
    }
  }

  const deleteProject = async (projectId) => {
    try {
      await projectService.deleteProject(projectId)
      setProjects(prev => Array.isArray(prev) 
        ? prev.filter(p => p.id !== projectId)
        : []
      )
      if (currentProject?.id === projectId) {
        setCurrentProject(null)
      }
    } catch (error) {
      console.error('Failed to delete project:', error)
      throw error
    }
  }

  const setCurrentProjectWithParse = async (project) => {
    setCurrentProject(project)
    console.log("Selected project:", project)  // Debugging statement
    if (project?.path) {
      try {
        console.log("Parsing project with path:", project.path)  // Debugging statement
        await parseService.parseChanges(project.id, project.path)
      } catch (error) {
        console.error('Failed to parse changes:', error)
      }
    }
  }

  return (
    <ProjectContext.Provider value={{
      projects: Array.isArray(projects) ? projects : [], // Always return array
      currentProject,
      loading,
      loadProjects,
      setCurrentProject,
      setCurrentProjectWithParse,
      createProject,
      updateProject,
      deleteProject
    }}>
      {children}
    </ProjectContext.Provider>
  )
}