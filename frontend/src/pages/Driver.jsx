import { useCallback, useEffect, useState } from "react";
import Layout from "../components/Layout.jsx";
import RouteView from "../components/RouteView.jsx";
import { get, post } from "../api/client";
import { useI18n } from "../useI18n";

export default function Driver() {
  const { t } = useI18n();
  const [route, setRoute] = useState(undefined); // undefined = loading, null = no route today
  const [error, setError] = useState("");
  const [busyStop, setBusyStop] = useState(null);

  const load = useCallback(async () => {
    try {
      setError("");
      setRoute((await get("/driver/route")).route);
    } catch (e) {
      setError(e.message);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  // Mark a stop as done. The server answers with the updated route.
  async function complete(stopId) {
    setBusyStop(stopId);
    try {
      setRoute((await post(`/driver/stops/${stopId}/complete`)).route);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusyStop(null);
    }
  }

  return (
    <Layout>
      <div className="row">
        <h2 style={{ margin: 0 }}>{t("todays_route")}</h2>
        <button className="btn ghost" onClick={load}>{t("refresh")}</button>
      </div>
      {error && <p className="err">{error}</p>}
      {route === undefined && !error && <p>{t("loading")}</p>}
      {route === null && <div className="card">{t("no_route_today")}</div>}
      {route && <RouteView route={route} onComplete={complete} busyStop={busyStop} />}
    </Layout>
  );
}
