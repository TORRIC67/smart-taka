import { useCallback, useEffect, useState } from "react";
import MapView from "../../components/MapView.jsx";
import { get } from "../../api/client";
import { useI18n } from "../../useI18n";

const tzs = (n) => `TZS ${Number(n).toLocaleString()}`;

// Every registered customer is always on the map, colored by their current status:
//   registered = grey, billed (SMS sent) = yellow, paid = green
const STATUS_COLOR = { registered: "#9ca3af", billed: "#eab308", paid: "#16a34a" };

export default function Overview() {
  const { t } = useI18n();
  const [sum, setSum] = useState(null);
  const [map, setMap] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const [s, m] = await Promise.all([get("/admin/summary"), get("/admin/map")]);
      setSum(s);
      setMap(m);
      setError("");
    } catch (e) {
      setError(e.message);
    }
  }, []);

  // Load now, then refresh every 30 seconds so the map stays "live"
  useEffect(() => {
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, [load]);

  if (error) return <p className="err">{error}</p>;
  if (!sum || !map) return <p>{t("loading")}</p>;

  // A customer already collected today turns grey again even though they're still "paid"
  const collectedIds = new Set(map.stops.filter((s) => s.kind === "customer" && s.status === "completed").map((s) => s.id));

  const points = [
    { lat: map.depot.lat, lng: map.depot.lng, color: "#2563eb", label: t("legend_depot"), radius: 10 },
    ...map.customers.map((c) => ({
      key: `c${c.id}`,
      lat: c.latitude,
      lng: c.longitude,
      label: `${c.full_name} (${c.ward}) - ${c.payment_status}`,
      color: collectedIds.has(c.id) ? "#9ca3af" : STATUS_COLOR[c.payment_status] || "#9ca3af",
    })),
    // every bin: red when full
    ...map.bins.map((b) => ({
      key: `b${b.id}`, lat: b.latitude, lng: b.longitude, label: `${t("bin_label")} ${b.code}: ${b.fill_level}%`,
      color: b.status === "full" ? "#dc2626" : "#94a3b8", radius: b.status === "full" ? 10 : 6,
    })),
  ];

  return (
    <>
      <div className="stats">
        <div className="stat"><b>{sum.residents_paid} / {sum.residents_total}</b><span>{t("stat_residents")}</span></div>
        <div className="stat"><b>{sum.coverage_percent}%</b><span>{t("stat_coverage")}</span></div>
        <div className="stat"><b>{tzs(sum.revenue_tzs)}</b><span>{t("stat_revenue")}</span></div>
        <div className="stat"><b>{sum.trucks_in_operation} / {sum.trucks_total}</b><span>{t("stat_trucks")}</span></div>
        <div className="stat"><b>{tzs(sum.cost_per_household_tzs)}</b><span>{t("stat_cost_household")}</span></div>
        <div className="stat"><b>{sum.complaints}</b><span>{t("stat_complaints")}</span></div>
      </div>

      <div className="card">
        <h3>{t("live_map_title")}</h3>
        <MapView points={points} height={420} />
        <div className="legend">
          <span><i className="dot" style={{ background: "#2563eb" }} />{t("legend_depot")}</span>
          <span><i className="dot" style={{ background: "#9ca3af" }} />{t("legend_registered")}</span>
          <span><i className="dot" style={{ background: "#eab308" }} />{t("legend_billed")}</span>
          <span><i className="dot" style={{ background: "#16a34a" }} />{t("legend_paid")}</span>
          <span><i className="dot" style={{ background: "#dc2626" }} />{t("legend_full_bin")}</span>
        </div>
      </div>
    </>
  );
}
