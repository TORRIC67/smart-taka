import { Navigate, Route, Routes } from "react-router-dom";
import { homeFor, useAuth } from "./auth.jsx";
import { useI18n } from "./useI18n";
import Login from "./pages/Login.jsx";
import SelfRegister from "./pages/SelfRegister.jsx";
import Admin from "./pages/Admin.jsx";
import Driver from "./pages/Driver.jsx";
import Resident from "./pages/Resident.jsx";

// Only lets the right role in; everyone else is sent to login or to their own page
function Protected({ role, children }) {
  const { user, loading } = useAuth();
  const { t } = useI18n();
  if (loading) return <p className="center">{t("loading")}</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== role) return <Navigate to={homeFor(user.role)} replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<SelfRegister />} />
      <Route path="/admin" element={<Protected role="admin"><Admin /></Protected>} />
      <Route path="/driver" element={<Protected role="driver"><Driver /></Protected>} />
      <Route path="/me" element={<Protected role="resident"><Resident /></Protected>} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
