import { createSlice } from "@reduxjs/toolkit";
import type { UploadState } from "../../types";

const initialState: UploadState = {
  isUploading: false,
  uploadProgress: 0,
  error: null,
};

const uploadSlice = createSlice({
  name: "upload",
  initialState,
  reducers: {
    uploadStarted(state) {
      state.isUploading = true;
      state.uploadProgress = 0;
      state.error = null;
    },
    uploadProgress(state, action) {
      state.uploadProgress = action.payload;
    },
    uploadFinished(state) {
      state.isUploading = false;
      state.uploadProgress = 100;
    },
    uploadFailed(state, action) {
      state.isUploading = false;
      state.error = action.payload;
    },
    resetUpload(state) {
      state.isUploading = false;
      state.uploadProgress = 0;
      state.error = null;
    },
  },
});

export const {
  uploadStarted,
  uploadProgress,
  uploadFinished,
  uploadFailed,
  resetUpload,
} = uploadSlice.actions;

export default uploadSlice.reducer;
