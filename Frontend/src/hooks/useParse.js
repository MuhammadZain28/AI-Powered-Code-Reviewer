import { useState, useCallback } from 'react'
import { parseService } from '../services/parseService'
import toast from 'react-hot-toast'

export const useParse = (projectId) => {
  const [parsing, setParsing] = useState(false)
  const [status, setStatus] = useState(null)
  const [chunks, setChunks] = useState([])
  const [embeddingStats, setEmbeddingStats] = useState(null)
  const [loading, setLoading] = useState(false)

  const startParsing = useCallback(async (repoUrl, branch = 'main') => {
    setParsing(true)
    try {
      const result = await parseService.parseRepository(projectId, repoUrl, branch)
      toast.success('Parsing started successfully')
      return result
    } catch (error) {
      toast.error(error.message || 'Failed to start parsing')
      throw error
    } finally {
      setParsing(false)
    }
  }, [projectId])

  const getParsingStatus = useCallback(async () => {
    try {
      const data = await parseService.getParsingStatus(projectId)
      setStatus(data)
      return data
    } catch (error) {
      console.error('Failed to get parsing status:', error)
      return null
    }
  }, [projectId])

  const loadChunks = useCallback(async (page = 1, limit = 50) => {
    setLoading(true)
    try {
      const data = await parseService.getProjectChunks(projectId, page, limit)
      setChunks(data)
      return data
    } catch (error) {
      toast.error('Failed to load chunks')
      throw error
    } finally {
      setLoading(false)
    }
  }, [projectId])

  const loadEmbeddingStats = useCallback(async () => {
    try {
      const data = await parseService.getEmbeddingStats(projectId)
      setEmbeddingStats(data)
      return data
    } catch (error) {
      console.error('Failed to load embedding stats:', error)
      return null
    }
  }, [projectId])

  const reindex = useCallback(async () => {
    setLoading(true)
    try {
      await parseService.reindexProject(projectId)
      toast.success('Re-indexing started')
    } catch (error) {
      toast.error(error.message || 'Failed to start re-indexing')
      throw error
    } finally {
      setLoading(false)
    }
  }, [projectId])

  const parseChanges = useCallback(async (project_id, repo_path) => {
    try {
      const result = await parseService.parseChanges(project_id, repo_path)
      toast.success('Changes parsed successfully')
      return result
    } catch (error) {
      toast.error(error.message || 'Failed to parse changes')
      throw error
    }
  }, [projectId])

  return {
    parsing,
    status,
    chunks,
    embeddingStats,
    loading,
    startParsing,
    getParsingStatus,
    loadChunks,
    loadEmbeddingStats,
    parseChanges,
    reindex
  }
}