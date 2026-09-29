import { useCallback, useEffect, useState } from "react";
import { get } from "../../api/client";
import { useAuth } from "../../auth.jsx";
import { useI18n } from "../../useI18n";

const GRANULARITIES = ["month", "quarter", "year"];

export default function Reports() {
  const { t } = useI18n();
  const { user } = useAuth();
  const [granularity, setGranularity] = useState("month");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const isSuperAdmin = user?.role === "super_admin";

  const load = useCallback(async () => {
    setError("");
    try {
      setData(await get(`/admin/reports/collections?granularity=${granularity}`));
    } catch (e) {
      setError(e.message);
    }
  }, [granularity]);
  useEffect(() => { load(); }, [load]);

  const rows = data?.rows || [];
  const max = Math.max(1, ...rows.map((r) => r.amount_tzs));

  return (
    <>
      <div className="row">
        {GRANULARITIES.map((g) => (
          <button key={g} className={`btn ${granularity === g ? "" : "ghost"}`} onClick={() => setGranularity(g)}>
            {t(`granularity_${g}`)}
          </button>
        ))}
      </div>
      {error && <p className="err">{error}</p>}

      <div className="card">
        <h3>{isSuperAdmin ? t("reports_all_zones_title") : t("reports_my_zone_title")}</h3>
        {rows.length === 0 && <p className="muted">{t("no_report_data")}</p>}
        {rows.map((r) => (
          <div key={r.period} className="row" style={{ alignItems: "center", margin: "6px 0" }}>
            <span style={{ width: 90 }}>{r.period}</span>
            <div style={{ flex: 1, background: "var(--line)", borderRadius: 4, overflow: "hidden" }}>
              <div style={{ width: `${(r.amount_tzs / max) * 100}%`, background: "var(--green)", padding: "4px 8px", color: "#fff", whiteSpace: "nowrap", fontSize: 13 }}>
                TZS {r.amount_tzs.toLocaleString()}
              </div>
            </div>
            <span className="muted" style={{ width: 90, textAlign: "right" }}>{t("payments_count_label", { n: r.payments_count })}</span>
          </div>
        ))}
      </div>

      {isSuperAdmin && data?.by_provider && (
        <div className="table-wrap">
          <table>
            <thead><tr><th>{t("th_zone")}</th><th>{t("th_total_collected")}</th></tr></thead>
            <tbody>
              {data.by_provider.map((p) => (
                <tr key={p.provider_id}><td>{p.name}</td><td>TZS {Number(p.total_tzs).toLocaleString()}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
