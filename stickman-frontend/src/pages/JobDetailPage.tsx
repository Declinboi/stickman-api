import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import {
  ArrowLeft,
  Download,
  CheckCircle,
  XCircle,
  Loader,
  Clock,
  Trash2,
} from "lucide-react";
import {
  clearCurrentJob,
  fetchJobById,
  deleteJob,
} from "../store/slices/jobsSlice";
import { useJobSocket } from "../hooks/useJobSocket";
import type { AppDispatch, RootState } from "../store";

export default function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();

  const { currentJob, isLoading } = useSelector(
    (state: RootState) => state.jobs,
  );

  // ← useState must be here, before any early returns
  const [isDeleting, setIsDeleting] = useState(false);

  useJobSocket(id ?? null);

  useEffect(() => {
    if (!id || id === "undefined") {
      navigate("/dashboard", { replace: true });
      return;
    }
    dispatch(clearCurrentJob());
    dispatch(fetchJobById(id));
  }, [id, dispatch, navigate]);

  useEffect(() => {
    if (
      currentJob?.status === "completed" &&
      !currentJob?.outputVideoUrl &&
      id
    ) {
      dispatch(fetchJobById(id));
    }
  }, [currentJob?.status, currentJob?.outputVideoUrl, id, dispatch]);

  const handleDelete = async () => {
    if (
      !currentJob ||
      !window.confirm("Delete this job? This cannot be undone.")
    )
      return;
    setIsDeleting(true);
    try {
      await dispatch(deleteJob(currentJob.id)).unwrap();
      navigate("/dashboard");
    } catch {
      setIsDeleting(false);
    }
  };

  // early returns AFTER all hooks
  if (isLoading || !currentJob) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="card animate-pulse h-64 bg-dark-700" />
      </div>
    );
  }

  const isProcessing = currentJob.status === "processing";
  const isCompleted = currentJob.status === "completed";
  const isFailed = currentJob.status === "failed";

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 animate-fade-in">
      <button
        onClick={() => navigate("/dashboard")}
        className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors mb-6"
      >
        <ArrowLeft size={18} />
        Back to Dashboard
      </button>

      <div className="card">
        {/* Title row with delete button */}
        <div className="flex items-start justify-between mb-1">
          <h1 className="text-xl font-bold text-white truncate flex-1">
            {currentJob.originalFilename}
          </h1>
          <button
            onClick={handleDelete}
            disabled={isDeleting || isProcessing}
            className="ml-4 flex items-center gap-1.5 text-sm text-red-400
                       hover:text-red-300 bg-red-400/10 hover:bg-red-400/20
                       px-3 py-1.5 rounded-lg transition-all duration-200
                       disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Trash2 size={15} />
            {isDeleting ? "Deleting..." : "Delete"}
          </button>
        </div>

        <p className="text-gray-500 text-sm mb-6">
          Created{" "}
          {new Date(currentJob.createdAt).toLocaleDateString("en-US", {
            weekday: "long",
            day: "numeric",
            month: "long",
            year: "numeric",
          })}
        </p>

        {/* Status */}
        <div className="flex items-center gap-3 mb-6">
          {currentJob.status === "pending" && (
            <span className="flex items-center gap-2 text-yellow-400 bg-yellow-400/10 px-4 py-2 rounded-full text-sm">
              <Clock size={16} /> Pending
            </span>
          )}
          {isProcessing && (
            <span className="flex items-center gap-2 text-blue-400 bg-blue-400/10 px-4 py-2 rounded-full text-sm">
              <Loader size={16} className="animate-spin" /> Processing
            </span>
          )}
          {isCompleted && (
            <span className="flex items-center gap-2 text-green-400 bg-green-400/10 px-4 py-2 rounded-full text-sm">
              <CheckCircle size={16} /> Completed
            </span>
          )}
          {isFailed && (
            <span className="flex items-center gap-2 text-red-400 bg-red-400/10 px-4 py-2 rounded-full text-sm">
              <XCircle size={16} /> Failed
            </span>
          )}
        </div>

        {/* Progress bar */}
        {isProcessing && (
          <div className="mb-6">
            <div className="flex justify-between text-sm text-gray-400 mb-2">
              <span>Converting to stickman...</span>
              <span>{currentJob.progress}%</span>
            </div>
            <div className="w-full bg-dark-600 rounded-full h-3">
              <div
                className="bg-primary-500 h-3 rounded-full transition-all duration-500"
                style={{ width: `${currentJob.progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Error message */}
        {isFailed && currentJob.errorMessage && (
          <div className="bg-red-400/10 border border-red-400/20 rounded-xl p-4 mb-6">
            <p className="text-red-400 text-sm">{currentJob.errorMessage}</p>
          </div>
        )}

        {/* Output video player */}
        {isCompleted && currentJob.outputVideoUrl && (
          <div className="mt-2">
            <h2 className="text-white font-semibold mb-3">Stickman Output</h2>
            <video
              controls
              className="w-full rounded-xl bg-black"
              src={currentJob.outputVideoUrl}
            />

            <a
              href={currentJob.outputVideoUrl}
              download
              target="_blank"
              rel="noreferrer"
              className="btn-primary flex items-center justify-center gap-2 mt-4 w-full"
            >
              <Download size={18} />
              Download Stickman Video
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
