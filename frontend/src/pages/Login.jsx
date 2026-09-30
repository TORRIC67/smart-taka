import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { homeFor, useAuth } from "../auth.jsx";
import { useI18n } from "../useI18n";
import LanguageSwitcher from "../components/LanguageSwitcher.jsx";

export default function Login() {
  const { user, login } = useAuth();
  const { t } = useI18n();
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={homeFor(user.role)} replace />; // already logged in

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(phone, password);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card form login" onSubmit={submit}>
      <div className="row" style={{ justifyContent: "space-between", margin: 0 }}>
        <h2 style={{ color: "var(--green-dark)", margin: 0 }}>Smart Taka</h2>
        <LanguageSwitcher />
      </div>
      <label>{t("phone_label")}
        <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="0712345678" required />
      </label>
      <label>{t("password_label")}
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
      </label>
      <button className="btn" disabled={busy}>{busy ? t("logging_in") : t("login_button")}</button>
      {error && <p className="err" style={{ margin: 0 }}>{error}</p>}
      <p className="muted" style={{ margin: 0 }}><Link to="/forgot-password">{t("forgot_password_link")}</Link></p>
      <p className="muted" style={{ margin: 0 }}>{t("no_account")} <Link to="/register">{t("register_here")}</Link></p>
    </form>
  );
}
