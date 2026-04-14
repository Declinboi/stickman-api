import { useEffect } from "react";
import { useDispatch } from "react-redux";
import { io } from "socket.io-client";
import type { AppDispatch } from "../store";
import {
  updateJobProgress,
  updateJobCompleted,
  updateJobFailed,
} from "../store/slices/jobsSlice";
import toast from "react-hot-toast";

const SOCKET_URL = import.meta.env.VITE_API_URL ?? "http://localhost:3000";

export function useJobSocket(jobId: string | null) {
  const dispatch = useDispatch<AppDispatch>();

  useEffect(() => {
    if (!jobId || jobId === "undefined") return; // guard against string "undefined" too

    const token = localStorage.getItem("token");

    const socket = io(`${SOCKET_URL}/video`, {
      transports: ["websocket"],
      auth: { token }, // pass JWT so backend can authenticate the socket
    });

    socket.on("connect", () => {
      socket.emit("subscribe_job", { jobId });
    });

    socket.on("connect_error", (err) => {
      console.error("Socket connection error:", err.message);
    });

    socket.on("job_progress", (data) => {
      dispatch(
        updateJobProgress({
          jobId: data.jobId,
          progress: data.progress,
          status: data.status,
        }),
      );
    });

    socket.on("job_completed", (data) => {
      dispatch(
        updateJobCompleted({
          jobId: data.jobId,
          outputVideoUrl: data.outputVideoUrl,
        }),
      );
      toast.success("Your stickman video is ready!");
    });

    socket.on("job_failed", (data) => {
      dispatch(
        updateJobFailed({
          jobId: data.jobId,
          errorMessage: data.errorMessage,
        }),
      );
      toast.error("Processing failed. Please try again.");
    });

    return () => {
      socket.emit("unsubscribe_job", { jobId });
      socket.disconnect();
    };
  }, [jobId, dispatch]);
}
