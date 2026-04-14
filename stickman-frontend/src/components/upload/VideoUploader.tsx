import { useCallback, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Upload, Film, X } from "lucide-react";
import toast from "react-hot-toast";
import api from "../../api/axios";
import type { AppDispatch, RootState } from "../../store";
import {
  uploadStarted,
  uploadProgress,
  uploadFinished,
  uploadFailed,
  resetUpload,
} from "../../store/slices/uploadSlice";
import { addJob } from "../../store/slices/jobsSlice";

const ACCEPTED_TYPES = [
  "video/mp4",
  "video/mpeg",
  "video/quicktime",
  "video/avi",
];
const MAX_SIZE_MB = 200;

export default function VideoUploader() {
  const dispatch = useDispatch<AppDispatch>();
  const { isUploading, uploadProgress: progress } = useSelector(
    (state: RootState) => state.upload,
  );

  const [dragOver, setDragOver] = useState(false);
  const [selected, setSelected] = useState<File | null>(null);

  const validate = (file: File): string | null => {
    if (!ACCEPTED_TYPES.includes(file.type))
      return "Only MP4, MOV, AVI and MPEG videos are supported.";
    if (file.size > MAX_SIZE_MB * 1024 * 1024)
      return `File must be under ${MAX_SIZE_MB}MB.`;
    return null;
  };

  const handleFile = (file: File) => {
    const err = validate(file);
    if (err) {
      toast.error(err);
      return;
    }
    setSelected(file);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, []);

  const handleUpload = async () => {
    if (!selected) return;

    dispatch(uploadStarted());
    const formData = new FormData();
    formData.append("video", selected);

    try {
      const res = await api.post("/upload/video", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) => {
          const pct = Math.round((e.loaded * 100) / (e.total ?? 1));
          dispatch(uploadProgress(pct));
        },
      });

      // Log this to confirm the shape of the response
      console.log("Upload response:", res.data);

      // Adjust depending on your API response shape:
      // If it's { job: {...} }  → use res.data.job
      // If it's the job directly → use res.data
      const job = {
        ...(res.data.job ?? res.data),
        id: res.data.job?.id ?? res.data.id ?? res.data.jobId,
      };

      if (!job?.id) {
        console.error("Upload response missing job ID:", res.data);
        toast.error("Upload succeeded but job ID is missing.");
        dispatch(uploadFailed("Missing job ID in response"));
        return;
      }

      dispatch(uploadFinished());
      dispatch(addJob(job));
      toast.success("Video uploaded! Processing has started.");
      setSelected(null);
    } catch (err: any) {
      const msg = err.response?.data?.message ?? "Upload failed";
      dispatch(uploadFailed(msg));
      toast.error(msg);
    }
  };

  return (
    <div className="card animate-slide-up">
      <h2 className="text-lg font-semibold text-white mb-4">
        Upload Fighting Scene
      </h2>

      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onClick={() => document.getElementById("file-input")?.click()}
        className={`border-2 border-dashed rounded-xl p-10 text-center
                    cursor-pointer transition-all duration-200
                    ${
                      dragOver
                        ? "border-primary-400 bg-primary-400/5"
                        : "border-dark-500 hover:border-dark-400"
                    }`}
      >
        <input
          id="file-input"
          type="file"
          accept="video/mp4,video/mpeg,video/quicktime,video/avi"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />

        {selected ? (
          <div className="flex items-center justify-center gap-3">
            <Film size={24} className="text-primary-400" />
            <span className="text-white font-medium truncate max-w-xs">
              {selected.name}
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setSelected(null);
                dispatch(resetUpload());
              }}
              className="text-gray-500 hover:text-red-400 transition-colors"
            >
              <X size={18} />
            </button>
          </div>
        ) : (
          <div>
            <Upload size={40} className="mx-auto text-gray-600 mb-3" />
            <p className="text-gray-400 font-medium">
              Drop your video here or{" "}
              <span className="text-primary-400">browse</span>
            </p>
            <p className="text-gray-600 text-sm mt-1">
              MP4, MOV, AVI, MPEG — max {MAX_SIZE_MB}MB
            </p>
          </div>
        )}
      </div>

      {/* Upload progress bar */}
      {isUploading && (
        <div className="mt-4">
          <div className="flex justify-between text-sm text-gray-400 mb-1">
            <span>Uploading...</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-dark-600 rounded-full h-2">
            <div
              className="bg-primary-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Upload button */}
      {selected && !isUploading && (
        <button onClick={handleUpload} className="btn-primary w-full mt-4">
          Convert to Stickman
        </button>
      )}
    </div>
  );
}
