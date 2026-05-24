import { NavLink } from "react-router-dom";

function Sidebar() {
  return (
    <div className="bg-slate-900 text-white w-64 min-h-screen p-5">
      <h2 className="text-2xl font-bold mb-10">
        Dashboard
      </h2>

      <ul className="space-y-4">
        <li>
          <NavLink
            to="/"
            className={({ isActive }) =>
              isActive
                ? "block bg-blue-600 p-3 rounded-lg"
                : "block hover:bg-slate-800 p-3 rounded-lg"
            }
          >
            Dashboard
          </NavLink>
        </li>

        <li>
          <NavLink
            to="/repositories"
            className={({ isActive }) =>
              isActive
                ? "block bg-blue-600 p-3 rounded-lg"
                : "block hover:bg-slate-800 p-3 rounded-lg"
            }
          >
            Repositories
          </NavLink>
        </li>

        <li>
          <NavLink
            to="/reviews"
            className={({ isActive }) =>
              isActive
                ? "block bg-blue-600 p-3 rounded-lg"
                : "block hover:bg-slate-800 p-3 rounded-lg"
            }
          >
            AI Reviews
          </NavLink>
        </li>

        <li>
          <NavLink
            to="/login"
            className={({ isActive }) =>
              isActive
                ? "block bg-blue-600 p-3 rounded-lg"
                : "block hover:bg-slate-800 p-3 rounded-lg"
            }
          >
            Login
          </NavLink>
        </li>
      </ul>
    </div>
  );
}

export default Sidebar;