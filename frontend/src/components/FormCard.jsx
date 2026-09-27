import { useState } from "react";
import { useI18n } from "../useI18n";

// A generic form. Give it a list of fields and an async onSubmit(values) that returns a success message.
// Used for: register customer, register driver + truck, register bin, self-registration.
export default function FormCard({ title, hint, fields, onSubmit, submitLabel, withLocation = false }) {
  const { t } = useI18n();
  const empty = () => Object.fromEntries(fields.map((f) => [f.name, ""]));
  const [values, setValues] = useState(empty);
  const [msg, setMsg] = useState(null); // {ok, text}
  const [busy, setBusy] = useState(false);
  const set = (name, v) => setValues((prev) => ({ ...prev, [name]: v }));

  // Fill latitude/longitude from the phone/computer GPS
  function fillMyLocation() {
    if (!navigator.geolocation) return setMsg({ ok: false, text: t("geo_unsupported") });
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        set("latitude", pos.coords.latitude.toFixed(6));
        set("longitude", pos.coords.longitude.toFixed(6));
      },
      () => setMsg({ ok: false, text: t("geo_failed") })
    );
  }

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      const payload = {};
      for (const f of fields) {
        const v = values[f.name];
        if (v === "" && !f.required) continue; // optional and empty: leave out
        payload[f.name] = f.type === "number" ? Number(v) : v;
      }
      const text = await onSubmit(payload);
      setMsg({ ok: true, text: text || t("saved_generic") });
      setValues(empty());
    } catch (err) {
      setMsg({ ok: false, text: err.message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card form" onSubmit={submit}>
      <h3>{title}</h3>
      {hint && <p className="muted" style={{ margin: 0 }}>{hint}</p>}
      <div className="grid2">
        {fields.map((f) => (
          <label key={f.name}>
            {f.labelKey ? t(f.labelKey) : f.label}
            <input
              type={f.type || "text"}
              step={f.step}
              required={f.required}
              placeholder={f.placeholder}
              value={values[f.name]}
              onChange={(e) => set(f.name, e.target.value)}
            />
          </label>
        ))}
      </div>
      {withLocation && (
        <button type="button" className="btn ghost" onClick={fillMyLocation}>{t("use_my_location")}</button>
      )}
      <button className="btn" disabled={busy}>{busy ? t("saving") : (submitLabel ?? t("save"))}</button>
      {msg && <p className={msg.ok ? "ok" : "err"} style={{ margin: 0 }}>{msg.text}</p>}
    </form>
  );
}
