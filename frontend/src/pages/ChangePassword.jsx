import { useState } from "react";
import { Link } from "react-router-dom";
import { homeFor, useAuth } from "../auth.jsx";
import { post } from "../api/client";
import { useI18n } from "../useI18n";

export default function ChangePassword() {
  const { t } = useI18n();
  const { user } = useAuth();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [msg, setMsg] = useState(null); // {ok, text}
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setMsg(null);
    if (next !== confirm) return setMsg({ ok: false, text: t("passwords_dont_match") });
    setBusy(true);
    try {
      await post("/auth/change-password", { current_password: current, new_password: next });
      setMsg({ ok: true, text: t("password_changed_success") });
      setCurrent(""); setNext(""); setConfirm("");
    } catch (err) {
      setMsg({ ok: false, text: err.message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="center">
      <form className="card form login" onSubmit={submit}>
        <h2 style={{ color: "var(--green-dark)", margin: 0 }}>{t("change_password_title")}</h2>
        <label>{t("current_password_label")}
          <input type="password" value={current} onChange={(e) => setCurrent(e.target.value)} required />
        </label>
        <label>{t("new_password_label")}
          <input type="password" value={next} onChange={(e) => setNext(e.target.value)} minLength={8} required />
        </label>
        <label>{t("confirm_password_label")}
          <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} minLength={8} required />
        </label>
        <button className="btn" disabled={busy}>{busy ? t("saving") : t("change_password_submit")}</button>
        {msg && <p className={msg.ok ? "ok" : "err"} style={{ margin: 0 }}>{msg.text}</p>}
        {user && <p className="muted" style={{ margin: 0 }}><Link to={homeFor(user.role)}>{t("back_to_dashboard")}</Link></p>}
      </form>
    </div>
  );
}
