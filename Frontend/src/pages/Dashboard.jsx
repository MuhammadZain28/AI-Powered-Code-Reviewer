import React, { useEffect, useState } from 'react'
import StatsCard from '../components/dashboard/StatsCard'
import ActivityChart from '../components/dashboard/ActivityChart'
import RecentProjects from '../components/dashboard/RecentProjects'
import { useProjects } from '../hooks/useProjects'
import Loader from '../components/ui/Loader'

const Dashboard = () => {
  const { projects, loading } = useProjects()
  const [stats, setStats] = useState({
    totalProjects: 0,
    totalReviews: 0,
    totalFiles: 0,
    avgReviewScore: 0
  })

  useEffect(() => {
    // Calculate stats from projects
    if (projects && projects.length > 0) {
      setStats({
        totalProjects: projects.length,
        totalReviews: projects.reduce((sum, p) => sum + (p.review_count || 0), 0),
        totalFiles: projects.reduce((sum, p) => sum + (p.file_count || 0), 0),
        avgReviewScore: 7.5 // Placeholder
      })
    }
  }, [projects])

  const chartData = [
    { date: 'Jan', reviews: 45, projects: 12 },
    { date: 'Feb', reviews: 52, projects: 15 },
    { date: 'Mar', reviews: 61, projects: 18 },
    { date: 'Apr', reviews: 58, projects: 20 },
    { date: 'May', reviews: 73, projects: 24 },
    { date: 'Jun', reviews: 85, projects: 28 }
  ]

  if (loading) {
    return <Loader fullScreen />
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Welcome back! Here's what's happening with your projects.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total Projects"
          value={stats.totalProjects}
          trend={12}
          icon={<svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>}
        />
        <StatsCard
          title="Total Reviews"
          value={stats.totalReviews}
          trend={8}
          color="green"
          icon={<svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>}
        />
        <StatsCard
          title="Files Analyzed"
          value={stats.totalFiles}
          trend={-3}
          color="yellow"
          icon={<svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>}
        />
        <StatsCard
          title="Avg Review Score"
          value={`${stats.avgReviewScore}/10`}
          trend={5}
          color="red"
          icon={<svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
          </svg>}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ActivityChart data={chartData} />
        </div>
        <div>
          <RecentProjects projects={projects} />
        </div>
      </div>
    </div>
  )
}

export default Dashboard