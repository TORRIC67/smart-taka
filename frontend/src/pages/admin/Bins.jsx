import { useCallback, useEffect, useState } from "react";
import { del, get, patch, post } from "../../api/client";
import { useI18n } from "../../useI18n";

const mapLink = (b) => `https://www.openstreetmap.org/?mlat=${b.latitude}&mlon=${b.longitude}#map=17/${b.latitude}/${b.longitude}`;

// One editable row. A bin's code is fixed (its sensor sends it); only where it is can change.
function EditRow({ bin, onSaved, onCancel }) {
  const { t } = useI18n();
  const [v, setV] = useState({ ward: bin.ward, latitude: bin.latitude, longitude: bin.longitude });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const set = (k, val) => setV((prev) => ({ ...prev, [k]: val }));

  // Handy when standing next to the bin at its new spot
  function fillMyLocation() {
    if (!navigator.geolocation) return setError(t("geo_unsupported"));
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        set("latitude", pos.coords.latitude.toFixed(6));
        set("longitude", pos.coords.longitude.toFixed(6));
      },
      () => setError(t("geo_failed"))
    );
  }

  async function save() {
    setBusy(true);
    setError("");
    try {
      onSaved(await patch(`/admin/bins/${bin.id}`, {
        ward: v.ward, latitude: Number(v.latitude), longitude: Number(v.longitude),
      }));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <tr>
      <td colSpan={6}>
        <p className="muted" style={{ margin: "0 0 8px" }}><b>{bin.code}</b> - {t("bin_edit_hint")}</p>
        <div className="grid2" style={{ marginBottom: 8 }}>
          <label>{t("field_ward")}<input value={v.ward} onChange={(e) => set("ward", e.target.value)} /></label>
          <label>{t("field_latitude")}<input type="number" step="any" value={v.latitude} onChange={(e) => set("latitude", e.target.value)} /></label>
          <label>{t("field_longitude")}<input type="number" step="any" value={v.longitude} onChange={(e) => set("longitude", e.target.value)} /></label>
        </div>
        <div className="row" style={{ margin: 0 }}>
          <button className="btn" disabled={busy} onClick={save}>{busy ? t("saving") : t("save")}</button>
          <button className="btn ghost" disabled={busy} onClick={onCancel}>{t("cancel")}</button>
          <button className="btn ghost" disabled={busy} onClick={fillMyLocation}>{t("use_my_location")}</button>
        </div>
        {error && <p className="err" style={{ margin: "6px 0 0" }}>{error}</p>}
      </td>
    </tr>
  );
}

export default function Bins() {
  const { t } = useI18n();
  const [rows, setRows] = useState([]);
  const [search, setSearch] = useState("");
  const [showRemoved, setShowRemoved] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [note, setNote] = useState(null); // {ok, text}
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setRows(await get(`/admin/bins?include_inactive=${showRemoved}`));
    } catch (e) {
      setNote({ ok: false, text: e.message });
    }
  }, [showRemoved]);
  useEffect(() => { load(); }, [load]);

  // Runs one action (remove / restore), shows the result and reloads the list
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

  const remove = (b) =>
    window.confirm(t("confirm_remove_bin", { code: b.code })) &&
    act(() => del(`/admin/bins/${b.id}`), t("bin_removed_notice", { code: b.code }));
  const restore = (b) => act(() => post(`/admin/bins/${b.id}/reactivate`), t("bin_restored_notice", { code: b.code }));

  function savedEdit(updated) {
    setRows((prev) => prev.map((row) => (row.id === updated.id ? updated : row)));
    setEditingId(null);
    setNote({ ok: true, text: t("bin_saved_notice", { code: updated.code }) });
  }

  const q = search.trim().toLowerCase();
  const shown = rows.filter((b) => !q || `${b.code} ${b.ward}`.toLowerCase().includes(q));
  const activeCount = rows.filter((b) => b.is_active).length;

  return (
    <>
      <div className="stats">
        <div className="stat"><b>{activeCount}</b><span>{t("bins_registered_label")}</span></div>
      </div>

      <div className="row">
        <input placeholder={t("search_placeholder")} value={search} onChange={(e) => setSearch(e.target.value)} />
        <label style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
          <input type="checkbox" checked={showRemoved} onChange={(e) => setShowRemoved(e.target.checked)} />
          {t("show_removed")}
        </label>
      </div>
      {note && <p className={note.ok ? "ok" : "err"}>{note.text}</p>}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>{t("th_code")}</th><th>{t("th_ward")}</th><th>{t("th_location")}</th>
              <th>{t("th_fill")}</th><th>{t("th_status")}</th><th>{t("th_actions")}</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((b) =>
              editingId === b.id ? (
                <EditRow key={b.id} bin={b} onSaved={savedEdit} onCancel={() => setEditingId(null)} />
              ) : (
                <tr key={b.id} style={b.is_active ? undefined : { opacity: 0.55 }}>
                  <td><b>{b.code}</b></td>
                  <td>{b.ward}</td>
                  <td>
                    {Number(b.latitude).toFixed(5)}, {Number(b.longitude).toFixed(5)}{" "}
                    <a href={mapLink(b)} target="_blank" rel="noreferrer">{t("open_map")}</a>
                  </td>
                  <td>{b.fill_level}%</td>
                  <td>
                    {!b.is_active
                      ? <span className="badge">{t("removed_badge")}</span>
                      : <span className={`badge ${b.status === "full" ? "bin" : "paid"}`}>{t(b.status === "full" ? "bin_status_full" : "bin_status_ok")}</span>}
                  </td>
                  <td>
                    <div className="row" style={{ margin: 0 }}>
                      {!b.is_active ? (
                        <button className="btn ghost" disabled={busy} onClick={() => restore(b)}>{t("reactivate_btn")}</button>
                      ) : (
                        <>
                          <button className="btn ghost" disabled={busy} onClick={() => setEditingId(b.id)}>{t("edit_btn")}</button>
                          <button className="btn ghost" style={{ color: "var(--red)", borderColor: "var(--red)" }}
                                  disabled={busy} onClick={() => remove(b)}>{t("remove_btn")}</button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              )
            )}
            {shown.length === 0 && <tr><td colSpan={6} className="muted">{t("no_bins")}</td></tr>}
          </tbody>
        </table>
      </div>
    </>
  );
}
