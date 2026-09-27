import { useEffect } from "react";
import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip, useMap } from "react-leaflet";

// Zooms the map so every point is visible
function FitBounds({ coords }) {
  const map = useMap();
  useEffect(() => {
    if (coords.length) map.fitBounds(coords, { padding: [30, 30], maxZoom: 16 });
  }, [map, JSON.stringify(coords)]); // eslint-disable-line react-hooks/exhaustive-deps
  return null;
}

// points: [{lat, lng, color, label, permanent}]   line: [[lat, lng], ...]
// Uses OpenStreetMap tiles (free, no API key). OSRM is used on the server for road distances.
export default function MapView({ points = [], line = [], height = 380 }) {
  const coords = points.map((p) => [p.lat, p.lng]);
  return (
    <MapContainer center={coords[0] || [-6.79, 39.21]} zoom={12} style={{ height, width: "100%", borderRadius: 8 }}>
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {line.length > 1 && <Polyline positions={line} pathOptions={{ color: "#16a34a", weight: 3, dashArray: "6 6" }} />}
      {points.map((p, i) => (
        <CircleMarker
          key={p.key ?? i}
          center={[p.lat, p.lng]}
          radius={p.radius ?? 9}
          pathOptions={{ color: p.color, fillColor: p.color, fillOpacity: 0.85 }}
        >
          {p.label != null && <Tooltip permanent={!!p.permanent}>{String(p.label)}</Tooltip>}
        </CircleMarker>
      ))}
      <FitBounds coords={coords} />
    </MapContainer>
  );
}
