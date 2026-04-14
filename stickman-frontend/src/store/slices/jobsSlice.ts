import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import type { JobsState, Job } from "../../types";
import api from "../../api/axios";

const initialState: JobsState = {
  jobs: [],
  currentJob: null,
  isLoading: false,
  error: null,
};

export const fetchJobs = createAsyncThunk(
  "jobs/fetchAll",
  async (_, { rejectWithValue }) => {
    try {
      const res = await api.get("/jobs");
      return res.data as Job[];
    } catch (err: any) {
      return rejectWithValue(
        err.response?.data?.message ?? "Failed to fetch jobs",
      );
    }
  },
);

export const fetchJobById = createAsyncThunk(
  "jobs/fetchOne",
  async (id: string, { rejectWithValue }) => {
    try {
      const res = await api.get(`/jobs/${id}`);
      return res.data as Job;
    } catch (err: any) {
      return rejectWithValue(
        err.response?.data?.message ?? "Failed to fetch job",
      );
    }
  },
);

export const deleteJob = createAsyncThunk(
  "jobs/delete",
  async (id: string, { rejectWithValue }) => {
    try {
      await api.delete(`/jobs/${id}`);
      return id;
    } catch (err: any) {
      return rejectWithValue(
        err.response?.data?.message ?? "Failed to delete job",
      );
    }
  },
);

const jobsSlice = createSlice({
  name: "jobs",
  initialState,
  reducers: {
    clearCurrentJob(state) {
      state.currentJob = null;
    },
    updateJobProgress(state, action) {
      const { jobId, progress, status } = action.payload;
      const job = state.jobs.find((j) => j.id === jobId);
      if (job) {
        job.progress = progress;
        job.status = status;
      }
      if (state.currentJob?.id === jobId) {
        state.currentJob.progress = progress;
        state.currentJob.status = status;
      }
    },
    updateJobCompleted(state, action) {
      const { jobId, outputVideoUrl } = action.payload;
      const job = state.jobs.find((j) => j.id === jobId);
      if (job) {
        job.status = "completed";
        job.progress = 100;
        job.outputVideoUrl = outputVideoUrl;
      }
      if (state.currentJob?.id === jobId) {
        state.currentJob.status = "completed";
        state.currentJob.progress = 100;
        state.currentJob.outputVideoUrl = outputVideoUrl;
      }
    },
    updateJobFailed(state, action) {
      const { jobId, errorMessage } = action.payload;
      const job = state.jobs.find((j) => j.id === jobId);
      if (job) {
        job.status = "failed";
        job.errorMessage = errorMessage;
      }
      if (state.currentJob?.id === jobId) {
        state.currentJob.status = "failed";
        state.currentJob.errorMessage = errorMessage;
      }
    },
    addJob(state, action) {
      state.jobs.unshift(action.payload);
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchJobs.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchJobs.fulfilled, (state, action) => {
        state.isLoading = false;
        state.jobs = action.payload;
      })
      .addCase(fetchJobs.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(fetchJobById.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchJobById.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentJob = action.payload;
      })
      .addCase(fetchJobById.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(deleteJob.fulfilled, (state, action) => {
        state.jobs = state.jobs.filter((j) => j.id !== action.payload);
        if (state.currentJob?.id === action.payload) state.currentJob = null;
      });
  },
});

export const {
  clearCurrentJob,
  updateJobProgress,
  updateJobCompleted,
  updateJobFailed,
  addJob,
} = jobsSlice.actions;

export default jobsSlice.reducer;
