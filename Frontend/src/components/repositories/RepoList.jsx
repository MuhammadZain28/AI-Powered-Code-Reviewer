import RepoCard from "./RepoCard";

export default function RepoList({ repos, onAnalyze }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">

      {repos.map((repo, index) => (
        <RepoCard
          key={index}
          repo={repo}
          onAnalyze={onAnalyze}
        />
      ))}

    </div>
  );
}