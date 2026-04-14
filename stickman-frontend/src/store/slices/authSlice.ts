import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { AuthState } from '../../types';
import api from '../../api/axios';

const initialState: AuthState = {
  user:      localStorage.getItem('user')
               ? JSON.parse(localStorage.getItem('user')!)
               : null,
  token:     localStorage.getItem('token'),
  isLoading: false,
  error:     null,
};

export const register = createAsyncThunk(
  'auth/register',
  async (
    data: { email: string; password: string; username?: string },
    { rejectWithValue },
  ) => {
    try {
      const res = await api.post('/auth/register', data);
      return res.data;
    } catch (err: any) {
      return rejectWithValue(
        err.response?.data?.message ?? 'Registration failed',
      );
    }
  },
);

export const login = createAsyncThunk(
  'auth/login',
  async (
    data: { email: string; password: string },
    { rejectWithValue },
  ) => {
    try {
      const res = await api.post('/auth/login', data);
      return res.data;
    } catch (err: any) {
      return rejectWithValue(
        err.response?.data?.message ?? 'Login failed',
      );
    }
  },
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout(state) {
      state.user  = null;
      state.token = null;
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Register
    builder
      .addCase(register.pending, (state) => {
        state.isLoading = true;
        state.error     = null;
      })
      .addCase(register.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user      = action.payload.user;
        state.token     = action.payload.accessToken;
        localStorage.setItem('token', action.payload.accessToken);
        localStorage.setItem('user', JSON.stringify(action.payload.user));
      })
      .addCase(register.rejected, (state, action) => {
        state.isLoading = false;
        state.error     = action.payload as string;
      });

    // Login
    builder
      .addCase(login.pending, (state) => {
        state.isLoading = true;
        state.error     = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user      = action.payload.user;
        state.token     = action.payload.accessToken;
        localStorage.setItem('token', action.payload.accessToken);
        localStorage.setItem('user', JSON.stringify(action.payload.user));
      })
      .addCase(login.rejected, (state, action) => {
        state.isLoading = false;
        state.error     = action.payload as string;
      });
  },
});

export const { logout, clearError } = authSlice.actions;
export default authSlice.reducer;