import { useCallback, useEffect, useState } from "react";
import { del, get, patch, post } from "../../api/client";
import { useAuth } from "../../auth.jsx";
import { useI18n } from "../../useI18n";

function EditWardsRow({ agent, onSaved, onCancel }) {
  const { t } = useI18n();
  const [value, setValue] = useState(agent.wards.join(", "));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function save() {
    setBusy(true);
    setError("");
    try {
      const wards = value.split(",").map((w) => w.trim()).filter(Boolean);
      onSaved(await patch(`/admin/agents/${agent.id}`, { wards }));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <tr>
      <td colSpan={5}>
        <p className="muted" style={{ margin: "0 0 8px" }}><b>{agent.full_name}</b> - {t("agent_wards_edit_hint")}</p>
        <div className="row">
          <input style={{ flex: 1 }} value={value} onChange={(e) => setValue(e.target.value)} placeholder="Sinza, Kinondoni, Mwenge" />
          <button className="btn" disabled={busy} onClick={save}>{t("save")}</button>
          <button className="btn ghost" disabled={busy} onClick={onCancel}>{t("cancel")}</button>
        </div>
        {error && <p className="err" style={{ margin: "6px 0 0" }}>{error}</p>}
      </td>
    </tr>
  );
}

export default function Agents() {
  const { t } = useI18n();
  const { user } = useAuth();
  const isSuperAdmin = user?.role === "super_admin";
  const [rows, setRows] = useState([]);
  const [providers, setProviders] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [note, setNote] = useState(null);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ full_name: "", phone: "", password: "", wards: "", provider_id: "" });

  const load = useCallback(async () => {
    try {
      const tasks = [get("/admin/agents")];
      if (isSuperAdmin) tasks.push(get("/admin/providers"));
      const [agents, zones] = await Promise.all(tasks);
      setRows(agents);
      if (zones) setProviders(zones);
    } catch (e) {
      setNote({ ok: false, text: e.message });
    }
  }, [isSuperAdmin]);
  useEffect(() => { load(); }, [load]);

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })); }

  async function createAgent(e) {
    e.preventDefault();
    setBusy(true);
    setNote(null);
    try {
      const wards = form.wards.split(",").map((w) => w.trim()).filter(Boolean);
      const payload = { ...form, wards };
      if (isSuperAdmin) payload.provider_id = Number(form.provider_id);
      else delete payload.provider_id;
      const created = await post("/admin/agents", payload);
      setNote({ ok: true, text: t("agent_added_success", { name: created.full_name }) });
      setForm({ full_name: "", phone: "", password: "", wards: "", provider_id: "" });
      load();
    } catch (e) {
      setNote({ ok: false, text: e.message });
    } finally {
      setBusy(false);
    }
  }

  async function act(fn, okText) {
    setBusy(true);
    setNote(null);
    try {
      await fn();
      setNote({ ok: true, text: okText });
      await load();
    } catch (e) {
      setNote({ ok: false, text: e.message });
    } finally {
      setBusy(false);
    }
  }
  const remove = (a) =>
    window.confirm(t("confirm_remove_agent", { name: a.full_name })) &&
    act(() => del(`/admin/agents/${a.id}`), t("agent_removed_notice", { name: a.full_name }));
  const restore = (a) => act(() => post(`/admin/agents/${a.id}/reactivate`), t("agent_restored_notice", { name: a.full_name }));

  return (
    <>
      <form className="card form" onSubmit={createAgent}>
        <h3>{t("agents_add_title")}</h3>
        <p className="muted" style={{ marginTop: -8 }}>{t("agents_add_hint")}</p>
        <div className="grid2">
          <label>{t("field_full_name")}<input value={form.full_name} onChange={(e) => set("full_name", e.target.value)} required /></label>
          <label>{t("field_phone")}<input type="tel" placeholder="0712345678" value={form.phone} onChange={(e) => set("phone", e.target.value)} required /></label>
          <label>{t("field_password")}<input type="password" value={form.password} onChange={(e) => set("password", e.target.value)} minLength={8} required /></label>
          <label>{t("agent_wards_field_label")}<input value={form.wards} onChange={(e) => set("wards", e.target.value)} placeholder="Sinza, Kinondoni" required /></label>
          {isSuperAdmin && (
            <label>{t("field_zone")}
              <select value={form.provider_id} onChange={(e) => set("provider_id", e.target.value)} required>
                <option value="" disabled>{t("field_zone_placeholder")}</option>
                {providers.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </label>
          )}
        </div>
        <button className="btn" disabled={busy}>{busy ? t("saving") : t("agents_add_submit")}</button>
      </form>

      {note && <p className={note.ok ? "ok" : "err"}>{note.text}</p>}

      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>{t("th_name")}</th><th>{t("th_phone")}</th><th>{t("agent_wards_column")}</th><th>{t("th_status")}</th><th>{t("th_actions")}</th></tr>
          </thead>
          <tbody>
            {rows.map((a) =>
              editingId === a.id ? (
                <EditWardsRow key={a.id} agent={a} onCancel={() => setEditingId(null)} onSaved={(updated) => { setRows((prev) => prev.map((r) => (r.id === updated.id ? updated : r))); setEditingId(null); }} />
              ) : (
                <tr key={a.id} style={a.is_active ? undefined : { opacity: 0.55 }}>
                  <td>{a.full_name}</td>
                  <td>{a.phone}</td>
                  <td>{a.wards.join(", ")}</td>
                  <td>{a.is_active ? <span className="badge paid">OK</span> : <span className="badge">{t("removed_badge")}</span>}</td>
                  <td>
                    <div className="row" style={{ margin: 0 }}>
                      {a.is_active ? (
                        <>
                          <button className="btn ghost" onClick={() => setEditingId(a.id)}>{t("edit_btn")}</button>
                          <button className="btn ghost" style={{ color: "var(--red)", borderColor: "var(--red)" }} disabled={busy} onClick={() => remove(a)}>{t("remove_btn")}</button>
                        </>
                      ) : (
                        <button className="btn ghost" disabled={busy} onClick={() => restore(a)}>{t("reactivate_btn")}</button>
                      )}
                    </div>
                  </td>
                </tr>
              )
            )}
            {rows.length === 0 && <tr><td colSpan={5} className="muted">{t("agent_no_agents")}</td></tr>}
          </tbody>
        </table>
      </div>
    </>
  );
}
