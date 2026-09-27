import MapView from "./MapView.jsx";
import { useI18n } from "../useI18n";

// Shows one route: totals, map with numbered stops, and the ordered list.
// Pass onComplete(stopId) to show completion buttons (driver screen).
export default function RouteView({ route, onComplete, busyStop }) {
  const { t } = useI18n();
  const stops = route.stops;
  const points = [
    { lat: route.depot.lat, lng: route.depot.lng, color: "#2563eb", label: t("legend_depot"), radius: 10 },
    ...stops.map((s) => ({
      key: s.id,
      lat: s.lat,
      lng: s.lng,
      label: s.sequence, // the number tells the driver the order
      permanent: true,
      color: s.status === "completed" ? "#9ca3af" : s.kind === "bin" ? "#dc2626" : "#16a34a",
    })),
  ];
  // Real road-following line from the backend (OSRM); falls back to straight lines if unavailable
  const line = route.line && route.line.length > 1
    ? route.line
    : [[route.depot.lat, route.depot.lng], ...stops.map((s) => [s.lat, s.lng]), [route.depot.lat, route.depot.lng]];

  return (
    <div className="card">
      <div className="row">
        <h3 style={{ margin: 0 }}>{t("truck_label", { plate: route.truck_plate })}</h3>
        <span className="muted">{t("driver_label")} {route.driver_name}</span>
        <span className={`badge ${route.status === "done" ? "paid" : "billed"}`}>{route.status}</span>
        <span className="muted">{t("stops_label")} {route.completed}/{route.total}</span>
      </div>

      <div className="stats">
        <div className="stat"><b>{route.total_distance_km} km</b><span>{t("distance_label")}</span></div>
        <div className="stat"><b>{route.est_minutes} min</b><span>{t("est_time_label")}</span></div>
        <div className="stat"><b>{route.fuel_liters} L</b><span>{t("fuel_label")}</span></div>
        <div className="stat"><b>TZS {Number(route.total_cost_tzs).toLocaleString()}</b><span>{t("trip_cost_label")}</span></div>
      </div>

      <MapView points={points} line={line} />
      <div className="legend">
        <span><i className="dot" style={{ background: "#2563eb" }} />{t("legend_depot")}</span>
        <span><i className="dot" style={{ background: "#16a34a" }} />{t("legend_household_paid")}</span>
        <span><i className="dot" style={{ background: "#dc2626" }} />{t("legend_bin_full_route")}</span>
        <span><i className="dot" style={{ background: "#9ca3af" }} />{t("legend_completed")}</span>
      </div>

      <ol className="route-list">
        {stops.map((s) => (
          <li key={s.id} className={s.status === "completed" ? "done" : ""}>
            <span className="seq">{s.sequence}</span>
            <div className="grow">
              <strong>{s.name}</strong>{" "}
              <span className={`badge ${s.kind}`}>{s.kind === "bin" ? t("bin_label") : t("household_label")}</span>
              <div className="muted">
                {[s.ward, s.address, s.kind === "bin" ? t("filled_percent", { pct: s.fill_level }) : null].filter(Boolean).join(", ")}
              </div>
            </div>
            {s.status === "completed" ? (
              <span className="ok">{t("completed_status")}</span>
            ) : (
              onComplete && (
                <>
                  <a className="btn ghost" target="_blank" rel="noreferrer"
                     href={`https://www.openstreetmap.org/directions?to=${s.lat}%2C${s.lng}`}>
                    {t("map_link")}
                  </a>
                  <button className="btn" disabled={busyStop === s.id} onClick={() => onComplete(s.id)}>
                    {t("completed_status")}
                  </button>
                </>
              )
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}
