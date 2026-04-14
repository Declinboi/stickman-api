import { Link, useNavigate } from "react-router-dom";
import { LogOut, Video, LayoutDashboard } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="bg-dark-800 border-b border-dark-600 px-6 py-4">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <Video className="text-primary-400" size={24} />
          <span className="text-xl font-bold text-white">
            Stick<span className="text-primary-400">Fight</span>
          </span>
        </Link>

        {isAuthenticated && (
          <div className="flex items-center gap-6">
            <Link
              to="/dashboard"
              className="flex items-center gap-2 text-gray-400
                         hover:text-white transition-colors"
            >
              <LayoutDashboard size={18} />
              Dashboard
            </Link>

            <span className="text-gray-500 text-sm">
              {user?.username ?? user?.email}
            </span>

            <button
              onClick={handleLogout}
              className="flex items-center gap-2 text-gray-400
                         hover:text-red-400 transition-colors"
            >
              <LogOut size={18} />
              Logout
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}
