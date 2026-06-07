import React, { useState } from 'react'
import { useProjects } from '../hooks/useProjects'
import ProjectCard from '../components/projects/ProjectCard'
import CreateProjectModal from '../components/projects/CreateProjectModal'
import Button from '../components/ui/Button'
import Loader from '../components/ui/Loader'
import EmptyState from '../components/ui/EmptyState'
import toast from 'react-hot-toast'

// Heroicons v1 imports
import { PlusIcon, SearchIcon, FilterIcon } from '@heroicons/react/outline'

const Projects = () => {
  const { projects, loading, createProject, deleteProject, setCurrentProject } = useProjects()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')

  const filteredProjects = projects.filter(project => {
    const matchesSearch = project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          (project.description && project.description.toLowerCase().includes(searchTerm.toLowerCase()))
    const matchesStatus = filterStatus === 'all' || project.status === filterStatus
    return matchesSearch && matchesStatus
  })

  const handleCreateProject = async (projectData) => {
    try {
      await createProject(projectData)
      toast.success('Project created successfully!')
      setIsModalOpen(false)
    } catch (error) {
      toast.error(error.message || 'Failed to create project')
      throw error
    }
  }

  const handleDeleteProject = async (projectId) => {
    if (window.confirm('Are you sure you want to delete this project?')) {
      try {
        await deleteProject(projectId)
        toast.success('Project deleted successfully')
      } catch (error) {
        toast.error(error.message || 'Failed to delete project')
      }
    }
  }

  if (loading) {
    return <Loader fullScreen />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-dark-text">Projects</h1>
          <p className="text-dark-textSecondary mt-1">Manage and analyze your code repositories with AI</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="flex items-center space-x-2">
          <PlusIcon className="w-5 h-5" />
          <span>New Project</span>
        </Button>
      </div>

      {/* Search and Filter */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1 relative">
          <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-dark-textSecondary" />
          <input
            type="text"
            placeholder="Search projects by name or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input pl-10"
          />
        </div>
        <div className="flex items-center space-x-2">
          <FilterIcon className="w-5 h-5 text-dark-textSecondary" />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="input w-40"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="processing">Processing</option>
            <option value="archived">Archived</option>
          </select>
        </div>
      </div>

      {/* Projects Grid */}
      {filteredProjects.length === 0 ? (
        <EmptyState
          title="No projects found"
          description={searchTerm ? "Try adjusting your search or filter" : "Get started by creating your first project"}
          action={
            !searchTerm && (
              <Button onClick={() => setIsModalOpen(true)}>
                <PlusIcon className="w-5 h-5 mr-2" />
                Create your first project
              </Button>
            )
          }
          icon={
            <svg className="mx-auto h-24 w-24 text-dark-textSecondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          }
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredProjects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onDelete={handleDeleteProject}
              onSelect={setCurrentProject}
            />
          ))}
        </div>
      )}

      {/* Create Project Modal */}
      <CreateProjectModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreate={handleCreateProject}
      />
    </div>
  )
}

export default Projects