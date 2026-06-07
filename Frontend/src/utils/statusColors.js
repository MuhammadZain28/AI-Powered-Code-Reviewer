export const getSeverityColor = (severity) => {
  console.log("Getting color for severity:", severity)
  const colors = {
    High: 'bg-red-100 text-red-800 border-red-200',
    Medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    Low: 'bg-green-100 text-green-800 border-green-200'
  }
  return colors[severity] || colors.Low
}

export const getProjectStatusColor = (status) => {
  const colors = {
    active: 'bg-green-100 text-green-800',
    archived: 'bg-gray-100 text-gray-800',
    processing: 'bg-blue-100 text-blue-800'
  }
  return colors[status] || colors.active
}