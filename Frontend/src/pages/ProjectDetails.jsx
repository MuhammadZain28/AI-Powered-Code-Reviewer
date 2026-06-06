import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useProjects } from '../hooks/useProjects'
import { projectService } from '../services/projectService'
import { parseService } from '../services/parseService'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import Loader from '../components/ui/Loader'
import { formatDate, formatFileSize } from '../utils/helpers'
import { getProjectStatusColor } from '../utils/statusColors'
import toast from 'react-hot-toast'

const ProjectDetails = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { projects } = useProjects()
  const [project, setProject] = useState(null)
  const [files, setFiles] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [parsing, setParsing] = useState(false)

  useEffect(() => {
    loadProjectDetails()
  }, [id])

  const loadProjectDetails = async () => {
    setLoading(true)
    try {
      const [projectData, filesData, statsData] = await Promise.all([
        projectService.getProject(id),
        projectService.getProjectFiles(id),
        projectService.getProjectStats(id)
      ])
      setProject(projectData)
      setFiles(filesData)
      setStats(statsData)
    } catch (error) {
      toast.error('Failed to load project details')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleParseProject = async () => {
    if (!project?.repo_url) {
      toast.error('No repository URL configured for this project')
      return
    }

    setParsing(true)
    try {
      await parseService.parseRepository(id, project.repo_url)
      toast.success('Parsing started successfully!')
      navigate(`/projects/${id}/parse`)
    } catch (error) {
      toast.error(error.message || 'Failed to start parsing')
    } finally {
      setParsing(false)
    }
  }

  if (loading) {
    return <Loader fullScreen />
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900">Project not found</h2>
        <Button onClick={() => navigate('/projects')} className="mt-4">
          Back to Projects
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
          <p className="text-gray-600 mt-1">{project.description}</p>
          <div className="flex items-center space-x-3 mt-3">
            <Badge variant={getProjectStatusColor(project.status)}>
              {project.status}
            </Badge>
            <span className="text-sm text-gray-500">
              Created {formatDate(project.created_at)}
            </span>
          </div>
        </div>
        <div className="flex space-x-3">
          {project.repo_url && project.status !== 'processing' && (
            <Button onClick={handleParseProject} loading={parsing}>
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              Parse Repository
            </Button>
          )}
          <Button variant="outline" onClick={() => navigate('/projects')}>
            Back
          </Button>
        </div>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-600">Total Files</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total_files || 0}</p>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-600">Code Chunks</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total_chunks || 0}</p>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-600">Reviews</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total_reviews || 0}</p>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-600">Issues Found</p>
              <p className="text-2xl font-bold text-red-600">{stats.total_issues || 0}</p>
            </div>
          </Card>
        </div>
      )}

      {/* Files List */}
      <Card title="Repository Files">
        {files.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            No files have been parsed yet. Click "Parse Repository" to start analyzing your code.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    File Path
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Size
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Chunks
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Modified
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {files.map((file) => (
                  <tr key={file.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {file.path}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {formatFileSize(file.size)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {file.chunk_count || 0}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {formatDate(file.modified_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}

export default ProjectDetails