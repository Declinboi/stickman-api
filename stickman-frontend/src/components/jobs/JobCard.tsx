import { Link } from "react-router-dom";
import {
  Clock,
  CheckCircle,
  XCircle,
  Loader,
  ChevronRight,
} from "lucide-react";
import type { Job } from "../../types";

const statusConfig = {
  pending: {
    icon: <Clock size={16} />,
    color: "text-yellow-400",
    bg: "bg-yellow-400/10",
    label: "Pending",
  },
  processing: {
    icon: <Loader size={16} className="animate-spin" />,
    color: "text-blue-400",
    bg: "bg-blue-400/10",
    label: "Processing",
  },
  completed: {
    icon: <CheckCircle size={16} />,
    color: "text-green-400",
    bg: "bg-green-400/10",
    label: "Completed",
  },
  failed: {
    icon: <XCircle size={16} />,
    color: "text-red-400",
    bg: "bg-red-400/10",
    label: "Failed",
  },
};

export default function JobCard({ job }: { job: Job }) {
  const cfg = statusConfig[job.status];

  return (
    <Link to={`/jobs/${job.id}`}>
      <div
        className="card hover:border-dark-400 transition-all
                      duration-200 cursor-pointer animate-fade-in"
      >
        <div className="flex items-center justify-between">
          <div className="flex-1 min-w-0">
            {/* Filename */}
            <p className="text-white font-medium truncate">
              {job.originalFilename}
            </p>

            {/* Date */}
            <p className="text-gray-500 text-sm mt-1">
              {new Date(job.createdAt).toLocaleDateString("en-US", {
                day: "numeric",
                month: "short",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
          </div>

          <div className="flex items-center gap-3 ml-4">
            {/* Status badge */}
            <span
              className={`flex items-center gap-1.5 text-xs
                              font-medium px-3 py-1 rounded-full
                              ${cfg.color} ${cfg.bg}`}
            >
              {cfg.icon}
              {cfg.label}
            </span>
            <ChevronRight size={16} className="text-gray-600" />
          </div>
        </div>

        {/* Progress bar for processing jobs */}
        {job.status === "processing" && (
          <div className="mt-4">
            <div
              className="flex justify-between text-xs
                            text-gray-500 mb-1"
            >
              <span>Processing...</span>
              <span>{job.progress}%</span>
            </div>
            <div className="w-full bg-dark-600 rounded-full h-1.5">
              <div
                className="bg-primary-500 h-1.5 rounded-full
                           transition-all duration-500"
                style={{ width: `${job.progress}%` }}
              />
            </div>
          </div>
        )}
      </div>
    </Link>
  );
}
