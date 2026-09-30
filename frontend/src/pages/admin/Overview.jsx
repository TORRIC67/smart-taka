import { useCallback, useEffect, useState } from "react";
import MapView from "../../components/MapView.jsx";
import { get, patch } from "../../api/client";
import { useAuth } from "../../auth.jsx";
import { useI18n } from "../../useI18n";

const tzs = (n) => `TZS ${Number(n).toLocaleString()}`;

// Every registered customer is always on the map, colored by their current status:
//   registered = grey, billed (SMS sent) = yellow, paid = green
const STATUS_COLOR = { registered: "#9ca3af", billed: "#eab308", paid: "#16a34a" };

export default function Overview() {
  const { t } = useI18n();
  const { user } = useAuth();
  const isSuperAdmin = user?.role === "super_admin";

  const [sum, setSum] = useState(null);
  const [map, setMap] = useState(null);
  const [error, setError] = useState("");

  // A regular admin can see/adjust their own zone's fuel price right here.
  const [myZone, setMyZone] = useState(null);
  const [fuelInput, setFuelInput] = useState("");
  const [editingFuel, setEditingFuel] = useState(false);
  const [fuelBusy, setFuelBusy] = useState(false);
  const [fuelMsg, setFuelMsg] = useState(null);
  useEffect(() => {
    if (!isSuperAdmin) get("/admin/providers/mine").then(setMyZone).catch(() => {});
  }, [isSuperAdmin]);
  async function saveFuel() {
    setFuelBusy(true);
    setFuelMsg(null);
    try {
      const updated = await patch(`/admin/providers/${myZone.id}`, { fuel_price_tzs_per_liter: Number(fuelInput) });
      setMyZone(updated);
      setEditingFuel(false);
      setFuelMsg({ ok: true, text: t("fuel_price_updated") });
    } catch (e) {
      setFuelMsg({ ok: false, text: e.message });
    } finally {
      setFuelBusy(false);
    }
  }

  // A super admin runs no single zone, so the live map (one depot) needs them to pick one.
  // A regular admin's own zone is used automatically - no picker needed.
  const [zones, setZones] = useState([]);
  const [zoneId, setZoneId] = useState(null);

  useEffect(() => {
    if (isSuperAdmin) {
      get("/admin/providers").then((rows) => {
        setZones(rows);
        setZoneId((prev) => prev ?? rows[0]?.id ?? null);
      }).catch((e) => setError(e.message));
    }
  }, [isSuperAdmin]);

  const load = useCallback(async () => {
    try {
      const mapPath = isSuperAdmin ? (zoneId ? `/admin/map?provider_id=${zoneId}` : null) : "/admin/map";
      const [s, m] = await Promise.all([get("/admin/summary"), mapPath ? get(mapPath) : Promise.resolve(null)]);
      setSum(s);
      setMap(m);
      setError("");
    } catch (e) {
      setError(e.message);
    }
  }, [isSuperAdmin, zoneId]);

  // Load now, then refresh every 30 seconds so the map stays "live"
  useEffect(() => {
    if (isSuperAdmin && zoneId == null) return;  // wait for the zone list first
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, [load, isSuperAdmin, zoneId]);

  if (error) return <p className="err">{error}</p>;
  if (!sum || (isSuperAdmin && zones.length === 0)) return <p>{t("loading")}</p>;

  // A customer already collected today turns grey again even though they're still "paid"
  const collectedIds = map ? new Set(map.stops.filter((s) => s.kind === "customer" && s.status === "completed").map((s) => s.id)) : new Set();

  const points = map ? [
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
  ] : [];

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
        <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ margin: 0 }}>{t("live_map_title")}</h3>
          {isSuperAdmin && (
            <select value={zoneId ?? ""} onChange={(e) => setZoneId(Number(e.target.value))} style={{ maxWidth: 220 }}>
              {zones.map((z) => <option key={z.id} value={z.id}>{z.name}</option>)}
            </select>
          )}
        </div>
        {map ? (
          <>
            <MapView points={points} height={420} />
            <div className="legend">
              <span><i className="dot" style={{ background: "#2563eb" }} />{t("legend_depot")}</span>
              <span><i className="dot" style={{ background: "#9ca3af" }} />{t("legend_registered")}</span>
              <span><i className="dot" style={{ background: "#eab308" }} />{t("legend_billed")}</span>
              <span><i className="dot" style={{ background: "#16a34a" }} />{t("legend_paid")}</span>
              <span><i className="dot" style={{ background: "#dc2626" }} />{t("legend_full_bin")}</span>
            </div>
          </>
        ) : <p className="muted">{t("loading")}</p>}
      </div>

      {!isSuperAdmin && myZone && (
        <div className="card">
          <h3>{t("fuel_price_card_title")}</h3>
          {editingFuel ? (
            <div className="row">
              <input type="number" value={fuelInput} onChange={(e) => setFuelInput(e.target.value)} style={{ width: 140 }} />
              <button className="btn" disabled={fuelBusy} onClick={saveFuel}>{t("save")}</button>
              <button className="btn ghost" disabled={fuelBusy} onClick={() => setEditingFuel(false)}>{t("cancel")}</button>
            </div>
          ) : (
            <div className="row" style={{ alignItems: "center" }}>
              <b>TZS {Number(myZone.fuel_price_tzs_per_liter).toLocaleString()} / {t("liter_short")}</b>
              <button className="btn ghost" onClick={() => { setFuelInput(String(myZone.fuel_price_tzs_per_liter)); setEditingFuel(true); }}>{t("edit_btn")}</button>
            </div>
          )}
          {fuelMsg && <p className={fuelMsg.ok ? "ok" : "err"}>{fuelMsg.text}</p>}
        </div>
      )}
    </>
  );
}
