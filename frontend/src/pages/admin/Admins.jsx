import { useCallback, useEffect, useState } from "react";
import FormCard from "../../components/FormCard.jsx";
import { del, get, post } from "../../api/client";
import { useI18n } from "../../useI18n";

// Super admin only (the backend enforces this too - a regular admin gets 403 on all of it).
export default function Admins() {
  const { t } = useI18n();
  const [rows, setRows] = useState([]);
  const [providers, setProviders] = useState([]);
  const [note, setNote] = useState(null); // {ok, text}
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const [admins, zones] = await Promise.all([get("/admin/admins"), get("/admin/providers")]);
      setRows(admins);
      setProviders(zones);
    } catch (e) {
      setNote({ ok: false, text: e.message });
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  const adminFields = [
    { name: "full_name", labelKey: "field_full_name", required: true },
    { name: "phone", labelKey: "field_phone", type: "tel", placeholder: "0712345678", required: true },
    { name: "password", labelKey: "field_password", type: "password", required: true },
    {
      name: "provider_id", labelKey: "field_zone", type: "select", numeric: true, required: true,
      placeholder: t("field_zone_placeholder"),
      options: providers.map((p) => ({ value: p.id, label: p.name })),
    },
  ];

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
    window.confirm(t("confirm_remove_admin", { name: a.full_name })) &&
    act(() => del(`/admin/admins/${a.id}`), t("admin_removed_notice", { name: a.full_name }));
  const restore = (a) => act(() => post(`/admin/admins/${a.id}/reactivate`), t("admin_restored_notice", { name: a.full_name }));

  return (
    <>
      <FormCard
        title={t("admins_add_title")}
        hint={t("admins_add_hint")}
        fields={adminFields}
        submitLabel={t("admins_add_submit")}
        onSubmit={async (v) => {
          const created = await post("/admin/admins", v);
          await load();
          return t("admins_add_success", { name: created.full_name });
        }}
      />

      {note && <p className={note.ok ? "ok" : "err"}>{note.text}</p>}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>{t("th_name")}</th><th>{t("th_phone")}</th><th>{t("th_role")}</th><th>{t("th_zone")}</th>
              <th>{t("th_status")}</th><th>{t("th_actions")}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((a) => (
              <tr key={a.id} style={a.is_active ? undefined : { opacity: 0.55 }}>
                <td>{a.full_name}</td>
                <td>{a.phone}</td>
                <td><span className={`badge ${a.role === "super_admin" ? "paid" : "registered"}`}>{t(a.role === "super_admin" ? "role_super_admin" : "role_admin")}</span></td>
                <td>{a.provider_name || "-"}</td>
                <td>{a.is_active ? <span className="badge paid">OK</span> : <span className="badge">{t("removed_badge")}</span>}</td>
                <td>
                  {/* A super admin can never be removed from here (nobody could get back in) */}
                  {a.role === "admin" && (a.is_active ? (
                    <button className="btn ghost" style={{ color: "var(--red)", borderColor: "var(--red)" }}
                            disabled={busy} onClick={() => remove(a)}>{t("remove_btn")}</button>
                  ) : (
                    <button className="btn ghost" disabled={busy} onClick={() => restore(a)}>{t("reactivate_btn")}</button>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
