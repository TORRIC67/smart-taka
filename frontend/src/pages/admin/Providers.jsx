import { useCallback, useEffect, useState } from "react";
import FormCard from "../../components/FormCard.jsx";
import { get, patch, post } from "../../api/client";
import { useI18n } from "../../useI18n";

const providerFields = [
  { name: "name", labelKey: "field_zone_name", required: true },
  { name: "depot_latitude", labelKey: "field_latitude", type: "number", step: "any", required: true },
  { name: "depot_longitude", labelKey: "field_longitude", type: "number", step: "any", required: true },
  { name: "fuel_price_tzs_per_liter", labelKey: "field_fuel_price", type: "number", required: true },
];

export default function Providers() {
  const { t } = useI18n();
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [fuelInput, setFuelInput] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setRows(await get("/admin/providers"));
    } catch (e) {
      setError(e.message);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  function startEdit(p) {
    setEditingId(p.id);
    setFuelInput(String(p.fuel_price_tzs_per_liter));
  }

  async function saveFuel(id) {
    setBusy(true);
    setError("");
    try {
      const updated = await patch(`/admin/providers/${id}`, { fuel_price_tzs_per_liter: Number(fuelInput) });
      setRows((prev) => prev.map((r) => (r.id === id ? updated : r)));
      setEditingId(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <FormCard
        title={t("providers_add_title")}
        hint={t("providers_add_hint")}
        fields={providerFields}
        submitLabel={t("providers_add_submit")}
        withLocation
        latField="depot_latitude"
        lngField="depot_longitude"
        onSubmit={async (v) => {
          const created = await post("/admin/providers", v);
          await load();
          return t("providers_add_success", { name: created.name });
        }}
      />

      {error && <p className="err">{error}</p>}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>{t("th_zone")}</th><th>{t("th_customers")}</th><th>{t("th_bins")}</th>
              <th>{t("th_trucks")}</th><th>{t("th_revenue_this_month")}</th><th>{t("th_fuel_price")}</th><th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.id}>
                <td><b>{p.name}</b></td>
                <td>{p.customers_total}</td>
                <td>{p.bins_total}</td>
                <td>{p.trucks_total}</td>
                <td>TZS {Number(p.revenue_this_month_tzs).toLocaleString()}</td>
                <td>
                  {editingId === p.id ? (
                    <span className="row" style={{ margin: 0, gap: 6 }}>
                      <input type="number" value={fuelInput} onChange={(e) => setFuelInput(e.target.value)} style={{ width: 100 }} />
                      <button className="btn" disabled={busy} onClick={() => saveFuel(p.id)}>{t("save")}</button>
                      <button className="btn ghost" disabled={busy} onClick={() => setEditingId(null)}>{t("cancel")}</button>
                    </span>
                  ) : (
                    <>TZS {Number(p.fuel_price_tzs_per_liter).toLocaleString()}</>
                  )}
                </td>
                <td>{editingId !== p.id && <button className="btn ghost" onClick={() => startEdit(p)}>{t("edit_btn")}</button>}</td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={7} className="muted">{t("no_providers")}</td></tr>}
          </tbody>
        </table>
      </div>
    </>
  );
}
