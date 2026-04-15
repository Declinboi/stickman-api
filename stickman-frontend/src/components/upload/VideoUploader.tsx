import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Swords, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import api from "../../api/axios";
import type { AppDispatch, RootState } from "../../store";
import {
  uploadStarted,
  uploadFinished,
  uploadFailed,
  resetUpload,
} from "../../store/slices/uploadSlice";
import { addJob } from "../../store/slices/jobsSlice";

const PLACEHOLDER = `Fighter 1 walks forward, Fighter 2 blocks.
Fighter 1 jabs, Fighter 2 dodges.
Fighter 2 kicks, Fighter 1 blocks.
Fighter 1 uppercut, Fighter 2 knockback.
Fighter 2 jump kick, Fighter 1 dodge.
Fighter 1 sweep kick, Fighter 2 falls.
Fighter 1 taunts.`;

export default function VideoUploader() {
  const dispatch = useDispatch<AppDispatch>();
  const { isUploading } = useSelector((state: RootState) => state.upload);
  const [description, setDescription] = useState("");

  const handleGenerate = async () => {
    const trimmed = description.trim();
    if (!trimmed) {
      toast.error("Please describe the fight sequence first.");
      return;
    }

    dispatch(uploadStarted());

    try {
      const res = await api.post("/upload/generate", { description: trimmed });

      console.log("Generate response:", res.data);

      const job = {
        ...(res.data.job ?? res.data),
        id: res.data.job?.id ?? res.data.id ?? res.data.jobId,
      };

      if (!job?.id) {
        console.error("Response missing job ID:", res.data);
        toast.error("Request succeeded but job ID is missing.");
        dispatch(uploadFailed("Missing job ID in response"));
        return;
      }

      dispatch(uploadFinished());
      dispatch(addJob(job));
      toast.success("Fight queued! Generating animation...");
      setDescription("");
    } catch (err: any) {
      const msg = err.response?.data?.message ?? "Generation failed";
      dispatch(uploadFailed(msg));
      toast.error(msg);
    }
  };

  return (
    <div className="card animate-slide-up">
      <h2 className="text-lg font-semibold text-white mb-1">
        Describe Your Fight
      </h2>
      <p className="text-gray-500 text-sm mb-4">
        Write the sequence of moves for each fighter.
      </p>

      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder={PLACEHOLDER}
        rows={9}
        disabled={isUploading}
        className="w-full bg-dark-700 border border-dark-500 rounded-xl
                   px-4 py-3 text-gray-200 text-sm placeholder-gray-600
                   focus:outline-none focus:border-primary-500
                   resize-none transition-colors duration-200
                   disabled:opacity-50"
      />

      <button
        onClick={handleGenerate}
        disabled={isUploading || !description.trim()}
        className="btn-primary w-full mt-4 flex items-center justify-center gap-2
                   disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isUploading ? (
          <>
            <Loader2 size={18} className="animate-spin" />
            Generating...
          </>
        ) : (
          <>
            <Swords size={18} />
            Generate Fight
          </>
        )}
      </button>
    </div>
  );
}
