import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Film } from "lucide-react";
import VideoUploader from "../components/upload/VideoUploader";
import JobCard from "../components/jobs/JobCard";
import { fetchJobs } from "../store/slices/jobsSlice";
import type { AppDispatch, RootState } from "../store";
import { useAuth } from "../hooks/useAuth";

export default function DashboardPage() {
  const dispatch = useDispatch<AppDispatch>();
  const { jobs, isLoading } = useSelector((state: RootState) => state.jobs);
  const { user } = useAuth();

  useEffect(() => {
    dispatch(fetchJobs());
  }, [dispatch]);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">
          Welcome back,{" "}
          <span className="text-primary-400">
            {user?.username ?? "Fighter"}
          </span>
        </h1>
        <p className="text-gray-500 mt-1">
          Describe a fight sequence and watch it come to life as stickman
          animation.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <VideoUploader />
        </div>

        <div className="lg:col-span-2">
          <h2 className="text-lg font-semibold text-white mb-4">
            Your Animations
          </h2>

          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="card animate-pulse h-20 bg-dark-700" />
              ))}
            </div>
          ) : jobs.length === 0 ? (
            <div className="card text-center py-16">
              <Film size={48} className="mx-auto text-gray-700 mb-3" />
              <p className="text-gray-500">
                No animations yet. Describe a fight to get started.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {jobs.map((job) => (
                <JobCard key={job.id} job={job} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
