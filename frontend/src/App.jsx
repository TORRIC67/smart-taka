import { Navigate, Route, Routes } from "react-router-dom";
import { homeFor, useAuth } from "./auth.jsx";
import { useI18n } from "./useI18n";
import Login from "./pages/Login.jsx";
import ForgotPassword from "./pages/ForgotPassword.jsx";
import ChangePassword from "./pages/ChangePassword.jsx";
import SelfRegister from "./pages/SelfRegister.jsx";
import Admin from "./pages/Admin.jsx";
import Driver from "./pages/Driver.jsx";
import Agent from "./pages/Agent.jsx";
import Resident from "./pages/Resident.jsx";

// Only lets the right role in; everyone else is sent to login or to their own page
function Protected({ role, children }) {
  const allowed = Array.isArray(role) ? role : [role];
  const { user, loading } = useAuth();
  const { t } = useI18n();
  if (loading) return <p className="center">{t("loading")}</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (!allowed.includes(user.role)) return <Navigate to={homeFor(user.role)} replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/register" element={<SelfRegister />} />
      <Route path="/change-password" element={<Protected role={["admin", "super_admin", "resident", "driver", "agent"]}><ChangePassword /></Protected>} />
      <Route path="/admin" element={<Protected role={["admin", "super_admin"]}><Admin /></Protected>} />
      <Route path="/driver" element={<Protected role="driver"><Driver /></Protected>} />
      <Route path="/agent" element={<Protected role="agent"><Agent /></Protected>} />
      <Route path="/me" element={<Protected role="resident"><Resident /></Protected>} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
