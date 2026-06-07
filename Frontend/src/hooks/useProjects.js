import { useEffect } from 'react'
import { useProject } from '../context/ProjectContext'

export const useProjects = () => {
  const {
    projects,
    currentProject,
    loading,
    loadProjects,
    setCurrentProject,
    createProject,
    updateProject,
    deleteProject,
    setCurrentProjectWithParse
  } = useProject()

  useEffect(() => {
    loadProjects()
  }, [loadProjects])

  return {
    projects,
    currentProject,
    loading,
    setCurrentProject,
    createProject,
    updateProject,
    deleteProject,
    setCurrentProjectWithParse,
    refreshProjects: loadProjects
  }
}