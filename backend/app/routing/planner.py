"""Turns the day's collection stops into optimized routes and saves them.
Also builds the JSON the admin and driver screens need."""
from datetime import date, datetime, timezone
from typing import List, Tuple
import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.customer import Customer
from app.models.fleet import Driver, Truck
from app.models.route import CollectionStop, Route
from app.models.user import User
from app.models.waste_bin import WasteBin

from .engine import Point, build_matrix, evaluate_route, fetch_route_geometry, solve_tsp, split_for_trucks


class PlanError(Exception):
    """Something the admin can fix (no stops, no trucks...). The message is shown to them."""


def depot_point() -> Point:
    return Point(settings.DEPOT_LATITUDE, settings.DEPOT_LONGITUDE)


def _stop_point(db: Session, stop: CollectionStop) -> Point:
    if stop.customer_id:
        c = db.get(Customer, stop.customer_id)
        return Point(c.latitude, c.longitude)
    b = db.get(WasteBin, stop.bin_id)
    return Point(b.latitude, b.longitude)


def plan_routes(db: Session, day: date) -> Tuple[List[Route], str]:
    """(Re)plan the day. Routes a driver has already started are never touched.
    Stops still pending from earlier days are carried over into today."""
    # 1) throw away routes nobody started yet and free their stops, so new payments/full bins get included
    for r in db.scalars(select(Route).where(Route.route_date == day, Route.status == "planned")).all():
        for s in db.scalars(select(CollectionStop).where(CollectionStop.route_id == r.id)).all():
            s.route_id, s.sequence = None, None
        db.delete(r)
    db.flush()

    stops = db.scalars(
        select(CollectionStop).where(
            CollectionStop.stop_date <= day, CollectionStop.status == "pending", CollectionStop.route_id.is_(None)
        )
    ).all()
    if not stops:
        raise PlanError("There are no collection centers for this day (no one has paid and there are no full bins).")

    busy = set(db.scalars(select(Route.truck_id).where(Route.route_date == day)).all())
    trucks = [t for t in db.scalars(select(Truck).where(Truck.is_active)).all() if t.id not in busy]
    if not trucks:
        raise PlanError("There are no available trucks for this day.")

    depot = depot_point()
    points = [_stop_point(db, s) for s in stops]
    groups = split_for_trucks(points, depot, min(len(trucks), len(stops)))

    routes, sources = [], []
    for truck, group in zip(trucks, groups):
        matrix_points = [depot] + [points[i] for i in group]  # index 0 = depot
        dist, dur, source = build_matrix(matrix_points)
        sources.append(source)
        order = solve_tsp(dist)
        stats = evaluate_route(
            order, dist, dur, truck.fuel_km_per_liter,
            settings.FUEL_PRICE_TZS_PER_LITER, settings.TRIP_FIXED_COST_TZS, settings.STOP_SERVICE_MINUTES,
        )
        visiting_path = [0] + list(order) + [0]
        geometry = fetch_route_geometry([matrix_points[i] for i in visiting_path])
        route = Route(
            truck_id=truck.id, route_date=day, status="planned",
            total_distance_km=stats["distance_km"], est_minutes=stats["minutes"],
            fuel_liters=stats["fuel_liters"], total_cost_tzs=stats["cost_tzs"],
            geometry_json=json.dumps(geometry) if geometry else None,
        )
        db.add(route)
        db.flush()
        for seq, idx in enumerate(order, start=1):
            stop = stops[group[idx - 1]]
            stop.route_id, stop.sequence = route.id, seq
        routes.append(route)

    db.commit()
    return routes, "; ".join(sorted(set(sources)))


# ------------------------------------------------------------------ JSON for the screens
def stop_dict(db: Session, s: CollectionStop) -> dict:
    if s.customer_id:
        c = db.get(Customer, s.customer_id)
        info = {"kind": "customer", "name": c.full_name, "ward": c.ward, "address": c.address,
                "lat": c.latitude, "lng": c.longitude, "phone": c.phone}
    else:
        b = db.get(WasteBin, s.bin_id)
        info = {"kind": "bin", "name": f"Bin {b.code}", "ward": b.ward, "address": None,
                "lat": b.latitude, "lng": b.longitude, "fill_level": b.fill_level}
    info.update(id=s.id, sequence=s.sequence, status=s.status)
    return info


def route_details(db: Session, route: Route) -> dict:
    truck = db.get(Truck, route.truck_id)
    driver = db.get(Driver, truck.driver_id)
    driver_user = db.get(User, driver.user_id)
    stops = db.scalars(
        select(CollectionStop).where(CollectionStop.route_id == route.id).order_by(CollectionStop.sequence)
    ).all()
    items = [stop_dict(db, s) for s in stops]
    return {
        "id": route.id,
        "date": route.route_date.isoformat(),
        "status": route.status,
        "truck_plate": truck.plate_number,
        "driver_name": driver_user.full_name,
        "total_distance_km": route.total_distance_km,
        "est_minutes": route.est_minutes,
        "fuel_liters": route.fuel_liters,
        "total_cost_tzs": route.total_cost_tzs,
        "depot": {"lat": settings.DEPOT_LATITUDE, "lng": settings.DEPOT_LONGITUDE},
        "line": json.loads(route.geometry_json) if route.geometry_json else None,
        "stops": items,
        "completed": sum(1 for i in items if i["status"] == "completed"),
        "total": len(items),
    }


def complete_stop(db: Session, stop: CollectionStop, route: Route) -> None:
    """Mark one stop as done. A full bin is emptied; the route becomes 'done' when nothing is left."""
    if stop.status == "completed":
        return
    stop.status = "completed"
    stop.completed_at = datetime.now(timezone.utc)
    if stop.bin_id:
        b = db.get(WasteBin, stop.bin_id)
        b.fill_level, b.status = 0, "ok"
    db.flush()
    remaining = db.scalar(
        select(func.count(CollectionStop.id)).where(CollectionStop.route_id == route.id, CollectionStop.status == "pending")
    )
    route.status = "done" if remaining == 0 else "in_progress"
