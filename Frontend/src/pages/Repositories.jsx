import Navbar from "../components/layout/Navbar";
import Sidebar from "../components/layout/Sidebar";

function Repositories() {
  return (
    <div className="bg-slate-950 min-h-screen">
      <Navbar />

      <div className="flex">
        <Sidebar />

        <div className="flex-1 p-8 text-white">
          <h1 className="text-4xl font-bold mb-6">
            Repositories
          </h1>

          <div className="bg-slate-900 p-6 rounded-2xl">
            <p>
              Repository management page
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Repositories;