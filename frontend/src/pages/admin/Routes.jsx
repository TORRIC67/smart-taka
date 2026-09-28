import { useCallback, useEffect, useState } from "react";
import RouteView from "../../components/RouteView.jsx";
import { get, post } from "../../api/client";
import { useI18n } from "../../useI18n";

const todayLocal = () => new Date().toLocaleDateString("en-CA"); // YYYY-MM-DD in the user's time zone

export default function RoutesTab() {
  const { t } = useI18n();
  const [day, setDay] = useState(todayLocal());
  const [routes, setRoutes] = useState([]);
  const [source, setSource] = useState(null); // where the distances came from (only known right after generating)
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [busyStop, setBusyStop] = useState(null);

  const load = useCallback(async () => {
    try {
      setError("");
      setRoutes((await get(`/admin/routes?day=${day}`)).routes);
    } catch (e) {
      setError(e.message);
    }
  }, [day]);
  useEffect(() => { load(); }, [load]);

  // Runs the AI route engine: paid customers + full bins -> best order, distance, fuel, cost
  async function generate() {
    setBusy(true);
    setError("");
    try {
      const r = await post(`/admin/routes/generate?day=${day}`);
      setRoutes(r.routes);
      setSource(r.source);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  // Same action the driver does on their phone - here as a backup for the admin.
  // The backend answers with the updated route, which replaces the old one on screen.
  async function markDone(request, stopId = null) {
    setBusyStop(stopId);
    setError("");
    try {
      const { route } = await request();
      setRoutes((prev) => prev.map((r) => (r.id === route.id ? route : r)));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusyStop(null);
    }
  }
  const completeStop = (stopId) => markDone(() => post(`/admin/routes/stops/${stopId}/complete`), stopId);
  const completeRoute = (routeId) =>
    window.confirm(t("confirm_complete_route")) && markDone(() => post(`/admin/routes/${routeId}/complete`));

  return (
    <>
      <div className="row">
        <input type="date" value={day} onChange={(e) => { setDay(e.target.value); setSource(null); }} />
        <button className="btn" disabled={busy} onClick={generate}>
          {busy ? t("calculating") : t("generate_routes_btn")}
        </button>
      </div>
      {source && (
        <p className={source === "OSRM" ? "ok" : "warn"}>
          {source === "OSRM" ? t("source_osrm") : t("source_estimate", { source })}
        </p>
      )}
      {error && <p className="err">{error}</p>}
      {routes.length === 0 && !error && <div className="card muted">{t("no_routes_today")}</div>}
      {routes.map((r) => (
        <RouteView key={r.id} route={r} onComplete={completeStop} busyStop={busyStop} onCompleteRoute={completeRoute} />
      ))}
    </>
  );
}
