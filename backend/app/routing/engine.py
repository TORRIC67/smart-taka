"""Route optimization engine (pure logic: no database in here).

Steps:
  1. build_matrix()  -> distance (metres) and time (seconds) between every pair of points.
                        Uses the public OSRM Table API, otherwise a straight-line estimate.
  2. solve_tsp()     -> best order to visit all stops, starting and ending at the depot (index 0).
                        Exact search for small routes, nearest-neighbour + 2-opt for bigger ones.
  3. evaluate_route()-> total distance, time, fuel and cost of that order.

Shortest distance is the goal because fuel and cost grow with distance.
"""
import itertools
import logging
import math
from dataclasses import dataclass
from typing import List, Tuple

import httpx

log = logging.getLogger("smarttaka.routing")

OSRM_TABLE_URL = "https://router.project-osrm.org/table/v1/driving"
OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving"
ROAD_FACTOR = 1.35      # straight line -> typical road distance (used only when OSRM is unavailable)
AVG_SPEED_KMH = 25      # slow urban speed of a waste truck (only for the estimate)
EXACT_LIMIT = 8         # up to 8 stops we try every order and get the true optimum


class RoutingError(Exception):
    pass


@dataclass
class Point:
    lat: float
    lng: float


def haversine_m(a: Point, b: Point) -> float:
    """Straight-line distance between two GPS points in metres."""
    r = 6371000.0
    p1, p2 = math.radians(a.lat), math.radians(b.lat)
    dphi, dlmb = p2 - p1, math.radians(b.lng - a.lng)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


# ---------------------------------------------------------------- distance matrix
def _estimate_matrix(points: List[Point]) -> Tuple[List[List[float]], List[List[float]]]:
    n = len(points)
    dist = [[0.0] * n for _ in range(n)]
    dur = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                d = haversine_m(points[i], points[j]) * ROAD_FACTOR
                dist[i][j] = d
                dur[i][j] = d / 1000 / AVG_SPEED_KMH * 3600
    return dist, dur


def _osrm_matrix(points: List[Point]) -> Tuple[List[List[float]], List[List[float]]]:
    n = len(points)
    coordinates = ";".join(f"{point.lng},{point.lat}" for point in points)
    url = f"{OSRM_TABLE_URL}/{coordinates}"
    with httpx.Client(timeout=30) as client:
        resp = client.get(url, params={"annotations": "distance,duration"})
    if resp.status_code >= 400:
        raise RoutingError(f"OSRM {resp.status_code}: {resp.text[:200]}")
    payload = resp.json()
    if payload.get("code") != "Ok":
        raise RoutingError(f"OSRM returned {payload.get('code', 'unknown error')}")
    distances, durations = payload.get("distances"), payload.get("durations")
    if not isinstance(distances, list) or not isinstance(durations, list):
        raise RoutingError("OSRM response did not include distance and duration matrices")
    if len(distances) != n or len(durations) != n:
        raise RoutingError("OSRM returned matrices with the wrong size")
    try:
        dist = [[float(value) for value in row] for row in distances]
        dur = [[float(value) for value in row] for row in durations]
    except (TypeError, ValueError):
        raise RoutingError("OSRM could not find a road route between all stops") from None
    if any(len(row) != n for row in dist + dur):
        raise RoutingError("OSRM returned matrices with the wrong size")
    return dist, dur


def build_matrix(points: List[Point]):
    """Returns (dist_m, dur_s, source), falling back if OSRM is unavailable."""
    try:
        dist, dur = _osrm_matrix(points)
        return dist, dur, "OSRM"
    except (RoutingError, httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        log.warning("OSRM failed, using estimate: %s", exc)
        dist, dur = _estimate_matrix(points)
        return dist, dur, f"estimate (OSRM failed: {exc})"[:300]


# ---------------------------------------------------------------- road-following line for the map
def fetch_route_geometry(ordered_points: List[Point]):
    """The real road-following line (depot -> stops in visiting order -> depot), as [[lat, lng], ...],
    for drawing on the map. Free public OSRM server, same one used above - no API key.
    Returns None if OSRM can't be reached; the map then falls back to straight lines
    between stops. This never affects the distance/fuel/cost numbers, which always come
    from build_matrix() above."""
    if len(ordered_points) < 2:
        return None
    coordinates = ";".join(f"{p.lng},{p.lat}" for p in ordered_points)
    url = f"{OSRM_ROUTE_URL}/{coordinates}"
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(url, params={"overview": "full", "geometries": "geojson"})
        if resp.status_code >= 400:
            return None
        payload = resp.json()
        if payload.get("code") != "Ok":
            return None
        coords = payload["routes"][0]["geometry"]["coordinates"]  # [[lng, lat], ...]
        return [[lat, lng] for lng, lat in coords]
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        log.warning("OSRM route geometry failed, map will use straight lines: %s", exc)
        return None


# ---------------------------------------------------------------- TSP
def tour_length(order: List[int], dist: List[List[float]]) -> float:
    """Distance of depot -> stops in `order` -> depot."""
    path = [0] + order + [0]
    return sum(dist[a][b] for a, b in zip(path, path[1:]))


def solve_tsp(dist: List[List[float]]) -> List[int]:
    """Best order of stops 1..n-1 (0 is the depot). Returns the stop indexes in visiting order."""
    n = len(dist)
    if n <= 2:
        return list(range(1, n))

    # Small route: try every order, so the answer is truly the shortest.
    if n - 1 <= EXACT_LIMIT:
        best = min(itertools.permutations(range(1, n)), key=lambda o: tour_length(list(o), dist))
        return list(best)

    # Bigger route: nearest neighbour first, then 2-opt improves it by un-crossing paths.
    unvisited, tour, cur = set(range(1, n)), [0], 0
    while unvisited:
        cur = min(unvisited, key=lambda j, current=cur: dist[current][j])
        unvisited.remove(cur)
        tour.append(cur)
    tour.append(0)

    improved = True
    while improved:
        improved = False
        for i in range(1, len(tour) - 2):
            for j in range(i + 1, len(tour) - 1):
                a, b, c, d = tour[i - 1], tour[i], tour[j], tour[j + 1]
                if dist[a][c] + dist[b][d] < dist[a][b] + dist[c][d] - 1e-9:
                    tour[i : j + 1] = reversed(tour[i : j + 1])
                    improved = True
    return tour[1:-1]


# ---------------------------------------------------------------- trip numbers
def evaluate_route(order, dist, dur, km_per_liter, fuel_price, fixed_cost, service_minutes):
    path = [0] + list(order) + [0]
    meters = sum(dist[a][b] for a, b in zip(path, path[1:]))
    seconds = sum(dur[a][b] for a, b in zip(path, path[1:]))
    km = meters / 1000
    liters = km / km_per_liter
    return {
        "distance_km": round(km, 2),
        "minutes": round(seconds / 60 + service_minutes * len(order)),
        "fuel_liters": round(liters, 2),
        "cost_tzs": round(liters * fuel_price + fixed_cost),  # fuel + one fixed allowance for the whole trip
    }


def split_for_trucks(points: List[Point], depot: Point, k: int) -> List[List[int]]:
    """With several trucks: sort stops by direction around the depot and cut into k slices.
    Returns lists of indexes into `points`."""
    if k <= 1:
        return [list(range(len(points)))]
    angle = lambda i: math.atan2(points[i].lat - depot.lat, points[i].lng - depot.lng)
    ordered = sorted(range(len(points)), key=angle)
    size = math.ceil(len(ordered) / k)
    return [ordered[i : i + size] for i in range(0, len(ordered), size)]
