import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { parseService } from '../services/parseService'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Loader from '../components/ui/Loader'
import ParseProgress from '../components/parse/ParseProgress'
import ChunkList from '../components/parse/ChunkList'
import EmbeddingStats from '../components/parse/EmbeddingStats'
import toast from 'react-hot-toast'

const ParseProject = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const [parsingStatus, setParsingStatus] = useState(null)
  const [chunks, setChunks] = useState([])
  const [embeddingStats, setEmbeddingStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [polling, setPolling] = useState(null)

  useEffect(() => {
    loadData()
    startPolling()

    return () => {
      if (polling) clearInterval(polling)
    }
  }, [id])

  const loadData = async () => {
    try {
      const [chunksData, statsData] = await Promise.all([
        parseService.getProjectChunks(id),
        parseService.getEmbeddingStats(id)
      ])
      setChunks(chunksData)
      setEmbeddingStats(statsData)
    } catch (error) {
      console.error('Failed to load data:', error)
      toast.error('Failed to load parsing data')
    } finally {
      setLoading(false)
    }
  }

  const startPolling = () => {
    const interval = setInterval(async () => {
      try {
        const status = await parseService.getParsingStatus(id)
        setParsingStatus(status)
        
        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(interval)
          if (status.status === 'completed') {
            toast.success('Parsing completed successfully!')
            await loadData()
          } else {
            toast.error('Parsing failed')
          }
        }
      } catch (error) {
        console.error('Failed to get parsing status:', error)
      }
    }, 3000)
    
    setPolling(interval)
  }

  const handleReindex = async () => {
    try {
      await parseService.reindexProject(id)
      toast.success('Re-indexing started')
      startPolling()
    } catch (error) {
      toast.error(error.message || 'Failed to start re-indexing')
    }
  }

  if (loading) {
    return <Loader fullScreen />
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Parse Project</h1>
          <p className="text-gray-600 mt-1">
            Analyze and index your codebase for semantic search
          </p>
        </div>
        <div className="flex space-x-3">
          <Button variant="outline" onClick={() => navigate(`/projects/${id}`)}>
            Back to Project
          </Button>
          <Button onClick={handleReindex}>
            Re-index Project
          </Button>
        </div>
      </div>

      {parsingStatus && parsingStatus.status !== 'completed' && (
        <ParseProgress status={parsingStatus} />
      )}

      {embeddingStats && <EmbeddingStats stats={embeddingStats} />}

      <Card title="Code Chunks">
        <ChunkList chunks={chunks} />
      </Card>
    </div>
  )
}

export default ParseProject