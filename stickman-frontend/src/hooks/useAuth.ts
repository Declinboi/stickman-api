import { useSelector, useDispatch } from "react-redux";
import type { RootState, AppDispatch } from "../store";
import { logout } from "../store/slices/authSlice";

export function useAuth() {
  const dispatch = useDispatch<AppDispatch>();
  const { user, token, isLoading, error } = useSelector(
    (state: RootState) => state.auth,
  );

  return {
    user,
    token,
    isLoading,
    error,
    isAuthenticated: !!token,
    logout: () => dispatch(logout()),
  };
}
