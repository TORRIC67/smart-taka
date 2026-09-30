import { useState } from "react";
import { Link } from "react-router-dom";
import LanguageSwitcher from "../components/LanguageSwitcher.jsx";
import { post } from "../api/client";
import { useI18n } from "../useI18n";

export default function ForgotPassword() {
  const { t } = useI18n();
  const [step, setStep] = useState(1); // 1 = enter phone, 2 = enter code + new password
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [msg, setMsg] = useState(null);
  const [busy, setBusy] = useState(false);

  async function requestCode(e) {
    e.preventDefault();
    setBusy(true); setMsg(null);
    try {
      await post("/auth/forgot-password", { phone });
      setMsg({ ok: true, text: t("otp_sent_notice") });
      setStep(2);
    } catch (err) {
      setMsg({ ok: false, text: err.message });
    } finally {
      setBusy(false);
    }
  }

  async function resetPassword(e) {
    e.preventDefault();
    setMsg(null);
    if (next !== confirm) return setMsg({ ok: false, text: t("passwords_dont_match") });
    setBusy(true);
    try {
      await post("/auth/reset-password", { phone, otp_code: otp, new_password: next });
      setMsg({ ok: true, text: t("password_reset_success") });
      setStep(3);
    } catch (err) {
      setMsg({ ok: false, text: err.message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login">
      <form className="card form login" onSubmit={step === 1 ? requestCode : resetPassword}>
        <div className="row" style={{ justifyContent: "space-between", margin: 0 }}>
          <h2 style={{ color: "var(--green-dark)", margin: 0 }}>{t("forgot_password_title")}</h2>
          <LanguageSwitcher />
        </div>

        {step === 1 && (
          <>
            <p className="muted" style={{ margin: 0 }}>{t("forgot_password_hint")}</p>
            <label>{t("phone_label")}
              <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="0712345678" required />
            </label>
            <button className="btn" disabled={busy}>{busy ? t("saving") : t("send_code_btn")}</button>
          </>
        )}

        {step === 2 && (
          <>
            <label>{t("otp_code_label")}
              <input value={otp} onChange={(e) => setOtp(e.target.value)} maxLength={6} required />
            </label>
            <label>{t("new_password_label")}
              <input type="password" value={next} onChange={(e) => setNext(e.target.value)} minLength={8} required />
            </label>
            <label>{t("confirm_password_label")}
              <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} minLength={8} required />
            </label>
            <button className="btn" disabled={busy}>{busy ? t("saving") : t("reset_password_submit")}</button>
          </>
        )}

        {step === 3 && <p className="ok" style={{ margin: 0 }}>{t("password_reset_success")}</p>}

        {msg && step !== 3 && <p className={msg.ok ? "ok" : "err"} style={{ margin: 0 }}>{msg.text}</p>}
        <p className="muted" style={{ margin: 0 }}><Link to="/login">{t("back_to_login")}</Link></p>
      </form>
    </div>
  );
}
