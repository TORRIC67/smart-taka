"""Route endpoints.
Admin:  POST /admin/routes/generate  -> runs the AI route engine for a day
        GET  /admin/routes           -> routes of a day
Driver: GET  /driver/route           -> my route today (ordered stops, distance, fuel, cost)
        POST /driver/stops/{id}/complete -> mark one stop done
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.fleet import Driver, Truck
from app.models.route import CollectionStop, Route
from app.models.user import Role, User
from app.routing.planner import PlanError, complete_stop, plan_routes, route_details
from app.services.billing import today_tz

admin_router = APIRouter(prefix="/admin/routes", tags=["routes"], dependencies=[Depends(require_roles(Role.ADMIN))])
driver_router = APIRouter(prefix="/driver", tags=["driver"])


@admin_router.post("/generate")
def generate(day: Optional[date] = None, db: Session = Depends(get_db)):
    """Calculates the best order of stops, distance, fuel and cost for each available truck."""
    day = day or today_tz()
    try:
        routes, source = plan_routes(db, day)
    except PlanError as exc:
        db.rollback()
        raise HTTPException(400, str(exc))
    return {"date": day.isoformat(), "source": source, "routes": [route_details(db, r) for r in routes]}


@admin_router.get("")
def list_routes(day: Optional[date] = None, db: Session = Depends(get_db)):
    day = day or today_tz()
    routes = db.scalars(select(Route).where(Route.route_date == day).order_by(Route.id)).all()
    return {"date": day.isoformat(), "routes": [route_details(db, r) for r in routes]}


def _my_driver(db: Session, user: User) -> Driver:
    driver = db.scalar(select(Driver).where(Driver.user_id == user.id))
    if driver is None:
        raise HTTPException(404, "No driver profile for this user")
    return driver


@driver_router.get("/route")
def my_route(
    day: Optional[date] = None,
    user: User = Depends(require_roles(Role.DRIVER)),
    db: Session = Depends(get_db),
):
    driver = _my_driver(db, user)
    truck_ids = db.scalars(select(Truck.id).where(Truck.driver_id == driver.id)).all()
    route = db.scalar(
        select(Route).where(Route.route_date == (day or today_tz()), Route.truck_id.in_(truck_ids)).order_by(Route.id.desc())
    )
    return {"route": route_details(db, route) if route else None}


@driver_router.post("/stops/{stop_id}/complete")
def complete(
    stop_id: int,
    user: User = Depends(require_roles(Role.DRIVER)),
    db: Session = Depends(get_db),
):
    stop = db.get(CollectionStop, stop_id)
    route = db.get(Route, stop.route_id) if stop and stop.route_id else None
    if route is None:
        raise HTTPException(404, "Stop not found")
    if db.get(Truck, route.truck_id).driver_id != _my_driver(db, user).id:
        raise HTTPException(403, "This stop is not on your route")
    complete_stop(db, stop, route)
    db.commit()
    return {"route": route_details(db, route)}
