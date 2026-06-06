import React from 'react'
import Badge from '../ui/Badge'

const SimilarityBadge = ({ score }) => {
  const getColor = () => {
    if (score > 0.8) return 'success'
    if (score > 0.6) return 'info'
    if (score > 0.4) return 'warning'
    return 'default'
  }

  return (
    <Badge variant={getColor()}>
      {(score * 100).toFixed(0)}% match
    </Badge>
  )
}

export default SimilarityBadge