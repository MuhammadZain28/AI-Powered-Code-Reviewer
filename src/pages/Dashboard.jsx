import Sidebar from "../components/layout/Sidebar";
import Navbar from "../components/layout/Navbar";
import StatsCard from "../components/dashboard/StatsCard";

function Dashboard() {
  return (
    <div className="bg-slate-950 min-h-screen">
      <Navbar />

      <div className="flex">
        <Sidebar />

        <div className="flex-1 p-8">
          <h2 className="text-white text-3xl font-bold mb-8">
            Dashboard Overview
          </h2>

          <div className="flex gap-6 flex-wrap">
            <StatsCard title="Repositories" value="12" />
            <StatsCard title="Bugs Found" value="48" />
            <StatsCard title="AI Suggestions" value="126" />
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;