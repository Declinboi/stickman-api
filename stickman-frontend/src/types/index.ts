export interface User {
  id: string;
  email: string;
  username?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
}

export type JobStatus = "pending" | "processing" | "completed" | "failed";

export interface Job {
  id: string;
  originalFilename: string;
  inputVideoUrl: string;
  outputVideoUrl?: string;
  status: JobStatus;
  progress: number;
  duration?: number;
  errorMessage?: string;
  createdAt: string;
  updatedAt: string;
}

export interface JobsState {
  jobs: Job[];
  currentJob: Job | null;
  isLoading: boolean;
  error: string | null;
}

export interface UploadState {
  isUploading: boolean;
  uploadProgress: number;
  error: string | null;
}
