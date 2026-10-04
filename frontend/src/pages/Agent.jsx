import { useCallback, useEffect, useState } from "react";
import Layout from "../components/Layout.jsx";
import { get, post } from "../api/client";
import { useI18n } from "../useI18n";

export default function Agent() {
  const { t } = useI18n();
  const [wards, setWards] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ full_name: "", phone: "", password: "", ward: "", address: "", latitude: "", longitude: "" });
  const [note, setNote] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const [w, c] = await Promise.all([get("/agent/my-wards"), get("/agent/customers")]);
      setWards(w.wards);
      setCustomers(c);
      setForm((f) => ({ ...f, ward: f.ward || w.wards[0] || "" }));
    } catch (e) {
      setError(e.message);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })); }

  function useMyLocation() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition((pos) => {
      set("latitude", pos.coords.latitude.toFixed(6));
      set("longitude", pos.coords.longitude.toFixed(6));
    });
  }

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setNote(null);
    try {
      await post("/agent/customers", {
        ...form, latitude: Number(form.latitude), longitude: Number(form.longitude),
      });
      setNote({ ok: true, text: t("agent_register_success", { name: form.full_name }) });
      setForm({ full_name: "", phone: "", password: "", ward: wards[0] || "", address: "", latitude: "", longitude: "" });
      load();
    } catch (err) {
      setNote({ ok: false, text: err.message });
    } finally {
      setBusy(false);
    }
  }

  const STATUS_LABEL = { registered: t("status_registered"), billed: t("status_billed"), paid: t("status_paid") };

  return (
    <Layout>
      <div className="card">
        <h2>{t("agent_dashboard_title")}</h2>
        <p className="muted">{t("agent_wards_label")}: <b>{wards.join(", ") || "-"}</b></p>
        <p className="muted">{t("agent_hint")}</p>
      </div>

      {error && <p className="err">{error}</p>}

      <form className="card form" onSubmit={submit}>
        <h3>{t("agent_register_title")}</h3>
        <div className="grid2">
          <label>{t("field_full_name")}<input value={form.full_name} onChange={(e) => set("full_name", e.target.value)} required /></label>
          <label>{t("field_phone")}<input type="tel" placeholder="0712345678" value={form.phone} onChange={(e) => set("phone", e.target.value)} required /></label>
          <label>{t("field_password")}<input type="password" value={form.password} onChange={(e) => set("password", e.target.value)} minLength={8} required /></label>
          <label>{t("field_ward")}
            <select value={form.ward} onChange={(e) => set("ward", e.target.value)} required>
              {wards.map((w) => <option key={w} value={w}>{w}</option>)}
            </select>
          </label>
          <label>{t("field_address")}<input value={form.address} onChange={(e) => set("address", e.target.value)} /></label>
          <label>{t("field_latitude")}<input type="number" step="any" value={form.latitude} onChange={(e) => set("latitude", e.target.value)} required /></label>
          <label>{t("field_longitude")}<input type="number" step="any" value={form.longitude} onChange={(e) => set("longitude", e.target.value)} required /></label>
        </div>
        <div className="row">
          <button className="btn" disabled={busy || wards.length === 0}>{busy ? t("saving") : t("agent_register_submit")}</button>
          <button type="button" className="btn ghost" onClick={useMyLocation}>{t("use_my_location")}</button>
        </div>
        {note && <p className={note.ok ? "ok" : "err"}>{note.text}</p>}
      </form>

      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>{t("th_name")}</th><th>{t("th_phone")}</th><th>{t("th_ward")}</th><th>{t("th_status")}</th></tr>
          </thead>
          <tbody>
            {customers.map((c) => (
              <tr key={c.id}>
                <td>{c.full_name}</td>
                <td>{c.phone}</td>
                <td>{c.ward}</td>
                <td><span className={`badge ${c.payment_status}`}>{STATUS_LABEL[c.payment_status]}</span></td>
              </tr>
            ))}
            {customers.length === 0 && <tr><td colSpan={4} className="muted">{t("agent_no_customers")}</td></tr>}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}
