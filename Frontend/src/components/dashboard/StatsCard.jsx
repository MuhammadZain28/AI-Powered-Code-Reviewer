function StatsCard({ title, value }) {
  return (
    <div className="bg-slate-900 text-white p-6 rounded-2xl shadow-lg w-72 border border-slate-800">
      <h2 className="text-slate-400 text-lg">
        {title}
      </h2>

      <p className="text-4xl font-bold mt-4">
        {value}
      </p>
    </div>
  );
}

export default StatsCard;