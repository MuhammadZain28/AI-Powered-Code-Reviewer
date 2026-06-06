import React from 'react'
import Badge from '../ui/Badge'
import { getSeverityColor } from '../../utils/statusColors'

const SeverityBadge = ({ severity }) => {
  return (
    <Badge variant={getSeverityColor(severity)}>
      {severity.toUpperCase()}
    </Badge>
  )
}

export default SeverityBadge