import Badge from "../ui/Badge";
import Button from "../ui/Button";

export default function RepoCard({ repo, onAnalyze }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg hover:border-slate-700 transition-all">

      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-white font-semibold text-lg">
            {repo.name}
          </h2>
          <p className="text-slate-400 text-sm">
            {repo.url}
          </p>
        </div>

        <Badge
          text={repo.status}
          type={
            repo.status === "Done"
              ? "success"
              : repo.status === "Processing"
              ? "warning"
              : "default"
          }
        />
      </div>

      {/* Meta */}
      <div className="mt-4 flex gap-3 text-sm text-slate-400">
        <span>🧠 {repo.language}</span>
        <span>📅 {repo.lastAnalyzed}</span>
      </div>

      {/* Actions */}
      <div className="mt-5 flex justify-between items-center">
        
        <div className="text-xs text-slate-500">
          AI Confidence: {repo.confidence || "85%"}
        </div>

        <Button
          variant="primary"
          onClick={() => onAnalyze(repo)}
        >
          Run AI Review
        </Button>

      </div>
    </div>
  );
}