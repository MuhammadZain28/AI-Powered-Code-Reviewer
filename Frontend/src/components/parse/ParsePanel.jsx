import React, { useState } from 'react'
import Card from '../ui/Card'
import Button from '../ui/Button'
import Input from '../ui/Input'
import { parseService } from '../../services/parseService'
import toast from 'react-hot-toast'

const ParsePanel = ({ projectId, onParseStart }) => {
  const [repoUrl, setRepoUrl] = useState('')
  const [branch, setBranch] = useState('main')
  const [loading, setLoading] = useState(false)

  const handleParse = async () => {
    if (!repoUrl) {
      toast.error('Please enter a repository URL')
      return
    }

    setLoading(true)
    try {
      const result = await parseService.parseRepository(projectId, repoUrl, branch)
      toast.success('Parsing started successfully!')
      onParseStart?.(result)
    } catch (error) {
      toast.error(error.message || 'Failed to start parsing')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card title="Parse Repository">
      <div className="space-y-4">
        <Input
          label="Repository URL"
          placeholder="https://github.com/username/repo"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          required
        />
        <Input
          label="Branch"
          placeholder="main"
          value={branch}
          onChange={(e) => setBranch(e.target.value)}
        />
        <Button onClick={handleParse} loading={loading} className="w-full">
          Start Parsing
        </Button>
      </div>
    </Card>
  )
}

export default ParsePanel