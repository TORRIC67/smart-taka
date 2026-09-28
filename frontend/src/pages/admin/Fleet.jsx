import { useCallback, useEffect, useState } from "react";
import { del, get } from "../../api/client";
import { useI18n } from "../../useI18n";

// Read-only overview of every driver and the truck they drive.
// New drivers/trucks are added from the Register tab.
export default function Fleet() {
  const { t } = useI18n();
  const [rows, setRows] = useState([]);
  const [note, setNote] = useState(null); // {ok, text}
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setRows(await get("/admin/drivers"));
    } catch (e) {
      setNote({ ok: false, text: e.message });
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  async function remove(d) {
    if (!window.confirm(t("confirm_remove_driver", { name: d.full_name, plate: d.plate_number }))) return;
    setBusy(true);
    setNote(null);
    try {
      await del(`/admin/drivers/${d.driver_id}`);
      setNote({ ok: true, text: t("driver_removed_notice", { name: d.full_name }) });
      await load();
    } catch (e) {
      setNote({ ok: false, text: e.message });
    } finally {
      setBusy(false);
    }
  }

  const activeCount = rows.filter((d) => d.is_active).length;

  return (
    <>
      <div className="stats">
        <div className="stat"><b>{activeCount}</b><span>{t("fleet_active_label")}</span></div>
      </div>
      <p className="muted">{t("fleet_register_hint")}</p>
      {note && <p className={note.ok ? "ok" : "err"}>{note.text}</p>}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>{t("th_driver")}</th><th>{t("th_phone")}</th><th>{t("th_truck")}</th>
              <th>{t("th_fuel")}</th><th>{t("th_status")}</th><th>{t("th_actions")}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((d) => (
              <tr key={d.driver_id} style={d.is_active ? undefined : { opacity: 0.55 }}>
                <td>{d.full_name}</td>
                <td>{d.phone}</td>
                <td><b>{d.plate_number}</b></td>
                <td>{d.fuel_km_per_liter}</td>
                <td>{d.is_active ? <span className="badge paid">OK</span> : <span className="badge">{t("removed_badge")}</span>}</td>
                <td>
                  {d.is_active && (
                    <button className="btn ghost" style={{ color: "var(--red)", borderColor: "var(--red)" }}
                            disabled={busy} onClick={() => remove(d)}>{t("remove_btn")}</button>
                  )}
                </td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={6} className="muted">{t("no_drivers")}</td></tr>}
          </tbody>
        </table>
      </div>
    </>
  );
}
