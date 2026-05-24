function Navbar() {
  return (
    <nav className="bg-slate-950 border-b border-slate-800 text-white px-8 py-4 flex justify-between items-center">
      <h1 className="text-3xl font-bold text-blue-500">
        AI Code Review System
      </h1>

      <button className="bg-blue-600 hover:bg-blue-700 px-5 py-2 rounded-lg">
        Login
      </button>
    </nav>
  );
}

export default Navbar;