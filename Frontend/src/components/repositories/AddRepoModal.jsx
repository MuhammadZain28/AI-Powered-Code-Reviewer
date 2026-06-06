import { useState } from "react";
import Modal from "../ui/Modal";
import Button from "../ui/Button";

export default function AddRepoModal({ isOpen, onClose, onAdd }) {
  const [url, setUrl] = useState("");

  const handleSubmit = () => {
    if (!url) return;

    const newRepo = {
      name: url.split("/").pop(),
      url,
      status: "Processing",
      language: "Detecting...",
      lastAnalyzed: "Just now",
      confidence: "N/A",
    };

    onAdd(newRepo);
    setUrl("");
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add GitHub Repository">

      <div className="space-y-4">

        <input
          type="text"
          placeholder="Enter GitHub repo URL..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="w-full px-4 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white outline-none focus:border-blue-500"
        />

        <div className="flex justify-end gap-3">

          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>

          <Button variant="primary" onClick={handleSubmit}>
            Add Repository
          </Button>

        </div>

      </div>

    </Modal>
  );
}