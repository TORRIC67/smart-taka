import { useCallback, useEffect, useState } from "react";
import FormCard from "../../components/FormCard.jsx";
import { get, post } from "../../api/client";
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

  const load = useCallback(async () => {
    try {
      setRows(await get("/admin/providers"));
    } catch (e) {
      setError(e.message);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

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
              <th>{t("th_trucks")}</th><th>{t("th_revenue_this_month")}</th><th>{t("th_fuel_price")}</th>
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
                <td>TZS {Number(p.fuel_price_tzs_per_liter).toLocaleString()}</td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={6} className="muted">{t("no_providers")}</td></tr>}
          </tbody>
        </table>
      </div>
    </>
  );
}
