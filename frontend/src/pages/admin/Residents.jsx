import { useCallback, useEffect, useState } from "react";
import MakePaymentButton from "../../components/MakePaymentButton.jsx";
import { del, downloadFile, get, patch, post } from "../../api/client";
import { useI18n } from "../../useI18n";

function billingSummary(r, t) {
  const parts = [
    t("billing_sent_count", { n: r.sent }),
    r.failed ? t("billing_failed_count", { n: r.failed }) : null,
    r.already_sent ? t("billing_already_sent", { n: r.already_sent }) : null,
    r.skipped_paid ? t("billing_skipped_paid", { n: r.skipped_paid }) : null,
  ].filter(Boolean);
  let text = parts.join(", ");
  const firstError = r.details.find((d) => !d.ok)?.error;
  if (firstError) text += `. ${t("billing_error_prefix", { err: firstError })}`;
  if (r.sms_provider === "mock") text += ` ${t("billing_mock_note")}`;
  return text;
}

const STATUS_BADGE = { registered: "status_badge_registered", billed: "status_badge_billed", paid: "status_badge_paid" };

// One editable row: full_name, phone, ward, address, latitude, longitude, category, custom fee.
// Kept as its own component so each row's draft state doesn't cause the whole table to re-render.
function EditRow({ customer, onSaved, onCancel }) {
  const { t } = useI18n();
  const [v, setV] = useState({
    full_name: customer.full_name, phone: customer.phone, ward: customer.ward,
    address: customer.address || "", latitude: customer.latitude, longitude: customer.longitude,
    category: customer.category || "residential", monthly_fee_tzs: customer.monthly_fee_tzs || "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const set = (k, val) => setV((prev) => ({ ...prev, [k]: val }));

  async function save() {
    setBusy(true);
    setError("");
    try {
      const updated = await patch(`/admin/customers/${customer.id}`, {
        ...v, latitude: Number(v.latitude), longitude: Number(v.longitude),
        monthly_fee_tzs: v.monthly_fee_tzs === "" ? 0 : Number(v.monthly_fee_tzs), // 0 = clear back to the zone's standard fee
      });
      onSaved(updated);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <tr>
      <td colSpan={6}>
        <div className="grid2" style={{ marginBottom: 8 }}>
          <label>{t("field_full_name")}<input value={v.full_name} onChange={(e) => set("full_name", e.target.value)} /></label>
          <label>{t("field_phone")}<input value={v.phone} onChange={(e) => set("phone", e.target.value)} /></label>
          <label>{t("field_ward")}<input value={v.ward} onChange={(e) => set("ward", e.target.value)} /></label>
          <label>{t("field_address")}<input value={v.address} onChange={(e) => set("address", e.target.value)} /></label>
          <label>{t("field_latitude")}<input type="number" step="any" value={v.latitude} onChange={(e) => set("latitude", e.target.value)} /></label>
          <label>{t("field_longitude")}<input type="number" step="any" value={v.longitude} onChange={(e) => set("longitude", e.target.value)} /></label>
          <label>{t("field_customer_category")}
            <select value={v.category} onChange={(e) => set("category", e.target.value)}>
              <option value="residential">{t("category_residential")}</option>
              <option value="institution">{t("category_institution")}</option>
            </select>
          </label>
          <label>{t("field_custom_fee")}
            <input type="number" placeholder={t("field_custom_fee_placeholder")} value={v.monthly_fee_tzs} onChange={(e) => set("monthly_fee_tzs", e.target.value)} />
          </label>
        </div>
        <div className="row" style={{ margin: 0 }}>
          <button className="btn" disabled={busy} onClick={save}>{busy ? t("saving") : t("save")}</button>
          <button className="btn ghost" disabled={busy} onClick={onCancel}>{t("cancel")}</button>
        </div>
        {error && <p className="err" style={{ margin: "6px 0 0" }}>{error}</p>}
      </td>
    </tr>
  );
}

export default function Residents() {
  const { t } = useI18n();
  const [rows, setRows] = useState([]);
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [showRemoved, setShowRemoved] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [note, setNote] = useState(null); // {ok, text}
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setRows(await get(`/admin/customers?include_inactive=${showRemoved}`));
    } catch (e) {
      setNote({ ok: false, text: e.message });
    }
  }, [showRemoved]);
  useEffect(() => { load(); }, [load]);

  // ids = [one customer] or nothing (= every customer who has not paid this month)
  async function sendBilling(ids) {
    setBusy(true);
    setNote(null);
    try {
      const r = await post("/admin/billing/send", ids ? { customer_ids: ids } : {});
      setNote({ ok: r.failed === 0, text: billingSummary(r, t) });
      await load();
    } catch (e) {
      setNote({ ok: false, text: e.message });
    } finally {
      setBusy(false);
    }
  }

  // Removes a customer: they can no longer log in, and disappear from the map/collection lists.
  // Their payment and complaint history is kept, so this asks for confirmation first.
  async function remove(r) {
    if (!window.confirm(t("confirm_remove", { name: r.full_name }))) return;
    setBusy(true);
    setNote(null);
    try {
      await del(`/admin/customers/${r.id}`);
      setNote({ ok: true, text: t("removed_notice", { name: r.full_name }) });
      await load();
    } catch (e) {
      setNote({ ok: false, text: e.message });
    } finally {
      setBusy(false);
    }
  }

  async function reactivate(r) {
    setBusy(true);
    setNote(null);
    try {
      await post(`/admin/customers/${r.id}/reactivate`);
      setNote({ ok: true, text: t("reactivated_notice", { name: r.full_name }) });
      await load();
    } catch (e) {
      setNote({ ok: false, text: e.message });
    } finally {
      setBusy(false);
    }
  }

  function savedEdit(updated) {
    setRows((prev) => prev.map((row) => (row.id === updated.id ? updated : row)));
    setEditingId(null);
  }

  const q = search.trim().toLowerCase();
  const shown = rows.filter(
    (r) => (!status || r.payment_status === status) && (!q || `${r.full_name} ${r.phone} ${r.ward}`.toLowerCase().includes(q))
  );

  return (
    <>
      <div className="row">
        <input placeholder={t("search_placeholder")} value={search} onChange={(e) => setSearch(e.target.value)} />
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">{t("status_all")}</option>
          <option value="registered">{t("status_badge_registered")}</option>
          <option value="billed">{t("status_badge_billed")}</option>
          <option value="paid">{t("status_badge_paid")}</option>
        </select>
        <button className="btn" disabled={busy} onClick={() => sendBilling(null)}>
          {busy ? t("sending_ellipsis") : t("send_billing_all")}
        </button>
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
              <th>{t("th_name")}</th><th>{t("th_phone")}</th><th>{t("th_ward")}</th>
              <th>{t("th_fee")}</th><th>{t("th_status")}</th><th>{t("th_actions")}</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((r) =>
              editingId === r.id ? (
                <EditRow key={r.id} customer={r} onSaved={savedEdit} onCancel={() => setEditingId(null)} />
              ) : (
                <tr key={r.id} style={r.is_active ? undefined : { opacity: 0.55 }}>
                  <td>{r.full_name}</td>
                  <td>{r.phone}</td>
                  <td>{r.ward}</td>
                  <td>
                    TZS {Number(r.effective_fee_tzs).toLocaleString()}
                    {r.category === "institution" && <span className="badge" style={{ marginLeft: 6 }}>{t("category_institution")}</span>}
                  </td>
                  <td>
                    {r.is_active
                      ? <span className={`badge ${r.payment_status}`}>{t(STATUS_BADGE[r.payment_status])}</span>
                      : <span className="badge">{t("removed_badge")}</span>}
                  </td>
                  <td>
                    <div className="row" style={{ margin: 0 }}>
                      {!r.is_active ? (
                        <button className="btn ghost" disabled={busy} onClick={() => reactivate(r)}>{t("reactivate_btn")}</button>
                      ) : (
                        <>
                          {r.payment_status !== "paid" && (
                            <button className="btn ghost" disabled={busy} onClick={() => sendBilling([r.id])}>{t("send_billing_one")}</button>
                          )}
                          {/* Sends the USSD payment prompt to the customer's phone */}
                          <MakePaymentButton customerId={r.id} alreadyPaid={r.payment_status === "paid"} onPaid={load} />
                          <button className="btn ghost" onClick={() => downloadFile(`/admin/customers/${r.id}/payments/pdf`, `statement-${r.id}.pdf`)}>{t("download_statement_btn")}</button>
                          <button className="btn ghost" disabled={busy} onClick={() => setEditingId(r.id)}>{t("edit_btn")}</button>
                          <button className="btn ghost" style={{ color: "var(--red)", borderColor: "var(--red)" }}
                                  disabled={busy} onClick={() => remove(r)}>{t("remove_btn")}</button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              )
            )}
            {shown.length === 0 && <tr><td colSpan={6} className="muted">{t("no_customers")}</td></tr>}
          </tbody>
        </table>
      </div>
    </>
  );
}
