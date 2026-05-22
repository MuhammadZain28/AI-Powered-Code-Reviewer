function Login() {
  return (
    <div className="bg-slate-950 min-h-screen flex items-center justify-center">
      <div className="bg-slate-900 p-10 rounded-2xl w-96">
        <h1 className="text-white text-3xl font-bold mb-6">
          Login
        </h1>

        <input
          type="email"
          placeholder="Enter email"
          className="w-full p-3 rounded-lg mb-4 bg-slate-800 text-white"
        />

        <input
          type="password"
          placeholder="Enter password"
          className="w-full p-3 rounded-lg mb-4 bg-slate-800 text-white"
        />

        <button className="w-full bg-blue-600 py-3 rounded-lg text-white">
          Login
        </button>
      </div>
    </div>
  );
}

export default Login;